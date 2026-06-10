"""Local vector database endpoints (semantic search over skills + knowledge).

The index is built lazily on first use (or explicitly via ``POST /v1/vector/rebuild``
/ ``scripts/vector_cli.py build``) and persists in SQLite, so restarts are cheap.
"""
from __future__ import annotations

from typing import List, Optional

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, Field

from ..config import Settings, get_settings
from ..deps import require_api_key
from ..vector_store import VectorStore, build_index

router = APIRouter(prefix="/v1/vector", tags=["vector"])


class VectorSearchRequest(BaseModel):
    query: str = Field(min_length=1, description="Natural-language query.")
    top_k: int = Field(default=5, ge=1, le=50)
    kind: Optional[str] = Field(
        default=None, description="Filter: 'skill' or 'knowledge' (default: both)."
    )


class VectorHit(BaseModel):
    doc_id: str
    kind: str
    title: str
    source: str
    chunk_index: int
    score: float
    snippet: str


class VectorSearchResponse(BaseModel):
    query: str
    hits: List[VectorHit]


class VectorStatsResponse(BaseModel):
    chunks: int
    documents: int
    dim: int
    embedder: str
    db_path: str


def _get_store(request: Request, settings: Settings) -> VectorStore:
    store = getattr(request.app.state, "vector_store", None)
    if store is None:
        store = VectorStore(settings.vector_db_file)
        request.app.state.vector_store = store
    if store.count() == 0:
        build_index(
            store,
            skills_dir=settings.skills_path,
            knowledge_dir=settings.knowledge_path,
        )
    return store


@router.post(
    "/search",
    response_model=VectorSearchResponse,
    summary="Semantic search over skills + knowledge docs (local, offline)",
    dependencies=[Depends(require_api_key)],
)
async def vector_search(req: VectorSearchRequest, request: Request) -> VectorSearchResponse:
    settings = get_settings()
    store = _get_store(request, settings)
    hits = store.search(req.query, top_k=req.top_k, kind=req.kind)
    return VectorSearchResponse(
        query=req.query,
        hits=[VectorHit(**h.__dict__) for h in hits],
    )


@router.post(
    "/rebuild",
    response_model=VectorStatsResponse,
    summary="Rebuild the vector index from skills/ and knowledge/ on disk",
    dependencies=[Depends(require_api_key)],
)
async def vector_rebuild(request: Request) -> VectorStatsResponse:
    settings = get_settings()
    store = getattr(request.app.state, "vector_store", None)
    if store is None:
        store = VectorStore(settings.vector_db_file)
        request.app.state.vector_store = store
    build_index(
        store,
        skills_dir=settings.skills_path,
        knowledge_dir=settings.knowledge_path,
    )
    return VectorStatsResponse(
        chunks=store.count(),
        documents=store.doc_count(),
        dim=store.embedder.dim,
        embedder=store.embedder.name,
        db_path=str(settings.vector_db_file),
    )


@router.get(
    "/stats",
    response_model=VectorStatsResponse,
    summary="Vector index statistics",
    dependencies=[Depends(require_api_key)],
)
async def vector_stats(request: Request) -> VectorStatsResponse:
    settings = get_settings()
    store = _get_store(request, settings)
    return VectorStatsResponse(
        chunks=store.count(),
        documents=store.doc_count(),
        dim=store.embedder.dim,
        embedder=store.embedder.name,
        db_path=str(settings.vector_db_file),
    )
