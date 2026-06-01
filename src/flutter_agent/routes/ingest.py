"""POST /v1/ingest — discover open-source dev signals (HF models + arXiv papers).

Discovery + deterministic scaffolding cost **no** model tokens. Setting
``distill=true`` model-fills each scaffold (COSTS TOKENS, needs DEEPSEEK_API_KEY).
"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Callable, Optional

from fastapi import APIRouter, Depends, HTTPException, status

from ..config import Settings
from ..deepseek_client import DeepSeekClient, UpstreamError
from ..deps import get_client, get_make_ingestor, get_settings, require_api_key
from ..ingestion import (
    DEFAULT_QUERIES,
    Ingestor,
    SeenStore,
    distill_and_write,
    write_scaffolds,
)
from ..schemas import ErrorResponse, IngestRequest, IngestResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["ingest"])


@router.post(
    "/ingest",
    response_model=IngestResponse,
    summary="Discover (and optionally scaffold/distill) open-source dev signals",
    responses={
        400: {"model": ErrorResponse, "description": "Bad request (e.g. distill without key)."},
        401: {"model": ErrorResponse, "description": "Missing or invalid API key."},
        502: {"model": ErrorResponse, "description": "Upstream model error during distill."},
    },
    dependencies=[Depends(require_api_key)],
)
async def ingest(
    payload: IngestRequest,
    settings: Settings = Depends(get_settings),
    client: DeepSeekClient = Depends(get_client),
    make_ingestor: Callable[[set, Optional[SeenStore]], Ingestor] = Depends(get_make_ingestor),
) -> IngestResponse:
    queries = payload.queries or list(DEFAULT_QUERIES)
    wanted = {s.strip().lower() for s in payload.sources if s.strip()}
    if not any(s in wanted for s in ("hf", "huggingface", "arxiv")):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="no valid sources; use 'hf' and/or 'arxiv'",
        )
    if payload.distill and not settings.deepseek_api_key:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="distill needs DEEPSEEK_API_KEY (the distill step costs tokens)",
        )

    seen = SeenStore(settings.ingestion_seen_file)
    ingestor = make_ingestor(wanted, seen)
    digest = await ingestor.discover(queries, limit_per_query=payload.limit)

    rows = [c for c in digest.candidates if (c.is_new or not payload.only_new)]
    if payload.only_new:
        digest.candidates = rows

    scaffolded = distilled = 0
    out_dir: Optional[Path] = None
    if payload.scaffold or payload.distill:
        out_dir = Path(payload.scaffold_dir) if payload.scaffold_dir else settings.skills_path
        if payload.distill:
            try:
                distilled = await distill_and_write(
                    client,
                    rows,
                    out_dir,
                    only_new=payload.only_new,
                    max_distill=payload.max_distill,
                    model=settings.deepseek_model,
                )
            except UpstreamError as exc:
                logger.error("distill upstream error: %s (status=%s)", exc, exc.status_code)
                raise HTTPException(
                    status_code=status.HTTP_502_BAD_GATEWAY,
                    detail=f"upstream error during distill: {exc}",
                ) from exc
        else:
            scaffolded = write_scaffolds(rows, out_dir, only_new=payload.only_new)

    if payload.commit:
        try:
            seen.commit(digest.candidates)
        except OSError as exc:  # persistence failure must not fail the call
            logger.error("failed to commit seen-store: %s", exc)

    return IngestResponse(
        digest=digest,
        scaffolded=scaffolded,
        distilled=distilled,
        scaffold_dir=str(out_dir) if out_dir is not None else None,
        committed=payload.commit,
    )
