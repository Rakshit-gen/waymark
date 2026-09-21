"""Pipeline wiring. Nothing here talks to the agents' internals, it just
calls them in order and persists what comes back. Route handlers call
into this module, not the agents or db directly, so the pipeline shape
lives in one place.
"""
from __future__ import annotations

import re

from backend import db
from backend.agents.contradiction import ContradictionChecker
from backend.agents.extractor import Extractor
from backend.agents.staleness import StalenessChecker
from backend.agents.synthesizer import Synthesizer

_extractor = Extractor()
_contradiction_checker = ContradictionChecker()
_staleness_checker = StalenessChecker()
_synthesizer = Synthesizer()

_WORD_RE = re.compile(r"[A-Za-z0-9]+")
# Filler words that would match nearly every statement and drown the real terms.
_FILLER = {"why", "is", "are", "was", "the", "we", "our", "did", "do", "does", "a", "an", "of", "to",
           "in", "on", "for", "this", "that", "way", "how", "what", "it", "and", "or", "so", "not"}


def add_source(conn, client, label: str, raw_text: str) -> list[dict]:
    """Runs Extractor, then Contradiction checker and Staleness checker for
    each new statement. Returns the new statements with their ids and any
    contradictions or staleness flags attached."""
    source_id = db.insert_source(conn, label, raw_text)
    extracted = _extractor.run(client, raw_text)

    results = []
    for item in extracted:
        statement_id = db.insert_statement(
            conn,
            source_id,
            item["claim"],
            item["rationale"],
            item["referenced_entities"],
            item["confidence"],
        )

        prior_by_id: dict[int, object] = {}
        for entity in item["referenced_entities"]:
            for row in db.statements_referencing(conn, entity, exclude_id=statement_id):
                prior_by_id[row["id"]] = row
        prior_statements = list(prior_by_id.values())

        contradictions = []
        if prior_statements:
            found = _contradiction_checker.run(client, item, prior_statements)
            for c in found:
                db.insert_contradiction(conn, statement_id, c["prior_id"], c["explanation"])
                contradictions.append(c)

        retired_names = db.retired_entity_names(conn)
        staleness = _staleness_checker.run(item["referenced_entities"], retired_names)
        for flag in staleness:
            db.insert_staleness_flag(conn, statement_id, flag["entity"], flag["reason"])

        results.append(
            {
                "id": statement_id,
                "source_id": source_id,
                **item,
                "contradictions": contradictions,
                "staleness_flags": staleness,
            }
        )
    return results


def _build_fts_query(question: str) -> str | None:
    words = _WORD_RE.findall(question)
    words = [w for w in words if len(w) >= 2 and w.lower() not in _FILLER]
    if not words:
        return None
    return " OR ".join(f'"{w}"' for w in words)


def ask(conn, client, question: str) -> dict:
    """Runs the Synthesizer against statements matched via FTS5."""
    query = _build_fts_query(question)
    if query is None:
        return {"answer": "Ask a more specific question, there's nothing to search on.", "cited_ids": [], "contested": False}

    rows = db.search_statements(conn, query)
    statements = []
    for row in rows:
        contested = len(db.contradictions_for_statement(conn, row["id"])) > 0
        statements.append(
            {"id": row["id"], "claim": row["claim"], "rationale": row["rationale"], "contested": contested}
        )

    return _synthesizer.run(client, question, statements)
