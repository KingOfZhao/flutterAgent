"""Guards for the 女娲/nuwa integration into this project.

Two things are protected here so the distilled knowledge stays growable and
does not silently regress:

1. ``flutter-skill-distillation`` — the in-project meta-skill that encodes the
   nuwa five-layer + triple-validation methodology for authoring mindset skills.
2. The concise "心智模型与诚实边界" (lens + honest-boundary) layer that every
   existing domain skill must now carry.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

VALID_STAGES = {s.value for s in Stage}

DISTILLATION_SKILL = "flutter-skill-distillation"

# Domain skills that must carry the distilled lens + honest-boundary layer.
DOMAIN_SKILLS = [
    "architecture-design",
    "flutter-accessibility",
    "flutter-ai-integration",
    "flutter-animation",
    "flutter-ci-cd",
    "flutter-cross-platform",
    "flutter-data-persistence",
    "flutter-desktop",
    "flutter-i18n",
    "flutter-mobile",
    "flutter-navigation",
    "flutter-network",
    "flutter-performance",
    "flutter-resource-lifecycle",
    "flutter-security",
    "flutter-testing",
    "flutter-web",
    "state-management",
    "task-refinement",
]

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_distillation_meta_skill_loads(registry: SkillRegistry) -> None:
    skill = registry.get(DISTILLATION_SKILL)
    assert skill is not None, f"{DISTILLATION_SKILL} should load"
    assert skill.body.strip()
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{DISTILLATION_SKILL} unknown stage_hints: "
        f"{set(skill.stage_hints) - VALID_STAGES}"
    )


def test_distillation_encodes_nuwa_method(registry: SkillRegistry) -> None:
    """The meta-skill must keep the five layers, triple validation and credit."""
    body = registry.get(DISTILLATION_SKILL).body
    for layer in ("怎么想", "怎么判断", "怎么说话", "什么不做", "知道局限"):
        assert layer in body, f"distillation skill missing nuwa layer: {layer}"
    for phase in ("Phase 1", "Phase 2", "Phase 3", "Phase 4"):
        assert phase in body, f"distillation skill missing {phase}"
    # Triple validation criteria.
    for crit in ("跨领域", "预测力", "排他性"):
        assert crit in body, f"distillation skill missing validation criterion: {crit}"
    assert "nuwa-skill" in body, "must credit the nuwa methodology source"


@pytest.mark.parametrize("skill_id", DOMAIN_SKILLS)
def test_domain_skill_has_lens_and_boundary_layer(
    registry: SkillRegistry, skill_id: str
) -> None:
    """Each domain skill carries the distilled lens + honest-boundary layer."""
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"
    assert LENS_HEADER in skill.body, f"{skill_id} missing '{LENS_HEADER}' layer"
    assert BOUNDARY_MARKER in skill.body, (
        f"{skill_id} must declare an honest boundary (诚实边界)"
    )
    # The layer should point back to the shared mindset/distillation skills so
    # the knowledge stays connected and growable.
    assert "flutter-engineer-mindset" in skill.body, (
        f"{skill_id} lens layer should reference flutter-engineer-mindset"
    )


def test_distillation_documented(registry: SkillRegistry) -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    assert DISTILLATION_SKILL in readme, "distillation skill not in README.md"
    assert DISTILLATION_SKILL in references, "distillation skill not in REFERENCES.md"
