"""Tests for /v1/agents endpoints (providers listing + collaborate)."""
from __future__ import annotations

import os

os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("LOCAL_API_KEY", "")

from fastapi.testclient import TestClient

from flutter_agent.collaboration import AgentTeam
from flutter_agent.main import app


def test_list_providers_default_only():
    with TestClient(app) as client:
        resp = client.get("/v1/agents/providers")
    assert resp.status_code == 200, resp.text
    data = resp.json()
    names = [p["name"] for p in data["providers"]]
    assert "default" in names
    for p in data["providers"]:
        assert "api_key" not in p


def test_collaborate_rejects_bad_mode():
    with TestClient(app) as client:
        resp = client.post("/v1/agents/collaborate", json={"task": "t", "mode": "swarm"})
    assert resp.status_code == 422


def test_collaborate_solo_with_stubbed_team():
    class _StubTeam:
        registry = None

        async def run(self, task, mode, agents=None, max_rounds=None):
            from flutter_agent.collaboration import CollaborationResult, TranscriptEntry

            return CollaborationResult(
                mode=mode,
                final_answer=f"echo:{task}",
                rounds_used=1,
                transcript=[
                    TranscriptEntry(agent="solo", role="proposer", round=1, content="x")
                ],
            )

    with TestClient(app) as client:
        original: AgentTeam = app.state.agent_team
        app.state.agent_team = _StubTeam()
        try:
            resp = client.post(
                "/v1/agents/collaborate", json={"task": "hello", "mode": "solo"}
            )
        finally:
            app.state.agent_team = original
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["final_answer"] == "echo:hello"
    assert data["mode"] == "solo"
    assert len(data["transcript"]) == 1


def test_collaborate_ground_prepends_retrieved_sources(tmp_path):
    from flutter_agent.vector_store import VectorStore, docs_from_memory

    captured = {}

    class _StubTeam:
        registry = None

        async def run(self, task, mode, agents=None, max_rounds=None):
            from flutter_agent.collaboration import CollaborationResult

            captured["task"] = task
            return CollaborationResult(mode=mode, final_answer="ok", rounds_used=1)

    store = VectorStore(tmp_path / "g.sqlite3")
    store.add(docs_from_memory("note-g", "约定", "离线同步采用 增量队列 与 冲突合并 策略"))
    with TestClient(app) as client:
        original = app.state.agent_team
        app.state.agent_team = _StubTeam()
        app.state.vector_store = store
        try:
            resp = client.post(
                "/v1/agents/collaborate",
                json={"task": "离线同步怎么做 冲突合并", "mode": "solo", "ground": True},
            )
        finally:
            app.state.agent_team = original
            store.close()
            del app.state.vector_store
    assert resp.status_code == 200, resp.text
    assert "memory:note-g" in captured["task"]
    assert captured["task"].endswith("离线同步怎么做 冲突合并")


def test_list_collaborations_reads_audit_log(tmp_path):
    import json

    from flutter_agent.config import Settings
    from flutter_agent.deps import get_settings

    log = tmp_path / "collab.jsonl"
    log.write_text(
        json.dumps({"mode": "solo", "winner": None}) + "\n"
        + json.dumps({"mode": "peer_review", "winner": "alpha"}) + "\n",
        encoding="utf-8",
    )
    app.dependency_overrides[get_settings] = lambda: Settings(
        deepseek_api_key="", local_api_key="", collab_log_path=str(log)
    )
    try:
        with TestClient(app) as client:
            resp = client.get("/v1/agents/collaborations", params={"limit": 1})
    finally:
        app.dependency_overrides.pop(get_settings, None)
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["enabled"] is True
    assert len(data["records"]) == 1
    assert data["records"][0]["mode"] == "peer_review"


def test_list_collaborations_disabled(tmp_path):
    from flutter_agent.config import Settings
    from flutter_agent.deps import get_settings

    app.dependency_overrides[get_settings] = lambda: Settings(
        deepseek_api_key="", local_api_key="", collab_log_path=""
    )
    try:
        with TestClient(app) as client:
            resp = client.get("/v1/agents/collaborations")
    finally:
        app.dependency_overrides.pop(get_settings, None)
    assert resp.status_code == 200, resp.text
    assert resp.json() == {"enabled": False, "records": []}


def test_collaborate_without_upstream_key_returns_502():
    """No API key configured: upstream call must fail cleanly as 502."""
    with TestClient(app) as client:
        resp = client.post(
            "/v1/agents/collaborate", json={"task": "hello", "mode": "solo"}
        )
    assert resp.status_code == 502
