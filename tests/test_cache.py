"""RunCache uses content-addressed lookups over runs.jsonl."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.cache import RunCache, make_cache_key  # noqa: E402


def test_make_cache_key_is_deterministic_and_canonical() -> None:
    a = make_cache_key(
        requirement="hello",
        skill_ids=["b", "a", "c"],
        stages=["spec", "classify"],
        temperature=0.2,
        max_tokens=4096,
        extra_context=None,
        model="deepseek-v4-pro",
    )
    # Reordering skill_ids must NOT change the key (we sort).
    b = make_cache_key(
        requirement="hello",
        skill_ids=["a", "b", "c"],
        stages=["spec", "classify"],
        temperature=0.2,
        max_tokens=4096,
        extra_context=None,
        model="deepseek-v4-pro",
    )
    assert a == b
    # Reordering stages MUST change the key (stage order is meaningful).
    c = make_cache_key(
        requirement="hello",
        skill_ids=["a", "b", "c"],
        stages=["classify", "spec"],
        temperature=0.2,
        max_tokens=4096,
        extra_context=None,
        model="deepseek-v4-pro",
    )
    assert a != c
    # Different model → different key.
    d = make_cache_key(
        requirement="hello",
        skill_ids=["a", "b", "c"],
        stages=["spec", "classify"],
        temperature=0.2,
        max_tokens=4096,
        extra_context=None,
        model="other-model",
    )
    assert a != d
    # Whitespace-only difference in requirement is normalized away.
    e = make_cache_key(
        requirement="  hello  ",
        skill_ids=["a", "b", "c"],
        stages=["spec", "classify"],
        temperature=0.2,
        max_tokens=4096,
        extra_context=None,
        model="deepseek-v4-pro",
    )
    assert a == e


def test_cache_reads_runs_jsonl(tmp_path: Path) -> None:
    log = tmp_path / "runs.jsonl"
    log.write_text(
        "\n".join(
            [
                json.dumps({"id": "run-1", "cache_key": "k1"}),
                json.dumps({"id": "run-2", "cache_key": "k2"}),
                "",  # tolerate blank line
                "{ corrupt",  # tolerate corruption
                json.dumps({"id": "run-3", "cache_key": "k1"}),  # duplicate, ignored
            ]
        ),
        encoding="utf-8",
    )
    cache = RunCache(log)
    cache.load()
    assert len(cache) == 2

    async def go() -> None:
        assert await cache.lookup("k1") == "run-1"  # first-wins
        assert await cache.lookup("k2") == "run-2"
        assert await cache.lookup("missing") is None
        await cache.index("k3", "run-4")
        assert await cache.lookup("k3") == "run-4"

    asyncio.run(go())


def test_cache_load_handles_missing_file(tmp_path: Path) -> None:
    cache = RunCache(tmp_path / "does-not-exist.jsonl")
    cache.load()
    assert len(cache) == 0
