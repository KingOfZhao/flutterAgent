"""Guards for the design-to-code, component-recipes, CI/CD-deepening and
observability skill set.

- ``flutter-design-to-code-playbook`` — end-to-end design → Flutter code SOP
- ``flutter-ui-component-recipes``     — component-level restoration recipes
- ``flutter-cicd-pipelines``           — CI/CD deepening (matrix / cache /
  artifacts / release automation)
- ``flutter-observability``            — crash reporting / logging / metrics /
  tracing / analytics

They must load, expose valid front-matter, apply to all platforms, cite
official sources, carry the distilled "心智模型与诚实边界" layer, be wired into
the orchestrator, and be documented in README.md and REFERENCES.md.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

VALID_STAGES = {s.value for s in Stage}

DELIVERY_UIKIT_SKILLS = [
    "flutter-design-to-code-playbook",
    "flutter-ui-component-recipes",
    "flutter-cicd-pipelines",
    "flutter-observability",
]

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"
ANTIPATTERN_MARKER = "## 反模式"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_delivery_uikit_skills_loaded(registry: SkillRegistry) -> None:
    ids = {s.id for s in registry.list()}
    missing = set(DELIVERY_UIKIT_SKILLS) - ids
    assert not missing, f"delivery/uikit skills not loaded: {missing}"


@pytest.mark.parametrize("skill_id", DELIVERY_UIKIT_SKILLS)
def test_delivery_uikit_front_matter(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"
    assert skill.name.strip(), f"{skill_id} missing name"
    assert skill.body.strip(), f"{skill_id} has empty body"
    assert skill.tags, f"{skill_id} must declare tags"
    assert skill.applies_when, f"{skill_id} must declare applies_when"
    assert skill.platforms, f"{skill_id} must declare platforms"
    assert "all" in {p.lower() for p in skill.platforms}, (
        f"{skill_id} should apply to all platforms"
    )
    assert skill.stage_hints, f"{skill_id} should declare at least one stage hint"
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{skill_id} has unknown stage_hints: {set(skill.stage_hints) - VALID_STAGES}"
    )


@pytest.mark.parametrize("skill_id", DELIVERY_UIKIT_SKILLS)
def test_delivery_uikit_body(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None
    body = skill.body
    assert "http" in body, f"{skill_id} must cite at least one source URL"
    assert ANTIPATTERN_MARKER in body, f"{skill_id} must list anti-patterns"
    assert LENS_HEADER in body, f"{skill_id} missing lens layer {LENS_HEADER!r}"
    assert BOUNDARY_MARKER in body, f"{skill_id} must declare honest boundaries"


def test_orchestrator_wires_delivery_uikit_skills(registry: SkillRegistry) -> None:
    """The workflow orchestrator must reference every skill in this set."""
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    for skill_id in DELIVERY_UIKIT_SKILLS:
        assert skill_id in orch.body, f"orchestrator should reference '{skill_id}'"


def test_delivery_uikit_skills_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in DELIVERY_UIKIT_SKILLS:
        assert skill_id in readme, f"{skill_id} not documented in README.md"
        assert skill_id in references, f"{skill_id} not documented in REFERENCES.md"
