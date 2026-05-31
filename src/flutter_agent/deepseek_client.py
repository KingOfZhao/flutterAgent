"""Thin async client for OpenAI-compatible chat completions (DeepSeek by default).

Features:
  * Bounded retry with exponential backoff for transient failures (network /
    429 / 5xx).
  * Non-streaming ``chat()`` returns the full JSON payload.
  * Streaming ``stream_chat()`` is an async generator yielding parsed delta
    dicts in OpenAI SSE shape.
"""
from __future__ import annotations

import asyncio
import json
import logging
import random
from typing import Any, AsyncIterator, Dict, List, Optional

import httpx

from .config import Settings

logger = logging.getLogger(__name__)

# HTTP status codes that are worth retrying. Anything else is a client / logic
# error and should surface immediately.
_RETRY_STATUS = {408, 425, 429, 500, 502, 503, 504}
_MAX_ATTEMPTS = 3
_BASE_BACKOFF = 0.6  # seconds; final delay = BASE * 2^n + jitter


class UpstreamError(RuntimeError):
    """Raised when the upstream model API returns a non-2xx or invalid payload."""

    def __init__(self, message: str, status_code: int = 0, body: str = ""):
        super().__init__(message)
        self.status_code = status_code
        self.body = body

    @property
    def retryable(self) -> bool:
        # status_code == 0 means transport-level error; treat as retryable.
        return self.status_code == 0 or self.status_code in _RETRY_STATUS


