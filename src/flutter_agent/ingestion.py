"""Continuous open-source ingestion.

Pulls *development / coding-focused* open-source signals from public APIs so
the skill library can keep learning from what the ecosystem ships:

  * Hugging Face Hub  — models (e.g. code/coding-agent models)
  * arXiv             — papers (program synthesis, SWE agents, code models)

Design choices (so this is testable and honest):

  * **Fetch and parse are split.** Parsing is pure (raw payload -> candidates)
    and unit-tested with fixtures; fetching is a thin httpx wrapper, so tests
    never touch the network.
  * **Dedup via a seen-store.** A small JSON file records candidate keys we've
    already reported, so each run only surfaces what's *new*.
  * **No model calls here.** Turning a candidate into a real skill costs tokens
    on the underlying model; this module only discovers + scaffolds. The
    deterministic scaffold (front-matter + sources + five-layer TODO headers)
    is produced without any model; a model fills the cognitive content later.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional

import httpx
from pydantic import BaseModel, Field

logger = logging.getLogger(__name__)

_HF_MODELS_URL = "https://huggingface.co/api/models"
_ARXIV_URL = "http://export.arxiv.org/api/query"
_ARXIV_NS = {"atom": "http://www.w3.org/2005/Atom"}
# arXiv asks API clients to identify themselves and throttles anonymous bursts
# harder; a descriptive UA reduces (does not eliminate) 429s from shared IPs.
_USER_AGENT = "flutterAgent-ingestion/0.1 (+https://github.com/KingOfZhao/flutterAgent)"

# Status codes worth retrying (arXiv loves to 429; HF can 5xx under load).
_RETRY_STATUS = {429, 500, 502, 503, 504}


async def _get_with_retry(
    client: httpx.AsyncClient,
    url: str,
    *,
    params: Optional[Dict[str, str]] = None,
    headers: Optional[Dict[str, str]] = None,
    retries: int = 3,
    backoff_base: float = 0.6,
) -> httpx.Response:
    """GET with bounded exponential backoff on 429/5xx/transport errors.

    Raises the last ``httpx`` error if all attempts are exhausted, so callers
    can keep their existing ``except httpx.HTTPError`` handling.
    """
    last_exc: Optional[httpx.HTTPError] = None
    for attempt in range(1, max(1, retries) + 1):
        try:
            resp = await client.get(url, params=params, headers=headers)
        except httpx.HTTPError as exc:
            last_exc = exc
        else:
            if resp.status_code in _RETRY_STATUS:
                last_exc = httpx.HTTPStatusError(
                    f"{resp.status_code} from {url}",
                    request=resp.request,
                    response=resp,
                )
            else:
                resp.raise_for_status()
                return resp
        if attempt < retries:
            delay = backoff_base * (2 ** (attempt - 1)) + random.uniform(0, 0.25)
            logger.warning(
                "GET %s attempt %d/%d failed (%s); retrying in %.2fs",
                url, attempt, retries, last_exc, delay,
            )
            await asyncio.sleep(delay)
    assert last_exc is not None
    raise last_exc

# Signals that a candidate is about software development / coding, not a random
# image/audio model or an unrelated paper. Matched case-insensitively against
# title + tags + summary.
DEFAULT_KEYWORDS = (
    "code", "coder", "coding", "codegen", "program", "programming",
    "software", "developer", "swe-bench", "swe agent", "repo", "repository",
    "completion", "refactor", "compiler", "agent", "flutter", "dart",
    "test generation", "bug", "synthesis",
)

# What we watch for by default. Override via CLI/args.
DEFAULT_QUERIES = (
    "code generation",
    "coding agent",
    "code model",
    "program synthesis",
    "SWE agent",
    "flutter",
    "dart language",
)


class IngestionCandidate(BaseModel):
    """One discovered open-source artifact (model or paper)."""

    source: str = Field(description="'huggingface' or 'arxiv'.")
    kind: str = Field(description="'model' or 'paper'.")
    ref: str = Field(description="Stable id within the source (model id / arxiv id).")
    title: str = ""
    url: str = ""
    summary: str = ""
    published_at: Optional[str] = None
    updated_at: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    metrics: Dict[str, int] = Field(default_factory=dict)
    is_new: bool = True

    @property
    def key(self) -> str:
        return f"{self.source}:{self.ref}"


class IngestionDigest(BaseModel):
    generated_at: int
    queries: List[str]
    total: int = 0
    new_count: int = 0
    sources_ok: Dict[str, bool] = Field(default_factory=dict)
    candidates: List[IngestionCandidate] = Field(default_factory=list)


# ---------------------------------------------------------------------------
# Pure parsers (raw payload -> candidates) — unit-tested without network.
# ---------------------------------------------------------------------------

def parse_hf_models(payload: object) -> List[IngestionCandidate]:
    """Parse the Hugging Face ``/api/models`` JSON array into candidates."""
    out: List[IngestionCandidate] = []
    if not isinstance(payload, list):
        return out
    for item in payload:
        if not isinstance(item, dict):
            continue
        ref = str(item.get("id") or item.get("modelId") or "").strip()
        if not ref:
            continue
        tags = [str(t) for t in (item.get("tags") or []) if isinstance(t, (str, int))]
        pipeline = item.get("pipeline_tag")
        if isinstance(pipeline, str) and pipeline:
            tags.append(pipeline)
        metrics: Dict[str, int] = {}
        for fld in ("downloads", "likes"):
            v = item.get(fld)
            if isinstance(v, int):
                metrics[fld] = v
        out.append(
            IngestionCandidate(
                source="huggingface",
                kind="model",
                ref=ref,
                title=ref,
                url=f"https://huggingface.co/{ref}",
                summary=", ".join(tags[:8]),
                published_at=_as_str(item.get("createdAt")),
                updated_at=_as_str(item.get("lastModified")),
                tags=tags,
                metrics=metrics,
            )
        )
    return out


def parse_arxiv_atom(xml_text: str) -> List[IngestionCandidate]:
    """Parse an arXiv Atom feed into candidates."""
    out: List[IngestionCandidate] = []
    if not xml_text or not xml_text.strip():
        return out
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError:
        logger.warning("arxiv: could not parse Atom XML")
        return out
    for entry in root.findall("atom:entry", _ARXIV_NS):
        url = _text(entry, "atom:id")
        ref = url.rsplit("/", 1)[-1] if url else ""
        if not ref:
            continue
        title = _norm_ws(_text(entry, "atom:title"))
        summary = _norm_ws(_text(entry, "atom:summary"))
        tags = [
            c.attrib.get("term", "")
            for c in entry.findall("atom:category", _ARXIV_NS)
            if c.attrib.get("term")
        ]
        out.append(
            IngestionCandidate(
                source="arxiv",
                kind="paper",
                ref=ref,
                title=title,
                url=url,
                summary=summary[:500],
                published_at=_text(entry, "atom:published") or None,
                updated_at=_text(entry, "atom:updated") or None,
                tags=tags,
            )
        )
    return out


def is_relevant(c: IngestionCandidate, keywords: tuple = DEFAULT_KEYWORDS) -> bool:
    """Keep only development/coding-related candidates."""
    haystack = " ".join([c.title, c.summary, " ".join(c.tags)]).lower()
    return any(kw in haystack for kw in keywords)


# ---------------------------------------------------------------------------
# Seen-store: remember what we've already reported.
# ---------------------------------------------------------------------------

class SeenStore:
    """Tracks candidate keys across runs in a small JSON file."""

    def __init__(self, path: Path):
        self._path = Path(path)
        self._seen: set = set()
        self._load()

    def _load(self) -> None:
        if self._path.exists():
            try:
                data = json.loads(self._path.read_text(encoding="utf-8"))
                if isinstance(data, dict) and isinstance(data.get("seen"), list):
                    self._seen = {str(k) for k in data["seen"]}
            except (ValueError, OSError):
                logger.warning("seen-store unreadable, starting fresh: %s", self._path)

    def mark_new(self, candidates: List[IngestionCandidate]) -> List[IngestionCandidate]:
        """Set ``is_new`` on each candidate based on the store (no write)."""
        for c in candidates:
            c.is_new = c.key not in self._seen
        return candidates

    def commit(self, candidates: List[IngestionCandidate]) -> None:
        for c in candidates:
            self._seen.add(c.key)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(
            json.dumps({"seen": sorted(self._seen)}, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )


# ---------------------------------------------------------------------------
# Sources (fetch = thin httpx wrapper around the pure parsers).
# ---------------------------------------------------------------------------

class HuggingFaceSource:
    name = "huggingface"

    def __init__(
        self, client: httpx.AsyncClient, retries: int = 3, backoff_base: float = 0.6
    ):
        self._client = client
        self._retries = retries
        self._backoff_base = backoff_base

    async def fetch(self, query: str, limit: int) -> List[IngestionCandidate]:
        params = {
            "search": query,
            "sort": "downloads",
            "direction": "-1",
            "limit": str(limit),
        }
        resp = await _get_with_retry(
            self._client,
            _HF_MODELS_URL,
            params=params,
            headers={"Accept": "application/json"},
            retries=self._retries,
            backoff_base=self._backoff_base,
        )
        return parse_hf_models(resp.json())


class ArxivSource:
    name = "arxiv"

    def __init__(
        self, client: httpx.AsyncClient, retries: int = 4, backoff_base: float = 1.0
    ):
        # arXiv rate-limits aggressively, so it gets one extra attempt and a
        # longer base delay than Hugging Face by default.
        self._client = client
        self._retries = retries
        self._backoff_base = backoff_base

    async def fetch(self, query: str, limit: int) -> List[IngestionCandidate]:
        params = {
            "search_query": f"all:{query}",
            "sortBy": "submittedDate",
            "sortOrder": "descending",
            "max_results": str(limit),
        }
        resp = await _get_with_retry(
            self._client,
            _ARXIV_URL,
            params=params,
            headers={"User-Agent": _USER_AGENT},
            retries=self._retries,
            backoff_base=self._backoff_base,
        )
        return parse_arxiv_atom(resp.text)


class Ingestor:
    """Run a watch-list of queries across sources and dedup the results."""

    def __init__(
        self,
        sources: List[object],
        seen: Optional[SeenStore] = None,
        keywords: tuple = DEFAULT_KEYWORDS,
    ):
        self._sources = sources
        self._seen = seen
        self._keywords = keywords

    async def discover(
        self, queries: List[str], limit_per_query: int = 10
    ) -> IngestionDigest:
        by_key: Dict[str, IngestionCandidate] = {}
        sources_ok: Dict[str, bool] = {}
        for src in self._sources:
            ok = True
            for q in queries:
                try:
                    cands = await src.fetch(q, limit_per_query)
                except httpx.HTTPError as exc:
                    logger.warning("%s fetch failed for %r: %s", src.name, q, exc)
                    ok = False
                    continue
                for c in cands:
                    if not is_relevant(c, self._keywords):
                        continue
                    # Keep the richest copy (first wins; dedup by key).
                    by_key.setdefault(c.key, c)
            sources_ok[src.name] = ok

        candidates = list(by_key.values())
        if self._seen is not None:
            self._seen.mark_new(candidates)
        candidates.sort(
            key=lambda c: (c.is_new, c.metrics.get("downloads", 0), c.updated_at or ""),
            reverse=True,
        )
        new_count = sum(1 for c in candidates if c.is_new)
        return IngestionDigest(
            generated_at=int(datetime.now(tz=timezone.utc).timestamp()),
            queries=list(queries),
            total=len(candidates),
            new_count=new_count,
            sources_ok=sources_ok,
            candidates=candidates,
        )


# ---------------------------------------------------------------------------
# Candidate -> SKILL.md scaffold (deterministic, no model call).
# ---------------------------------------------------------------------------

_SLUG_RE = re.compile(r"[^a-z0-9]+")


def candidate_skill_id(c: IngestionCandidate) -> str:
    base = c.ref.split("/")[-1] if c.source == "huggingface" else c.ref
    slug = _SLUG_RE.sub("-", base.lower()).strip("-")
    prefix = "model" if c.kind == "model" else "paper"
    return f"flutter-watch-{prefix}-{slug}"[:64]


def candidate_to_skill_scaffold(c: IngestionCandidate) -> str:
    """Produce a distillation-ready SKILL.md skeleton for a candidate.

    The cognitive content (five layers) is left as TODO for a model run — this
    function deterministically pins the *sourcing* so the eventual skill is
    auditable and follows the anti-hallucination rules.
    """
    today = datetime.now(tz=timezone.utc).strftime("%Y-%m-%d")
    skill_id = candidate_skill_id(c)
    tags = ", ".join((c.tags or ["watch"])[:10])
    return f"""---
