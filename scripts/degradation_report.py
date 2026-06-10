#!/usr/bin/env python3
"""Run all degradation detectors over runs.jsonl and print a JSON report.

Exit code 0 when no detector alerts, 1 when any alert fires — usable both
as a cron health check and an ad-hoc first step of regression attribution
(knowledge/capability-degradation-taxonomy.md 归因总顺序).

Usage:

  python scripts/degradation_report.py
  python scripts/degradation_report.py --runs logs/runs.jsonl --window 100
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

from flutter_agent.degradation import DEFAULT_WINDOW, load_runs, run_all_detectors  # noqa: E402


def main(
    runs: Path = typer.Option(
        ROOT / "logs" / "runs.jsonl", "--runs", help="Path to runs.jsonl."
    ),
    window: int = typer.Option(DEFAULT_WINDOW, "--window", help="Runs per comparison window."),
) -> None:
    summary = run_all_detectors(load_runs(runs), window=window)
    typer.echo(json.dumps(summary, ensure_ascii=False, indent=2))
    raise typer.Exit(code=1 if summary["alerts"] else 0)


if __name__ == "__main__":
    typer.run(main)
