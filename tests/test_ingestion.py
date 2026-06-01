"""Ingestion never hits the network in tests; we mock httpx and feed fixtures."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.ingestion import (  # noqa: E402
    ArxivSource,
    HuggingFaceSource,
    IngestionCandidate,
    Ingestor,
    SeenStore,
    _get_with_retry,
    _strip_code_fence,
    candidate_skill_id,
    candidate_to_skill_scaffold,
    distill_candidate,
    is_relevant,
    parse_arxiv_atom,
    parse_hf_models,
)

_HF_PAYLOAD = [
    {
        "id": "Qwen/Qwen2.5-Coder-7B",
        "tags": ["code", "text-generation"],
        "pipeline_tag": "text-generation",
        "downloads": 12345,
        "likes": 67,
        "createdAt": "2024-09-01T00:00:00.000Z",
        "lastModified": "2025-01-02T00:00:00.000Z",
    },
    {
        "id": "stabilityai/stable-diffusion-xl",  # irrelevant (image)
        "tags": ["text-to-image", "diffusion"],
        "downloads": 999999,
        "likes": 5000,
    },
    {"tags": ["code"]},  # no id -> dropped
]

_ARXIV_XML = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <entry>
    <id>http://arxiv.org/abs/2501.01234v1</id>
    <title>A Coding Agent for Program Synthesis</title>
    <summary>We present a code generation agent that  refactors   repositories.</summary>
    <published>2025-01-05T00:00:00Z</published>
    <updated>2025-01-06T00:00:00Z</updated>
    <category term="cs.SE"/>
    <category term="cs.AI"/>
  </entry>
  <entry>
    <id>http://arxiv.org/abs/2501.09999v1</id>
    <title>On the Migration Patterns of Arctic Birds</title>
    <summary>A study of bird flight, unrelated to any engineering topic.</summary>
    <published>2025-01-04T00:00:00Z</published>
  </entry>
</feed>"""


# ---- pure parsers ---------------------------------------------------------

def test_parse_hf_models() -> None:
    cands = parse_hf_models(_HF_PAYLOAD)
    assert len(cands) == 2  # the id-less entry is dropped
    first = cands[0]
    assert first.source == "huggingface" and first.kind == "model"
    assert first.ref == "Qwen/Qwen2.5-Coder-7B"
    assert first.url == "https://huggingface.co/Qwen/Qwen2.5-Coder-7B"
    assert first.metrics == {"downloads": 12345, "likes": 67}
    assert first.updated_at == "2025-01-02T00:00:00.000Z"


def test_parse_hf_models_garbage() -> None:
    assert parse_hf_models("not a list") == []
    assert parse_hf_models([1, "x", None]) == []


def test_parse_arxiv_atom() -> None:
    cands = parse_arxiv_atom(_ARXIV_XML)
    assert len(cands) == 2
    paper = cands[0]
    assert paper.source == "arxiv" and paper.kind == "paper"
    assert paper.ref == "2501.01234v1"
    assert "Coding Agent" in paper.title
    # whitespace normalised
    assert "  " not in paper.summary
    assert "cs.SE" in paper.tags


def test_parse_arxiv_atom_bad_xml() -> None:
    assert parse_arxiv_atom("") == []
    assert parse_arxiv_atom("<not<valid") == []


def test_is_relevant_filters_unrelated() -> None:
    cands = parse_hf_models(_HF_PAYLOAD)
    relevant = [c for c in cands if is_relevant(c)]
    assert [c.ref for c in relevant] == ["Qwen/Qwen2.5-Coder-7B"]
    papers = [c for c in parse_arxiv_atom(_ARXIV_XML) if is_relevant(c)]
    assert [p.ref for p in papers] == ["2501.01234v1"]


# ---- seen-store -----------------------------------------------------------

def test_seen_store_roundtrip(tmp_path: Path) -> None:
    path = tmp_path / "seen.json"
    store = SeenStore(path)
    c = IngestionCandidate(source="arxiv", kind="paper", ref="2501.01234v1")
    store.mark_new([c])
    assert c.is_new is True
    store.commit([c])
    # New store instance reads persisted state.
    store2 = SeenStore(path)
    store2.mark_new([c])
    assert c.is_new is False


# ---- Ingestor (fake async sources) ---------------------------------------

class _FakeSource:
    def __init__(self, name, cands, fail=False):
        self.name = name
        self._cands = cands
        self._fail = fail

    async def fetch(self, query, limit):
        if self._fail:
            raise httpx.ConnectError("boom")
        return list(self._cands)


def test_ingestor_dedups_filters_and_counts_new(tmp_path: Path) -> None:
    hf = parse_hf_models(_HF_PAYLOAD)  # 1 relevant + 1 image
    arx = parse_arxiv_atom(_ARXIV_XML)  # 1 relevant + 1 birds
    # duplicate the coder model to prove dedup by key
    src_a = _FakeSource("huggingface", hf + [hf[0]])
    src_b = _FakeSource("arxiv", arx)
    store = SeenStore(tmp_path / "seen.json")
    ing = Ingestor([src_a, src_b], seen=store)
    digest = asyncio.run(ing.discover(["code"], limit_per_query=5))

    refs = sorted(c.ref for c in digest.candidates)
    assert refs == ["2501.01234v1", "Qwen/Qwen2.5-Coder-7B"]  # irrelevant dropped
    assert digest.total == 2
    assert digest.new_count == 2
    assert digest.sources_ok == {"huggingface": True, "arxiv": True}


