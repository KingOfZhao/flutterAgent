#!/usr/bin/env python3
"""Local vector database CLI.

Build and query the offline vector index over skills/ + knowledge/:

  # (Re)build the index into data/vector_store.sqlite3
  python scripts/vector_cli.py build

  # Semantic search (both kinds)
  python scripts/vector_cli.py search "离线同步架构怎么选"

  # Only knowledge docs, top 3
  python scripts/vector_cli.py search "模型能力演进的必要条件" --kind knowledge -k 3

No network, no model downloads: embeddings are deterministic feature-hashing
vectors (see src/flutter_agent/vector_store.py).
"""
from __future__ import annotations

import sys
from pathlib import Path
from typing import Optional

import typer
from rich.console import Console
from rich.table import Table

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from flutter_agent.config import get_settings  # noqa: E402
from flutter_agent.vector_store import VectorStore, build_index  # noqa: E402

app = typer.Typer(add_completion=False, help=__doc__)
console = Console()


@app.command()
def build() -> None:
    """(Re)build the vector index from skills/ and knowledge/."""
    settings = get_settings()
    store = VectorStore(settings.vector_db_file)
    stats = build_index(
        store, skills_dir=settings.skills_path, knowledge_dir=settings.knowledge_path
    )
    console.print(
        f"[green]built[/green] {stats['chunks']} chunks "
        f"({stats['skill_chunks']} skill + {stats['knowledge_chunks']} knowledge) "
        f"from {stats['documents']} documents -> {settings.vector_db_file} "
        f"(dim={stats['dim']}, embedder={stats['embedder']})"
    )
    store.close()


@app.command()
def search(
    query: str,
    k: int = typer.Option(5, "--top-k", "-k", min=1, max=50),
    kind: Optional[str] = typer.Option(None, "--kind", help="'skill' or 'knowledge'"),
) -> None:
    """Semantic search; builds the index first if it is empty."""
    settings = get_settings()
    store = VectorStore(settings.vector_db_file)
    if store.count() == 0:
        build_index(
            store, skills_dir=settings.skills_path, knowledge_dir=settings.knowledge_path
        )
    hits = store.search(query, top_k=k, kind=kind)
    table = Table(title=f"top-{k} for: {query}")
    table.add_column("score", justify="right")
    table.add_column("kind")
    table.add_column("doc")
    table.add_column("snippet", overflow="fold", max_width=70)
    for h in hits:
        table.add_row(f"{h.score:.4f}", h.kind, f"{h.doc_id}#{h.chunk_index}", h.snippet)
    console.print(table)
    store.close()


@app.command()
def stats() -> None:
    """Show index statistics."""
    settings = get_settings()
    store = VectorStore(settings.vector_db_file)
    console.print(
        f"chunks={store.count()} documents={store.doc_count()} "
        f"dim={store.embedder.dim} db={settings.vector_db_file}"
    )
    store.close()


if __name__ == "__main__":
    app()
