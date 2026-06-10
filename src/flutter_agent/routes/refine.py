"""POST /v1/refine — run the full requirement refinement pipeline.

Also exposes ``POST /v1/refine/stream``: the same pipeline, but progress is
pushed to the client as SSE events (``pipeline_start`` / ``stage_start`` /
``stage_complete`` / ``cache_hit`` / ``done`` / ``error``) so callers can show
live stage-by-stage feedback instead of waiting for the whole run.
"""
from __future__ import annotations

import asyncio
import contextlib
import json
import logging
from typing import Any, AsyncIterator, Dict, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

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


def _sse(event: Dict[str, Any]) -> str:
    return f"data: {json.dumps(event, ensure_ascii=False)}\n\n"


@router.post(
    "/refine/stream",
    summary="Refine with live SSE progress (stage-by-stage events + final result)",
    response_model=None,
    responses={
        200: {
            "description": (
                "text/event-stream of JSON events: pipeline_start, stage_start, "
                "stage_complete (elapsed/usage/cost), cache_hit, done (full "
                "RefineResponse), error. Terminated by `data: [DONE]`."
            ),
            "content": {"text/event-stream": {}},
        },
        401: {"model": ErrorResponse, "description": "Missing or invalid API key."},
    },
    dependencies=[Depends(require_api_key)],
)
async def refine_stream(
    payload: RefineRequest,
    pipeline: RefinementPipeline = Depends(get_pipeline),
    store: RunStore = Depends(get_run_store),
) -> StreamingResponse:
    """Run the pipeline while streaming progress events over SSE.

    Stages can take tens of seconds each against a real upstream model; this
    endpoint lets clients render live progress instead of a blank wait.
    """
    queue: "asyncio.Queue[Optional[Dict[str, Any]]]" = asyncio.Queue()

    async def progress(event: Dict[str, Any]) -> None:
        await queue.put(event)

    async def runner() -> None:
        try:
            result = await pipeline.run(payload, progress=progress)
            if not result.cached:
                try:
                    await store.append(result)
                except OSError as exc:
                    logger.error("failed to persist run %s: %s", result.id, exc)
            await queue.put(
                {"type": "done", "response": result.model_dump(mode="json")}
            )
        except UpstreamError as exc:
            logger.error("upstream error: %s (status=%s)", exc, exc.status_code)
            await queue.put(
                {"type": "error", "detail": f"upstream error: {exc}",
                 "status_code": exc.status_code}
            )
        except Exception as exc:  # noqa: BLE001 - surfaced to the client
            logger.exception("refine stream failed")
            await queue.put({"type": "error", "detail": str(exc)})
        finally:
            await queue.put(None)

    async def event_stream() -> AsyncIterator[str]:
        task = asyncio.create_task(runner())
        try:
            while True:
                event = await queue.get()
                if event is None:
                    break
                yield _sse(event)
            yield "data: [DONE]\n\n"
        finally:
            task.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await task

    return StreamingResponse(
        event_stream(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
