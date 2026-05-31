#!/usr/bin/env python3
"""Dump the FastAPI OpenAPI 3.x schema to disk without starting the server.

Useful for committing the schema next to the codebase and for feeding it into
openapi-generator-cli, Postman, etc.

Usage:

  python scripts/export_openapi.py            # -> ./openapi.json
  python scripts/export_openapi.py -o out.json
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


def main(
    out: Path = typer.Option(
        ROOT / "openapi.json", "--out", "-o", help="Destination JSON file."
    ),
) -> None:
    from flutter_agent.main import app  # imported lazily so sys.path is ready

    schema = app.openapi()
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(json.dumps(schema, ensure_ascii=False, indent=2), encoding="utf-8")
    typer.echo(f"openapi schema -> {out}")


if __name__ == "__main__":
    typer.run(main)
