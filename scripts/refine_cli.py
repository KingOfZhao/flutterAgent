#!/usr/bin/env python3
"""Command-line wrapper around the refinement pipeline.

Examples:

  python scripts/refine_cli.py "做一个跨端的待办清单 App" \
      --platforms mobile,desktop --out out/todo-spec.md

  python scripts/refine_cli.py - --stdin \
      --platforms mobile --json out/result.json
"""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path
from typing import List, Optional

import typer
from rich.console import Console
from rich.panel import Panel

# Make ``src`` importable when run from the repo root.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.config import get_settings  # noqa: E402
from flutter_agent.deepseek_client import DeepSeekClient, UpstreamError  # noqa: E402
from flutter_agent.pipeline import RefinementPipeline  # noqa: E402
from flutter_agent.schemas import Platform, RefineRequest, Stage  # noqa: E402
from flutter_agent.skill_loader import SkillRegistry  # noqa: E402

app = typer.Typer(add_completion=False, help="Refine a Flutter requirement locally.")
console = Console()


def _parse_platforms(value: str) -> List[Platform]:
    items = [v.strip().lower() for v in value.split(",") if v.strip()]
    out: List[Platform] = []
    for it in items:
        try:
            out.append(Platform(it))
        except ValueError:
            raise typer.BadParameter(
                f"unknown platform '{it}'; valid: mobile,desktop,web,auto"
            )
    return out or [Platform.auto]


def _parse_skills(value: Optional[str]) -> Optional[List[str]]:
    if not value:
        return None
    return [v.strip() for v in value.split(",") if v.strip()]


def _parse_stages(value: Optional[str]) -> List[Stage]:
    if not value:
        return [
            Stage.classify,
            Stage.spec,
            Stage.architecture,
            Stage.breakdown,
            Stage.implementation,
            Stage.review,
            Stage.acceptance,
            Stage.markdown,
        ]
    out: List[Stage] = []
    for it in (v.strip().lower() for v in value.split(",") if v.strip()):
        try:
            out.append(Stage(it))
        except ValueError:
            raise typer.BadParameter(f"unknown stage '{it}'")
    return out


@app.command()
def refine(
    requirement: str = typer.Argument(
        ...,
        help="The requirement text. Pass '-' together with --stdin to read from stdin.",
    ),
    stdin: bool = typer.Option(False, "--stdin", help="Read requirement from stdin."),
    platforms: str = typer.Option(
        "auto", "--platforms", "-p", help="Comma-separated: mobile,desktop,web,auto"
    ),
    skills: Optional[str] = typer.Option(
        None, "--skills", "-s", help="Comma-separated skill ids to force."
    ),
    stages: Optional[str] = typer.Option(
        None,
        "--stages",
        help="Comma-separated stages to run. Default: all.",
    ),
    temperature: Optional[float] = typer.Option(None, "--temperature", "-t"),
    max_tokens: Optional[int] = typer.Option(None, "--max-tokens"),
    out: Optional[Path] = typer.Option(
        None, "--out", "-o", help="Write the final markdown PRD to this file."
    ),
    json_out: Optional[Path] = typer.Option(
        None, "--json", help="Write the full RefineResponse JSON here."
    ),
    out_dir: Optional[Path] = typer.Option(
        None,
        "--out-dir",
        help="Write each stage's raw + parsed output to this directory.",
    ),
    dry_run: bool = typer.Option(
        False,
        "--dry-run",
        help="Don't call the upstream model. Print the prompts that would be sent.",
    ),
) -> None:
    if stdin or requirement == "-":
        requirement = sys.stdin.read().strip()
    if not requirement:
        raise typer.BadParameter("requirement is empty")

    req = RefineRequest(
        requirement=requirement,
        platforms=_parse_platforms(platforms),
        skills=_parse_skills(skills),
        stages=_parse_stages(stages),
        temperature=temperature,
        max_tokens=max_tokens,
    )

    if dry_run:
        _dry_run(req)
        return

    asyncio.run(_run(req, out=out, json_out=json_out, out_dir=out_dir))


