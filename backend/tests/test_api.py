import json

from fastapi.testclient import TestClient

from backend import db, main
from backend.tests.fake_llm_client import FakeLLMClient


def make_client(tmp_path, monkeypatch, responses):
    path = tmp_path / "test.db"
    conn = db.get_connection(path)
    db.init_db(conn)
    conn.close()
    monkeypatch.setattr(main, "get_conn", lambda: db.get_connection(path))
    fake = FakeLLMClient(responses)
    main.app.dependency_overrides[main.get_llm_client] = lambda: fake
    return TestClient(main.app)


def teardown_function():
    main.app.dependency_overrides.clear()


def test_full_flow_through_http(tmp_path, monkeypatch):
    first = json.dumps([{"claim": "We use Jenkins for CI", "rationale": "legacy", "referenced_entities": ["Jenkins"], "confidence": 0.8}])
    second = json.dumps([{"claim": "CI runs on GitHub Actions", "rationale": "simpler", "referenced_entities": ["Jenkins"], "confidence": 0.9}])
    conflict = json.dumps([{"prior_id": 1, "explanation": "CI cannot run on both"}])
    answer = json.dumps({"answer": "CI moved (see #2)", "cited_ids": [2], "contested": True})
    client = make_client(tmp_path, monkeypatch, [first, second, conflict, answer])

    assert client.post("/entities", json={"name": "Jenkins", "status": "retired"}).status_code == 200
    assert client.post("/entities", json={"name": "Jenkins", "status": "bogus"}).status_code == 400
    assert client.get("/entities").json()["entities"][0]["status"] == "retired"

    client.post("/sources", json={"label": "a", "raw_text": "text a"})
    r = client.post("/sources", json={"label": "b", "raw_text": "text b"})
    assert r.json()["statements"][0]["contradictions"][0]["prior_id"] == 1

    statements = client.get("/statements").json()["statements"]
    assert [s["id"] for s in statements] == [2, 1]
    assert statements[0]["source_label"] == "b"
    assert statements[0]["contradictions"] and statements[0]["staleness_flags"]

    contradictions = client.get("/contradictions").json()["contradictions"]
    assert contradictions[0]["statement_b_claim"] == "We use Jenkins for CI"

    result = client.get("/ask", params={"q": "why github actions"}).json()
    assert result["cited_ids"] == [2] and result["contested"] is True


def test_missing_api_key_is_503(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch, [])
    main.app.dependency_overrides.clear()
    monkeypatch.delenv("GROQ_API_KEY", raising=False)
    assert client.get("/ask", params={"q": "anything"}).status_code == 503


def test_unreadable_model_output_is_502(tmp_path, monkeypatch):
    client = make_client(tmp_path, monkeypatch, ["this is not json"])
    r = client.post("/sources", json={"label": "a", "raw_text": "text"})
    assert r.status_code == 502
    assert "could not read" in r.json()["detail"]
