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


def test_collaborate_without_upstream_key_returns_502():
    """No API key configured: upstream call must fail cleanly as 502."""
    with TestClient(app) as client:
        resp = client.post(
            "/v1/agents/collaborate", json={"task": "hello", "mode": "solo"}
        )
    assert resp.status_code == 502