id: {skill_id}
name: 【待蒸馏】{c.title}
version: 0.0.1
platforms: [all]
tags: [{tags}]
applies_when: 评估是否将 {c.title} 的能力/方法引入开发流程时
stage_hints: [classify, architecture, breakdown]
see_also: [flutter-skill-distillation]
metadata:
  status: draft-scaffold
  source: {c.source}
  ingested_at: {today}
---

# 【待蒸馏】{c.title}

> 自动生成的蒸馏脚手架(ingestion)。认知内容需由一次模型运行按
> `flutter-skill-distillation` 的五层 + 三重验证填充,**未填充前不可作为成熟 skill 使用**。

## 来源(必须保留)
- 来源平台: {c.source} / {c.kind}
- 链接: {c.url}
- 发布: {c.published_at or '—'} ,更新: {c.updated_at or '—'}
- 抓取日期: {today}

## 摘要(原始,待提炼)
{c.summary or '(无摘要)'}

## 怎么想 · 心智模型
TODO(模型填充): 这个模型/论文带来哪条可迁移的思维?给一句话 + 官方依据 + 应用 + 局限。

## 怎么判断 · 决策启发式
TODO(模型填充)

## 怎么说话 · 表达方式
TODO(模型填充)

## 什么不做 · 反模式与红线
TODO(模型填充)

