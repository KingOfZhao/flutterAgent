"""Multi-provider registry: config parsing, routing refs, fallback behaviour."""
from __future__ import annotations

import asyncio
import json
import sys
from pathlib import Path

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.config import Settings  # noqa: E402
from flutter_agent.providers import (  # noqa: E402
    DEFAULT_PROVIDER,
    MultiProviderClient,
    ProviderConfig,
    ProviderRegistry,
    load_provider_configs,
)


def _settings(**kwargs) -> Settings:
    base = dict(
        deepseek_api_key="default-key",
        deepseek_base_url="https://default.invalid/v1",
        deepseek_model="deepseek-chat",
        providers_config_path="does/not/exist.json",
    )
    base.update(kwargs)
    return Settings(**base)


def _providers_json() -> str:
    return json.dumps(
        [
            {
                "name": "openai",
                "base_url": "https://openai.invalid/v1",
                "model": "gpt-x",
                "api_key": "openai-key",
                "roles": ["reviewer"],
            },
            {
                "name": "local",
                "base_url": "http://localhost:11434/v1",
                "model": "qwen",
                "api_key": "x",
                "roles": ["judge"],
            },
        ]
    )


# ------------------------------------------------------------------ parsing


def test_default_only_when_unconfigured() -> None:
    reg = ProviderRegistry(_settings())
    assert reg.names == [DEFAULT_PROVIDER]
    cfg = reg.get_config(DEFAULT_PROVIDER)
    assert cfg.base_url == "https://default.invalid/v1"
    assert cfg.model == "deepseek-chat"


def test_env_json_providers_loaded() -> None:
    s = _settings(model_providers=_providers_json())
    reg = ProviderRegistry(s)
    assert set(reg.names) == {DEFAULT_PROVIDER, "openai", "local"}
    assert reg.get_config("openai").roles == ["reviewer"]


def test_file_providers_loaded(tmp_path) -> None:
    f = tmp_path / "providers.json"
    f.write_text(json.dumps({"providers": json.loads(_providers_json())}), encoding="utf-8")
    s = _settings(providers_config_path=str(f))
    configs = load_provider_configs(s)
    assert {c.name for c in configs} == {"openai", "local"}


def test_env_overrides_file_on_name_collision(tmp_path) -> None:
    f = tmp_path / "providers.json"
    f.write_text(
        json.dumps([{"name": "openai", "base_url": "https://file.invalid/v1",
                     "model": "file-model", "api_key": "k"}]),
        encoding="utf-8",
    )
    s = _settings(providers_config_path=str(f), model_providers=_providers_json())
    configs = {c.name: c for c in load_provider_configs(s)}
    assert configs["openai"].base_url == "https://openai.invalid/v1"


def test_invalid_env_json_is_ignored() -> None:
    reg = ProviderRegistry(_settings(model_providers="{not json"))
    assert reg.names == [DEFAULT_PROVIDER]


def test_api_key_env_resolution(monkeypatch) -> None:
    monkeypatch.setenv("MY_PROVIDER_KEY", "from-env")
    cfg = ProviderConfig(
        name="p", base_url="https://x.invalid/v1", model="m", api_key_env="MY_PROVIDER_KEY"
    )
    assert cfg.resolve_api_key() == "from-env"


# ------------------------------------------------------------------ routing


@pytest.fixture()
def registry() -> ProviderRegistry:
    return ProviderRegistry(_settings(model_providers=_providers_json()))


def test_resolve_explicit_provider_and_model(registry) -> None:
    client, model = registry.resolve("openai:gpt-x-mini")
    assert client is registry.get_client("openai")
    assert model == "gpt-x-mini"


def test_resolve_provider_default_model(registry) -> None:
    client, model = registry.resolve("openai:")
    assert client is registry.get_client("openai")
    assert model is None
    client2, model2 = registry.resolve("local")
    assert client2 is registry.get_client("local")
    assert model2 is None


def test_resolve_role_ref(registry) -> None:
    client, model = registry.resolve("@reviewer")
    assert client is registry.get_client("openai")
    assert model is None


def test_resolve_unknown_role_falls_back_to_default(registry) -> None:
    client, _ = registry.resolve("@nonexistent")
    assert client is registry.get_client(DEFAULT_PROVIDER)


def test_resolve_plain_model_name_keeps_legacy_behaviour(registry) -> None:
    client, model = registry.resolve("deepseek-reasoner")
    assert client is registry.get_client(DEFAULT_PROVIDER)
    assert model == "deepseek-reasoner"


def test_resolve_none_uses_default(registry) -> None:
    client, model = registry.resolve(None)
    assert client is registry.get_client(DEFAULT_PROVIDER)
    assert model is None


def test_describe_never_leaks_keys(registry) -> None:
    for item in registry.describe():
        assert "api_key" not in item
        assert isinstance(item["has_api_key"], bool)


# ------------------------------------------------- multi-provider chat path


def _ok_payload(text: str, model: str) -> dict:
    return {
        "id": "c1",
        "object": "chat.completion",
        "created": 1,
        "model": model,
        "choices": [
            {"index": 0, "message": {"role": "assistant", "content": text},
             "finish_reason": "stop"}
        ],
        "usage": {"prompt_tokens": 1, "completion_tokens": 1, "total_tokens": 2},
    }


def test_multi_provider_client_routes_by_host(monkeypatch) -> None:
    """A 'openai:...' ref must hit the openai base_url, not the default."""
    s = _settings(model_providers=_providers_json())
    reg = ProviderRegistry(s)

    def handler(request: httpx.Request) -> httpx.Response:
        body = json.loads(request.content)
        return httpx.Response(
            200, json=_ok_payload(f"host={request.url.host} model={body['model']}", body["model"])
        )

    # Swap each provider's transport for the mock.
    for name in reg.names:
        cfg = reg.get_config(name)
        client = reg.get_client(name)
        client._client = httpx.AsyncClient(
            transport=httpx.MockTransport(handler), base_url=cfg.base_url.rstrip("/")
        )

    mpc = MultiProviderClient(reg)

    async def run() -> None:
        r1 = await mpc.chat([{"role": "user", "content": "hi"}], model="openai:gpt-x")
        assert "host=openai.invalid" in mpc.extract_text(r1)
        r2 = await mpc.chat([{"role": "user", "content": "hi"}])
        assert "host=default.invalid" in mpc.extract_text(r2)
        assert "model=deepseek-chat" in mpc.extract_text(r2)
        await mpc.aclose()

    asyncio.run(run())
