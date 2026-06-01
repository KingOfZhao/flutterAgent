#!/usr/bin/env python3
"""Continuous open-source ingestion CLI.

Discover development/coding-focused open-source signals (Hugging Face models,
arXiv papers) and optionally scaffold them into distillation-ready skills.

Examples:

  # Discover with the default watch-list, print a table, remember what's seen
  python scripts/ingest_cli.py discover

  # Custom queries, JSON out, do NOT update the seen-store (dry run)
  python scripts/ingest_cli.py discover -q "code agent" -q "dart" \\
      --json out/digest.json --no-commit

  # Only new candidates, and scaffold each into skills/<id>/SKILL.md
  python scripts/ingest_cli.py discover --only-new --scaffold-dir skills

Cron (continuous): run daily and append new candidates to a digest log:

  0 7 * * *  cd /path/to/flutterAgent && .venv/bin/python scripts/ingest_cli.py \\
             discover --only-new --json data/digests/$(date +\\%F).json

Note: discovery + scaffolding cost NO model tokens. Filling a scaffold's
five cognitive layers into a real skill requires a model run (token/compute).
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import httpx
import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.config import get_settings  # noqa: E402
from flutter_agent.deepseek_client import DeepSeekClient  # noqa: E402
from flutter_agent.ingestion import (  # noqa: E402
    DEFAULT_QUERIES,
    ArxivSource,
    HuggingFaceSource,
    Ingestor,
    SeenStore,
    candidate_skill_id,
    candidate_to_skill_scaffold,
    distill_candidate,
)

app = typer.Typer(add_completion=False, help="Ingest open-source dev signals.")
console = Console()


@app.callback()
def _main() -> None:
    """Continuous open-source ingestion (Hugging Face + arXiv)."""


@app.command()
def discover(
    query: List[str] = typer.Option(
        None, "--query", "-q", help="Override watch-list query (repeatable)."
    ),
    sources: str = typer.Option(
        "hf,arxiv", "--sources", help="Comma list: hf,arxiv."
    ),
    limit: int = typer.Option(10, "--limit", help="Results per query per source."),
    only_new: bool = typer.Option(False, "--only-new", help="Show only new candidates."),
    commit: bool = typer.Option(
        True, "--commit/--no-commit", help="Update the seen-store after the run."
    ),
    json_out: Optional[Path] = typer.Option(None, "--json", help="Write digest JSON."),
    scaffold_dir: Optional[Path] = typer.Option(
        None, "--scaffold-dir", help="Write a SKILL.md scaffold per new candidate."
    ),
    distill: bool = typer.Option(
        False,
        "--distill",
        help="Fill each scaffold into a mature skill via the model (COSTS TOKENS).",
    ),
    max_distill: int = typer.Option(
        5, "--max-distill", help="Cap model-distilled skills per run (token guard)."
    ),
    timeout: float = typer.Option(15.0, "--timeout"),
) -> None:
    queries = query or list(DEFAULT_QUERIES)
    wanted = {s.strip().lower() for s in sources.split(",") if s.strip()}
    settings = get_settings()
    seen = SeenStore(settings.ingestion_seen_file)

    digest = asyncio.run(_run(queries, wanted, limit, seen, timeout))

    rows = [c for c in digest.candidates if (c.is_new or not only_new)]
    table = Table(title=f"Ingestion — {digest.new_count} new / {digest.total} total")
    table.add_column("new", justify="center")
    table.add_column("src")
    table.add_column("kind")
    table.add_column("title", overflow="fold", max_width=48)
    table.add_column("dl/likes", justify="right")
    table.add_column("url", overflow="fold", max_width=42)
    for c in rows:
        m = c.metrics
        metric = f"{m.get('downloads', 0)}/{m.get('likes', 0)}" if m else "—"
        table.add_row(
            "★" if c.is_new else "",
            c.source[:4],
            c.kind,
            c.title,
            metric,
            c.url,
        )
    console.print(table)
    ok = ", ".join(f"{k}={'ok' if v else 'FAIL'}" for k, v in digest.sources_ok.items())
    console.print(f"[dim]sources: {ok}[/dim]")

    if scaffold_dir is not None:
        if distill:
            if not settings.deepseek_api_key:
                raise typer.BadParameter(
                    "--distill needs DEEPSEEK_API_KEY (the distill step costs tokens)"
                )
            written = asyncio.run(
                _distill_and_write(rows, scaffold_dir, only_new, max_distill, settings)
            )
            console.print(
                f"[green]distilled {written} skill(s) via model -> {scaffold_dir}[/green]"
            )
        else:
            written = _write_scaffolds(rows, scaffold_dir, only_new)
            console.print(
                f"[green]scaffolded {written} skill(s) -> {scaffold_dir}[/green]"
            )

    if json_out is not None:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            digest.model_dump_json(indent=2), encoding="utf-8"
        )
        console.print(f"[green]wrote {json_out}[/green]")

    if commit:
        seen.commit(digest.candidates)
        console.print(f"[dim]seen-store updated: {settings.ingestion_seen_file}[/dim]")
    else:
        console.print("[dim]--no-commit: seen-store unchanged[/dim]")


def _write_scaffolds(rows, scaffold_dir: Path, only_new: bool) -> int:
    written = 0
    for c in rows:
        if only_new and not c.is_new:
            continue
        sid = candidate_skill_id(c)
        dest = scaffold_dir / sid / "SKILL.md"
        if dest.exists():
            continue  # never clobber an existing (possibly filled) skill
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(candidate_to_skill_scaffold(c), encoding="utf-8")
        written += 1
    return written


async def _distill_and_write(
    rows, scaffold_dir: Path, only_new: bool, max_distill: int, settings
) -> int:
    """Distill (model-fill) up to ``max_distill`` candidates into skills."""
    client = DeepSeekClient(settings)
    written = 0
    try:
        for c in rows:
            if written >= max_distill:
                break
            if only_new and not c.is_new:
                continue
            sid = candidate_skill_id(c)
            dest = scaffold_dir / sid / "SKILL.md"
            if dest.exists():
                continue  # never clobber an existing (possibly filled) skill
            markdown = await distill_candidate(client, c, model=settings.deepseek_model)
            dest.parent.mkdir(parents=True, exist_ok=True)
            dest.write_text(markdown, encoding="utf-8")
            written += 1
    finally:
        await client.aclose()
    return written


async def _run(queries, wanted, limit, seen, timeout):
    async with httpx.AsyncClient(timeout=timeout, follow_redirects=True) as client:
        srcs = []
        if "hf" in wanted or "huggingface" in wanted:
            srcs.append(HuggingFaceSource(client))
        if "arxiv" in wanted:
            srcs.append(ArxivSource(client))
        if not srcs:
            raise typer.BadParameter("no valid sources; use hf and/or arxiv")
        return await Ingestor(srcs, seen=seen).discover(queries, limit_per_query=limit)


if __name__ == "__main__":
    app()
