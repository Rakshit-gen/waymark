"""Shared helper for parsing JSON out of an LLM text response.

Models sometimes wrap JSON in a markdown code fence even when told not to,
so strip that before parsing. Used by every agent.
"""
from __future__ import annotations

import json
import re

_FENCE_RE = re.compile(r"^```(?:json)?\s*|\s*```$", re.MULTILINE)


def parse_json_response(text: str):
    cleaned = _FENCE_RE.sub("", text.strip())
    return json.loads(cleaned)
