from backend.tests.fake_llm_client import FakeLLMClient


def test_fake_client_returns_scripted_responses_in_order():
    client = FakeLLMClient(["first", "second"])
    assert client.complete("sys", "a") == "first"
    assert client.complete("sys", "b") == "second"
    assert client.calls == [("sys", "a"), ("sys", "b")]


def test_fake_client_raises_when_exhausted():
    client = FakeLLMClient([])
    try:
        client.complete("sys", "a")
        assert False, "expected AssertionError"
    except AssertionError:
        pass
