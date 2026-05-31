"""Runtime configuration loaded from environment / .env."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Optional

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


REPO_ROOT = Path(__file__).resolve().parents[2]


class Settings(BaseSettings):
    """All knobs are env-driven so the script is 12-factor friendly."""

    model_config = SettingsConfigDict(
        env_file=str(REPO_ROOT / ".env"),
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
    )

    # ---- DeepSeek / OpenAI-compatible upstream ----
    deepseek_api_key: str = Field(default="", description="API key for DeepSeek.")
    deepseek_base_url: str = Field(
        default="https://api.deepseek.com/v1",
        description="OpenAI-compatible base URL.",
    )
    deepseek_model: str = Field(
        default="deepseek-chat",
        description="Primary chat completion model name (use a model your account can call).",
    )
    deepseek_planner_model: Optional[str] = Field(
        default=None,
        description="Optional dedicated model for planning/classify stage.",
    )

    # ---- Local server ----
    host: str = Field(default="127.0.0.1")
    port: int = Field(default=8765)
    local_api_key: str = Field(
        default="",
        description="If set, callers must send 'Authorization: Bearer <key>'.",
    )

    # ---- Skills ----
    skills_dir: str = Field(default="skills")

    # ---- Run history ----
    runs_log_path: str = Field(
        default="logs/runs.jsonl",
        description="Append-only JSONL file recording every /v1/refine call.",
    )

    # ---- Logging ----
    log_format: str = Field(
        default="text",
        description="Log output format: 'text' (human) or 'json' (structured).",
    )
    log_level: str = Field(default="INFO", description="Root log level.")

    # ---- Generation defaults ----
    default_temperature: float = 0.2
    default_max_tokens: int = 4096
    request_timeout_seconds: float = 120.0

    # ---- Concurrency / context governance ----
    max_concurrent_upstream: int = Field(
        default=8,
        ge=1,
        description="Global cap on simultaneous in-flight upstream model calls.",
    )
    max_prior_context_chars: int = Field(
        default=12000,
        ge=1000,
        description=(
            "Per-stage budget for serialized prior-stage JSON injected into the "
            "user prompt. Larger payloads are projected + truncated to fit."
        ),
    )

    @property
    def skills_path(self) -> Path:
        p = Path(self.skills_dir)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def runs_log_file(self) -> Path:
        p = Path(self.runs_log_path)
        return p if p.is_absolute() else (REPO_ROOT / p)

    @property
    def planner_model(self) -> str:
        return self.deepseek_planner_model or self.deepseek_model


@lru_cache(maxsize=1)
def get_settings() -> Settings:
    return Settings()
