"""Discover and parse ``SKILL.md`` files from the skills directory.

A skill file looks like::

    ---
    id: flutter-mobile
    name: ...
    platforms: [mobile]
    ---
    # body markdown ...

We support both ``SKILL.md`` inside a directory and a top-level ``*.md`` file.
"""
from __future__ import annotations

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional

import yaml

from .schemas import SkillDetail, SkillMeta, SkillSummary

logger = logging.getLogger(__name__)

_FRONT_MATTER_RE = re.compile(
    r"\A---\s*\n(?P<yaml>.*?)\n---\s*\n(?P<body>.*)\Z",
    re.DOTALL,
)


class SkillLoadError(RuntimeError):
    pass


class SkillRegistry:
    """In-memory registry, refreshable at runtime."""

    def __init__(self, root: Path):
        self.root = root
        self._skills: Dict[str, SkillDetail] = {}

    # ------------------------------------------------------------------ API

    def reload(self) -> int:
        self._skills.clear()
        if not self.root.exists():
            logger.warning("skills dir %s does not exist", self.root)
            return 0

        for md_path in sorted(self.root.rglob("*.md")):
            # accept either <skill_id>/SKILL.md or <skill_id>.md
            if md_path.name.lower() not in ("skill.md",) and md_path.parent == self.root:
                # top-level markdown — also OK
                pass
            try:
                skill = self._parse(md_path)
            except SkillLoadError as exc:
                logger.error("failed to load %s: %s", md_path, exc)
                continue
            if skill.id in self._skills:
                logger.warning(
                    "duplicate skill id '%s' (was %s, now %s); keeping first",
                    skill.id,
                    self._skills[skill.id].path,
                    skill.path,
                )
                continue
            self._skills[skill.id] = skill
        logger.info("loaded %d skill(s) from %s", len(self._skills), self.root)
        return len(self._skills)

    def list(self) -> List[SkillSummary]:
        return [
            SkillSummary(**s.model_dump(exclude={"body"})) for s in self._skills.values()
        ]

    def get(self, skill_id: str) -> Optional[SkillDetail]:
        return self._skills.get(skill_id)

    def get_many(self, ids: List[str]) -> List[SkillDetail]:
        out: List[SkillDetail] = []
        for sid in ids:
            s = self.get(sid)
            if s is None:
                logger.warning("requested unknown skill id: %s", sid)
                continue
            out.append(s)
        return out

    def filter_by_platforms(self, platforms: List[str]) -> List[SkillDetail]:
        """Return skills whose ``platforms`` overlap with the requested set.

        Skills whose ``platforms`` includes ``all`` are always returned.
        """
        wanted = {p.lower() for p in platforms}
        out: List[SkillDetail] = []
        for s in self._skills.values():
            sp = {p.lower() for p in s.platforms}
            if "all" in sp or sp & wanted:
                out.append(s)
        return out

    def __len__(self) -> int:
        return len(self._skills)

    # -------------------------------------------------------------- internals

    def _parse(self, path: Path) -> SkillDetail:
        text = path.read_text(encoding="utf-8")
        m = _FRONT_MATTER_RE.match(text)
        if not m:
            raise SkillLoadError(
                f"missing YAML front-matter in {path} (expected '---' block at top)"
            )
        try:
            data = yaml.safe_load(m.group("yaml")) or {}
        except yaml.YAMLError as exc:
            raise SkillLoadError(f"invalid YAML in {path}: {exc}") from exc

        if not isinstance(data, dict):
            raise SkillLoadError(f"front-matter in {path} must be a mapping")

        # default id from parent dir if not provided
        data.setdefault("id", path.parent.name if path.name.lower() == "skill.md" else path.stem)
        try:
            meta = SkillMeta(**data)
        except Exception as exc:  # pragma: no cover - validated by pydantic
            raise SkillLoadError(f"invalid metadata in {path}: {exc}") from exc

        body = m.group("body").strip()
        return SkillDetail(**meta.model_dump(), path=str(path), body=body)
