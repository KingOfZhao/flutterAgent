"""Multi-provider model configuration and routing.

Lets the service talk to several OpenAI-compatible upstreams at once
(DeepSeek, OpenAI, Ollama, vLLM, ...) while staying fully backward
compatible: with no extra configuration there is exactly one provider,
``default``, synthesized from the existing ``DEEPSEEK_*`` settings.

Configuration sources (merged, later wins on name collisions):
  1. JSON file at ``settings.providers_config_file`` (``data/providers.json``)
     containing ``{"providers": [...]}`` or a bare list.
  2. ``MODEL_PROVIDERS`` env var with the same JSON list.

Each entry::

    {
      "name": "openai",
      "base_url": "https://api.openai.com/v1",
      "api_key_env": "OPENAI_API_KEY",   // or "api_key": "sk-..."
      "model": "gpt-5.2",
      "roles": ["reviewer"],             // optional routing roles
      "temperature": 0.1,                // optional generation overrides
      "max_tokens": 8192
    }

Routing references accepted everywhere a model name is accepted:
  * ``"provider:model"``  explicit provider + model
  * ``"provider:"``       provider with its configured default model
  * ``"@role"``           first provider declaring that role
  * anything else         default provider, ref used as the model name
"""
from __future__ import annotations

import json
import logging
import os
from typing import Any, AsyncIterator, Dict, List, Optional, Tuple

from pydantic import BaseModel, Field

from .config import Settings
from .deepseek_client import DeepSeekClient

logger = logging.getLogger(__name__)

DEFAULT_PROVIDER = "default"


class ProviderConfig(BaseModel):
    """One OpenAI-compatible upstream endpoint."""

    name: str = Field(min_length=1, pattern=r"^[A-Za-z0-9_-]+$")
    base_url: str = Field(min_length=1)
    model: str = Field(min_length=1)
    api_key: str = Field(default="", repr=False)
    api_key_env: str = Field(
        default="",
        description="Env var holding the key; preferred over inline api_key.",
    )
    roles: List[str] = Field(default_factory=list)
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None

    def resolve_api_key(self) -> str:
        if self.api_key_env:
            return os.environ.get(self.api_key_env, "") or self.api_key
        return self.api_key


def _parse_provider_list(raw: Any, source: str) -> List[ProviderConfig]:
    if isinstance(raw, dict):
        raw = raw.get("providers", [])
    if not isinstance(raw, list):
        raise ValueError(f"{source}: expected a JSON list of provider objects")
    return [ProviderConfig.model_validate(item) for item in raw]


def load_provider_configs(settings: Settings) -> List[ProviderConfig]:
    """Merge file + env provider declarations (env wins on name collisions)."""
    merged: Dict[str, ProviderConfig] = {}

    path = settings.providers_config_file
    if path.exists():
        try:
            file_raw = json.loads(path.read_text(encoding="utf-8"))
            for cfg in _parse_provider_list(file_raw, str(path)):
                merged[cfg.name] = cfg
        except (ValueError, OSError) as exc:
            logger.error("ignoring invalid providers file %s: %s", path, exc)

    if settings.model_providers.strip():
        try:
            env_raw = json.loads(settings.model_providers)
            for cfg in _parse_provider_list(env_raw, "MODEL_PROVIDERS"):
                merged[cfg.name] = cfg
        except ValueError as exc:
            logger.error("ignoring invalid MODEL_PROVIDERS env: %s", exc)

    return list(merged.values())


