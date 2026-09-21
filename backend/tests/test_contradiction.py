import json

from backend.agents.contradiction import ContradictionChecker
from backend.tests.fake_llm_client import FakeLLMClient


class Row(dict):
    """Mimics sqlite3.Row's __getitem__ access for a plain dict in tests."""


def test_no_prior_statements_short_circuits_without_calling_llm():
    client = FakeLLMClient([])
    result = ContradictionChecker().run(client, {"claim": "x"}, [])
    assert result == []
    assert client.calls == []


def test_flags_conflict_from_scripted_response():
    scripted = json.dumps([{"prior_id": 7, "explanation": "one says weekly, the other says never"}])
    client = FakeLLMClient([scripted])
    prior = [Row(id=7, claim="We ship on Fridays", rationale="team likes a clean week")]
    new_statement = {"claim": "We never ship on Fridays", "rationale": "too risky"}

    result = ContradictionChecker().run(client, new_statement, prior)

    assert result == [{"prior_id": 7, "explanation": "one says weekly, the other says never"}]


def test_empty_array_means_no_contradiction():
    client = FakeLLMClient(["[]"])
    prior = [Row(id=1, claim="We use Postgres", rationale="scales fine")]
    result = ContradictionChecker().run(client, {"claim": "We use Postgres for analytics too"}, prior)
    assert result == []
