"""Skill discovery endpoints."""
from __future__ import annotations

from typing import List

from fastapi import APIRouter, Depends, HTTPException, status

from ..deps import get_registry, require_api_key
from ..pipeline import _platforms_to_strs, _resolve_foundational_ids
from ..schemas import (
    ErrorResponse,
    SkillDetail,
    SkillRankItem,
    SkillRankRequest,
    SkillRankResponse,
    SkillSummary,
)
from ..skill_loader import SkillRegistry
from ..skill_ranker import (
    DEFAULT_SKILL_TOKEN_BUDGET,
    build_families,
    estimate_tokens,
    rank_skills,
    select_within_budget,
)

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


@router.post(
    "/rank",
    response_model=SkillRankResponse,
    summary="Dry-run the skill selection for a requirement (no model calls)",
    dependencies=[Depends(require_api_key)],
)
async def rank_skills_for_requirement(
    payload: SkillRankRequest,
    registry: SkillRegistry = Depends(get_registry),
) -> SkillRankResponse:
    """Explain which skills would be injected for a requirement and why.

    Runs the exact same ranker the pipeline uses (keyword scores, foundational
    pinning, family de-dup, token budget) and returns every skill's score and
    selection outcome — purely local, zero upstream tokens.
    """
    all_skills: List[SkillDetail] = registry.get_many(
        [s.id for s in registry.list()]
    )
    platforms = _platforms_to_strs(payload.platforms)
    foundational = _resolve_foundational_ids(payload.requirement, platforms)
    budget = payload.token_budget or DEFAULT_SKILL_TOKEN_BUDGET

    ranked = rank_skills(
        requirement=payload.requirement,
        skills=all_skills,
        platforms=platforms,
        always_include=foundational,
    )
    families = build_families(all_skills)
    selected = select_within_budget(
        ranked,
        token_budget=budget,
        always_include=set(foundational),
        families=families,
    )
    selected_ids = [s.id for s in selected]
    selected_set = set(selected_ids)

    items = [
        SkillRankItem(
            id=skill.id,
            name=skill.name,
            score=round(score, 4),
            selected=skill.id in selected_set,
            foundational=skill.id in foundational,
            family=families.get(skill.id) if families.get(skill.id) != skill.id else None,
            estimated_tokens=estimate_tokens(skill.body),
        )
        for skill, score in ranked
    ]
    return SkillRankResponse(
        requirement=payload.requirement,
        platforms=platforms,
        token_budget=budget,
        foundational=foundational,
        selected=selected_ids,
        ranked=items,
    )
