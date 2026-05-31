"""Rank and select skills based on requirement text relevance + token budget.

Strategy (simple but effective):
1. Keyword overlap: tokenize requirement into CJK chars + latin words, compute
   Jaccard coefficient against each skill's `tags` + `applies_when` + first 200
   chars of body.
2. Platform match gives a bonus.
3. Skills are sorted by score descending; we greedily fill until the token
   budget is exhausted.

No external NLP libs required — works offline with pure string ops.
"""
from __future__ import annotations

import re
from typing import Dict, List, Optional, Set, Tuple

from .schemas import SkillDetail

# Rough token estimate: 1 token ≈ 4 chars for English, ≈ 1.5 chars for CJK.
# We use a blended average since skills contain mixed content.
_CHARS_PER_TOKEN = 2.8

# Default token budget for the system prompt (skills portion only).
# DeepSeek chat context is 128k; we allocate 40k tokens for skills, leaving
# 88k for user prompt + model output.  This is conservative and configurable.
DEFAULT_SKILL_TOKEN_BUDGET = 40_000

# Tokenizer: split on whitespace, punctuation, CJK boundaries.
_WORD_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+", re.UNICODE)


def _tokenize(text: str) -> Set[str]:
    """Extract a bag of lowercase tokens from text."""
    return {m.group(0).lower() for m in _WORD_RE.finditer(text or "")}


def _skill_keywords(skill: SkillDetail) -> Set[str]:
    """Build keyword set for a skill from tags + applies_when + body snippet."""
    parts: List[str] = []
    parts.extend(skill.tags)
    if skill.applies_when:
        parts.append(skill.applies_when)
    # Use the skill name as well
    parts.append(skill.name)
    # First 300 chars of body for additional keyword density
    parts.append(skill.body[:300])
    combined = " ".join(parts)
    return _tokenize(combined)


def estimate_tokens(text: str) -> int:
    """Rough token count (no tiktoken dependency)."""
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


def rank_skills(
    requirement: str,
    skills: List[SkillDetail],
    platforms: List[str],
    *,
    always_include: Optional[List[str]] = None,
) -> List[Tuple[SkillDetail, float]]:
    """Return skills sorted by descending relevance score.

    Parameters
    ----------
    requirement : str
        The user's raw requirement text.
    skills : list
        All candidate skills.
    platforms : list
        Requested target platforms (e.g. ["mobile", "desktop"]).
    always_include : list or None
        Skill IDs that must always be included regardless of score.

    Returns
    -------
    list of (SkillDetail, score) sorted descending.
    """
    always = set(always_include or [])
    req_tokens = _tokenize(requirement)
    platform_set = {p.lower() for p in platforms}

    scored: List[Tuple[SkillDetail, float]] = []
    for skill in skills:
        score = 0.0

        # 1. Keyword overlap (Jaccard-like but we only care about overlap size
        #    relative to requirement length)
        sk_kw = _skill_keywords(skill)
        overlap = req_tokens & sk_kw
        if req_tokens:
            score += len(overlap) / max(len(req_tokens), 1) * 5.0

        # 2. Tag direct match bonus
        tag_set = {t.lower() for t in skill.tags}
        tag_overlap = req_tokens & tag_set
        score += len(tag_overlap) * 2.0

        # 3. Platform match
        skill_plats = {p.lower() for p in skill.platforms}
        if "all" in skill_plats:
            score += 1.0  # mild bonus for universal skills
        elif skill_plats & platform_set:
            score += 3.0

        # 4. Always-include skills get top priority
        if skill.id in always:
            score += 100.0

        scored.append((skill, score))

    scored.sort(key=lambda x: (-x[1], x[0].id))
    return scored


def select_within_budget(
    ranked: List[Tuple[SkillDetail, float]],
    token_budget: int = DEFAULT_SKILL_TOKEN_BUDGET,
    *,
    min_skills: int = 3,
    always_include: Optional[Set[str]] = None,
) -> List[SkillDetail]:
    """Greedily select top-ranked skills until the token budget is exhausted.

    Parameters
    ----------
    ranked : list
        Output of ``rank_skills()``.
    token_budget : int
        Max tokens for all skill bodies combined.
    min_skills : int
        Minimum skills to include regardless of budget (top N by score).
    always_include : set or None
        Skill IDs that must be included even if they bust the budget.

    Returns
    -------
    Selected skills in relevance order.
    """
    always = always_include or set()
    selected: List[SkillDetail] = []
    used_tokens = 0

    for skill, _score in ranked:
        body_tokens = estimate_tokens(skill.body)
        must = skill.id in always or len(selected) < min_skills
        if must or (used_tokens + body_tokens <= token_budget):
            selected.append(skill)
            used_tokens += body_tokens
        # If budget exhausted and not a must-include, skip.

    return selected
