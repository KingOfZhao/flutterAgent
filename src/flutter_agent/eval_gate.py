"""Eval gate: compare candidate results against a baseline (flywheel stage 4).

Implements the ratchet's change-gate rule from
``knowledge/capability-fixation.md`` §2: a change passes only when it is
*not worse* than the baseline — hard-criterion regressions block outright,
and mean quality may not drop by more than the noise margin (differences
within noise are treated as a tie, never as an improvement claim).

Result rows are judge outputs, one per sample:
``{"sample_id": str, "hard_pass": bool, "quality": float}``.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Dict, List

from .eval_store import is_draft

DEFAULT_NOISE_MARGIN = 0.05


def load_results(path: Path) -> Dict[str, dict]:
    """Load judge results keyed by sample_id; last row wins on duplicates."""
    if not path.exists():
        return {}
    rows: Dict[str, dict] = {}
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        sid = str(obj.get("sample_id", "")).strip()
        if not sid:
            continue
        rows[sid] = {
            "sample_id": sid,
            "hard_pass": bool(obj.get("hard_pass", False)),
            "quality": float(obj.get("quality", 0.0) or 0.0),
        }
    return rows


def gate(
    samples: List[dict],
    baseline: Dict[str, dict],
    candidate: Dict[str, dict],
    *,
    noise_margin: float = DEFAULT_NOISE_MARGIN,
) -> dict:
    """Return a gate report: passed flag, verdict, regressions, coverage.

    Rules, in order:
    1. Drafts are excluded; they carry no verified rubric.
    2. A sample present in baseline but missing from candidate blocks
       (silent coverage loss is a regression, not a tie).
    3. hard_pass True -> False on any sample blocks.
    4. Mean quality drop beyond ``noise_margin`` blocks; within margin is
       a tie; only a gain beyond margin may be called an improvement.
    """
    eligible = [s for s in samples if not is_draft(s)]
    hard_regressions: List[str] = []
    missing: List[str] = []
    base_q: List[float] = []
    cand_q: List[float] = []

    for s in eligible:
        sid = str(s["id"])
        b = baseline.get(sid)
        c = candidate.get(sid)
        if b is None:
            continue
        if c is None:
            missing.append(sid)
            continue
        if b["hard_pass"] and not c["hard_pass"]:
            hard_regressions.append(sid)
        base_q.append(b["quality"])
        cand_q.append(c["quality"])

    mean_base = sum(base_q) / len(base_q) if base_q else 0.0
    mean_cand = sum(cand_q) / len(cand_q) if cand_q else 0.0
    delta = mean_cand - mean_base

    if hard_regressions or missing:
        verdict = "blocked"
    elif delta < -noise_margin:
        verdict = "blocked"
    elif delta > noise_margin:
        verdict = "improved"
    else:
        verdict = "tie"

    return {
        "passed": verdict in ("tie", "improved"),
        "verdict": verdict,
        "compared_samples": len(base_q),
        "excluded_drafts": len(samples) - len(eligible),
        "missing_in_candidate": missing,
        "hard_regressions": hard_regressions,
        "mean_quality_baseline": round(mean_base, 4),
        "mean_quality_candidate": round(mean_cand, 4),
        "quality_delta": round(delta, 4),
        "noise_margin": noise_margin,
    }
