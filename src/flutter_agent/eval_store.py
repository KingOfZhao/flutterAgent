"""Eval-set storage: load, validate and split regression samples.

Samples live in JSONL files under ``eval/``. Each sample carries a rubric
with hard (veto) criteria and scored quality dimensions, following
``knowledge/claude-eval-methodology.md``. The sealed holdout split is
deterministic on the sample id so the same sample never migrates between
the working set and the sealed set as the file grows.
"""
from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import List, Tuple

SAMPLE_KINDS = ("regression", "smoke")

DRAFT_MARKER = "TODO(判)"


def draft_from_candidate(candidate: dict) -> dict:
    """Turn a harvested failure candidate into a draft eval sample.

    The rubric is intentionally a template: hard criteria and quality
    dimensions must be written by a human (or strong-model-assisted) triage
    pass before the sample counts toward the eval set. Drafts are excluded
    by ``is_draft`` until every TODO marker is replaced.
    """
    reasons = list(candidate.get("reasons") or [])
    return {
        "id": f"cand-{candidate.get('id', '')}",
        "kind": "regression",
        "requirement": str(candidate.get("requirement", "")),
        "source": {
            "run_id": str(candidate.get("id", "")),
            "created_at": int(candidate.get("created_at", 0) or 0),
            "reasons": reasons,
            "selected_skills": list(candidate.get("selected_skills") or []),
        },
        "rubric": {
            "hard_criteria": [f"{DRAFT_MARKER}: 把失败机制写成可判定的否决项 (来源: {r})" for r in reasons]
            or [f"{DRAFT_MARKER}: 写出至少一条否决项"],
            "quality_dims": [f"{DRAFT_MARKER}: 写出 1-3 个打分维度"],
        },
    }


def is_draft(sample: dict) -> bool:
    """A sample is a draft while any rubric entry still carries the TODO marker."""
    rubric = sample.get("rubric") or {}
    entries = list(rubric.get("hard_criteria") or []) + list(rubric.get("quality_dims") or [])
    return any(DRAFT_MARKER in str(e) for e in entries)


def validate_sample(obj: dict) -> List[str]:
    """Return a list of human-readable problems; empty list means valid."""
    errors: List[str] = []
    if not isinstance(obj, dict):
        return ["sample is not an object"]
    if not str(obj.get("id", "")).strip():
        errors.append("missing id")
    if not str(obj.get("requirement", "")).strip():
        errors.append("missing requirement")
    kind = obj.get("kind", "regression")
    if kind not in SAMPLE_KINDS:
        errors.append(f"unknown kind: {kind!r}")
    rubric = obj.get("rubric")
    if not isinstance(rubric, dict):
        errors.append("missing rubric")
    else:
        hard = rubric.get("hard_criteria")
        if not isinstance(hard, list) or not hard:
            errors.append("rubric.hard_criteria must be a non-empty list")
        dims = rubric.get("quality_dims")
        if not isinstance(dims, list):
            errors.append("rubric.quality_dims must be a list")
    return errors


def load_samples(path: Path, *, strict: bool = False) -> List[dict]:
    """Load samples from a JSONL file, skipping (or raising on) invalid rows."""
    if not path.exists():
        return []
    samples: List[dict] = []
    seen: set = set()
    for lineno, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            if strict:
                raise ValueError(f"{path}:{lineno}: invalid JSON")
            continue
        errors = validate_sample(obj)
        if not errors and obj["id"] in seen:
            errors = [f"duplicate id: {obj['id']}"]
        if errors:
            if strict:
                raise ValueError(f"{path}:{lineno}: " + "; ".join(errors))
            continue
        seen.add(obj["id"])
        samples.append(obj)
    return samples


def is_sealed(sample_id: str, *, ratio: float = 0.2) -> bool:
    """Deterministically assign a sample to the sealed holdout set.

    Uses the first 8 hex chars of sha256(id) mapped to [0, 1); stable across
    runs, machines and file ordering.
    """
    digest = hashlib.sha256(sample_id.encode("utf-8")).hexdigest()
    bucket = int(digest[:8], 16) / 0xFFFFFFFF
    return bucket < ratio


def split_sealed(samples: List[dict], *, ratio: float = 0.2) -> Tuple[List[dict], List[dict]]:
    """Split samples into (working, sealed) sets deterministically by id."""
    working: List[dict] = []
    sealed: List[dict] = []
    for s in samples:
        (sealed if is_sealed(str(s["id"]), ratio=ratio) else working).append(s)
    return working, sealed
