"""POST /v1/chat/completions — OpenAI-compatible facade.

Two behaviours, dispatched by the ``model`` field:

* ``flutter-agent`` (default)  -> runs the refinement pipeline using the last
  user message as the requirement, and returns the final markdown PRD as the
  assistant's reply.
* anything else               -> proxies straight through to the upstream
  DeepSeek / OpenAI-compatible chat completion API, preserving the model name.

This lets the same endpoint serve both "I want a fully-refined Flutter PRD"
and "I just want raw model chat" use-cases through a single SDK.
"""
from __future__ import annotations

import json
import logging
import time
import uuid
from typing import AsyncIterator

from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import StreamingResponse

from ..deepseek_client import DeepSeekClient, UpstreamError
from ..deps import get_client, get_pipeline, get_run_store, require_api_key
from ..pipeline import RefinementPipeline
from ..run_store import RunStore
from ..schemas import (
    ChatCompletionChoice,
    ChatCompletionRequest,
    ChatCompletionResponse,
    ChatCompletionUsage,
    ChatMessage,
    ErrorResponse,
    Platform,
    RefineRequest,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["openai-compat"])

AGENT_MODEL_ALIASES = {"flutter-agent", "flutter-agent-refine"}


def _now() -> int:
    return int(time.time())


def _new_id() -> str:
    return f"chatcmpl-{uuid.uuid4().hex[:24]}"


@router.post(
    "/chat/completions",
    summary="OpenAI-compatible chat completion (supports stream=true SSE)",
    response_model=None,  # we may return either JSON or text/event-stream
    responses={
        200: {
            "description": "Either application/json (ChatCompletionResponse) "
            "or text/event-stream (OpenAI SSE deltas).",
            "content": {
                "application/json": {},
                "text/event-stream": {},
            },
        },
        400: {"model": ErrorResponse},
        401: {"model": ErrorResponse},
        502: {"model": ErrorResponse},
    },
    dependencies=[Depends(require_api_key)],
)
async def chat_completions(
    payload: ChatCompletionRequest,
    client: DeepSeekClient = Depends(get_client),
    pipeline: RefinementPipeline = Depends(get_pipeline),
    store: RunStore = Depends(get_run_store),
):
    if not payload.messages:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="messages must not be empty",
        )

    is_agent = payload.model.lower() in AGENT_MODEL_ALIASES

    # ---- streaming branch -------------------------------------------------
    if payload.stream:
        if is_agent:
            return StreamingResponse(
                _agent_stream(payload, pipeline, store),
                media_type="text/event-stream",
                headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
            )
        return StreamingResponse(
            _passthrough_stream(payload, client),
            media_type="text/event-stream",
            headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
        )

    # ---- non-streaming branch --------------------------------------------
    if is_agent:
        return await _agent_chat(payload, pipeline, store)
    return await _passthrough_chat(payload, client)


# ---------------------------------------------------------------------------


def _agent_request_from(payload: ChatCompletionRequest) -> RefineRequest:
    last_user = next(
        (m.content for m in reversed(payload.messages) if m.role == "user"), None
    )
    if not last_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="at least one user message is required",
        )
    system_extra = "\n\n".join(
        m.content for m in payload.messages if m.role == "system"
    )
    return RefineRequest(
        requirement=last_user,
        platforms=[Platform.auto],
        temperature=payload.temperature,
        max_tokens=payload.max_tokens,
        extra_context=system_extra or None,
    )


async def _agent_chat(
    payload: ChatCompletionRequest,
    pipeline: RefinementPipeline,
    store: RunStore,
) -> ChatCompletionResponse:
    req = _agent_request_from(payload)
    try:
        result = await pipeline.run(req)
    except UpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"upstream error: {exc}",
        ) from exc

    try:
        await store.append(result)
    except OSError as exc:
        logger.error("failed to persist run %s: %s", result.id, exc)

    content = result.markdown or "(pipeline produced no markdown stage)"
    return ChatCompletionResponse(
        id=result.id,
        created=result.created_at or _now(),
        model=payload.model,
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content),
                finish_reason="stop",
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=result.usage.prompt_tokens,
            completion_tokens=result.usage.completion_tokens,
            total_tokens=result.usage.total_tokens,
        ),
    )


