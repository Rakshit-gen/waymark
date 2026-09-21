"""Staleness checker: flags when a statement references a retired entity.

This is a plain set membership check against entity_registry, not a
judgment call, so it does not go through the LLM. Kept as its own class
so the orchestrator calls it the same way it calls the other agents.
"""
from __future__ import annotations


class StalenessChecker:
    def run(self, referenced_entities: list[str], retired_names: set[str]) -> list[dict]:
        flags = []
        for entity in referenced_entities:
            if entity in retired_names:
                flags.append({"entity": entity, "reason": f"{entity} is marked retired in the entity registry"})
        return flags
