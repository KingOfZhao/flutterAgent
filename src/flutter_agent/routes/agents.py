"""Multi-provider listing and multi-agent collaboration endpoints.

  * GET  /v1/agents/providers    key-free view of configured providers
  * POST /v1/agents/collaborate  run solo / debate / committee collaboration
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, Request
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