async def _run(
    req: RefineRequest,
    *,
    out: Optional[Path],
    json_out: Optional[Path],
    out_dir: Optional[Path],
) -> None:
    settings = get_settings()
    registry = SkillRegistry(settings.skills_path)
    registry.reload()
    if len(registry) == 0:
        console.print(
            f"[red]no skills loaded from {settings.skills_path}[/red] — "
            "check SKILLS_DIR in your .env"
        )
        raise typer.Exit(2)

    client = DeepSeekClient(settings)
    pipeline = RefinementPipeline(settings, client, registry)

    console.print(
        Panel.fit(
            f"[bold]requirement:[/bold] {req.requirement}\n"
            f"[bold]platforms:[/bold]   {[p.value for p in req.platforms]}\n"
            f"[bold]stages:[/bold]      {[s.value for s in req.stages]}\n"
            f"[bold]upstream:[/bold]    {settings.deepseek_base_url} ({settings.deepseek_model})",
            title="flutter-agent",
            border_style="cyan",
        )
    )

    try:
        result = await pipeline.run(req)
    except UpstreamError as exc:
        console.print(f"[red]upstream error:[/red] {exc}")
        if exc.body:
            console.print(exc.body[:1000])
        raise typer.Exit(2)
    finally:
        await client.aclose()

    for sr in result.stages:
        marker = "✓" if not sr.repaired else "✎"
        color = "green" if not sr.repaired else "yellow"
        console.print(
            f"[{color}]{marker}[/{color}] stage [bold]{sr.stage.value}[/bold] "
            f"({sr.elapsed_ms} ms, model={sr.model}, attempts={sr.attempts}, "
            f"tokens={sr.usage.total_tokens})"
        )
    console.print(
        f"[bold]total:[/bold] {result.usage.total_tokens} tokens "
        f"(prompt={result.usage.prompt_tokens}, completion={result.usage.completion_tokens})"
    )

    if out:
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(result.markdown or "", encoding="utf-8")
        console.print(f"[cyan]markdown PRD ->[/cyan] {out}")

    if json_out:
        json_out.parent.mkdir(parents=True, exist_ok=True)
        json_out.write_text(
            json.dumps(result.model_dump(), ensure_ascii=False, indent=2),
            encoding="utf-8",
        )
        console.print(f"[cyan]full JSON     ->[/cyan] {json_out}")

    if out_dir:
        out_dir.mkdir(parents=True, exist_ok=True)
        for sr in result.stages:
            base = out_dir / f"{sr.stage.value}"
            (base.with_suffix(".raw.txt")).write_text(sr.raw_output, encoding="utf-8")
            if sr.parsed is not None:
                (base.with_suffix(".json")).write_text(
                    json.dumps(sr.parsed, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
        if result.markdown:
            (out_dir / "prd.md").write_text(result.markdown, encoding="utf-8")
        console.print(f"[cyan]per-stage     ->[/cyan] {out_dir}/")

    if not out and not json_out and not out_dir:
        console.rule("Markdown PRD")
        console.print(result.markdown or "(empty)")


def _dry_run(req: RefineRequest) -> None:
    """Print the system + user prompts for each stage WITHOUT calling upstream."""
    settings = get_settings()
    registry = SkillRegistry(settings.skills_path)
    registry.reload()
    if len(registry) == 0:
        console.print(f"[red]no skills loaded from {settings.skills_path}[/red]")
        raise typer.Exit(2)

    # We instantiate the pipeline only to reuse its prompt-building logic;
    # we never call the client.
    pipeline = RefinementPipeline(settings, DeepSeekClient.__new__(DeepSeekClient), registry)
    if req.skills:
        skills = registry.get_many(req.skills)
    else:
        skills = pipeline._initial_skill_guess(req)  # type: ignore[attr-defined]
    if not any(s.id == "task-refinement" for s in skills):
        meta = registry.get("task-refinement")
        if meta is not None:
            skills.insert(0, meta)

    console.print(
        Panel.fit(
            f"[bold]requirement:[/bold] {req.requirement}\n"
            f"[bold]platforms:[/bold]   {[p.value for p in req.platforms]}\n"
            f"[bold]skills:[/bold]      {[s.id for s in skills]}\n"
            f"[bold]stages:[/bold]      {[s.value for s in req.stages]}",
            title="flutter-agent (dry-run)",
            border_style="yellow",
        )
    )

    for stage in req.stages:
        sys_prompt = pipeline._build_system_prompt(stage, skills)  # type: ignore[attr-defined]
        user_prompt = pipeline._build_user_prompt(stage, req, prior={})  # type: ignore[attr-defined]
        console.rule(f"[bold]{stage.value}[/bold]")
        console.print(
            f"[dim]system prompt: {len(sys_prompt)} chars, "
            f"user prompt: {len(user_prompt)} chars[/dim]"
        )
        console.print("[bold]system >[/bold]")
        console.print(sys_prompt[:1500] + ("\n… (truncated)" if len(sys_prompt) > 1500 else ""))
        console.print("[bold]user >[/bold]")
        console.print(user_prompt)


if __name__ == "__main__":
    app()
