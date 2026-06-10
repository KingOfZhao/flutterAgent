#!/usr/bin/env python3
"""Harvest candidate regression samples from logs/runs.jsonl.

First stage of the reinforcement flywheel (knowledge/capability-fixation.md §8):
scan run history for runs where the pipeline itself recorded unresolved
problems and emit them as JSONL candidates for human/strong-model triage.

Usage:

  python scripts/harvest_failures.py                      # -> ./eval/candidates.jsonl
  python scripts/harvest_failures.py --runs logs/runs.jsonl -o out.jsonl --limit 50
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

from flutter_agent.run_store import RunStore  # noqa: E402


def main(
    runs: Path = typer.Option(
        ROOT / "logs" / "runs.jsonl", "--runs", help="Path to runs.jsonl."
    ),
    out: Path = typer.Option(
        ROOT / "eval" / "candidates.jsonl", "--out", "-o", help="Destination JSONL file."
    ),
    limit: int = typer.Option(100, "--limit", help="Max candidates to emit."),
    since: int = typer.Option(0, "--since", help="Skip runs older than this epoch (seconds)."),
) -> None:
    store = RunStore(runs)
    candidates = store.harvest_failures(limit=limit, since=since)
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for row in candidates:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    reason_counts: dict = {}
    for row in candidates:
        for r in row.get("reasons", []):
            reason_counts[r] = reason_counts.get(r, 0) + 1
    typer.echo(f"[harvest] {len(candidates)} candidate(s) -> {out}")
    for r, n in sorted(reason_counts.items(), key=lambda kv: -kv[1]):
        typer.echo(f"[harvest]   {r}: {n}")


if __name__ == "__main__":
    typer.run(main)
