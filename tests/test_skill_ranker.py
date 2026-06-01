"""Tests for skill_ranker: ranking, scoring, and token budget selection."""
from __future__ import annotations

import pytest

from flutter_agent.schemas import SkillDetail
from flutter_agent.skill_ranker import (
    _bigram_tokens,
    _tokenize,
    build_families,
    estimate_tokens,
    rank_skills,
    select_within_budget,
)


def _skill(
    sid: str,
    tags=None,
    platforms=None,
    applies_when="",
    body="x" * 100,
    extends=None,
    see_also=None,
):
    return SkillDetail(
        id=sid,
        name=sid.replace("-", " ").title(),
        version="1.0.0",
        platforms=platforms or ["all"],
        tags=tags or [],
        applies_when=applies_when,
        stage_hints=[],
        extends=extends or [],
        see_also=see_also or [],
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


class TestBigramTokens:
    def test_multi_char_cjk_becomes_bigrams(self):
        toks = _bigram_tokens("通信协议选型")
        assert "协议" in toks
        assert "选型" in toks
        # a single shared character should NOT be a token on its own here
        assert "协" not in toks

    def test_latin_words_kept_whole(self):
        toks = _bigram_tokens("使用 go_router 实现")
        assert "go_router" in toks

    def test_unrelated_terms_do_not_collide(self):
        # 性能 (performance) and 协议 (protocol) share no bigram even though
        # under unigram tokenization they might collide on common characters.
        a = _bigram_tokens("性能优化")
        b = _bigram_tokens("通信协议")
        assert not (a & b)


class TestBuildFamilies:
    def test_extends_groups_into_one_family(self):
        skills = [
            _skill("parent"),
            _skill("child", extends=["parent"]),
            _skill("loner"),
        ]
        fam = build_families(skills)
        assert fam["parent"] == fam["child"]
        assert fam["loner"] != fam["parent"]

    def test_unknown_extends_target_ignored(self):
        skills = [_skill("a", extends=["does-not-exist"])]
        fam = build_families(skills)
        # forms its own singleton family without error
        assert fam["a"] == "a"


class TestFamilyDedup:
    def _ranked(self):
        # parent ranks above child; both score higher than others
        return [
            (_skill("parent", body="x" * 100), 10.0),
            (_skill("child", extends=["parent"], body="x" * 100), 9.0),
            (_skill("other-a", body="x" * 100), 8.0),
            (_skill("other-b", body="x" * 100), 7.0),
        ]

    def test_only_top_family_member_selected(self):
        ranked = self._ranked()
        fam = build_families([s for s, _ in ranked])
        selected = select_within_budget(
            ranked, token_budget=10_000, min_skills=3, families=fam
        )
        ids = [s.id for s in selected]
        assert "parent" in ids
        assert "child" not in ids  # de-duplicated even inside min_skills floor

    def test_always_include_can_override_dedup(self):
        ranked = self._ranked()
        fam = build_families([s for s, _ in ranked])
        selected = select_within_budget(
            ranked, token_budget=10_000, min_skills=0,
            always_include={"child"}, families=fam,
        )
        ids = [s.id for s in selected]
        assert "parent" in ids and "child" in ids

    def test_no_families_means_no_dedup(self):
        ranked = self._ranked()
        selected = select_within_budget(
            ranked, token_budget=10_000, min_skills=3, families=None
        )
        ids = [s.id for s in selected]
        assert "parent" in ids and "child" in ids


class TestFoundationalIdResolution:
    """A3: foundational skills are only force-pinned when warranted."""

    def test_narrow_ops_task_pins_nothing(self):
        from flutter_agent.pipeline import _resolve_foundational_ids
        ids = _resolve_foundational_ids("Android 打包发布，配置签名和混淆", ["mobile"])
        assert ids == []

    def test_profiling_task_pins_nothing(self):
        from flutter_agent.pipeline import _resolve_foundational_ids
        ids = _resolve_foundational_ids("性能剖析定位掉帧 jank", ["mobile"])
        assert ids == []

    def test_state_task_pins_state(self):
        from flutter_agent.pipeline import _resolve_foundational_ids
        ids = _resolve_foundational_ids("用 riverpod 管理登录状态", ["mobile"])
        assert "state-management" in ids

    def test_generic_signalless_task_pins_both(self):
        # No structure/state/ops signal at all -> fall back to pinning both.
        from flutter_agent.pipeline import _resolve_foundational_ids
        ids = _resolve_foundational_ids("帮我做一个聊天应用", ["mobile"])
        assert "architecture-design" in ids and "state-management" in ids

    def test_cross_platform_added_for_mobile_and_desktop(self):
        from flutter_agent.pipeline import _resolve_foundational_ids
        ids = _resolve_foundational_ids("配置 CI 流水线", ["mobile", "desktop"])
        assert "flutter-cross-platform" in ids
