"""Tests for the distilled Flutter engineering-workflow skill set.

These guard the "fix / feature / verify / docs / deliver" framework skills:
they must load, expose valid front-matter, declare sane stage_hints, and
cross-reference each other so the orchestrator skill actually wires the loop
together.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

# id -> (expected stage_hints subset that must be present)
FRAMEWORK_SKILLS = {
    "flutter-engineering-workflow": {"breakdown", "acceptance"},
    "flutter-feature-development": {"architecture", "breakdown"},
    "flutter-debugging": {"breakdown", "acceptance"},
    "flutter-verification": {"acceptance"},
    "flutter-documentation": {"markdown", "acceptance"},
}

VALID_STAGES = {s.value for s in Stage}

# Skills authored in the official flutter/skills body structure
# (https://github.com/flutter/skills). They keep this project's front-matter
# fields too, so they must load AND look like official skills.
OFFICIAL_FORMAT_SKILLS = {
    "flutter-environment-setup",
    "flutter-build-and-release",
    "flutter-performance-profiling",
}

# Section headers that mark the official skill structure.
OFFICIAL_SECTIONS = ("## Contents", "## Core Concepts", "**Task Progress:**")


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_framework_skills_are_loaded(registry: SkillRegistry) -> None:
    ids = {s.id for s in registry.list()}
    missing = set(FRAMEWORK_SKILLS) - ids
    assert not missing, f"framework skills not loaded: {missing}"


@pytest.mark.parametrize("skill_id, expected_hints", FRAMEWORK_SKILLS.items())
def test_framework_skill_metadata(
    registry: SkillRegistry, skill_id: str, expected_hints: set
) -> None:
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"

    # Front-matter sanity.
    assert skill.name.strip(), f"{skill_id} missing name"
    assert skill.body.strip(), f"{skill_id} has empty body"
    assert "all" in {p.lower() for p in skill.platforms}, (
        f"{skill_id} should apply to all platforms"
    )

    # stage_hints must be valid pipeline stages and include the expected ones.
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{skill_id} has unknown stage_hints: {set(skill.stage_hints) - VALID_STAGES}"
    )
    assert expected_hints <= set(skill.stage_hints), (
        f"{skill_id} stage_hints {skill.stage_hints} missing {expected_hints}"
    )


def test_orchestrator_references_phase_skills(registry: SkillRegistry) -> None:
    """The top-level workflow skill must wire every phase skill into the loop."""
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    for phase_id in (
        "flutter-debugging",
        "flutter-feature-development",
        "flutter-verification",
        "flutter-documentation",
    ):
        assert phase_id in orch.body, (
            f"orchestrator should reference '{phase_id}'"
        )


def test_framework_skills_cite_sources(registry: SkillRegistry) -> None:
    """Every framework skill must carry traceable references (project rule)."""
    for skill_id in FRAMEWORK_SKILLS:
        skill = registry.get(skill_id)
        assert skill is not None
        assert "http" in skill.body, f"{skill_id} must cite at least one source URL"


def test_framework_skills_referenced_in_docs() -> None:
    """README + REFERENCES must list the new skills (docs follow the change)."""
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in (*FRAMEWORK_SKILLS, *OFFICIAL_FORMAT_SKILLS):
        assert skill_id in readme, f"{skill_id} not documented in README.md"
        assert skill_id in references, f"{skill_id} not documented in REFERENCES.md"


@pytest.mark.parametrize("skill_id", sorted(OFFICIAL_FORMAT_SKILLS))
def test_official_format_skills_load_and_are_rankable(
    registry: SkillRegistry, skill_id: str
) -> None:
    """Official-format skills must still parse and stay usable by the pipeline."""
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"
    assert skill.body.strip(), f"{skill_id} has empty body"
    # Functional front-matter the ranker/pipeline rely on.
    assert skill.platforms, f"{skill_id} must declare platforms"
    assert skill.tags, f"{skill_id} must declare tags"
    assert skill.applies_when, f"{skill_id} must declare applies_when"
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{skill_id} has unknown stage_hints: {set(skill.stage_hints) - VALID_STAGES}"
    )
    assert skill.stage_hints, f"{skill_id} should declare at least one stage hint"


@pytest.mark.parametrize("skill_id", sorted(OFFICIAL_FORMAT_SKILLS))
def test_official_format_skills_follow_flutter_structure(
    registry: SkillRegistry, skill_id: str
) -> None:
    """Body should follow the flutter/skills structure and cite sources."""
    skill = registry.get(skill_id)
    assert skill is not None
    for marker in OFFICIAL_SECTIONS:
        assert marker in skill.body, f"{skill_id} missing official section: {marker!r}"
    assert "http" in skill.body, f"{skill_id} must cite at least one source URL"
