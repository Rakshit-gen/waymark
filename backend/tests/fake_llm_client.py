"""Test double for LLMClient. Same shape (complete(system, user) -> str),
scripted with a queue of responses so tests control exactly what each
pipeline step sees, no mocking framework needed.
"""
from __future__ import annotations


class FakeLLMClient:
    def __init__(self, responses: list[str]):
        self._responses = list(responses)
        self.calls: list[tuple[str, str]] = []

    def complete(self, system: str, user: str) -> str:
        self.calls.append((system, user))
        if not self._responses:
            raise AssertionError("FakeLLMClient ran out of scripted responses")
        return self._responses.pop(0)
