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

# Expert "cognitive OS" skills distilled with the nuwa five-layer method.
# Each must keep the five layers, credit the method, and stay honest about
# being a public-info lens (not the person).
EXPERT_SKILLS = [
    "remi-rousselet-mindset",
    "felix-angelov-mindset",
    "tim-sneath-mindset",
    "andrea-bizzotto-mindset",
    "filip-hracek-mindset",
    "devin-ai-engineer-mindset",
]

EXPERT_LAYERS = (
    "## 核心心智模型",
    "## 决策启发式",
    "## 表达 DNA",
    "## 价值观与反模式",
    "## 诚实边界",
)


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
    # README 必须有"蒸馏方法"章节,讲清五层 + 三重验证 + Phase 1–4
    assert "## 蒸馏方法" in readme, "distillation method section missing from README.md"
    for marker in ("五层", "三重验证", "Phase 1", "已蒸馏花名册"):
        assert marker in readme, f"distillation method README missing '{marker}'"


@pytest.mark.parametrize("skill_id", EXPERT_SKILLS)
def test_expert_mindset_skill_structure(registry: SkillRegistry, skill_id: str) -> None:
    """Each distilled expert skill follows the nuwa five-layer structure."""
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"
    assert skill.body.strip() and skill.tags and skill.applies_when
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{skill_id} unknown stage_hints: {set(skill.stage_hints) - VALID_STAGES}"
    )
    for layer in EXPERT_LAYERS:
        assert layer in skill.body, f"{skill_id} missing nuwa layer: {layer!r}"
    # Anti-hallucination: must be an honest, sourced lens — not the real person.
    assert "诚实边界" in skill.body, f"{skill_id} must declare honest boundaries"
    assert "镜片" in skill.body or "不代表" in skill.body or "非本人" in skill.body, (
        f"{skill_id} must clarify it is a public-info lens, not the person"
    )
    assert "nuwa-skill" in skill.body, f"{skill_id} must credit the nuwa method"
    assert "http" in skill.body, f"{skill_id} must cite sources"


def test_expert_skills_in_distillation_roster(registry: SkillRegistry) -> None:
    """The meta-skill roster must list every distilled expert (single source)."""
    roster = registry.get(DISTILLATION_SKILL).body
    for skill_id in EXPERT_SKILLS:
        assert skill_id in roster, f"{skill_id} missing from distillation roster"


def test_expert_skills_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in EXPERT_SKILLS:
        assert skill_id in readme, f"{skill_id} not in README.md"
        assert skill_id in references, f"{skill_id} not in REFERENCES.md"
