"""Guards for the permission/compile-time-config skill and the deepened
UI-restoration layer.

- ``flutter-permissions-and-config`` — runtime permission ≠ manifest
  declaration ≠ compile-time macro/flavor switch: all three layers must be
  checked together (a classic blind spot of LLM-generated permission code).
- ``flutter-ui-from-image`` v1.1 — pixel-level restoration & acceptance
  (line-height, font weight, alpha blending, golden tests, overlay diff).
"""
from __future__ import annotations

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from flutter_agent.config import get_settings
from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.schemas import Stage

VALID_STAGES = {s.value for s in Stage}

PERMISSIONS_SKILL = "flutter-permissions-and-config"

LENS_HEADER = "## 心智模型与诚实边界"
BOUNDARY_MARKER = "诚实边界"
ANTIPATTERN_MARKER = "## 反模式"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(get_settings().skills_path)
    reg.reload()
    return reg


def test_permissions_skill_loaded(registry: SkillRegistry) -> None:
    assert PERMISSIONS_SKILL in {s.id for s in registry.list()}


def test_permissions_front_matter(registry: SkillRegistry) -> None:
    skill = registry.get(PERMISSIONS_SKILL)
    assert skill is not None
    assert skill.name.strip()
    assert skill.body.strip()
    assert skill.tags
    assert skill.applies_when
    assert "all" in {p.lower() for p in skill.platforms}
    assert skill.stage_hints
    assert set(skill.stage_hints) <= VALID_STAGES


def test_permissions_body_covers_three_layers(registry: SkillRegistry) -> None:
    body = registry.get(PERMISSIONS_SKILL).body
    assert "http" in body
    assert ANTIPATTERN_MARKER in body
    assert LENS_HEADER in body
    assert BOUNDARY_MARKER in body
    # the core fix: compile-time macro/flavor layer must be explicit
    assert "dart-define" in body or "fromEnvironment" in body
    assert "flavor" in body
    assert "AndroidManifest" in body
    assert "Info.plist" in body
    assert "permanentlyDenied" in body


def test_ui_from_image_has_pixel_level_layer(registry: SkillRegistry) -> None:
    body = registry.get("flutter-ui-from-image").body
    assert "像素级验收" in body
    assert "matchesGoldenFile" in body
    assert "行高" in body
    assert "alphaBlend" in body


def test_orchestrator_wires_permissions_skill(registry: SkillRegistry) -> None:
    orch = registry.get("flutter-engineering-workflow")
    assert orch is not None
    assert PERMISSIONS_SKILL in orch.body


def test_permissions_skill_documented() -> None:
    root = Path(get_settings().skills_path).resolve().parent
    readme = (root / "README.md").read_text(encoding="utf-8")
    references = (root / "REFERENCES.md").read_text(encoding="utf-8")
    assert PERMISSIONS_SKILL in readme
    assert PERMISSIONS_SKILL in references


def test_rank_surfaces_permissions_skill() -> None:
    from flutter_agent.main import app

    with TestClient(app) as client:
        resp = client.post(
            "/v1/skills/rank",
            json={
                "requirement": "相机权限在某个 flavor 下不生效,dart-define 宏配置和运行时权限判断不一致",
                "platforms": ["mobile"],
            },
        )
    assert resp.status_code == 200
    body = resp.json()
    ranked = {item["id"]: item for item in body["ranked"]}
    assert PERMISSIONS_SKILL in ranked
    assert ranked[PERMISSIONS_SKILL]["selected"], (
        "permission/config skill should be selected for a permission+flavor requirement"
    )
