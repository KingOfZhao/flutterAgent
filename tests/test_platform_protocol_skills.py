"""Guards for the platform & protocol skill set.

These skills strengthen the project's *platform engineering* (PC / iOS / Android)
and *communication protocol* coverage:

- ``flutter-platform-channels``  — native interop (MethodChannel / Pigeon / FFI)
- ``flutter-android-platform``   — Android project layer (Gradle / Manifest / R8)
- ``flutter-ios-platform``       — iOS/Apple project layer (Xcode / Info.plist / ATS)
- ``flutter-desktop-platform``   — Windows / macOS / Linux packaging & signing
- ``flutter-network-protocols``  — HTTP/2·3, REST, gRPC, GraphQL, WebSocket, SSE, MQTT, TLS
- ``flutter-auth-protocols``     — OAuth2 / OIDC / PKCE / JWT / refresh / biometric

They must load, expose valid front-matter, cite official sources, carry the
distilled "心智模型与诚实边界" layer, be wired into the orchestrator, and be
documented in README.md and REFERENCES.md.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

VALID_STAGES = {s.value for s in Stage}
VALID_PLATFORMS = {"all", "mobile", "desktop", "web"}

# Platform-scoped skills legitimately target a single platform family.
PLATFORM_SKILLS = [
    "flutter-platform-channels",
    "flutter-android-platform",
    "flutter-ios-platform",
    "flutter-desktop-platform",
]
# Protocol skills are platform-agnostic, so they must apply to "all".
PROTOCOL_SKILLS = [
    "flutter-network-protocols",
    "flutter-auth-protocols",
]
PLATFORM_PROTOCOL_SKILLS = PLATFORM_SKILLS + PROTOCOL_SKILLS

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"
ANTIPATTERN_MARKER = "## 反模式"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_platform_protocol_skills_loaded(registry: SkillRegistry) -> None:
    ids = {s.id for s in registry.list()}
    missing = set(PLATFORM_PROTOCOL_SKILLS) - ids
    assert not missing, f"platform/protocol skills not loaded: {missing}"


@pytest.mark.parametrize("skill_id", PLATFORM_PROTOCOL_SKILLS)
def test_platform_protocol_front_matter(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None, f"{skill_id} should load"
    assert skill.name.strip(), f"{skill_id} missing name"
    assert skill.body.strip(), f"{skill_id} has empty body"
    assert skill.tags, f"{skill_id} must declare tags"
    assert skill.applies_when, f"{skill_id} must declare applies_when"
    assert skill.platforms, f"{skill_id} must declare platforms"
    assert {p.lower() for p in skill.platforms} <= VALID_PLATFORMS, (
        f"{skill_id} has unknown platforms: "
        f"{set(skill.platforms) - VALID_PLATFORMS}"
    )
    assert skill.stage_hints, f"{skill_id} should declare at least one stage hint"
    assert set(skill.stage_hints) <= VALID_STAGES, (
        f"{skill_id} has unknown stage_hints: {set(skill.stage_hints) - VALID_STAGES}"
    )


@pytest.mark.parametrize("skill_id", PROTOCOL_SKILLS)
def test_protocol_skills_are_platform_agnostic(
    registry: SkillRegistry, skill_id: str
) -> None:
    skill = registry.get(skill_id)
    assert skill is not None
    assert "all" in {p.lower() for p in skill.platforms}, (
        f"{skill_id} (a protocol skill) should apply to all platforms"
    )


@pytest.mark.parametrize("skill_id", PLATFORM_PROTOCOL_SKILLS)
def test_platform_protocol_body(registry: SkillRegistry, skill_id: str) -> None:
    skill = registry.get(skill_id)
    assert skill is not None
    body = skill.body
    assert "http" in body, f"{skill_id} must cite at least one source URL"
    assert ANTIPATTERN_MARKER in body, f"{skill_id} must list anti-patterns"
    assert LENS_HEADER in body, f"{skill_id} missing lens layer {LENS_HEADER!r}"
    assert BOUNDARY_MARKER in body, f"{skill_id} must declare honest boundaries"


def test_orchestrator_wires_platform_protocol_skills(registry: SkillRegistry) -> None:
    """The workflow orchestrator must reference every platform/protocol skill."""
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    for skill_id in PLATFORM_PROTOCOL_SKILLS:
        assert skill_id in orch.body, f"orchestrator should reference '{skill_id}'"


def test_platform_protocol_skills_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    for skill_id in PLATFORM_PROTOCOL_SKILLS:
        assert skill_id in readme, f"{skill_id} not documented in README.md"
        assert skill_id in references, f"{skill_id} not documented in REFERENCES.md"
