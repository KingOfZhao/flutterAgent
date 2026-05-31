"""POST /v1/refine — run the full requirement refinement pipeline."""
from __future__ import annotations

import logging

from fastapi import APIRouter, Depends, HTTPException, status

from ..deepseek_client import UpstreamError
from ..deps import get_pipeline, get_run_store, require_api_key
from ..pipeline import RefinementPipeline
from ..run_store import RunStore
from ..schemas import ErrorResponse, RefineRequest, RefineResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["refine"])


@router.post(
    "/refine",
    response_model=RefineResponse,
    summary="Refine a Flutter requirement into spec / architecture / tasks",
    responses={
        401: {"model": ErrorResponse, "description": "Missing or invalid API key."},
        502: {"model": ErrorResponse, "description": "Upstream model error."},
    },
    dependencies=[Depends(require_api_key)],
)
async def refine(
    payload: RefineRequest,
    pipeline: RefinementPipeline = Depends(get_pipeline),
    store: RunStore = Depends(get_run_store),
) -> RefineResponse:
    """Run the multi-stage refinement pipeline against the configured upstream."""
    try:
        result = await pipeline.run(payload)
    except UpstreamError as exc:
        logger.error("upstream error: %s (status=%s)", exc, exc.status_code)
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"upstream error: {exc}",
        ) from exc

    # Persist to runs.jsonl. Failure to persist must NOT fail the API call.
    try:
        await store.append(result)
    except OSError as exc:
        logger.error("failed to persist run %s: %s", result.id, exc)
    return result
