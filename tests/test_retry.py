"""Verify the DeepSeek client actually retries on transient failures."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.config import Settings  # noqa: E402
from flutter_agent.deepseek_client import DeepSeekClient, UpstreamError  # noqa: E402


def _settings() -> Settings:
    # Provide a bogus key so the client doesn't short-circuit on missing key.
    return Settings(
        deepseek_api_key="test-key-not-real",
        deepseek_base_url="https://example.invalid/v1",
        deepseek_model="deepseek-v4-pro",
        request_timeout_seconds=5.0,
    )


def _ok_payload(text: str = "ok") -> dict:
    return {
        "id": "chatcmpl-1",
        "object": "chat.completion",
        "created": 1,
        "model": "deepseek-v4-pro",
        "choices": [{"index": 0, "message": {"role": "assistant", "content": text}, "finish_reason": "stop"}],
        "usage": {"prompt_tokens": 1, "completion_tokens": 2, "total_tokens": 3},
    }


def test_chat_retries_on_429_then_succeeds(monkeypatch) -> None:
    """First two responses 429, third 200: client must succeed and only call thrice."""
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        if calls["n"] < 3:
            return httpx.Response(429, json={"error": "rate limit"})
        return httpx.Response(200, json=_ok_payload("retried-ok"))

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://example.invalid/v1")

    # Patch asyncio.sleep so the test runs fast.
    sleeps: list[float] = []

    async def fake_sleep(d: float) -> None:
        sleeps.append(d)

    monkeypatch.setattr("flutter_agent.deepseek_client.asyncio.sleep", fake_sleep)

    deep = DeepSeekClient(_settings(), client=client)

    async def go() -> dict:
        try:
            return await deep.chat([{"role": "user", "content": "hi"}])
        finally:
            await deep.aclose()

    result = asyncio.run(go())
    assert calls["n"] == 3
    assert DeepSeekClient.extract_text(result) == "retried-ok"
    # Two retries means two backoffs.
    assert len(sleeps) == 2


def test_chat_does_not_retry_on_400(monkeypatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(400, json={"error": "bad request"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://example.invalid/v1")

    async def fake_sleep(d: float) -> None:  # pragma: no cover - shouldn't fire
        raise AssertionError("sleep should not be called for non-retryable errors")

    monkeypatch.setattr("flutter_agent.deepseek_client.asyncio.sleep", fake_sleep)

    deep = DeepSeekClient(_settings(), client=client)

    async def go():
        with pytest.raises(UpstreamError) as ei:
            await deep.chat([{"role": "user", "content": "hi"}])
        await deep.aclose()
        return ei.value

    err = asyncio.run(go())
    assert err.status_code == 400
    assert calls["n"] == 1  # no retry


def test_chat_gives_up_after_max_attempts(monkeypatch) -> None:
    calls = {"n": 0}

    def handler(request: httpx.Request) -> httpx.Response:
        calls["n"] += 1
        return httpx.Response(503, json={"error": "down"})

    transport = httpx.MockTransport(handler)
    client = httpx.AsyncClient(transport=transport, base_url="https://example.invalid/v1")

    async def fake_sleep(d: float) -> None:
        return None

    monkeypatch.setattr("flutter_agent.deepseek_client.asyncio.sleep", fake_sleep)

    deep = DeepSeekClient(_settings(), client=client)

    async def go():
        with pytest.raises(UpstreamError) as ei:
            await deep.chat([{"role": "user", "content": "hi"}])
        await deep.aclose()
        return ei.value

    err = asyncio.run(go())
    assert err.status_code == 503
    # Default _MAX_ATTEMPTS is 3.
    assert calls["n"] == 3