class ProviderRegistry:
    """Owns one ``DeepSeekClient`` per configured provider.

    The ``default`` provider always exists (built from ``DEEPSEEK_*``),
    unless an explicit provider is also named ``default``, which overrides it.
    """

    def __init__(self, settings: Settings, configs: Optional[List[ProviderConfig]] = None):
        self._settings = settings
        self._configs: Dict[str, ProviderConfig] = {}
        self._clients: Dict[str, DeepSeekClient] = {}

        default_cfg = ProviderConfig(
            name=DEFAULT_PROVIDER,
            base_url=settings.deepseek_base_url,
            model=settings.deepseek_model,
            api_key=settings.deepseek_api_key,
            roles=["default"],
        )
        self._register(default_cfg, settings)

        for cfg in (configs if configs is not None else load_provider_configs(settings)):
            self._register(cfg, settings)

    def _register(self, cfg: ProviderConfig, base: Settings) -> None:
        provider_settings = base.model_copy(
            update={
                "deepseek_api_key": cfg.resolve_api_key(),
                "deepseek_base_url": cfg.base_url,
                "deepseek_model": cfg.model,
                **(
                    {"default_temperature": cfg.temperature}
                    if cfg.temperature is not None
                    else {}
                ),
                **(
                    {"default_max_tokens": cfg.max_tokens}
                    if cfg.max_tokens is not None
                    else {}
                ),
            }
        )
        old = self._clients.pop(cfg.name, None)
        if old is not None:
            logger.info("provider %r re-registered; previous client dropped", cfg.name)
        self._configs[cfg.name] = cfg
        self._clients[cfg.name] = DeepSeekClient(provider_settings)

    # ---------------------------------------------------------------- query

    @property
    def names(self) -> List[str]:
        return list(self._configs)

    def get_config(self, name: str) -> ProviderConfig:
        return self._configs[name]

    def get_client(self, name: str) -> DeepSeekClient:
        return self._clients[name]

    def describe(self) -> List[Dict[str, Any]]:
        """Key-free view of configured providers (safe to expose over HTTP)."""
        return [
            {
                "name": c.name,
                "base_url": c.base_url,
                "model": c.model,
                "roles": c.roles,
                "has_api_key": bool(c.resolve_api_key()),
            }
            for c in self._configs.values()
        ]

    def resolve_named(
        self, ref: Optional[str]
    ) -> Tuple[str, DeepSeekClient, Optional[str]]:
        """Map a routing reference to ``(provider_name, client, model_or_None)``.

        ``None`` model means "use the client's configured default".
        Unknown refs fall back to the default provider with ``ref`` as the
        raw model name, preserving pre-multi-provider behaviour.
        """
        if not ref:
            return DEFAULT_PROVIDER, self._clients[DEFAULT_PROVIDER], None
        if ref.startswith("@"):
            role = ref[1:]
            for cfg in self._configs.values():
                if role in cfg.roles:
                    return cfg.name, self._clients[cfg.name], None
            logger.warning("no provider declares role %r; using default", role)
            return DEFAULT_PROVIDER, self._clients[DEFAULT_PROVIDER], None
        if ":" in ref:
            name, _, model = ref.partition(":")
            if name in self._clients:
                return name, self._clients[name], (model or None)
        if ref in self._clients:
            return ref, self._clients[ref], None
        return DEFAULT_PROVIDER, self._clients[DEFAULT_PROVIDER], ref

    def resolve(self, ref: Optional[str]) -> Tuple[DeepSeekClient, Optional[str]]:
        """Like :meth:`resolve_named` without the provider name."""
        _, client, model = self.resolve_named(ref)
        return client, model

    async def aclose(self) -> None:
        for client in self._clients.values():
            await client.aclose()


class MultiProviderClient:
    """Drop-in replacement for ``DeepSeekClient`` that routes by model ref.

    The pipeline and the OpenAI-compatible facade keep passing a plain
    ``model`` string; refs like ``"openai:gpt-5.2"`` or ``"@reviewer"``
    transparently select another provider.
    """

    def __init__(self, registry: ProviderRegistry):
        self._registry = registry

    @property
    def registry(self) -> ProviderRegistry:
        return self._registry

    async def chat(self, messages: List[Dict[str, str]], *, model: Optional[str] = None, **kwargs: Any) -> Dict[str, Any]:
        client, resolved = self._registry.resolve(model)
        return await client.chat(messages, model=resolved, **kwargs)

    async def stream_chat(self, messages: List[Dict[str, str]], *, model: Optional[str] = None, **kwargs: Any) -> AsyncIterator[Dict[str, Any]]:
        client, resolved = self._registry.resolve(model)
        async for chunk in client.stream_chat(messages, model=resolved, **kwargs):
            yield chunk

    async def aclose(self) -> None:
        await self._registry.aclose()

    extract_text = staticmethod(DeepSeekClient.extract_text)
    extract_usage = staticmethod(DeepSeekClient.extract_usage)
