#!/usr/bin/env python3
"""Track skill-corpus drift (taxonomy D3): snapshot and diff SKILL.md hashes.

First run writes a baseline snapshot; later runs diff against it and exit 1
when silent growth exceeds the ratio (default 10%) — patch-style prompt
drift is invisible in any single diff, only the cumulative trend shows it.

Usage:

  python scripts/corpus_drift.py snapshot              # write baseline
  python scripts/corpus_drift.py diff                  # compare vs baseline
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

from flutter_agent.degradation import diff_corpus, snapshot_corpus  # noqa: E402

app = typer.Typer(help=__doc__)
DEFAULT_SKILLS = ROOT / "skills"
DEFAULT_BASELINE = ROOT / "eval" / "corpus_baseline.json"


@app.command()
def snapshot(
    skills: Path = typer.Option(DEFAULT_SKILLS, "--skills"),
    out: Path = typer.Option(DEFAULT_BASELINE, "--out", "-o"),
) -> None:
    snap = snapshot_corpus(skills)
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(snap, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"[corpus] {snap['skill_count']} skills / {snap['total_chars']} chars -> {out}")


@app.command()
def diff(
    skills: Path = typer.Option(DEFAULT_SKILLS, "--skills"),
    baseline: Path = typer.Option(DEFAULT_BASELINE, "--baseline"),
    max_growth_ratio: float = typer.Option(0.10, "--max-growth-ratio"),
) -> None:
    if not baseline.exists():
        typer.echo(f"[corpus] no baseline at {baseline}; run `snapshot` first")
        raise typer.Exit(code=1)
    old = json.loads(baseline.read_text(encoding="utf-8"))
    report = diff_corpus(old, snapshot_corpus(skills), max_growth_ratio=max_growth_ratio)
    typer.echo(json.dumps(report, ensure_ascii=False, indent=2))
    raise typer.Exit(code=1 if report["alert"] else 0)


if __name__ == "__main__":
    app()
