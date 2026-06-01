"""Guards for the UI recognition & theming skill set.

These skills strengthen the project's ability to go from a *UI image / design*
to a Flutter implementation:

- ``flutter-ui-from-image``        — read an image into a structured UI spec
  (color sampling, proportional font/spacing scaling, gradient direction,
  key-info extraction)
- ``flutter-design-tokens-theming`` — turn extracted tokens into an engineered
  theme (ColorScheme / TextTheme / ThemeData / light+dark)

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

UI_DESIGN_SKILLS = [
    "flutter-ui-from-image",
    "flutter-design-tokens-theming",
]

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"
ANTIPATTERN_MARKER = "## 反模式"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_ui_design_skills_loaded(registry: SkillRegistry) -> None:
    ids = {s.id for s in registry.list()}
    missing = set(UI_DESIGN_SKILLS) - ids
    assert not missing, f"ui-design skills not loaded: {missing}"


@pytest.mark.parametrize("skill_id", UI_DESIGN_SKILLS)
def test_ui_design_front_matter(registry: SkillRegistry, skill_id: str) -> None:
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


@pytest.mark.parametrize("skill_id", UI_DESIGN_SKILLS)
def test_ui_design_body(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None
    body = skill.body
    assert "http" in body, f"{skill_id} must cite at least one source URL"
    assert ANTIPATTERN_MARKER in body, f"{skill_id} must list anti-patterns"
    assert LENS_HEADER in body, f"{skill_id} missing lens layer {LENS_HEADER!r}"
    assert BOUNDARY_MARKER in body, f"{skill_id} must declare honest boundaries"


def test_orchestrator_wires_ui_design_skills(registry: SkillRegistry) -> None:
    """The workflow orchestrator must reference every ui-design skill."""
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    for skill_id in UI_DESIGN_SKILLS:
        assert skill_id in orch.body, f"orchestrator should reference '{skill_id}'"


def test_ui_design_skills_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in UI_DESIGN_SKILLS:
        assert skill_id in readme, f"{skill_id} not documented in README.md"
        assert skill_id in references, f"{skill_id} not documented in REFERENCES.md"
