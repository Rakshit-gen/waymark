"""Contradiction checker: compares a new statement against prior statements
that share a referenced entity, and flags any that conflict."""
from __future__ import annotations

from backend.json_utils import parse_json_response

SYSTEM_PROMPT = """You compare one new decision statement against a list of prior statements that reference the same system, tool, or vendor. Decide if any prior statement conflicts with the new one, meaning they cannot both be true or both be followed at the same time.

Do not flag statements that are simply about different aspects of the same entity, or that update each other without conflict (a documented migration is not a contradiction). Only flag a real disagreement.

Respond with a JSON array. Each element is an object with:
- prior_id: the id of the prior statement that conflicts
- explanation: one or two sentences on what conflicts and why

If nothing conflicts, respond with an empty JSON array. No markdown fences, no commentary."""


def _format_prior(prior_statements) -> str:
    lines = []
    for row in prior_statements:
        lines.append(f"id={row['id']}: claim=\"{row['claim']}\" rationale=\"{row['rationale']}\"")
    return "\n".join(lines)


class ContradictionChecker:
    def run(self, client, new_statement: dict, prior_statements: list) -> list[dict]:
        if not prior_statements:
            return []
        user = (
            f'New statement: claim="{new_statement["claim"]}" rationale="{new_statement.get("rationale", "")}"\n\n'
            f"Prior statements referencing the same entity:\n{_format_prior(prior_statements)}"
        )
        response = client.complete(SYSTEM_PROMPT, user)
        data = parse_json_response(response)
        if not isinstance(data, list):
            raise ValueError("contradiction checker response was not a JSON array")
        return [{"prior_id": int(item["prior_id"]), "explanation": item["explanation"]} for item in data]
