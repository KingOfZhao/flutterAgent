"""Integrity checks for the real skills/ corpus.

Guards the cross-reference graph between SKILL.md files:
- ``see_also`` / ``extends`` targets must exist
- ``extends`` must be acyclic (it drives family de-dup in the ranker)
- backticked skill-id references in markdown bodies must resolve
- every skill directory must actually load (no silent parse failures)
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

from flutter_agent.skill_loader import SkillRegistry

ROOT = Path(__file__).resolve().parents[1]
SKILLS_DIR = ROOT / "skills"

# Backticked tokens that look like skill ids but are legitimately external
# (pub packages, CI action inputs, npm packages...). Extend as needed.
NON_SKILL_ALLOWLIST = {
    "flutter-version",      # subosito/flutter-action input name
    "figma-developer-mcp",  # npm package
}

# A body reference is "skill-like" when it is hyphenated lowercase and starts
# with a namespace we own, or matches a known standalone skill id pattern.
_SKILL_LIKE_RE = re.compile(r"^[a-z][a-z0-9]*(?:-[a-z0-9]+)+$")
_OWNED_PREFIXES = ("flutter-", "dart-")
_OWNED_SUFFIXES = ("-mindset", "-analysis", "-thinking", "-refinement", "-management", "-design")


@pytest.fixture(scope="module")
def registry() -> SkillRegistry:
    reg = SkillRegistry(SKILLS_DIR)
    assert reg.reload() > 0, "no skills loaded — wrong path or corrupt corpus"
    return reg


def _skill_like(token: str) -> bool:
    if not _SKILL_LIKE_RE.match(token):
        return False
    if token in NON_SKILL_ALLOWLIST:
        return False
    return token.startswith(_OWNED_PREFIXES) or token.endswith(_OWNED_SUFFIXES)


def test_every_skill_dir_loads(registry: SkillRegistry):
    """Each skill directory's SKILL.md must parse into the registry."""
    dirs = {p.name for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").exists()}
    loaded = {s.id for s in registry.list()}
    missing = dirs - loaded
    assert not missing, f"skill dirs failed to load (parse error or duplicate id): {missing}"


def test_see_also_targets_exist(registry: SkillRegistry):
    ids = {s.id for s in registry.list()}
    dangling = [
        f"{s.id} -> {t}"
        for s in registry.list()
        for t in s.see_also
        if t not in ids
    ]
    assert not dangling, f"dangling see_also references: {dangling}"


def test_extends_targets_exist(registry: SkillRegistry):
    ids = {s.id for s in registry.list()}
    dangling = [
        f"{s.id} -> {t}"
        for s in registry.list()
        for t in s.extends
        if t not in ids
    ]
    assert not dangling, f"dangling extends references: {dangling}"


def test_extends_is_acyclic(registry: SkillRegistry):
    """extends drives ranker family de-dup; a cycle would be a design error."""
    edges = {s.id: set(s.extends) for s in registry.list()}

    WHITE, GRAY, BLACK = 0, 1, 2
    color = {sid: WHITE for sid in edges}

    def visit(node: str, path: list) -> None:
        color[node] = GRAY
        for nxt in edges.get(node, ()):  # pragma: no branch
            if color.get(nxt, BLACK) == GRAY:
                pytest.fail(f"extends cycle: {' -> '.join(path + [node, nxt])}")
            if color.get(nxt) == WHITE:
                visit(nxt, path + [node])
        color[node] = BLACK

    for sid in edges:
        if color[sid] == WHITE:
            visit(sid, [])


def test_body_skill_references_resolve(registry: SkillRegistry):
    """`backticked-skill-ids` mentioned in prose must point at real skills."""
    ids = {s.id for s in registry.list()}
    dangling = []
    for s in registry.list():
        body = Path(s.path).read_text(encoding="utf-8")
        for token in set(re.findall(r"`([a-z][a-z0-9-]{3,})`", body)):
            if _skill_like(token) and token not in ids:
                dangling.append(f"{s.id} -> `{token}`")
    assert not dangling, f"body references to non-existent skills: {sorted(dangling)}"
