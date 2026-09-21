"""Thin wrapper around the hosted model API (Groq).

One method, complete(system, user) -> str, so agents don't touch the SDK
directly and tests can pass in a fake with the same shape.
"""
from __future__ import annotations

import os

MODEL = "llama-3.3-70b-versatile"


class LLMClient:
    def __init__(self, api_key: str | None = None, model: str = MODEL):
        from groq import Groq  # imported lazily so tests never need the package at import time

        key = api_key or os.environ.get("GROQ_API_KEY")
        if not key:
            raise RuntimeError("GROQ_API_KEY is not set")
        self._client = Groq(api_key=key)
        self.model = model

    def complete(self, system: str, user: str) -> str:
        response = self._client.chat.completions.create(
            model=self.model,
            max_tokens=4096,
            temperature=0,
            messages=[
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
        )
        return response.choices[0].message.content or ""
