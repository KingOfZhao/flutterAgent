"""Tests for degradation detectors (taxonomy D1/D2/D5 automation)."""
from __future__ import annotations

import json
from pathlib import Path

from flutter_agent.degradation import (
    detect_cache_staleness,
    detect_failure_rate_shift,
    detect_model_change,
    diff_corpus,
    load_runs,
    run_all_detectors,
    snapshot_corpus,
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


def _corpus(tmp_path: Path, skills: dict) -> Path:
    d = tmp_path / "skills"
    for name, text in skills.items():
        (d / name).mkdir(parents=True, exist_ok=True)
        (d / name / "SKILL.md").write_text(text, encoding="utf-8")
    return d


def test_snapshot_and_diff_detect_changes(tmp_path: Path):
    old_dir = _corpus(tmp_path / "old", {"a": "aaa", "b": "bbb"})
    new_dir = _corpus(tmp_path / "new", {"a": "aaa!", "c": "ccc"})
    report = diff_corpus(snapshot_corpus(old_dir), snapshot_corpus(new_dir))
    assert report["added"] == ["c"]
    assert report["removed"] == ["b"]
    assert report["changed"] == ["a"]


def test_diff_alerts_on_growth(tmp_path: Path):
    old_dir = _corpus(tmp_path / "old", {"a": "x" * 100})
    new_dir = _corpus(tmp_path / "new", {"a": "x" * 100, "b": "y" * 50})
    report = diff_corpus(snapshot_corpus(old_dir), snapshot_corpus(new_dir))
    assert report["alert"]
    assert report["growth_ratio"] == 0.5


def test_diff_no_alert_within_budget(tmp_path: Path):
    old_dir = _corpus(tmp_path / "old", {"a": "x" * 100})
    new_dir = _corpus(tmp_path / "new", {"a": "x" * 105})
    assert not diff_corpus(snapshot_corpus(old_dir), snapshot_corpus(new_dir))["alert"]


def test_load_runs_skips_bad_lines(tmp_path: Path):
    p = tmp_path / "runs.jsonl"
    p.write_text(json.dumps(_run("ok")) + "\nnot-json\n", encoding="utf-8")
    assert [r["id"] for r in load_runs(p)] == ["ok"]
    assert load_runs(tmp_path / "nope.jsonl") == []
