"""Closed-loop review helpers.

These are the pure, model-independent pieces of the review→re-implement loop:
severity ranking, the blocking decision, merging deterministic structural
findings, the per-pass audit record, and turning findings into feedback.

Kept out of ``pipeline.py`` so the orchestration there stays readable; the
pipeline imports these names directly.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from .consistency import check_implementation_consistency
from .schemas import ReviewPass, Stage

_SEVERITY_RANK = {"blocker": 3, "major": 2, "minor": 1, "nit": 0}


def _blocking_severities(threshold: str) -> set:
    """Severities at or above the configured threshold count as blocking."""
    t = _SEVERITY_RANK.get(str(threshold).lower(), 2)
    return {s for s, r in _SEVERITY_RANK.items() if r >= t}


def _review_is_blocking(
    review: Optional[Dict[str, Any]], threshold: str = "major"
) -> bool:
    """A review blocks the implementation when it says so, or when any finding
    is at/above the configured severity threshold. Defensive against loose
    fields."""
    if not isinstance(review, dict):
        return False
    if review.get("blocking") is True:
        return True
    blocking = _blocking_severities(threshold)
    findings = review.get("findings")
    if isinstance(findings, list):
        for f in findings:
            if isinstance(f, dict) and str(f.get("severity", "")).lower() in blocking:
                return True
    return False


def _augment_review_with_consistency(prior: Dict[Stage, Dict[str, Any]]) -> int:
    """Merge deterministic structural findings into prior[review].findings.

    Returns the number of static findings added. Idempotent per review output:
    each fresh review starts without static findings, so re-reviews re-derive
    them from the (possibly updated) implementation."""
    review = prior.get(Stage.review)
    if not isinstance(review, dict):
        return 0
    static = check_implementation_consistency(
        prior.get(Stage.implementation),
        prior.get(Stage.breakdown),
        prior.get(Stage.architecture),
    )
    if not static:
        return 0
    findings = review.get("findings")
    if not isinstance(findings, list):
        findings = []
    existing = {
        (f.get("path"), f.get("issue"))
        for f in findings
        if isinstance(f, dict)
    }
    added = 0
    for f in static:
        if (f["path"], f["issue"]) not in existing:
            findings.append(f)
            added += 1
    review["findings"] = findings
    return added


def _summarize_review_pass(
    review: Optional[Dict[str, Any]], iteration: int, threshold: str = "major"
) -> ReviewPass:
    """Compact audit entry for one review evaluation."""
    by_severity: Dict[str, int] = {}
    by_source: Dict[str, int] = {}
    total = 0
    summary = None
    if isinstance(review, dict):
        s = review.get("summary")
        if isinstance(s, str) and s.strip():
            summary = s.strip()
        findings = review.get("findings")
        if isinstance(findings, list):
            for f in findings:
                if not isinstance(f, dict):
                    continue
                total += 1
                sev = str(f.get("severity", "unknown")).lower()
                by_severity[sev] = by_severity.get(sev, 0) + 1
                src = str(f.get("source", "llm")).lower()
                by_source[src] = by_source.get(src, 0) + 1
    return ReviewPass(
        iteration=iteration,
        blocking=_review_is_blocking(review, threshold),
        findings=total,
        by_severity=by_severity,
        by_source=by_source,
        summary=summary,
    )


def _format_review_feedback(review: Dict[str, Any], threshold: str = "major") -> str:
    """Turn review findings into a concrete fix list fed back to implementation."""
    blocking = _blocking_severities(threshold)
    lines: List[str] = []
    summary = review.get("summary")
    if isinstance(summary, str) and summary.strip():
        lines.append(f"评审总评: {summary.strip()}")
    findings = review.get("findings")
    if isinstance(findings, list):
        for i, f in enumerate(findings, 1):
            if not isinstance(f, dict):
                continue
            sev = str(f.get("severity", "?"))
            if sev.lower() not in blocking:
                continue
            path = f.get("path", "<general>")
            issue = f.get("issue", "")
            sug = f.get("suggestion", "")
            lines.append(f"{i}. [{sev}] {path}: {issue} → 修复建议: {sug}")
    lines.append(
        f"请在保留原有文件结构的前提下,仅针对上述 {'/'.join(sorted(blocking))} 级别问题修订骨架,"
        "输出完整的 implementation JSON(不要省略未改动的文件)。"
    )
    return "\n".join(lines)
