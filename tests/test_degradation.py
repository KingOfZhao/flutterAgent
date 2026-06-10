"""Tests for degradation detectors (taxonomy D1/D2/D5 automation)."""
from __future__ import annotations

import json
from pathlib import Path

from flutter_agent.degradation import (
    detect_cache_staleness,
    detect_failure_rate_shift,
    detect_model_change,
    load_runs,
    run_all_detectors,
)


def _run(run_id: str, *, model: str = "deepseek-chat", cached: bool = False, failing: bool = False) -> dict:
    return {
        "id": run_id,
        "created_at": 1000,
        "cached": cached,
        "requirement": "需求",
        "stages": [{"stage": "user_stories", "model": model, "stage_valid": True}],
        "review_history": [],
        "acceptance_gaps": ["缺验收"] if failing else [],
        "validations": [],
    }


def test_model_change_detected():
    runs = [_run(f"a{i}") for i in range(3)] + [_run("b", model="deepseek-v4")]
    report = detect_model_change(runs)
    assert report["alert"]
    assert report["transitions"][0]["from"] == "deepseek-chat"
    assert report["transitions"][0]["to"] == "deepseek-v4"


def test_stable_model_no_alert():
    report = detect_model_change([_run(f"a{i}") for i in range(5)])
    assert not report["alert"]
    assert report["models_seen"] == ["deepseek-chat"]


def test_failure_rate_shift_alerts():
    prior = [_run(f"p{i}") for i in range(10)]
    recent = [_run(f"r{i}", failing=True) for i in range(10)]
    report = detect_failure_rate_shift(prior + recent, window=10)
    assert report["alert"]
    assert report["recent_failure_rate"] == 1.0
    assert report["prior_failure_rate"] == 0.0


def test_failure_rate_no_prior_window_no_alert():
    report = detect_failure_rate_shift([_run(f"r{i}", failing=True) for i in range(5)], window=10)
    assert not report["alert"]


def test_cache_staleness_alerts_on_high_share():
    runs = [_run(f"c{i}", cached=True) for i in range(9)] + [_run("f")]
    report = detect_cache_staleness(runs, window=10)
    assert report["alert"]
    assert report["cached_share"] == 0.9


def test_cache_staleness_ok_below_threshold():
    runs = [_run(f"c{i}", cached=i % 2 == 0) for i in range(10)]
    assert not detect_cache_staleness(runs, window=10)["alert"]


def test_run_all_detectors_aggregates_alerts():
    runs = [_run(f"p{i}") for i in range(10)] + [
        _run(f"r{i}", model="deepseek-v4", failing=True) for i in range(10)
    ]
    summary = run_all_detectors(runs, window=10)
    assert "D1" in summary["alerts"]
    assert "D1/D2" in summary["alerts"]
    assert summary["total_runs"] == 20


def test_load_runs_skips_bad_lines(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    p.write_text(json.dumps(_run("ok")) + "\nnot-json\n", encoding="utf-8")
    assert [r["id"] for r in load_runs(p)] == ["ok"]
    assert load_runs(tmp_path / "nope.jsonl") == []
