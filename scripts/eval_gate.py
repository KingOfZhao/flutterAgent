#!/usr/bin/env python3
"""Run the eval gate: candidate judge results vs baseline (flywheel stage 4: 门).

Exit code 0 when the gate passes (tie or improved), 1 when blocked — so it
can sit directly in CI before merging skill/prompt/model changes.

Usage:

  python scripts/eval_gate.py --samples eval/samples.jsonl \
      --baseline eval/results_baseline.jsonl --candidate eval/results_candidate.jsonl
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import typer

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.eval_gate import DEFAULT_NOISE_MARGIN, gate, load_results  # noqa: E402
from flutter_agent.eval_store import load_samples  # noqa: E402


def main(
    samples: Path = typer.Option(
        ROOT / "eval" / "samples.jsonl", "--samples", help="Eval set JSONL."
    ),
    baseline: Path = typer.Option(..., "--baseline", help="Baseline judge results JSONL."),
    candidate: Path = typer.Option(..., "--candidate", help="Candidate judge results JSONL."),
    noise_margin: float = typer.Option(
        DEFAULT_NOISE_MARGIN, "--noise-margin", help="Quality delta treated as a tie."
    ),
) -> None:
    report = gate(
        load_samples(samples),
        load_results(baseline),
        load_results(candidate),
        noise_margin=noise_margin,
    )
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    raise typer.Exit(code=0 if report["passed"] else 1)


if __name__ == "__main__":
    typer.run(main)