class DeepSeekClient:
    """Async OpenAI-compatible chat client.

    Works against any provider that exposes ``/chat/completions`` with the
    OpenAI request/response shape: DeepSeek, OpenAI, Together, Ollama, vLLM, ...
    """

    def __init__(self, settings: Settings, client: Optional[httpx.AsyncClient] = None):
        self._settings = settings
        self._owned_client = client is None
        self._client = client or httpx.AsyncClient(
            timeout=httpx.Timeout(settings.request_timeout_seconds),
            base_url=settings.deepseek_base_url.rstrip("/"),
        )

    async def aclose(self) -> None:
        if self._owned_client:
            await self._client.aclose()

    # ---------------------------------------------------------------- chat

    async def chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
        response_format: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Call ``POST /chat/completions`` and return the parsed JSON body.

        Retries up to ``_MAX_ATTEMPTS`` times on transient failures.
        """
        payload = self._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            stream=False,
        )
        headers = self._headers()

        last_exc: Optional[UpstreamError] = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                resp = await self._client.post(
                    "/chat/completions", json=payload, headers=headers
                )
            except httpx.HTTPError as exc:
                last_exc = UpstreamError(f"network error: {exc}")
            else:
                if resp.status_code < 400:
                    try:
                        return resp.json()
                    except ValueError as exc:
                        raise UpstreamError(
                            f"upstream returned non-JSON: {resp.text[:200]}"
                        ) from exc
                last_exc = UpstreamError(
                    f"upstream returned {resp.status_code}",
                    status_code=resp.status_code,
                    body=resp.text[:2000],
                )

            if attempt < _MAX_ATTEMPTS and last_exc.retryable:
                delay = _BASE_BACKOFF * (2 ** (attempt - 1))
                delay += random.uniform(0, 0.25)
                logger.warning(
                    "upstream attempt %d/%d failed (%s); retrying in %.2fs",
                    attempt,
                    _MAX_ATTEMPTS,
                    last_exc,
                    delay,
                )
                await asyncio.sleep(delay)
                continue
            break

        assert last_exc is not None
        raise last_exc

    # -------------------------------------------------------- stream_chat

    async def stream_chat(
        self,
        messages: List[Dict[str, str]],
        *,
        model: Optional[str] = None,
        temperature: Optional[float] = None,
        max_tokens: Optional[int] = None,
    ) -> AsyncIterator[Dict[str, Any]]:
        """Yield OpenAI-shaped streaming chunks (``chat.completion.chunk``).

        Each yielded value is the *parsed* JSON object that came after a
        ``data:`` line. The terminal ``[DONE]`` marker is **not** yielded;
        consumers should treat the end of the iterator as end-of-stream.

        Streaming requests are NOT retried mid-stream: a transient failure
        before the first byte triggers up to ``_MAX_ATTEMPTS`` reconnects, but
        once bytes have flowed we fail-fast so callers see a deterministic
        prefix.
        """
        payload = self._build_payload(
            messages=messages,
            model=model,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=None,
            stream=True,
        )
        headers = self._headers()

        last_exc: Optional[UpstreamError] = None
        for attempt in range(1, _MAX_ATTEMPTS + 1):
            try:
                async with self._client.stream(
                    "POST", "/chat/completions", json=payload, headers=headers
                ) as resp:
                    if resp.status_code >= 400:
                        body = (await resp.aread()).decode("utf-8", errors="replace")
                        last_exc = UpstreamError(
                            f"upstream returned {resp.status_code}",
                            status_code=resp.status_code,
                            body=body[:2000],
                        )
                        if attempt < _MAX_ATTEMPTS and last_exc.retryable:
                            await asyncio.sleep(_BASE_BACKOFF * (2 ** (attempt - 1)))
                            continue
                        raise last_exc

                    async for line in resp.aiter_lines():
                        if not line:
                            continue
                        if not line.startswith("data:"):
                            continue
                        body = line[len("data:") :].strip()
                        if body == "[DONE]":
                            return
                        try:
                            yield json.loads(body)
                        except json.JSONDecodeError:
                            logger.warning("skipping malformed SSE line: %r", body[:120])
                            continue
                    return
            except httpx.HTTPError as exc:
                last_exc = UpstreamError(f"network error: {exc}")
                if attempt < _MAX_ATTEMPTS:
                    await asyncio.sleep(_BASE_BACKOFF * (2 ** (attempt - 1)))
                    continue
                raise

        assert last_exc is not None
        raise last_exc

    # ---------------------------------------------------------------- util

    def _build_payload(
        self,
        *,
        messages: List[Dict[str, str]],
        model: Optional[str],
        temperature: Optional[float],
        max_tokens: Optional[int],
        response_format: Optional[Dict[str, Any]],
        stream: bool,
    ) -> Dict[str, Any]:
        s = self._settings
        if not s.deepseek_api_key:
            raise UpstreamError(
                "DEEPSEEK_API_KEY is not set; cannot reach upstream model. "
                "Edit .env and restart, or pass a different upstream via "
                "DEEPSEEK_BASE_URL."
            )
        payload: Dict[str, Any] = {
            "model": model or s.deepseek_model,
            "messages": messages,
            "temperature": temperature if temperature is not None else s.default_temperature,
            "max_tokens": max_tokens or s.default_max_tokens,
            "stream": stream,
        }
        if response_format is not None:
            payload["response_format"] = response_format
        return payload

    def _headers(self) -> Dict[str, str]:
        return {
            "Authorization": f"Bearer {self._settings.deepseek_api_key}",
            "Content-Type": "application/json",
        }

    @staticmethod
    def extract_text(completion: Dict[str, Any]) -> str:
        """Pull the assistant text out of an OpenAI-shaped chat completion."""
        try:
            return completion["choices"][0]["message"]["content"] or ""
        except (KeyError, IndexError, TypeError) as exc:
            raise UpstreamError(
                f"unexpected completion shape: {completion}"
            ) from exc

    @staticmethod
    def extract_usage(completion: Dict[str, Any]) -> Dict[str, int]:
        """Return ``{prompt_tokens, completion_tokens, total_tokens}`` if present."""
        usage = completion.get("usage") or {}
        return {
            "prompt_tokens": int(usage.get("prompt_tokens", 0) or 0),
            "completion_tokens": int(usage.get("completion_tokens", 0) or 0),
            "total_tokens": int(usage.get("total_tokens", 0) or 0),
        }
