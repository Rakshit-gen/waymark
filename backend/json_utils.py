"""Shared helper for parsing JSON out of an LLM text response.

Models often wrap JSON in a markdown fence or add a sentence before or
after it, even when told not to. Try the whole text first, then fall back
to the first JSON value found anywhere in it. Used by every agent.
"""
from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_response(text: str):
    cleaned = _FENCE_RE.sub("", text.strip())
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    decoder = json.JSONDecoder()
    for i, ch in enumerate(cleaned):
        if ch in "[{":
            try:
                value, _ = decoder.raw_decode(cleaned, i)
                return value
            except json.JSONDecodeError:
                continue
    raise ValueError("no JSON found in model response")