## 知道局限 · 诚实边界
- 本条目由公开资料蒸馏,是**方法/能力镜片**,不代表官方背书。
- 抓取自动化,采用前需人工核对来源时效与许可证。
"""


# ---------------------------------------------------------------------------
# Optional: fill a scaffold into a mature skill via the model (costs tokens).
# ---------------------------------------------------------------------------

DISTILL_SYSTEM = (
    "你是一名严谨的知识蒸馏师,按『女娲五层造 skill 法』把一个开源条目"
    "(模型或论文)的脚手架填充为成熟的 Flutter/Dart 开发 SKILL.md。要求:\n"
    "1) 保留原 front-matter 的 id;把 name 去掉『【待蒸馏】』前缀;version 设为 0.1.0;"
    "metadata.status 改为 distilled。\n"
    "2) 必须**原样保留**『## 来源』整段(平台/链接/日期),这是反幻觉红线。\n"
    "3) 用真实可迁移的内容填满五层(怎么想/怎么判断/怎么说话/什么不做/知道局限),"
    "每层简洁、具体、可执行;不要写『TODO』。\n"
    "4) **不得编造**超出给定摘要与常识的事实;不确定就在『知道局限』里诚实声明,"
    "并写明这是『能力镜片,非官方背书,基于抓取日期的时点快照』。\n"
    "5) 只输出完整的 SKILL.md(以 `---` front-matter 开头),不要任何额外解释或代码围栏。"
)


def _strip_code_fence(text: str) -> str:
    """Drop a leading/trailing ```markdown fence if the model added one."""
    t = text.strip()
    if t.startswith("```"):
        lines = t.splitlines()
        if lines and lines[0].startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        t = "\n".join(lines).strip()
    return t


