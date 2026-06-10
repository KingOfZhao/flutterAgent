"""Tests for RunStore.harvest_failures (reinforcement flywheel stage 1)."""
from __future__ import annotations

import json
from pathlib import Path

from flutter_agent.run_store import RunStore, _failure_reasons


def _run(run_id: str, **overrides) -> dict:
    base = {
        "id": run_id,
        "created_at": 1000,
        "cached": False,
        "requirement": "需求 " + run_id,
        "selected_skills": ["skill-a"],
        "stages": [],
        "review_history": [],
        "acceptance_gaps": [],
        "validations": [],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }
    base.update(overrides)
    return base


def _write(path: Path, runs: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(r, ensure_ascii=False) for r in runs) + "\n",
        encoding="utf-8",
    )


def test_clean_runs_yield_no_candidates(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    _write(p, [_run("ok-1"), _run("ok-2")])
    assert RunStore(p).harvest_failures() == []


def test_blocking_final_review_is_harvested(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    history = [
        {"iteration": 0, "blocking": True},
        {"iteration": 1, "blocking": True},
    ]
    _write(p, [_run("bad-1", review_history=history)])
    rows = RunStore(p).harvest_failures()
    assert len(rows) == 1
    assert rows[0]["id"] == "bad-1"
    assert "final_review_blocking" in rows[0]["reasons"]


def test_resolved_review_is_not_harvested(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    history = [
        {"iteration": 0, "blocking": True},
        {"iteration": 1, "blocking": False},
    ]
    _write(p, [_run("fixed-1", review_history=history)])
    assert RunStore(p).harvest_failures() == []


def test_multiple_reasons_collected(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    run = _run(
        "bad-2",
        acceptance_gaps=[{"kind": "missing_acceptance"}],
        validations=[{"package": "x", "exists": False}],
        stages=[{"stage": "review", "stage_valid": False, "elapsed_ms": 1}],
    )
    _write(p, [run])
    rows = RunStore(p).harvest_failures()
    assert rows[0]["reasons"] == ["acceptance_gaps", "bad_package", "invalid_stage"]


def test_cached_runs_are_skipped(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    run = _run("cached-1", cached=True, acceptance_gaps=[{"kind": "gap"}])
    _write(p, [run])
    assert RunStore(p).harvest_failures() == []


def test_limit_and_newest_first(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    runs = [
        _run(f"bad-{i}", created_at=1000 + i, acceptance_gaps=[{"kind": "gap"}])
        for i in range(5)
    ]
    _write(p, runs)
    rows = RunStore(p).harvest_failures(limit=2)
    assert [r["id"] for r in rows] == ["bad-4", "bad-3"]


def test_failure_reasons_empty_for_clean_run():
    assert _failure_reasons(_run("ok")) == []


def test_missing_file_returns_empty(tmp_path: Path):
    assert RunStore(tmp_path / "absent.jsonl").harvest_failures() == []
