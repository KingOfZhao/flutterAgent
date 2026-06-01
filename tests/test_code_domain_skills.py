"""Guards for the code-domain skill set.

These skills strengthen the project's *programming & code-maintenance* ability
(as opposed to feature-domain knowledge or expert mindsets):

- ``dart-language-idioms``        — write idiomatic Dart (Effective Dart + Dart 3)
- ``flutter-code-review``         — review SOP / red lines / feedback
- ``flutter-refactoring``         — safe, behavior-preserving refactoring
- ``flutter-dependency-maintenance`` — keep dependencies healthy
- ``flutter-error-handling``      — model failure paths
- ``flutter-codegen``             — build_runner / freezed / json / riverpod

They must load, expose valid front-matter, cite sources, carry the distilled
"心智模型与诚实边界" layer, be wired into the orchestrator, and be documented.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

VALID_STAGES = {s.value for s in Stage}

CODE_DOMAIN_SKILLS = [
    "dart-language-idioms",
    "flutter-code-review",
    "flutter-refactoring",
    "flutter-dependency-maintenance",
    "flutter-error-handling",
    "flutter-codegen",
    "flutter-concurrency-isolates",
    "dart-api-package-design",
    "flutter-static-analysis",
    "flutter-monorepo-melos",
]

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"
ANTIPATTERN_MARKER = "## 反模式"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_code_domain_skills_loaded(registry: SkillRegistry) -> None:
    ids = {s.id for s in registry.list()}
    missing = set(CODE_DOMAIN_SKILLS) - ids
    assert not missing, f"code-domain skills not loaded: {missing}"


@pytest.mark.parametrize("skill_id", CODE_DOMAIN_SKILLS)
def test_code_domain_skill_front_matter(registry: SkillRegistry, skill_id: str) -> None:
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


@pytest.mark.parametrize("skill_id", CODE_DOMAIN_SKILLS)
def test_code_domain_skill_body(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None
    body = skill.body
    # Traceable sources (project anti-hallucination rule).
    assert "http" in body, f"{skill_id} must cite at least one source URL"
    # Explicit anti-pattern section.
    assert ANTIPATTERN_MARKER in body, f"{skill_id} must list anti-patterns"
    # Distilled lens + honest-boundary layer keeps these skills self-aware.
    assert LENS_HEADER in body, f"{skill_id} missing lens layer {LENS_HEADER!r}"
    assert BOUNDARY_MARKER in body, f"{skill_id} must declare honest boundaries"


def test_orchestrator_wires_code_domain_skills(registry: SkillRegistry) -> None:
    """The workflow orchestrator must reference every code-domain skill."""
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    for skill_id in CODE_DOMAIN_SKILLS:
        assert skill_id in orch.body, (
            f"orchestrator should reference '{skill_id}'"
        )


def test_code_domain_skills_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in CODE_DOMAIN_SKILLS:
        assert skill_id in readme, f"{skill_id} not documented in README.md"
        assert skill_id in references, f"{skill_id} not documented in REFERENCES.md"
