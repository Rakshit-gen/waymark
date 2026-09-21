"""Thin wrapper around the Anthropic API.

One method, complete(system, user) -> str, so agents don't touch the SDK
directly and tests can pass in a fake with the same shape.
"""
from __future__ import annotations

import os

DEFAULT_MODEL = os.environ.get("ANTHROPIC_MODEL", "claude-opus-5")


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        import anthropic  # imported lazily so tests never need the package installed at import time

        key = api_key or os.environ.get("ANTHROPIC_API_KEY")
        if not key:
            raise RuntimeError("ANTHROPIC_API_KEY is not set")
        self._client = anthropic.Anthropic(api_key=key)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.messages.create(
            model=self.model,
            max_tokens=4096,
            system=system,
            messages=[{"role": "user", "content": user}],
        )
        for block in response.content:
            if block.type == "text":
                return block.text
        return ""
