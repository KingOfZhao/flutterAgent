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

# Weight applied to semantic (vector cosine) scores when blended into ranking.
# Cosine scores from the hashing embedder typically land in 0.1–0.45 for real
# matches, so this scales them to be comparable with 1–2 specific bigram hits.
SEMANTIC_WEIGHT = 8.0

# Tokenizer: split on whitespace, punctuation, CJK boundaries.
_WORD_RE = re.compile(r"[\u4e00-\u9fff]|[a-zA-Z0-9_]+", re.UNICODE)


def _tokenize(text: str) -> Set[str]:
    """Extract a bag of lowercase unigram tokens from text.

    CJK characters become single-char tokens; latin runs stay whole words.
    """
    return {m.group(0).lower() for m in _WORD_RE.finditer(text or "")}


def _bigram_tokens(text: str) -> Set[str]:
    """Tokens biased toward specificity to cut single-CJK-char noise.

    - latin/number words are kept whole (e.g. ``go_router``)
    - each maximal run of CJK chars yields adjacent **bigrams**
      (e.g. ``协议选型`` -> ``协议`` ``议选`` ``选型``), and the single char
      when the run has length 1.

    Bigrams make multi-char terms (``协议`` / ``性能`` / ``打包``) match each
    other specifically, so unrelated skills no longer collide just because
    they share one common character.
    """
    tokens: Set[str] = set()
    # CJK runs and latin words, in order.
    for m in re.finditer(r"[\u4e00-\u9fff]+|[a-zA-Z0-9_]+", text or ""):
        chunk = m.group(0)
        if chunk[0].isascii():
            tokens.add(chunk.lower())
            continue
        if len(chunk) == 1:
            tokens.add(chunk)
        else:
            for i in range(len(chunk) - 1):
                tokens.add(chunk[i : i + 2])
    return tokens


def _skill_keywords(skill: SkillDetail) -> Set[str]:
    """Unigram keyword set: tags + applies_when + name + short body snippet."""
    parts: List[str] = []
    parts.extend(skill.tags)
    if skill.applies_when:
        parts.append(skill.applies_when)
    parts.append(skill.name)
    # Short body snippet for recall; kept small to limit incidental noise.
    parts.append(skill.body[:200])
    return _tokenize(" ".join(parts))


def _skill_specific_tokens(skill: SkillDetail) -> Set[str]:
    """Bigram/word tokens from the *curated* metadata only (no body).

    Excludes the body so that prose intros do not generate spurious matches;
    only intentional tags / applies_when / name drive specific scoring.
    """
    parts: List[str] = list(skill.tags)
    if skill.applies_when:
        parts.append(skill.applies_when)
    parts.append(skill.name)
    return _bigram_tokens(" ".join(parts))


def estimate_tokens(text: str) -> int:
    """Rough token count (no tiktoken dependency)."""
    return max(1, int(len(text) / _CHARS_PER_TOKEN))


