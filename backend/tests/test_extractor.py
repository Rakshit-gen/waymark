import json

from backend.agents.extractor import Extractor
from backend.tests.fake_llm_client import FakeLLMClient


def test_extractor_parses_statements_from_json_response():
    scripted = json.dumps(
        [
            {
                "claim": "We use Postgres for the primary datastore",
                "rationale": "it handles our write volume and the team knows it well",
                "referenced_entities": ["Postgres"],
                "confidence": 0.9,
            }
        ]
    )
    client = FakeLLMClient([scripted])
    statements = Extractor().run(client, "some meeting notes")

    assert len(statements) == 1
    s = statements[0]
    assert s["claim"] == "We use Postgres for the primary datastore"
    assert s["referenced_entities"] == ["Postgres"]
    assert s["confidence"] == 0.9


def test_extractor_handles_markdown_fenced_response():
    scripted = "```json\n[]\n```"
    client = FakeLLMClient([scripted])
    statements = Extractor().run(client, "no decisions here")
    assert statements == []


def test_extractor_fills_defaults_for_missing_fields():
    scripted = json.dumps([{"claim": "We dropped vendor X"}])
    client = FakeLLMClient([scripted])
    statements = Extractor().run(client, "text")
    assert statements[0]["rationale"] == ""
    assert statements[0]["referenced_entities"] == []
    assert statements[0]["confidence"] == 0.5
