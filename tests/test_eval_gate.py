"""Tests for eval_gate (ratchet change gate: 不劣于 + 噪声判平)."""
from __future__ import annotations

import json
from pathlib import Path

from flutter_agent.eval_gate import gate, load_results
from flutter_agent.eval_store import DRAFT_MARKER


def _sample(sample_id: str, draft: bool = False) -> dict:
    hard = [f"{DRAFT_MARKER}: 待写"] if draft else ["输出为合法 JSON"]
    return {
        "id": sample_id,
        "kind": "regression",
        "requirement": "需求 " + sample_id,
        "rubric": {"hard_criteria": hard, "quality_dims": ["可测性"]},
    }


def _res(sample_id: str, hard_pass: bool = True, quality: float = 0.8) -> dict:
    return {"sample_id": sample_id, "hard_pass": hard_pass, "quality": quality}


def test_tie_within_noise_passes():
    samples = [_sample("a"), _sample("b")]
    base = {"a": _res("a", quality=0.80), "b": _res("b", quality=0.80)}
    cand = {"a": _res("a", quality=0.78), "b": _res("b", quality=0.80)}
    report = gate(samples, base, cand)
    assert report["passed"] and report["verdict"] == "tie"


def test_hard_regression_blocks():
    samples = [_sample("a")]
    base = {"a": _res("a", hard_pass=True)}
    cand = {"a": _res("a", hard_pass=False, quality=0.99)}
    report = gate(samples, base, cand)
    assert not report["passed"]
    assert report["hard_regressions"] == ["a"]


def test_quality_drop_beyond_noise_blocks():
    samples = [_sample("a")]
    base = {"a": _res("a", quality=0.90)}
    cand = {"a": _res("a", quality=0.70)}
    report = gate(samples, base, cand)
    assert report["verdict"] == "blocked" and not report["passed"]


def test_gain_beyond_noise_is_improved():
    samples = [_sample("a")]
    base = {"a": _res("a", quality=0.70)}
    cand = {"a": _res("a", quality=0.90)}
    report = gate(samples, base, cand)
    assert report["verdict"] == "improved" and report["passed"]


def test_missing_candidate_result_blocks():
    samples = [_sample("a"), _sample("b")]
    base = {"a": _res("a"), "b": _res("b")}
    cand = {"a": _res("a")}
    report = gate(samples, base, cand)
    assert not report["passed"]
    assert report["missing_in_candidate"] == ["b"]


def test_drafts_are_excluded():
    samples = [_sample("a"), _sample("d", draft=True)]
    base = {"a": _res("a"), "d": _res("d", hard_pass=True)}
    cand = {"a": _res("a"), "d": _res("d", hard_pass=False)}
    report = gate(samples, base, cand)
    assert report["passed"]
    assert report["excluded_drafts"] == 1


def test_load_results_parses_and_dedupes(tmp_path: Path):
    p = tmp_path / "results.jsonl"
    rows = [_res("a", quality=0.1), _res("a", quality=0.9), {"no_id": True}]
    p.write_text("\n".join(json.dumps(r) for r in rows) + "\nbad-json\n", encoding="utf-8")
    results = load_results(p)
    assert set(results) == {"a"}
    assert results["a"]["quality"] == 0.9


def test_missing_results_file_is_empty(tmp_path: Path):
    assert load_results(tmp_path / "nope.jsonl") == {}