def rank_skills(
    requirement: str,
    skills: List[SkillDetail],
    platforms: List[str],
    *,
    always_include: Optional[List[str]] = None,
    semantic_scores: Optional[Dict[str, float]] = None,
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
    semantic_scores : dict or None
        Optional ``skill_id -> cosine score`` from the local vector store
        (see ``vector_store.semantic_skill_scores``). Blended additively so
        keyword ranking still works when the vector index is unavailable.

    Returns
    -------
    list of (SkillDetail, score) sorted descending.
    """
    always = set(always_include or [])
    semantic = semantic_scores or {}
    req_tokens = _tokenize(requirement)
    req_specific = _bigram_tokens(requirement)
    platform_set = {p.lower() for p in platforms}

    scored: List[Tuple[SkillDetail, float]] = []
    for skill in skills:
        score = 0.0

        # 1. Unigram keyword overlap (recall). Weight reduced vs. earlier so a
        #    single shared CJK character contributes less incidental noise.
        sk_kw = _skill_keywords(skill)
        overlap = req_tokens & sk_kw
        if req_tokens:
            score += len(overlap) / max(len(req_tokens), 1) * 2.5

        # 2. Specific (bigram / whole-word) overlap against curated metadata.
        #    Multi-char terms like 协议 / 性能 / 打包 must match as a unit, so
        #    unrelated skills no longer collide on a shared single character.
        sk_specific = _skill_specific_tokens(skill)
        specific_overlap = req_specific & sk_specific
        score += len(specific_overlap) * 3.0

        # 3. Tag direct match bonus
        tag_set = {t.lower() for t in skill.tags}
        tag_overlap = req_tokens & tag_set
        score += len(tag_overlap) * 2.0

        # 4. Platform match
        skill_plats = {p.lower() for p in skill.platforms}
        if "all" in skill_plats:
            score += 1.0  # mild bonus for universal skills
        elif skill_plats & platform_set:
            score += 3.0

        # 5. Semantic similarity from the vector store (synonym/paraphrase
        #    recall that keyword overlap misses).
        score += semantic.get(skill.id, 0.0) * SEMANTIC_WEIGHT

        # 6. Always-include skills get top priority
        if skill.id in always:
            score += 100.0

        scored.append((skill, score))

    scored.sort(key=lambda x: (-x[1], x[0].id))
    return scored


def build_families(skills: List[SkillDetail]) -> Dict[str, str]:
    """Group skills into families via ``extends`` edges (union-find).

    Returns a map ``skill_id -> family_root``. A skill and every id it
    ``extends`` (and transitively) share one root. Skills with no ``extends``
    edge to/from anything form their own singleton family.
    """
    parent: Dict[str, str] = {}

    def find(x: str) -> str:
        parent.setdefault(x, x)
        root = x
        while parent[root] != root:
            root = parent[root]
        # path compression
        while parent[x] != root:
            parent[x], x = root, parent[x]
        return root

    def union(a: str, b: str) -> None:
        ra, rb = find(a), find(b)
        if ra != rb:
            # deterministic root: smaller id wins
            lo, hi = sorted((ra, rb))
            parent[hi] = lo

    ids = {s.id for s in skills}
    for s in skills:
        find(s.id)
        for target in s.extends:
            if target in ids:
                union(s.id, target)
    return {sid: find(sid) for sid in parent}


def select_within_budget(
    ranked: List[Tuple[SkillDetail, float]],
    token_budget: int = DEFAULT_SKILL_TOKEN_BUDGET,
    *,
    min_skills: int = 3,
    always_include: Optional[Set[str]] = None,
    families: Optional[Dict[str, str]] = None,
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
    families : dict or None
        Optional ``skill_id -> family_root`` map (see ``build_families``).
        When provided, only the **top-ranked** member of each family is
        selected; lower-ranked members of an already-covered family are
        skipped so a broad parent and its narrow child do not both consume
        budget. ``always_include`` and ``min_skills`` members bypass de-dup.

    Returns
    -------
    Selected skills in relevance order.
    """
    always = always_include or set()
    fam = families or {}
    selected: List[SkillDetail] = []
    used_tokens = 0
    covered_families: Set[str] = set()

    for skill, _score in ranked:
        body_tokens = estimate_tokens(skill.body)
        is_always = skill.id in always
        family = fam.get(skill.id)

        # Family de-dup runs before the min_skills floor: only explicit
        # always-include skills may bring in a second member of a family.
        # This stops a parent+child pair from both filling the top-N seats.
        if not is_always and family is not None and family in covered_families:
            continue

        must = is_always or len(selected) < min_skills
        if must or (used_tokens + body_tokens <= token_budget):
            selected.append(skill)
            used_tokens += body_tokens
            if family is not None:
                covered_families.add(family)
        # If budget exhausted and not a must-include, skip.

    return selected
