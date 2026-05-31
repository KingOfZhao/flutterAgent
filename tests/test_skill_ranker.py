"""Tests for skill_ranker: ranking, scoring, and token budget selection."""
from __future__ import annotations

import pytest

from flutter_agent.schemas import SkillDetail
from flutter_agent.skill_ranker import (
    _tokenize,
    estimate_tokens,
    rank_skills,
    select_within_budget,
)


def _skill(sid: str, tags=None, platforms=None, applies_when="", body="x" * 100):
    return SkillDetail(
        id=sid,
        name=sid.replace("-", " ").title(),
        version="1.0.0",
        platforms=platforms or ["all"],
        tags=tags or [],
        applies_when=applies_when,
        stage_hints=[],
        path=f"/fake/{sid}/SKILL.md",
        body=body,
    )


class TestTokenize:
    def test_latin(self):
        tokens = _tokenize("Hello world flutter animation")
        assert "hello" in tokens
        assert "flutter" in tokens

    def test_cjk(self):
        tokens = _tokenize("需要动画效果")
        assert "动" in tokens
        assert "画" in tokens

    def test_mixed(self):
        tokens = _tokenize("使用 go_router 实现深度链接")
        assert "go_router" in tokens
        assert "深" in tokens


class TestEstimateTokens:
    def test_returns_positive(self):
        assert estimate_tokens("Hello world") >= 1

    def test_longer_is_more(self):
        assert estimate_tokens("a" * 1000) > estimate_tokens("a" * 10)


class TestRankSkills:
    @pytest.fixture()
    def skills(self):
        return [
            _skill("flutter-animation", tags=["animation", "motion", "hero"],
                   applies_when="涉及动画、过渡效果"),
            _skill("flutter-navigation", tags=["navigation", "routing", "deeplink"],
                   applies_when="涉及页面跳转、深度链接"),
            _skill("flutter-mobile", tags=["mobile", "ios", "android"],
                   platforms=["mobile"]),
            _skill("architecture-design", tags=["architecture", "clean"],
                   applies_when="任何项目"),
        ]

    def test_animation_requirement_ranks_animation_first(self, skills):
        ranked = rank_skills(
            "需要 hero animation 过渡动画和 motion 运动效果",
            skills,
            platforms=["web"],  # use non-mobile platform to avoid mobile bonus
            always_include=None,
        )
        ids = [s.id for s, _ in ranked]
        assert ids[0] == "flutter-animation"

    def test_navigation_requirement_ranks_navigation_first(self, skills):
        ranked = rank_skills(
            "实现深度链接 deep link 和 tab navigation",
            skills,
            platforms=["mobile"],
        )
        ids = [s.id for s, _ in ranked]
        assert ids[0] == "flutter-navigation"

    def test_always_include_gets_top_score(self, skills):
        ranked = rank_skills(
            "simple app",
            skills,
            platforms=["mobile"],
            always_include=["architecture-design"],
        )
        top = ranked[0]
        assert top[0].id == "architecture-design"
        assert top[1] >= 100.0

    def test_platform_bonus(self, skills):
        ranked = rank_skills(
            "some requirement",
            skills,
            platforms=["mobile"],
        )
        scores = {s.id: sc for s, sc in ranked}
        # flutter-mobile should score higher due to platform match
        assert scores["flutter-mobile"] > scores.get("flutter-navigation", 0)


class TestSelectWithinBudget:
    def test_selects_at_least_min_skills(self):
        skills = [
            (_skill(f"skill-{i}", body="x" * 10000), 10 - i) for i in range(5)
        ]
        selected = select_within_budget(skills, token_budget=100, min_skills=3)
        assert len(selected) >= 3

    def test_respects_budget(self):
        skills = [
            (_skill(f"skill-{i}", body="x" * 5000), 10 - i) for i in range(10)
        ]
        selected = select_within_budget(
            skills, token_budget=5000, min_skills=1
        )
        # Should not select all 10 skills (50k chars / 2.8 ≈ 17k tokens > 5k budget)
        assert len(selected) < 10

    def test_always_include_even_over_budget(self):
        skills = [
            (_skill("must-have", body="x" * 100000), 1.0),
            (_skill("optional", body="x" * 100), 5.0),
        ]
        selected = select_within_budget(
            skills, token_budget=100, min_skills=0,
            always_include={"must-have"},
        )
        ids = [s.id for s in selected]
        assert "must-have" in ids
