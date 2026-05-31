"""Skill discovery endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_registry, require_api_key
from ..schemas import ErrorResponse, SkillDetail, SkillSummary
from ..skill_loader import SkillRegistry

router = APIRouter(prefix="/v1/skills", tags=["skills"])


@router.get(
    "",
    response_model=List[SkillSummary],
    summary="List all loaded skills",
    dependencies=[Depends(require_api_key)],
)
async def list_skills(
    registry: SkillRegistry = Depends(get_registry),
) -> List[SkillSummary]:
    return registry.list()


@router.get(
    "/{skill_id}",
    response_model=SkillDetail,
    summary="Get a single skill (incl. full markdown body)",
    responses={404: {"model": ErrorResponse}},
    dependencies=[Depends(require_api_key)],
)
async def get_skill(
    skill_id: str,
    registry: SkillRegistry = Depends(get_registry),
) -> SkillDetail:
    skill = registry.get(skill_id)
    if skill is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"unknown skill id: {skill_id}",
        )
    return skill


@router.post(
    "/reload",
    response_model=dict,
    summary="Hot-reload skill markdown files from disk",
    dependencies=[Depends(require_api_key)],
)
async def reload_skills(
    registry: SkillRegistry = Depends(get_registry),
) -> dict:
    count = registry.reload()
    return {"loaded": count}
