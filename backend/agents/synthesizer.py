"""Synthesizer: answers a free text question using stored statements found
via full text search, citing which statements it drew from."""
from __future__ import annotations

from backend.json_utils import parse_json_response

SYSTEM_PROMPT = """You answer a question about why a decision was made, using only the statements given to you. Each statement has an id, a claim, a rationale, and whether it is contested (has an unresolved contradiction on record).

Write a short, direct answer grounded only in the statements provided. Do not invent reasoning that is not in them. If a statement you rely on is contested, say so plainly in the answer rather than presenting it as settled fact. If none of the statements actually answer the question, say that plainly instead of guessing.

Respond with a JSON object with these fields:
- answer: the answer text, citing statement ids inline like (see #3)
- cited_ids: a list of the statement ids you actually drew from
- contested: true if any statement you cited is contested, false otherwise

No markdown fences, no commentary outside the JSON object."""


def _format_statements(statements: list[dict]) -> str:
    lines = []
    for s in statements:
        contested = "contested" if s["contested"] else "not contested"
        lines.append(f'id={s["id"]} ({contested}): claim="{s["claim"]}" rationale="{s["rationale"]}"')
    return "\n".join(lines)


class Synthesizer:
    def run(self, client, question: str, statements: list[dict]) -> dict:
        if not statements:
            return {"answer": "No recorded statements match this question yet.", "cited_ids": [], "contested": False}
        user = f"Question: {question}\n\nStatements:\n{_format_statements(statements)}"
        response = client.complete(SYSTEM_PROMPT, user)
        data = parse_json_response(response)
        return {
            "answer": data["answer"],
            "cited_ids": [int(i) for i in data.get("cited_ids", [])],
            "contested": bool(data.get("contested", False)),
        }
