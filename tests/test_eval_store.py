"""Tests for eval_store (eval-set loading, validation, sealed split)."""
from __future__ import annotations

import json
from pathlib import Path

from flutter_agent.eval_store import (
    draft_from_candidate,
    is_draft,
    is_sealed,
    load_samples,
    split_sealed,
    validate_sample,
)


def _sample(sample_id: str, **overrides) -> dict:
    base = {
        "id": sample_id,
        "kind": "regression",
        "requirement": "需求 " + sample_id,
        "rubric": {
            "hard_criteria": ["输出为合法 JSON"],
            "quality_dims": ["验收标准可测"],
        },
    }
    base.update(overrides)
    return base


def _write(path: Path, samples: list[dict]) -> None:
    path.write_text(
        "\n".join(json.dumps(s, ensure_ascii=False) for s in samples) + "\n",
        encoding="utf-8",
    )


def test_valid_sample_has_no_errors():
    assert validate_sample(_sample("s-1")) == []


def test_validation_catches_missing_fields():
    errors = validate_sample({"id": "", "rubric": {}})
    assert "missing id" in errors
    assert "missing requirement" in errors
    assert any("hard_criteria" in e for e in errors)


def test_unknown_kind_rejected():
    assert any("kind" in e for e in validate_sample(_sample("s-1", kind="vibe")))


def test_load_skips_invalid_rows(tmp_path: Path):
    p = tmp_path / "samples.jsonl"
    p.write_text(
        json.dumps(_sample("good")) + "\nnot-json\n" + json.dumps({"id": "bad"}) + "\n",
        encoding="utf-8",
    )
    samples = load_samples(p)
    assert [s["id"] for s in samples] == ["good"]


def test_load_strict_raises(tmp_path: Path):
    p = tmp_path / "samples.jsonl"
    p.write_text(json.dumps({"id": "bad"}) + "\n", encoding="utf-8")
    try:
        load_samples(p, strict=True)
    except ValueError as exc:
        assert "missing requirement" in str(exc)
    else:
        raise AssertionError("expected ValueError")


def test_load_rejects_duplicate_ids(tmp_path: Path):
    p = tmp_path / "samples.jsonl"
    _write(p, [_sample("dup"), _sample("dup")])
    assert len(load_samples(p)) == 1


def test_missing_file_returns_empty(tmp_path: Path):
    assert load_samples(tmp_path / "nope.jsonl") == []


def test_sealed_split_is_deterministic_and_stable():
    ids = [f"s-{i}" for i in range(200)]
    first = {i: is_sealed(i) for i in ids}
    second = {i: is_sealed(i) for i in ids}
    assert first == second
    sealed_count = sum(first.values())
    # ratio 0.2 over 200 ids: loose bounds, deterministic so never flaky.
    assert 20 <= sealed_count <= 60


def test_committed_smoke_samples_are_valid():
    repo_root = Path(__file__).resolve().parents[1]
    samples = load_samples(repo_root / "eval" / "smoke_samples.jsonl", strict=True)
    assert len(samples) == 3
    assert all(s["kind"] == "smoke" for s in samples)
    assert not any(is_draft(s) for s in samples)


def test_draft_from_candidate_carries_source_and_todo_rubric():
    cand = {
        "id": "run-9",
        "created_at": 1234,
        "requirement": "需求 X",
        "selected_skills": ["skill-a"],
        "reasons": ["final_review_blocking", "bad_package"],
    }
    draft = draft_from_candidate(cand)
    assert draft["id"] == "cand-run-9"
    assert draft["source"]["run_id"] == "run-9"
    assert len(draft["rubric"]["hard_criteria"]) == 2
    assert is_draft(draft)


def test_completed_draft_is_not_draft():
    draft = draft_from_candidate({"id": "run-1", "reasons": ["acceptance_gaps"]})
    draft["rubric"]["hard_criteria"] = ["产出必须覆盖全部验收缺口"]
    draft["rubric"]["quality_dims"] = ["验收标准可测"]
    assert not is_draft(draft)


def test_split_sealed_partitions_all_samples():
    samples = [_sample(f"s-{i}") for i in range(50)]
    working, sealed = split_sealed(samples)
    assert len(working) + len(sealed) == 50
    overlap = {s["id"] for s in working} & {s["id"] for s in sealed}
    assert overlap == set()
