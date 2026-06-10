"""Tests for the comprehensive-thinking (全面思考) skill integration.

Verifies:
  * the skill loads with valid front-matter,
  * its body keeps the five-review output contract,
  * the ranker surfaces it for requirements that explicitly ask for 全面思考 /
    架构判断-style high-stakes reasoning.
"""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.config import get_settings  # noqa: E402
from flutter_agent.skill_loader import SkillRegistry  # noqa: E402
from flutter_agent.skill_ranker import rank_skills  # noqa: E402

SKILL_ID = "comprehensive-thinking"


def _registry() -> SkillRegistry:
    registry = SkillRegistry(get_settings().skills_path)
    registry.reload()
    return registry


def test_skill_loads_with_expected_metadata() -> None:
    skill = _registry().get(SKILL_ID)
    assert skill is not None, "comprehensive-thinking skill failed to load"
    assert skill.platforms == ["all"]
    assert "全面思考" in skill.tags
    assert skill.applies_when
    assert set(skill.stage_hints) <= {
        "classify", "spec", "architecture", "breakdown",
        "implementation", "review", "acceptance", "markdown",
    }


def test_body_keeps_five_review_contract() -> None:
    skill = _registry().get(SKILL_ID)
    assert skill is not None
    for marker in (
        "第一重审视",
        "第二重审视",
        "第三重审视",
        "第四重审视",
        "第五重审视",
        "最终判断",
        "最强反方意见",
        "前提辩证分析",
        "大师理论体系研究法",
    ):
        assert marker in skill.body, f"missing section: {marker}"


def test_ranker_surfaces_skill_for_comprehensive_thinking_requirement() -> None:
    registry = _registry()
    skills = list(registry._skills.values())
    ranked = rank_skills(
        requirement="请全面思考:这个多数据源离线同步架构方案到底该怎么选,做架构判断和根因分析",
        skills=skills,
        platforms=["mobile"],
    )
    top_ids = [s.id for s, _ in ranked[:10]]
    assert SKILL_ID in top_ids, f"{SKILL_ID} not in top 10: {top_ids}"
