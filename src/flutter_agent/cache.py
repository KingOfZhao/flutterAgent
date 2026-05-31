"""Content-addressed cache for refinement runs.

The cache key is a stable SHA-256 of the *deterministic* inputs:
``(requirement, sorted skill ids, sorted stages, temperature, max_tokens,
extra_context, upstream model name)``. Non-deterministic factors like wall
clock or run id are excluded.

Storage is layered on top of ``logs/runs.jsonl`` — we don't introduce a
second database. On startup we scan the JSONL and build an in-memory
``{cache_key: run_id}`` index (kept in memory; rebuilt on reload). Each
appended run augments the index immediately.

Concurrency: a single asyncio lock protects the index. The pipeline always
calls ``lookup`` -> (run pipeline) -> ``index(...)`` from the same task, so
there is no race-on-write within a single run.
"""
from __future__ import annotations

import asyncio
import hashlib
import json
import logging
from pathlib import Path
from typing import Dict, List, Optional, Sequence

logger = logging.getLogger(__name__)


def make_cache_key(
    *,
    requirement: str,
    skill_ids: Sequence[str],
    stages: Sequence[str],
    temperature: Optional[float],
    max_tokens: Optional[int],
    extra_context: Optional[str],
    model: str,
) -> str:
    """Return a deterministic SHA-256 hex digest of the cache inputs."""
    canonical = json.dumps(
        {
            "requirement": (requirement or "").strip(),
            "skill_ids": sorted(skill_ids or []),
            "stages": list(stages or []),
            "temperature": temperature,
            "max_tokens": max_tokens,
            "extra_context": (extra_context or "").strip(),
            "model": model,
        },
        sort_keys=True,
        ensure_ascii=False,
        separators=(",", ":"),
    )
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


class RunCache:
    """In-memory ``cache_key -> run_id`` index backed by ``runs.jsonl``."""

    def __init__(self, runs_log_path: Path):
        self._log_path = runs_log_path
        self._index: Dict[str, str] = {}
        # Lazily created so RunCache can be instantiated outside a running
        # asyncio loop (Python 3.9 raises if asyncio.Lock() is constructed
        # without a current loop).
        self._lock: Optional[asyncio.Lock] = None
        self._loaded = False

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    # ------------------------------------------------------------------ API

    def load(self) -> int:
        """Synchronously read the JSONL and rebuild the index."""
        self._index.clear()
        if not self._log_path.exists():
            self._loaded = True
            return 0
        for line in self._log_path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            key = obj.get("cache_key")
            run_id = obj.get("id")
            if key and run_id and key not in self._index:
                # First-wins: keep oldest cached entry to maintain idempotency.
                self._index[key] = run_id
        self._loaded = True
        logger.info(
            "run cache loaded: %d entries from %s", len(self._index), self._log_path
        )
        return len(self._index)

    async def lookup(self, cache_key: str) -> Optional[str]:
        """Return a run_id for ``cache_key`` or None if not cached."""
        async with self._get_lock():
            if not self._loaded:
                self.load()
            return self._index.get(cache_key)

    async def index(self, cache_key: str, run_id: str) -> None:
        async with self._get_lock():
            if cache_key and run_id:
                self._index.setdefault(cache_key, run_id)

    def __len__(self) -> int:  # for diagnostics
        return len(self._index)

    def keys(self) -> List[str]:
        return list(self._index.keys())