async def _passthrough_chat(
    payload: ChatCompletionRequest,
    client: DeepSeekClient,
) -> ChatCompletionResponse:
    """Forward verbatim to upstream and reshape into our response model."""
    try:
        upstream = await client.chat(
            [m.model_dump() for m in payload.messages],
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        )
    except UpstreamError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"upstream error: {exc}",
        ) from exc

    content = DeepSeekClient.extract_text(upstream)
    usage_dict = upstream.get("usage") or {}
    return ChatCompletionResponse(
        id=str(upstream.get("id") or _new_id()),
        created=int(upstream.get("created") or _now()),
        model=str(upstream.get("model") or payload.model),
        choices=[
            ChatCompletionChoice(
                index=0,
                message=ChatMessage(role="assistant", content=content),
                finish_reason=str(
                    (upstream.get("choices") or [{}])[0].get("finish_reason") or "stop"
                ),
            )
        ],
        usage=ChatCompletionUsage(
            prompt_tokens=int(usage_dict.get("prompt_tokens", 0)),
            completion_tokens=int(usage_dict.get("completion_tokens", 0)),
            total_tokens=int(usage_dict.get("total_tokens", 0)),
        ),
    )


# ---------------------------------------------------------------------------
# Streaming
# ---------------------------------------------------------------------------


def _sse(obj: dict) -> bytes:
    return f"data: {json.dumps(obj, ensure_ascii=False)}\n\n".encode("utf-8")


def _sse_done() -> bytes:
    return b"data: [DONE]\n\n"


async def _passthrough_stream(
    payload: ChatCompletionRequest, client: DeepSeekClient
) -> AsyncIterator[bytes]:
    """Proxy the upstream SSE stream verbatim into our HTTP response."""
    try:
        async for chunk in client.stream_chat(
            [m.model_dump() for m in payload.messages],
            model=payload.model,
            temperature=payload.temperature,
            max_tokens=payload.max_tokens,
        ):
            yield _sse(chunk)
    except UpstreamError as exc:
        yield _sse({"error": {"message": f"upstream error: {exc}", "code": exc.status_code}})
    yield _sse_done()


async def _agent_stream(
    payload: ChatCompletionRequest,
    pipeline: RefinementPipeline,
    store: RunStore,
) -> AsyncIterator[bytes]:
    """Run the full pipeline, then stream the resulting markdown PRD as SSE.

    Stage progress is emitted as small ``content`` deltas so that consumers can
    display a live activity log while the pipeline runs.
    """
    req = _agent_request_from(payload)
    chunk_id = _new_id()
    created = _now()

    def role_chunk() -> dict:
        return {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": payload.model,
            "choices": [
                {"index": 0, "delta": {"role": "assistant"}, "finish_reason": None}
            ],
        }

    def content_chunk(delta: str, finish_reason: str | None = None) -> dict:
        return {
            "id": chunk_id,
            "object": "chat.completion.chunk",
            "created": created,
            "model": payload.model,
            "choices": [
                {
                    "index": 0,
                    "delta": {"content": delta} if delta else {},
                    "finish_reason": finish_reason,
                }
            ],
        }

    yield _sse(role_chunk())
    yield _sse(content_chunk("⏳ 启动流水线…\n"))

    try:
        result = await pipeline.run(req)
    except UpstreamError as exc:
        yield _sse(
            content_chunk(f"\n❌ 上游错误: {exc}\n", finish_reason="stop")
        )
        yield _sse_done()
        return

    try:
        await store.append(result)
    except OSError as exc:
        logger.error("failed to persist run %s: %s", result.id, exc)

    yield _sse(content_chunk(f"✅ 完成 {len(result.stages)} 个阶段,总 token={result.usage.total_tokens}\n\n"))

    md = result.markdown or "(pipeline produced no markdown stage)"
    # chunk by ~256 chars for visible streaming without flooding the client
    step = 256
    for i in range(0, len(md), step):
        yield _sse(content_chunk(md[i : i + step]))
    yield _sse(content_chunk("", finish_reason="stop"))
    yield _sse_done()
