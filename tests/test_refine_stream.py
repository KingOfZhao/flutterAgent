"""Tests for pipeline progress events and the /v1/refine/stream SSE endpoint.

Verifies:
- pipeline.run(progress=...) emits pipeline_start / stage_start / stage_complete
- cache hits emit a cache_hit event
- a failing progress callback never breaks the run
- the SSE route streams events and terminates with a done event + [DONE]
"""
from __future__ import annotations

import json

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient

from flutter_agent.cache import RunCache
from flutter_agent.config import Settings
from flutter_agent.pipeline import RefinementPipeline
from flutter_agent.routes import refine
from flutter_agent.run_store import RunStore
from flutter_agent.schemas import Platform, RefineRequest, Stage
from flutter_agent.skill_loader import SkillRegistry

_MOCK_CLASSIFY = json.dumps({
    "recommended_skills": ["flutter-mobile"],
    "platforms": ["mobile"],
    "complexity": "S",
})

_MOCK_MARKDOWN = "# PRD\n\n一句话需求的精炼结果。"


class _MockClient:
    def __init__(self):
        self.calls = 0

    async def chat(self, messages, *, model=None, temperature=None,
                   max_tokens=None, response_format=None):
        self.calls += 1
        text = _MOCK_CLASSIFY if response_format else _MOCK_MARKDOWN
        return {
            "choices": [{"message": {"content": text}}],
            "usage": {"prompt_tokens": 100, "completion_tokens": 50,
                      "total_tokens": 150},
        }

    @staticmethod
    def extract_text(completion):
        return completion["choices"][0]["message"]["content"] or ""

    @staticmethod
    def extract_usage(completion):
        u = completion.get("usage", {})
        return {
            "prompt_tokens": int(u.get("prompt_tokens", 0)),
            "completion_tokens": int(u.get("completion_tokens", 0)),
            "total_tokens": int(u.get("total_tokens", 0)),
        }


@pytest.fixture()
def settings(tmp_path):
    return Settings(
        deepseek_api_key="test-key",
        deepseek_base_url="http://localhost:9999/v1",
        deepseek_model="test-model",
        skills_dir=str(Settings().skills_path),
        runs_log_path=str(tmp_path / "runs.jsonl"),
    )


@pytest.fixture()
def registry(settings):
    reg = SkillRegistry(settings.skills_path)
    reg.reload()
    return reg


def _make_pipeline(settings, registry, run_store=None, cache=None):
    return RefinementPipeline(
        settings=settings,
        client=_MockClient(),
        registry=registry,
        cache=cache,
        pub_validator=None,
        run_store=run_store,
    )


def _request(**overrides) -> RefineRequest:
    base = dict(
        requirement="做一个移动端待办应用",
        platforms=[Platform.mobile],
        stages=[Stage.classify, Stage.markdown],
        validate_packages=False,
    )
    base.update(overrides)
    return RefineRequest(**base)


@pytest.mark.asyncio
async def test_progress_events_emitted(settings, registry):
    pipeline = _make_pipeline(settings, registry)
    events = []

    async def progress(event):
        events.append(event)

    response = await pipeline.run(_request(), progress=progress)
    assert response.markdown

    types = [e["type"] for e in events]
    assert types[0] == "pipeline_start"
    assert types.count("stage_start") == 2
    assert types.count("stage_complete") == 2

    start = events[0]
    assert start["stages"] == ["classify", "markdown"]
    assert start["run_id"].startswith("run-")

    completes = [e for e in events if e["type"] == "stage_complete"]
    assert [e["stage"] for e in completes] == ["classify", "markdown"]
    for e in completes:
        assert e["usage"]["total_tokens"] == 150
        assert e["stage_valid"] is True
        assert e["repaired"] is False


@pytest.mark.asyncio
async def test_progress_callback_failure_does_not_break_run(settings, registry):
    pipeline = _make_pipeline(settings, registry)

    async def bad_progress(event):
        raise RuntimeError("boom")

    response = await pipeline.run(_request(), progress=bad_progress)
    assert response.markdown
    assert len(response.stages) == 2


@pytest.mark.asyncio
async def test_cache_hit_emits_event(settings, registry, tmp_path):
    run_store = RunStore(settings.runs_log_file)
    cache = RunCache(settings.runs_log_file)
    pipeline = _make_pipeline(settings, registry, run_store=run_store, cache=cache)

    first = await pipeline.run(_request(use_cache=True))
    await run_store.append(first)

    events = []

    async def progress(event):
        events.append(event)

    second = await pipeline.run(_request(use_cache=True), progress=progress)
    assert second.cached is True
    assert events and events[0]["type"] == "cache_hit"
    assert events[0]["run_id"] == first.id


def _make_app(settings, registry, tmp_path) -> FastAPI:
    app = FastAPI()
    app.include_router(refine.router)
    run_store = RunStore(settings.runs_log_file)
    app.state.settings = settings
    app.state.pipeline = _make_pipeline(settings, registry, run_store=run_store)
    app.state.run_store = run_store
    return app


def test_refine_stream_endpoint(settings, registry, tmp_path):
    app = _make_app(settings, registry, tmp_path)
    client = TestClient(app)

    with client.stream(
        "POST",
        "/v1/refine/stream",
        json={
            "requirement": "做一个移动端待办应用",
            "platforms": ["mobile"],
            "stages": ["classify", "markdown"],
            "validate_packages": False,
        },
    ) as resp:
        assert resp.status_code == 200
        assert resp.headers["content-type"].startswith("text/event-stream")
        body = "".join(resp.iter_text())

    lines = [l for l in body.split("\n") if l.startswith("data: ")]
    assert lines[-1] == "data: [DONE]"
    events = [json.loads(l[len("data: "):]) for l in lines[:-1]]

    types = [e["type"] for e in events]
    assert types[0] == "pipeline_start"
    assert "stage_start" in types
    assert "stage_complete" in types
    assert types[-1] == "done"

    done = events[-1]
    assert done["response"]["markdown"]
    assert done["response"]["id"].startswith("run-")

    # The run must have been persisted to the store.
    store: RunStore = app.state.run_store
    assert store.get(done["response"]["id"]) is not None