async def distill_candidate(
    client: Any, c: IngestionCandidate, *, model: Optional[str] = None
) -> str:
    """Fill a candidate's scaffold into a mature SKILL.md using ``client``.

    ``client`` is duck-typed to a ``DeepSeekClient``: it must expose
    ``async chat(messages, *, model=..., temperature=..., max_tokens=...)``
    returning an OpenAI-shaped completion, and a static ``extract_text``.
    This call **costs model tokens**; callers gate it behind an explicit flag.
    Falls back to the deterministic scaffold if the model returns nothing.
    """
    scaffold = candidate_to_skill_scaffold(c)
    user = (
        "以下是待填充的脚手架,请按系统要求蒸馏为成熟 SKILL.md:\n\n"
        f"{scaffold}\n\n"
        f"补充上下文 —— 标题: {c.title}\n标签: {', '.join(c.tags[:12])}\n"
        f"摘要: {c.summary or '(无)'}"
    )
    completion = await client.chat(
        [
            {"role": "system", "content": DISTILL_SYSTEM},
            {"role": "user", "content": user},
        ],
        model=model,
        temperature=0.2,
        max_tokens=2048,
    )
    text = _strip_code_fence(client.extract_text(completion) or "")
    return text if text.startswith("---") else scaffold


# ---------------------------------------------------------------------------
# small helpers
# ---------------------------------------------------------------------------

def _text(entry: ET.Element, path: str) -> str:
    el = entry.find(path, _ARXIV_NS)
    return (el.text or "").strip() if el is not None and el.text else ""


def _norm_ws(s: str) -> str:
    return re.sub(r"\s+", " ", s).strip()


def _as_str(v: object) -> Optional[str]:
    if v is None:
        return None
    return str(v)
