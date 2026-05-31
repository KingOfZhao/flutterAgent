"""Smoke tests that do NOT require an upstream API key.

Covers:
  * SKILL.md parsing (registry loads >= 8 skills, front-matter is valid).
  * OpenAPI schema generation (FastAPI app boots and emits a spec).
  * /v1/skills, /v1/skills/{id}, /v1/skills/reload, /healthz, /v1/runs endpoints.
  * /v1/refine rejects calls when DEEPSEEK_API_KEY is missing (502 path).
  * pipeline JSON repair helper handles malformed outputs.
  * UpstreamError.retryable categorisation.
  * SSE stream chunk encoding helper.
"""
from __future__ import annotations

import json
import os
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

# Make sure tests never accidentally hit a real upstream.
os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("LOCAL_API_KEY", "")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from flutter_agent.config import get_settings  # noqa: E402
from flutter_agent.deepseek_client import UpstreamError  # noqa: E402
from flutter_agent.main import app  # noqa: E402
from flutter_agent.pipeline import _try_parse_json  # noqa: E402
from flutter_agent.routes.openai_compat import _sse, _sse_done  # noqa: E402
from flutter_agent.skill_loader import SkillRegistry  # noqa: E402


def test_skill_registry_loads_expected_skills() -> None:
    settings = get_settings()
    registry = SkillRegistry(settings.skills_path)
    registry.reload()
    ids = {s.id for s in registry.list()}
    expected = {
        "flutter-mobile",
        "flutter-desktop",
        "flutter-cross-platform",
        "task-refinement",
        "architecture-design",
        "state-management",
        "flutter-testing",
        "flutter-performance",
        "flutter-accessibility",
        "flutter-i18n",
        "flutter-ci-cd",
        "flutter-security",
        "flutter-animation",
        "flutter-navigation",
        "flutter-data-persistence",
        "flutter-ai-integration",
        "flutter-resource-lifecycle",
        "flutter-web",
        "flutter-network",
    }
    assert expected.issubset(ids), f"missing skills: {expected - ids}"
    assert len(registry) >= 19


def test_openapi_schema_contains_core_routes() -> None:
    schema = app.openapi()
    paths = set(schema.get("paths", {}).keys())
    for required in (
        "/healthz",
        "/v1/skills",
        "/v1/skills/{skill_id}",
        "/v1/skills/reload",
        "/v1/refine",
        "/v1/chat/completions",
        "/v1/runs",
        "/v1/runs/{run_id}",
        "/v1/metrics",
    ):
        assert required in paths, f"missing route in OpenAPI: {required}"

    # Confirm the Pydantic models we expose are surfaced in components.schemas.
    schema_names = set(schema.get("components", {}).get("schemas", {}).keys())
    for required in (
        "RefineRequest",
        "RefineResponse",
        "TokenUsage",
        "CostBreakdown",
        "PackageValidation",
        "RunSummary",
        "StageResult",
        "MetricsResponse",
    ):
        assert required in schema_names, f"missing component schema: {required}"


def test_healthz_and_skill_listing() -> None:
    with TestClient(app) as client:
        r = client.get("/healthz")
        assert r.status_code == 200, r.text
        body = r.json()
        assert body["status"] == "ok"
        assert body["skills_loaded"] >= 15

        r = client.get("/v1/skills")
        assert r.status_code == 200
        ids = {s["id"] for s in r.json()}
        assert {"flutter-mobile", "flutter-testing", "flutter-performance"}.issubset(ids)

        r = client.get("/v1/skills/flutter-mobile")
        assert r.status_code == 200
        detail = r.json()
        assert detail["id"] == "flutter-mobile"
        assert "Flutter Mobile" in detail["body"] or "Flutter Mobile" in detail["name"]

        r = client.get("/v1/skills/__missing__")
        assert r.status_code == 404

        r = client.post("/v1/skills/reload")
        assert r.status_code == 200
        assert r.json()["loaded"] >= 8


def test_metrics_endpoint_returns_valid_response() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/metrics")
        assert r.status_code == 200, r.text
        body = r.json()
        assert "total_runs" in body
        assert "skills_loaded" in body
        assert body["skills_loaded"] >= 15
        assert "stage_success_rate" in body
        assert isinstance(body["top_skills"], list)


def test_refine_without_api_key_returns_502() -> None:
    """When DEEPSEEK_API_KEY is unset, the pipeline should fail with 502."""
    with TestClient(app) as client:
        r = client.post(
            "/v1/refine",
            json={"requirement": "做一个跨端待办 App", "platforms": ["mobile"]},
        )
        # 502 = upstream error; we surface it cleanly rather than crashing.
        assert r.status_code == 502, r.text
        assert "DEEPSEEK_API_KEY" in r.json().get("detail", "")


def test_chat_completions_rejects_empty_messages() -> None:
    with TestClient(app) as client:
        r = client.post(
            "/v1/chat/completions",
            json={"model": "flutter-agent", "messages": []},
        )
        assert r.status_code == 400


def test_runs_listing_handles_empty_history() -> None:
    with TestClient(app) as client:
        r = client.get("/v1/runs")
        # The path may have prior runs from the developer's machine; just
        # verify it responds 200 with a list.
        assert r.status_code == 200
        assert isinstance(r.json(), list)

        r = client.get("/v1/runs/__nope__")
        assert r.status_code == 404


# ---------------------------------------------------------------------------
# Pure unit-level checks (no FastAPI involved)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text,expected_keys",
    [
        ('{"a": 1}', {"a"}),
        ('```json\n{"a": 1}\n```', {"a"}),
        ('garbage before {"a": 1, "b": [2,3]} trailing', {"a", "b"}),
        ('[1,2,3]', {"_list"}),
        ("not json at all", None),
        ("", None),
    ],
)
def test_pipeline_json_repair_helper(text: str, expected_keys) -> None:
    parsed = _try_parse_json(text)
    if expected_keys is None:
        assert parsed is None
    else:
        assert parsed is not None and set(parsed.keys()) == expected_keys


@pytest.mark.parametrize(
    "status_code,retryable",
    [
        (0, True),    # transport-level
        (429, True),
        (500, True),
        (502, True),
        (503, True),
        (504, True),
        (400, False),
        (401, False),
        (404, False),
    ],
)
def test_upstream_error_retryable_classification(status_code: int, retryable: bool) -> None:
    err = UpstreamError("x", status_code=status_code)
    assert err.retryable is retryable


def test_sse_helpers_emit_proper_format() -> None:
    chunk = _sse({"choices": [{"delta": {"content": "hi"}}]})
    assert chunk.startswith(b"data: ")
    assert chunk.endswith(b"\n\n")
    payload = json.loads(chunk[len(b"data: ") : -2])
    assert payload["choices"][0]["delta"]["content"] == "hi"

    done = _sse_done()
    assert done == b"data: [DONE]\n\n"
