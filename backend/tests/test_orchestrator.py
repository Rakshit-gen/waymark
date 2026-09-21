import json

from backend import db, orchestrator
from backend.tests.fake_llm_client import FakeLLMClient


def make_conn():
    conn = db.get_connection(":memory:")
    db.init_db(conn)
    return conn


def test_add_source_pipeline_lands_statement_contradiction_and_staleness():
    conn = make_conn()
    db.upsert_entity(conn, "Postgres", "active")
    db.upsert_entity(conn, "Jenkins", "retired")

    first_extraction = json.dumps(
        [
            {
                "claim": "We use Postgres for the primary store",
                "rationale": "handles our write volume",
                "referenced_entities": ["Postgres"],
                "confidence": 0.9,
            }
        ]
    )
    second_extraction = json.dumps(
        [
            {
                "claim": "We migrated off Postgres to MySQL",
                "rationale": "cost",
                "referenced_entities": ["Postgres", "Jenkins"],
                "confidence": 0.85,
            }
        ]
    )
    contradiction_response = json.dumps(
        [{"prior_id": 1, "explanation": "one says we use Postgres, the other says we migrated off it"}]
    )

    client = FakeLLMClient([first_extraction, second_extraction, contradiction_response])

    first_results = orchestrator.add_source(conn, client, "meeting notes A", "raw text A")
    assert len(first_results) == 1
    first_id = first_results[0]["id"]
    assert first_results[0]["contradictions"] == []
    assert first_results[0]["staleness_flags"] == []

    second_results = orchestrator.add_source(conn, client, "meeting notes B", "raw text B")
    assert len(second_results) == 1
    second = second_results[0]

    assert second["contradictions"] == [
        {"prior_id": first_id, "explanation": "one says we use Postgres, the other says we migrated off it"}
    ]
    assert len(second["staleness_flags"]) == 1
    assert second["staleness_flags"][0]["entity"] == "Jenkins"

    all_statements = db.all_statements(conn)
    assert len(all_statements) == 2

    contradictions = db.all_contradictions(conn)
    assert len(contradictions) == 1
    assert contradictions[0]["statement_a_id"] == second["id"]
    assert contradictions[0]["statement_b_id"] == first_id

    flags = db.staleness_for_statement(conn, second["id"])
    assert len(flags) == 1
    assert flags[0]["entity"] == "Jenkins"


def test_ask_runs_synthesizer_against_matching_statements():
    conn = make_conn()
    extraction = json.dumps(
        [
            {
                "claim": "We use Postgres for the primary store",
                "rationale": "handles our write volume",
                "referenced_entities": ["Postgres"],
                "confidence": 0.9,
            }
        ]
    )
    answer = json.dumps({"answer": "Postgres was chosen for write volume (see #1)", "cited_ids": [1], "contested": False})
    client = FakeLLMClient([extraction, answer])

    orchestrator.add_source(conn, client, "notes", "raw text")
    result = orchestrator.ask(conn, client, "why do we use postgres")

    assert result["cited_ids"] == [1]
    assert result["contested"] is False
    assert "Postgres" in result["answer"]


def test_ask_with_no_matches_skips_llm_call():
    conn = make_conn()
    client = FakeLLMClient([])
    result = orchestrator.ask(conn, client, "anything at all")
    assert result["cited_ids"] == []
