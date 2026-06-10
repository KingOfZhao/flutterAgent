"""End-to-end smoke: the committed smoke set drives scripts/eval_gate.py via CLI.

This is the ratchet's own self-test — if the gate chain (samples → results →
verdict → exit code) breaks, CI hookup later would silently pass everything.
"""
from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SMOKE = ROOT / "eval" / "smoke_samples.jsonl"
GATE = ROOT / "scripts" / "eval_gate.py"


def _results(path: Path, rows: list) -> Path:
    path.write_text("\n".join(json.dumps(r) for r in rows) + "\n", encoding="utf-8")
    return path


def _sample_ids() -> list:
    return [
        json.loads(line)["id"]
        for line in SMOKE.read_text(encoding="utf-8").splitlines()
        if line.strip()
    ]


def _run_gate(samples: Path, baseline: Path, candidate: Path):
    return subprocess.run(
        [sys.executable, str(GATE), "--samples", str(samples), "--baseline", str(baseline), "--candidate", str(candidate)],
        capture_output=True,
        text=True,
    )


def test_gate_cli_passes_on_tie(tmp_path: Path):
    rows = [{"sample_id": sid, "hard_pass": True, "quality": 0.8} for sid in _sample_ids()]
    baseline = _results(tmp_path / "baseline.jsonl", rows)
    candidate = _results(tmp_path / "candidate.jsonl", rows)
    proc = _run_gate(SMOKE, baseline, candidate)
    assert proc.returncode == 0, proc.stdout + proc.stderr
    report = json.loads(proc.stdout)
    assert report["verdict"] == "tie"
    assert report["compared_samples"] == 3


def test_gate_cli_blocks_on_hard_regression(tmp_path: Path):
    ids = _sample_ids()
    base_rows = [{"sample_id": sid, "hard_pass": True, "quality": 0.8} for sid in ids]
    cand_rows = [
        {"sample_id": sid, "hard_pass": sid != ids[0], "quality": 0.8} for sid in ids
    ]
    proc = _run_gate(
        SMOKE,
        _results(tmp_path / "baseline.jsonl", base_rows),
        _results(tmp_path / "candidate.jsonl", cand_rows),
    )
    assert proc.returncode == 1
    report = json.loads(proc.stdout)
    assert report["verdict"] == "blocked"
    assert report["hard_regressions"] == [ids[0]]
