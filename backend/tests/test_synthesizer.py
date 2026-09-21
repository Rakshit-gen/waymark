import json

from backend.agents.synthesizer import Synthesizer
from backend.tests.fake_llm_client import FakeLLMClient


def test_no_statements_returns_default_without_calling_llm():
    client = FakeLLMClient([])
    result = Synthesizer().run(client, "why postgres?", [])
    assert result["cited_ids"] == []
    assert result["contested"] is False
    assert client.calls == []


def test_synthesizer_parses_answer_and_cites():
    scripted = json.dumps(
        {"answer": "We use Postgres because it scales (see #1)", "cited_ids": [1], "contested": False}
    )
    client = FakeLLMClient([scripted])
    statements = [{"id": 1, "claim": "We use Postgres", "rationale": "it scales", "contested": False}]
    result = Synthesizer().run(client, "why postgres?", statements)
    assert result["answer"].startswith("We use Postgres")
    assert result["cited_ids"] == [1]
    assert result["contested"] is False


def test_synthesizer_flags_contested_record():
    scripted = json.dumps({"answer": "This is contested (see #2)", "cited_ids": [2], "contested": True})
    client = FakeLLMClient([scripted])
    statements = [{"id": 2, "claim": "We ship on Fridays", "rationale": "clean week", "contested": True}]
    result = Synthesizer().run(client, "do we ship on fridays?", statements)
    assert result["contested"] is True
