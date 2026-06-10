#!/usr/bin/env python3
"""Turn harvested candidates into draft eval samples (flywheel stage 2: 判).

Reads ``eval/candidates.jsonl`` (output of scripts/harvest_failures.py) and
emits draft samples with a rubric template into ``eval/drafts.jsonl``.
Drafts carry TODO(判) markers and are ignored by the eval gate until a human
(or strong-model-assisted) triage pass replaces every marker with a real,
decidable criterion.

Usage:

  python scripts/triage_candidates.py
  python scripts/triage_candidates.py --candidates eval/candidates.jsonl -o eval/drafts.jsonl
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

from flutter_agent.eval_store import draft_from_candidate  # noqa: E402


def main(
    candidates: Path = typer.Option(
        ROOT / "eval" / "candidates.jsonl", "--candidates", help="Harvested candidates JSONL."
    ),
    out: Path = typer.Option(
        ROOT / "eval" / "drafts.jsonl", "--out", "-o", help="Destination drafts JSONL."
    ),
) -> None:
    if not candidates.exists():
        typer.echo(f"[triage] no candidates file: {candidates}")
        raise typer.Exit(code=1)
    drafts = []
    for line in candidates.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            obj = json.loads(line)
        except json.JSONDecodeError:
            continue
        drafts.append(draft_from_candidate(obj))
    out.parent.mkdir(parents=True, exist_ok=True)
    with out.open("w", encoding="utf-8") as f:
        for d in drafts:
            f.write(json.dumps(d, ensure_ascii=False) + "\n")
    typer.echo(f"[triage] {len(drafts)} draft(s) -> {out} (fill every TODO(判) before gating)")


if __name__ == "__main__":
    typer.run(main)
