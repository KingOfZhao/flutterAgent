"""POST /v1/ingest tests — a fake source is injected so no network is touched."""
from __future__ import annotations

import os
import sys
from pathlib import Path
from typing import List

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

os.environ.setdefault("DEEPSEEK_API_KEY", "")
os.environ.setdefault("LOCAL_API_KEY", "")

import pytest  # noqa: E402
from fastapi.testclient import TestClient  # noqa: E402

from flutter_agent.deepseek_client import UpstreamError  # noqa: E402
from flutter_agent.deps import get_client, get_make_ingestor  # noqa: E402
from flutter_agent.ingestion import IngestionCandidate, Ingestor, SeenStore  # noqa: E402
from flutter_agent.main import app  # noqa: E402


class _FakeSource:
    """Returns a fixed set of relevant candidates regardless of query."""

    name = "huggingface"

    def __init__(self, candidates: List[IngestionCandidate]):
        self._candidates = candidates
        self.calls = 0

    async def fetch(self, query: str, limit: int) -> List[IngestionCandidate]:
        self.calls += 1
        return list(self._candidates)


def _candidates() -> List[IngestionCandidate]:
    return [
        IngestionCandidate(
            source="huggingface",
            kind="model",
            ref="Qwen/Qwen2.5-Coder-7B",
            title="Qwen2.5-Coder-7B",
            url="https://huggingface.co/Qwen/Qwen2.5-Coder-7B",
            summary="code generation model",
            tags=["code", "text-generation"],
            metrics={"downloads": 100, "likes": 5},
        ),
    ]


def _override_with(candidates: List[IngestionCandidate]):
    async def _factory():
        def make(wanted: set, seen):
            # de-dups across the queries; one fake source is enough.
            return Ingestor([_FakeSource(candidates)], seen=seen)

        yield make

    return _factory


def test_ingest_discovers_without_network() -> None:
    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    try:
        with TestClient(app) as client:
            r = client.post("/v1/ingest", json={"queries": ["code"], "sources": ["hf"]})
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["digest"]["total"] == 1
            assert body["digest"]["candidates"][0]["ref"] == "Qwen/Qwen2.5-Coder-7B"
            assert body["scaffolded"] == 0 and body["distilled"] == 0
            assert body["committed"] is False
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)


def test_ingest_rejects_unknown_sources() -> None:
    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    try:
        with TestClient(app) as client:
            r = client.post("/v1/ingest", json={"sources": ["bogus"]})
            assert r.status_code == 400, r.text
            assert "valid sources" in r.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)


def test_ingest_distill_requires_api_key() -> None:
    """With DEEPSEEK_API_KEY unset, distill must be refused (no token burn)."""
    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    try:
        with TestClient(app) as client:
            r = client.post("/v1/ingest", json={"sources": ["hf"], "distill": True})
            assert r.status_code == 400, r.text
            assert "DEEPSEEK_API_KEY" in r.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)


def test_ingest_scaffolds_to_disk(tmp_path: Path) -> None:
    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    try:
        with TestClient(app) as client:
            r = client.post(
                "/v1/ingest",
                json={
                    "sources": ["hf"],
                    "scaffold": True,
                    "scaffold_dir": str(tmp_path),
                },
            )
            assert r.status_code == 200, r.text
            body = r.json()
            assert body["scaffolded"] == 1
            assert body["scaffold_dir"] == str(tmp_path)
            written = list(tmp_path.glob("*/SKILL.md"))
            assert len(written) == 1
            text = written[0].read_text(encoding="utf-8")
            assert text.startswith("---")
            assert "## 来源" in text  # sourcing pinned for anti-hallucination
            # Second call must not clobber the existing scaffold.
            r2 = client.post(
                "/v1/ingest",
                json={"sources": ["hf"], "scaffold": True, "scaffold_dir": str(tmp_path)},
            )
            assert r2.json()["scaffolded"] == 0
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)


def test_ingest_commit_updates_seen_store(tmp_path: Path, monkeypatch) -> None:
    """commit=true should persist seen-keys so a later run sees nothing new."""
    seen_file = tmp_path / "seen.json"

    def _fake_seen_path(self):  # patch the settings property
        return seen_file

    from flutter_agent.config import Settings

    monkeypatch.setattr(Settings, "ingestion_seen_file", property(_fake_seen_path))

    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    try:
        with TestClient(app) as client:
            r = client.post(
                "/v1/ingest",
                json={"sources": ["hf"], "commit": True, "only_new": True},
            )
            assert r.status_code == 200, r.text
            assert r.json()["committed"] is True
            assert seen_file.exists()
            # Now the same candidate is no longer "new".
            store = SeenStore(seen_file)
            cands = _candidates()
            store.mark_new(cands)
            assert cands[0].is_new is False
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)


class _FailingClient:
    """A DeepSeek-shaped client whose chat() always fails upstream."""

    async def chat(self, *a, **k):
        raise UpstreamError("upstream returned 401", status_code=401)

    @staticmethod
    def extract_text(completion) -> str:  # pragma: no cover - never reached
        return ""


def test_ingest_distill_upstream_error_maps_to_502(tmp_path: Path, monkeypatch) -> None:
    """When the model call fails, distill surfaces 502 (not an opaque 500)."""
    from flutter_agent.config import Settings

    monkeypatch.setattr(
        Settings, "deepseek_api_key", property(lambda self: "test-key"), raising=False
    )
    app.dependency_overrides[get_make_ingestor] = _override_with(_candidates())
    app.dependency_overrides[get_client] = lambda: _FailingClient()
    try:
        with TestClient(app) as client:
            r = client.post(
                "/v1/ingest",
                json={
                    "sources": ["hf"],
                    "distill": True,
                    "scaffold_dir": str(tmp_path),
                    "limit": 1,
                },
            )
            assert r.status_code == 502, r.text
            assert "upstream error" in r.json()["detail"]
    finally:
        app.dependency_overrides.pop(get_make_ingestor, None)
        app.dependency_overrides.pop(get_client, None)


def test_openapi_exposes_ingest_route() -> None:
    schema = app.openapi()
    assert "/v1/ingest" in schema.get("paths", {})
    names = set(schema.get("components", {}).get("schemas", {}).keys())
    assert {"IngestRequest", "IngestResponse"}.issubset(names)
