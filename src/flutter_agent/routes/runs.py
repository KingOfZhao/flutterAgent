"""GET /v1/runs — list past refinement runs; GET /v1/runs/{id} — full record."""
from __future__ import annotations

from typing import Any, Dict, List

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..deps import get_run_store, require_api_key
from ..run_store import RunStore
from ..schemas import ErrorResponse, RunSummary

router = APIRouter(prefix="/v1/runs", tags=["runs"])


@router.get(
    "",
    response_model=List[RunSummary],
    summary="List recent refinement runs (newest first).",
    dependencies=[Depends(require_api_key)],
)
async def list_runs(
    limit: int = Query(default=50, ge=1, le=500),
    store: RunStore = Depends(get_run_store),
) -> List[RunSummary]:
    return store.list(limit=limit)


@router.get(
    "/{run_id}",
    summary="Fetch the full RefineResponse for a given run id.",
    response_model=Dict[str, Any],
    responses={404: {"model": ErrorResponse}},
    dependencies=[Depends(require_api_key)],
)
async def get_run(
    run_id: str,
    store: RunStore = Depends(get_run_store),
) -> Dict[str, Any]:
    obj = store.get(run_id)
    if obj is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown run id: {run_id}",
        )
    return obj
