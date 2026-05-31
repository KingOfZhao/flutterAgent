"""GET /v1/metrics — aggregate run statistics."""
from __future__ import annotations

from fastapi import APIRouter, Depends

from ..deps import get_registry, get_run_store, require_api_key
from ..run_store import RunStore
from ..schemas import MetricsResponse
from ..skill_loader import SkillRegistry

router = APIRouter(prefix="/v1", tags=["meta"])


@router.get(
    "/metrics",
    response_model=MetricsResponse,
    summary="Aggregate statistics across all recorded runs.",
    dependencies=[Depends(require_api_key)],
)
async def get_metrics(
    store: RunStore = Depends(get_run_store),
    registry: SkillRegistry = Depends(get_registry),
) -> MetricsResponse:
    data = store.compute_metrics()
    data["skills_loaded"] = len(registry)
    return MetricsResponse(**data)
