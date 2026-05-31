"""FastAPI dependency-injection helpers.

The app stores the long-lived objects (settings, registry, client, pipeline)
on ``app.state`` at startup; these helpers fetch them out of the current
request so individual routes stay testable.
"""
from __future__ import annotations

import secrets
from typing import Optional

from fastapi import Depends, Header, HTTPException, Request, status

from .config import Settings
from .deepseek_client import DeepSeekClient
from .pipeline import RefinementPipeline
from .run_store import RunStore
from .skill_loader import SkillRegistry


def get_settings(request: Request) -> Settings:
    return request.app.state.settings


def get_registry(request: Request) -> SkillRegistry:
    return request.app.state.registry


def get_client(request: Request) -> DeepSeekClient:
    return request.app.state.client


def get_pipeline(request: Request) -> RefinementPipeline:
    return request.app.state.pipeline


def get_run_store(request: Request) -> RunStore:
    return request.app.state.run_store


def require_api_key(
    settings: Settings = Depends(get_settings),
    authorization: Optional[str] = Header(default=None),
) -> None:
    """If LOCAL_API_KEY is set, demand a matching Bearer token."""
    expected = (settings.local_api_key or "").strip()
    if not expected:
        return  # auth disabled
    if not authorization or not authorization.lower().startswith("bearer "):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="missing bearer token",
            headers={"WWW-Authenticate": "Bearer"},
        )
    token = authorization.split(" ", 1)[1].strip()
    if token != expected:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="invalid api key",
        )