def test_ingestor_marks_source_failure(tmp_path: Path) -> None:
    good = _FakeSource("huggingface", parse_hf_models(_HF_PAYLOAD))
    bad = _FakeSource("arxiv", [], fail=True)
    ing = Ingestor([good, bad], seen=SeenStore(tmp_path / "s.json"))
    digest = asyncio.run(ing.discover(["code"]))
    assert digest.sources_ok == {"huggingface": True, "arxiv": False}
    assert digest.total == 1  # good source still contributes


# ---- source fetch via MockTransport (no network) -------------------------

def test_hf_source_fetch_mocked() -> None:
    import json as _json

    def handler(request: httpx.Request) -> httpx.Response:
        assert request.url.path == "/api/models"
        return httpx.Response(200, json=_HF_PAYLOAD)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    cands = asyncio.run(HuggingFaceSource(client).fetch("code", 5))
    assert any(c.ref == "Qwen/Qwen2.5-Coder-7B" for c in cands)


def test_arxiv_source_fetch_mocked() -> None:
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(200, text=_ARXIV_XML)

    client = httpx.AsyncClient(transport=httpx.MockTransport(handler))
    cands = asyncio.run(ArxivSource(client).fetch("code", 5))
    assert cands[0].ref == "2501.01234v1"


# ---- scaffold (deterministic, no model) ----------------------------------

def test_candidate_skill_id_slug() -> None:
    c = IngestionCandidate(
        source="huggingface", kind="model", ref="Qwen/Qwen2.5-Coder-7B"
    )
    assert candidate_skill_id(c) == "flutter-watch-model-qwen2-5-coder-7b"


def test_scaffold_has_sources_layers_and_honesty() -> None:
    c = parse_arxiv_atom(_ARXIV_XML)[0]
    md = candidate_to_skill_scaffold(c)
    assert "id: flutter-watch-paper-2501-01234v1" in md
    assert c.url in md  # source pinned
    assert "draft-scaffold" in md
    for layer in ("怎么想", "怎么判断", "怎么说话", "什么不做", "知道局限"):
        assert layer in md
    assert "诚实边界" in md


# ---- retry / backoff (no real sleeps thanks to backoff_base=0) -----------

def _counting_client(responses):
    """MockTransport that returns ``responses`` in order, repeating the last."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        i = min(calls["n"], len(responses) - 1)
        calls["n"] += 1
        return responses[i]

    return httpx.AsyncClient(transport=httpx.MockTransport(handler)), calls


def test_get_with_retry_recovers_after_429() -> None:
    client, calls = _counting_client(
        [httpx.Response(429), httpx.Response(429), httpx.Response(200, text="ok")]
    )

    async def go():
        return await _get_with_retry(
            client, "https://x/y", retries=3, backoff_base=0.0
        )

    resp = asyncio.run(go())
    assert resp.status_code == 200
    assert calls["n"] == 3  # two retries then success


def test_get_with_retry_exhausts_and_raises() -> None:
    client, calls = _counting_client([httpx.Response(429)])

    async def go():
        return await _get_with_retry(
            client, "https://x/y", retries=2, backoff_base=0.0
        )

    try:
        asyncio.run(go())
        raised = False
    except httpx.HTTPStatusError:
        raised = True
    assert raised and calls["n"] == 2


def test_arxiv_source_retries_then_succeeds() -> None:
    client, calls = _counting_client(
        [httpx.Response(429), httpx.Response(200, text=_ARXIV_XML)]
    )
    src = ArxivSource(client, retries=3, backoff_base=0.0)
    cands = asyncio.run(src.fetch("code", 5))
    assert calls["n"] == 2
    assert cands[0].ref == "2501.01234v1"


# ---- distill (model-backed, fully mocked — no tokens spent) --------------

class _FakeChatClient:
    def __init__(self, content: str):
        self._content = content
        self.calls = 0

    async def chat(self, messages, *, model=None, temperature=None, max_tokens=None):
        self.calls += 1
        self.last_messages = messages
        return {"choices": [{"message": {"content": self._content}}]}

    @staticmethod
    def extract_text(completion) -> str:
        return completion["choices"][0]["message"]["content"]


def test_strip_code_fence() -> None:
    assert _strip_code_fence("```markdown\n---\nid: x\n---\n```") == "---\nid: x\n---"
    assert _strip_code_fence("---\nid: x\n---") == "---\nid: x\n---"


def test_distill_candidate_returns_model_markdown() -> None:
    c = parse_arxiv_atom(_ARXIV_XML)[0]
    filled = "---\nid: flutter-watch-paper-2501-01234v1\n---\n# done"
    client = _FakeChatClient(filled)
    out = asyncio.run(distill_candidate(client, c, model="m"))
    assert out == filled
    assert client.calls == 1


def test_distill_candidate_falls_back_to_scaffold_on_junk() -> None:
    c = parse_arxiv_atom(_ARXIV_XML)[0]
    client = _FakeChatClient("sorry I cannot help")  # not a SKILL.md
    out = asyncio.run(distill_candidate(client, c, model="m"))
    assert out.startswith("---")  # fell back to deterministic scaffold
    assert "draft-scaffold" in out
