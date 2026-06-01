"""Guards for the overlap-cluster relationships (B-layer of the redundancy fix).

These ensure the 6 known overlap clusters keep their ``extends`` / ``see_also``
front-matter wiring and a human-readable 分工 (division-of-labour) note in the
body, so the ranker can de-duplicate families and readers know which skill owns
what. If someone edits a skill and drops the wiring, these fail loudly.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from flutter_agent.skill_loader import SkillRegistry
from flutter_agent.skill_ranker import build_families

SKILLS_DIR = Path(__file__).resolve().parent.parent / "skills"


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(SKILLS_DIR)
    reg.reload()
    return reg


# (skill_id, expected extends, expected see_also subset)
_EXTENDS = {
    "flutter-performance-profiling": "flutter-performance",
    "flutter-cicd-pipelines": "flutter-ci-cd",
}

_SEE_ALSO = {
    "flutter-performance": ["flutter-performance-profiling"],
    "flutter-ci-cd": ["flutter-cicd-pipelines"],
    "flutter-network": ["flutter-network-protocols"],
    "flutter-network-protocols": ["flutter-network"],
    "flutter-mobile": ["flutter-android-platform", "flutter-ios-platform"],
    "flutter-android-platform": ["flutter-mobile"],
    "flutter-ios-platform": ["flutter-mobile"],
    "flutter-desktop": ["flutter-desktop-platform"],
    "flutter-desktop-platform": ["flutter-desktop"],
    "flutter-build-and-release": ["flutter-cicd-pipelines"],
}

# skills that must carry an explicit division-of-labour note in the body
_NEEDS_DIVISION_NOTE = sorted(set(_EXTENDS) | set(_SEE_ALSO))


class TestExtendsWiring:
    @pytest.mark.parametrize("sid,parent", sorted(_EXTENDS.items()))
    def test_extends_points_to_parent(self, registry, sid, parent):
        sk = registry.get(sid)
        assert sk is not None, f"missing skill {sid}"
        assert parent in sk.extends, f"{sid} must declare extends: [{parent}]"

    def test_extends_targets_exist(self, registry):
        for sk in registry.list():
            for target in sk.extends:
                assert registry.get(target) is not None, (
                    f"{sk.id} extends unknown skill '{target}'"
                )


class TestSeeAlsoWiring:
    @pytest.mark.parametrize("sid,refs", sorted(_SEE_ALSO.items()))
    def test_see_also_contains_expected(self, registry, sid, refs):
        sk = registry.get(sid)
        assert sk is not None, f"missing skill {sid}"
        for ref in refs:
            assert ref in sk.see_also, f"{sid} should see_also '{ref}'"

    def test_see_also_targets_exist(self, registry):
        for sk in registry.list():
            for target in sk.see_also:
                assert registry.get(target) is not None, (
                    f"{sk.id} see_also unknown skill '{target}'"
                )


class TestFamiliesFormFromExtends:
    def test_two_dedup_families_exist(self, registry):
        skills = list(registry._skills.values())
        fam = build_families(skills)
        # both members of each extends pair must share a family root
        assert fam["flutter-performance"] == fam["flutter-performance-profiling"]
        assert fam["flutter-ci-cd"] == fam["flutter-cicd-pipelines"]


class TestDivisionNotePresent:
    @pytest.mark.parametrize("sid", _NEEDS_DIVISION_NOTE)
    def test_body_has_division_note(self, registry, sid):
        sk = registry.get(sid)
        assert sk is not None, f"missing skill {sid}"
        # The 分工 note names a sibling skill so humans/models know the split.
        assert "分工" in sk.body or "解决" in sk.body, (
            f"{sid} body should carry a 分工/division note pointing at siblings"
        )
