"""Multi-provider listing and multi-agent collaboration endpoints.

  * GET  /v1/agents/providers       key-free view of configured providers
  * POST /v1/agents/collaborate     run solo / debate / committee collaboration
  * GET  /v1/agents/collaborations  tail of the JSONL audit log
"""
from __future__ import annotations

import json

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, Field

from ..collaboration import AgentSpec, AgentTeam, CollaborationResult
from ..deepseek_client import UpstreamError
from ..deps import get_settings, require_api_key
from ..config import Settings

router = APIRouter(prefix="/v1/agents", tags=["agents"])


def get_team(request: Request) -> AgentTeam:
    return request.app.state.agent_team


class CollaborateRequest(BaseModel):
    task: str = Field(min_length=1, description="The task all agents work on.")
    mode: str = Field(
        default="debate",
        pattern=r"^(solo|debate|committee|peer_review)$",
        description="Collaboration topology.",
    )
    agents: List[AgentSpec] = Field(
        default_factory=list,
        description="Optional explicit roster; sensible defaults per mode.",
    )
    max_rounds: Optional[int] = Field(default=None, ge=1, le=5)


@router.get(
    "/providers",
    dependencies=[Depends(require_api_key)],
)
async def list_providers(request: Request) -> Dict[str, Any]:
    team: AgentTeam = get_team(request)
    return {"providers": team.registry.describe()}


@router.get(
    "/collaborations",
    dependencies=[Depends(require_api_key)],
)
async def list_collaborations(
    settings: Settings = Depends(get_settings),
    limit: int = Query(default=20, ge=1, le=200),
) -> Dict[str, Any]:
    """Return the last ``limit`` audit records (newest last)."""
    path = settings.collab_log_file
    if path is None:
        return {"enabled": False, "records": []}
    records: List[Dict[str, Any]] = []
    try:
        with path.open("r", encoding="utf-8") as fh:
            lines = fh.readlines()
    except FileNotFoundError:
        return {"enabled": True, "records": []}
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            records.append(json.loads(line))
        except ValueError:
            continue
    return {"enabled": True, "records": records}


@router.post(
    "/collaborate",
    response_model=CollaborationResult,
    dependencies=[Depends(require_api_key)],
)
async def collaborate(
    body: CollaborateRequest,
    request: Request,
    settings: Settings = Depends(get_settings),
) -> CollaborationResult:
    team = get_team(request)
    try:
        return await team.run(
            body.task, body.mode, agents=body.agents, max_rounds=body.max_rounds
        )
    except ValueError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except UpstreamError as exc:
        raise HTTPException(status_code=502, detail=str(exc)) from exc
