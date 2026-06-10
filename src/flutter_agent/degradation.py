"""Degradation detectors over runs.jsonl (knowledge/capability-degradation-taxonomy.md).

Each detector turns one degradation source's "检测" row into code. Detectors
are pure functions over parsed run dicts so they can be unit-tested without
a server; ``load_runs`` adapts the JSONL on disk. Windows are split by run
order (newest tail vs the runs before it) because traffic volume, not wall
time, is what gives the comparison statistical footing.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List

from .run_store import _failure_reasons

DEFAULT_WINDOW = 50


def load_runs(path: Path) -> List[dict]:
    if not path.exists():
        return []
    runs: List[dict] = []
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            runs.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return runs


def _split_windows(runs: List[dict], window: int) -> tuple:
    recent = runs[-window:]
    prior = runs[:-window][-window:]
    return prior, recent


def detect_model_change(runs: List[dict], *, window: int = DEFAULT_WINDOW) -> dict:
    """D1: report distinct upstream model strings and transitions in the tail."""
    seen: List[str] = []
    transitions: List[dict] = []
    for run in runs[-window * 2:]:
        for stage in run.get("stages") or []:
            model = str(stage.get("model", "")).strip()
            if not model:
                continue
            if not seen or seen[-1] != model:
                if seen:
                    transitions.append(
                        {
                            "run_id": str(run.get("id", "")),
                            "created_at": int(run.get("created_at", 0) or 0),
                            "from": seen[-1],
                            "to": model,
                        }
                    )
                seen.append(model)
    return {
        "source": "D1",
        "alert": bool(transitions),
        "models_seen": sorted(set(seen)),
        "transitions": transitions,
    }


def detect_failure_rate_shift(
    runs: List[dict], *, window: int = DEFAULT_WINDOW, threshold: float = 0.10
) -> dict:
    """D1/D2 symptom monitor: failure-reason rate, recent window vs prior window."""
    prior, recent = _split_windows(runs, window)

    def rate(rs: List[dict]) -> float:
        if not rs:
            return 0.0
        return sum(1 for r in rs if _failure_reasons(r)) / len(rs)

    prior_rate, recent_rate = rate(prior), rate(recent)
    delta = recent_rate - prior_rate
    return {
        "source": "D1/D2",
        "alert": bool(prior) and delta > threshold,
        "prior_failure_rate": round(prior_rate, 4),
        "recent_failure_rate": round(recent_rate, 4),
        "delta": round(delta, 4),
        "threshold": threshold,
        "prior_runs": len(prior),
        "recent_runs": len(recent),
    }


def detect_cache_staleness(
    runs: List[dict], *, window: int = DEFAULT_WINDOW, max_cached_share: float = 0.8
) -> dict:
    """D5 proxy: an unusually high cached share means most answers are frozen
    history — quality complaints then point at the cache, not the model."""
    recent = runs[-window:]
    cached = sum(1 for r in recent if r.get("cached"))
    share = cached / len(recent) if recent else 0.0
    return {
        "source": "D5",
        "alert": bool(recent) and share > max_cached_share,
        "cached_share": round(share, 4),
        "max_cached_share": max_cached_share,
        "recent_runs": len(recent),
    }


def snapshot_corpus(skills_dir: Path) -> dict:
    """D3 baseline: per-skill content hashes plus corpus size totals."""
    skills: dict = {}
    total_chars = 0
    for md in sorted(skills_dir.glob("*/SKILL.md")):
        text = md.read_text(encoding="utf-8")
        total_chars += len(text)
        skills[md.parent.name] = {
            "sha256": hashlib.sha256(text.encode("utf-8")).hexdigest(),
            "chars": len(text),
        }
    return {"skill_count": len(skills), "total_chars": total_chars, "skills": skills}


def diff_corpus(
    old: dict, new: dict, *, max_growth_ratio: float = 0.10
) -> dict:
    """D3: compare two corpus snapshots; alert on silent growth beyond ratio.

    Per-skill changes are listed regardless — D3 is patch-style drift, so the
    valuable output is *which* skills changed, not just that the total grew.
    """
    old_skills = old.get("skills") or {}
    new_skills = new.get("skills") or {}
    added = sorted(set(new_skills) - set(old_skills))
    removed = sorted(set(old_skills) - set(new_skills))
    changed = sorted(
        name
        for name in set(old_skills) & set(new_skills)
        if old_skills[name]["sha256"] != new_skills[name]["sha256"]
    )
    old_total = int(old.get("total_chars", 0) or 0)
    new_total = int(new.get("total_chars", 0) or 0)
    growth = (new_total - old_total) / old_total if old_total else 0.0
    return {
        "source": "D3",
        "alert": growth > max_growth_ratio,
        "added": added,
        "removed": removed,
        "changed": changed,
        "old_total_chars": old_total,
        "new_total_chars": new_total,
        "growth_ratio": round(growth, 4),
        "max_growth_ratio": max_growth_ratio,
    }


def run_all_detectors(runs: List[dict], *, window: int = DEFAULT_WINDOW) -> dict:
    reports = [
        detect_model_change(runs, window=window),
        detect_failure_rate_shift(runs, window=window),
        detect_cache_staleness(runs, window=window),
    ]
    return {
        "total_runs": len(runs),
        "window": window,
        "alerts": [r["source"] for r in reports if r["alert"]],
        "reports": reports,
    }
