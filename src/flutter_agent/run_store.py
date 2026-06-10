"""Append-only JSON Lines store for past refinement runs.

Each line in ``logs/runs.jsonl`` is a complete ``RefineResponse`` plus a
``created_at`` epoch field, so the file doubles as both an audit log and a
recovery cache. Concurrent appends are serialised with an asyncio lock
because we only target a single-process FastAPI server.
"""
from __future__ import annotations

import asyncio
import json
import logging
from pathlib import Path
from typing import List, Optional

from .schemas import RefineResponse, RunSummary

logger = logging.getLogger(__name__)


class RunStore:
    def __init__(self, path: Path):
        self.path = path
        # Lazily created so RunStore can be instantiated outside an asyncio
        # loop (Python 3.9 raises if asyncio.Lock() is constructed without
        # a current loop).
        self._lock: asyncio.Lock | None = None

    def _get_lock(self) -> asyncio.Lock:
        if self._lock is None:
            self._lock = asyncio.Lock()
        return self._lock

    async def append(self, response: RefineResponse) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        line = json.dumps(response.model_dump(), ensure_ascii=False)
        async with self._get_lock():
            with self.path.open("a", encoding="utf-8") as f:
                f.write(line + "\n")
        logger.info("run %s persisted (%d bytes)", response.id, len(line))

    def list(self, *, limit: int = 50) -> List[RunSummary]:
        if not self.path.exists():
            return []
        # Read tail-first by loading the whole file (fine up to a few MB);
        # for huge histories we'd switch to seek-based reverse scan.
        rows: List[RunSummary] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                logger.warning("skipping corrupt run line: %r", line[:120])
                continue
            try:
                rows.append(_summarise(obj))
            except Exception as exc:  # pragma: no cover - belt & suspenders
                logger.warning("skipping unsummarisable run: %s", exc)
        rows.reverse()
        return rows[:limit]

    def get(self, run_id: str) -> Optional[dict]:
        if not self.path.exists():
            return None
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("id") == run_id:
                return obj
        return None


    def compute_metrics(self) -> dict:
        """Scan all runs and return aggregate stats as a dict.

        Returns a dict matching MetricsResponse fields.
        """
        from collections import Counter

        if not self.path.exists():
            return {}

        total = 0
        cached = 0
        total_tokens = 0
        total_cost = 0.0
        total_elapsed = 0
        bad_pkg = 0
        skill_counter: Counter = Counter()
        stage_ok: dict = {}      # stage -> [bool, ...]
        stage_total: dict = {}

        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue

            total += 1
            if obj.get("cached"):
                cached += 1

            usage = obj.get("usage") or {}
            total_tokens += int(usage.get("total_tokens", 0) or 0)

            cost = obj.get("cost") or {}
            total_cost += float(cost.get("total_cost_usd", 0) or 0)

            for s in obj.get("stages", []):
                elapsed = int(s.get("elapsed_ms", 0) or 0)
                total_elapsed += elapsed
                sname = s.get("stage", "")
                if sname:
                    stage_total[sname] = stage_total.get(sname, 0) + 1
                    if s.get("stage_valid", True):
                        stage_ok[sname] = stage_ok.get(sname, 0) + 1

            for sk in obj.get("selected_skills", []):
                skill_counter[sk] += 1

            validations = obj.get("validations") or []
            for v in validations:
                if isinstance(v, dict) and (
                    not v.get("exists")
                    or v.get("is_discontinued")
                    or v.get("constraint_ok") is False
                ):
                    bad_pkg += 1

        avg_elapsed = (total_elapsed / total) if total else 0.0
        top_skills = [sk for sk, _ in skill_counter.most_common(10)]

        success_rate = {}
        for sname, count in stage_total.items():
            ok_count = stage_ok.get(sname, 0)
            success_rate[sname] = round(ok_count / count, 4) if count else 1.0

        return {
            "total_runs": total,
            "cached_runs": cached,
            "total_tokens": total_tokens,
            "total_cost_usd": round(total_cost, 6),
            "avg_elapsed_ms": round(avg_elapsed, 1),
            "bad_packages_total": bad_pkg,
            "top_skills": top_skills,
            "stage_success_rate": success_rate,
        }


    def harvest_failures(self, *, limit: int = 100, since: int = 0) -> List[dict]:
        """Scan all runs and return candidate regression samples.

        A run is a candidate when the pipeline itself recorded unresolved
        problems: a still-blocking final review pass, deterministic
        acceptance gaps, failed package validations, or an invalid stage.
        Output rows carry the failure reasons so a reviewer can decide
        which candidates deserve a rubric and a place in the eval set.
        ``since`` (epoch seconds) skips older runs so periodic harvests
        only re-triage the new tail of the log.
        """
        if not self.path.exists():
            return []
        rows: List[dict] = []
        for line in self.path.read_text(encoding="utf-8").splitlines():
            line = line.strip()
            if not line:
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if obj.get("cached"):
                continue
            if since and int(obj.get("created_at", 0) or 0) < since:
                continue
            reasons = _failure_reasons(obj)
            if reasons:
                rows.append(
                    {
                        "id": str(obj.get("id", "")),
                        "created_at": int(obj.get("created_at", 0) or 0),
                        "requirement": str(obj.get("requirement", "")),
                        "selected_skills": list(obj.get("selected_skills") or []),
                        "reasons": reasons,
                    }
                )
        rows.reverse()
        return rows[:limit]


def _failure_reasons(obj: dict) -> List[str]:
    reasons: List[str] = []
    history = obj.get("review_history") or []
    if history:
        last = history[-1]
        if isinstance(last, dict) and last.get("blocking"):
            reasons.append("final_review_blocking")
    if obj.get("acceptance_gaps"):
        reasons.append("acceptance_gaps")
    for v in obj.get("validations") or []:
        if isinstance(v, dict) and (
            not v.get("exists")
            or v.get("is_discontinued")
            or v.get("constraint_ok") is False
        ):
            reasons.append("bad_package")
            break
    for s in obj.get("stages") or []:
        if isinstance(s, dict) and s.get("stage_valid", True) is False:
            reasons.append("invalid_stage")
            break
    return reasons


def _summarise(obj: dict) -> RunSummary:
    elapsed = sum(int(s.get("elapsed_ms", 0) or 0) for s in obj.get("stages", []))
    validations = obj.get("validations") or []
    bad = sum(
        1
        for v in validations
        if isinstance(v, dict)
        and (
            not v.get("exists")
            or v.get("is_discontinued")
            or v.get("constraint_ok") is False
        )
    )
    return RunSummary(
        id=str(obj.get("id", "")),
        created_at=int(obj.get("created_at", 0) or 0),
        cached=bool(obj.get("cached", False)),
        cache_key=str(obj.get("cache_key", "")),
        requirement=str(obj.get("requirement", ""))[:240],
        selected_skills=list(obj.get("selected_skills") or []),
        usage=obj.get("usage") or {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0},
        cost=obj.get("cost"),
        elapsed_ms_total=elapsed,
        stages=[str(s.get("stage", "")) for s in obj.get("stages", [])],
        bad_packages=bad,
    )
