"""Extractor agent: turns raw pasted text into decision-shaped statements."""
from __future__ import annotations

from backend.json_utils import parse_json_response

SYSTEM_PROMPT = """You read raw text from meeting notes, Slack threads, or design docs and pull out decision-shaped statements: things that were decided, chosen, rejected, or committed to, along with why.

For each statement, return an object with these fields:
- claim: the decision or fact, stated plainly, in one sentence.
- rationale: the reason given for it, or an empty string if none was given.
- referenced_entities: a list of system, tool, vendor, or service names the statement depends on (e.g. ["Postgres", "Jenkins"]). Empty list if none.
- confidence: a number from 0 to 1 for how clearly this text states a real decision, not a guess or aside.

Only extract statements that describe an actual decision or its reasoning. Skip small talk, questions, and action items that are not decisions.

Respond with a JSON array of these objects and nothing else. No markdown fences, no commentary. An empty array is fine if there are no decisions in the text."""


class Extractor:
    def run(self, client, raw_text: str) -> list[dict]:
        response = client.complete(SYSTEM_PROMPT, raw_text)
        data = parse_json_response(response)
        if not isinstance(data, list):
            raise ValueError("extractor response was not a JSON array")
        statements = []
        for item in data:
            statements.append(
                {
                    "claim": item["claim"],
                    "rationale": item.get("rationale", ""),
                    "referenced_entities": item.get("referenced_entities", []),
                    "confidence": float(item.get("confidence", 0.5)),
                }
            )
        return statements
