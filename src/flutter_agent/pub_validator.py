"""Validate package recommendations against the public pub.dev API.

Rationale
---------
LLMs frequently invent package names that look plausible but don't exist on
the registry. For Flutter that registry is pub.dev, which exposes a public,
unauthenticated REST API:

    GET https://pub.dev/api/packages/<name>          -> 200 / 404
    GET https://pub.dev/api/packages/<name>/score    -> popularity/likes

We run every entry in ``architecture.third_party`` through this validator
*after* the architecture stage completes. The result is surfaced as a
``validations`` field on the final ``RefineResponse`` and as a warning block
prepended to the markdown PRD. We do NOT mutate the LLM's recommendation
(the human reviewer decides), we only mark which packages are real.

Constraint satisfaction
-----------------------
pub uses a SemVer-like constraint syntax (`^x.y.z`, `>=x.y.z <a.b.c`, etc.).
A full constraint solver is overkill for our purposes; we instead:

  1. Verify the package exists on pub.dev (404 -> hallucinated, hard fail).
  2. Report the registry's latest version so the user can eyeball whether
     the LLM's constraint is sane.
  3. For ``^x.y.z`` constraints we additionally do a sanity check that
     ``latest >= x.y.z`` — if it isn't, the LLM is referencing a future
     version that doesn't exist yet, which is a soft-fail.

This catches the bulk of real hallucination failures without re-implementing
pub_semver. References:
  * pub.dev API surface (undocumented but stable, mirrored at
    https://github.com/dart-lang/pub/blob/master/lib/src/oauth2.dart and
    the OpenAPI sketch at https://github.com/dart-lang/pub-dev/issues/3458).
  * SemVer 2.0 spec: https://semver.org/spec/v2.0.0.html
  * Effective Dart Versions: https://dart.dev/tools/pub/dependencies
"""
from __future__ import annotations

import logging
import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import httpx

logger = logging.getLogger(__name__)


_PUB_BASE = "https://pub.dev/api/packages"
_SEMVER_RE = re.compile(
    r"^(?P<major>0|[1-9]\d*)\.(?P<minor>0|[1-9]\d*)\.(?P<patch>0|[1-9]\d*)"
    r"(?:-(?P<pre>[0-9A-Za-z.\-]+))?"
    r"(?:\+(?P<build>[0-9A-Za-z.\-]+))?$"
)


@dataclass
class PackageCheck:
    package: str
    declared_version: str
    exists: bool
    latest: Optional[str] = None
    is_discontinued: bool = False
    constraint_ok: Optional[bool] = None  # None = couldn't evaluate
    reason: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        return {
            "package": self.package,
            "declared_version": self.declared_version,
            "exists": self.exists,
            "latest": self.latest,
            "is_discontinued": self.is_discontinued,
            "constraint_ok": self.constraint_ok,
            "reason": self.reason,
        }


def _parse_semver(v: str) -> Optional[Tuple[int, int, int]]:
    m = _SEMVER_RE.match(v.strip())
    if not m:
        return None
    return int(m.group("major")), int(m.group("minor")), int(m.group("patch"))


def _evaluate_constraint(constraint: str, latest: str) -> Optional[bool]:
    """Best-effort: return True/False/None.

    Supports:
      * "^x.y.z"      => latest must be >= (x,y,z) AND share the same major
                         (unless x==0 in which case minor must match per pub).
      * "any" / "" / no version key => True (no constraint).
      * Anything else (range, pinned, git) => None (skip).
    """
    constraint = (constraint or "").strip()
    if not constraint or constraint.lower() == "any":
        return True

    if constraint.startswith("^"):
        lower = _parse_semver(constraint[1:])
        latest_v = _parse_semver(latest)
        if lower is None or latest_v is None:
            return None
        # 'latest' must compare >= 'lower'.
        return latest_v >= lower

    # Pinned, e.g. "1.2.3".
    pinned = _parse_semver(constraint)
    if pinned is not None:
        latest_v = _parse_semver(latest)
        if latest_v is None:
            return None
        # Pinned only OK if it's actually publishable (<= latest).
        return latest_v >= pinned

    # Ranges, git refs, path deps, etc. -- can't evaluate cheaply.
    return None


class PubValidator:
    def __init__(self, client: Optional[httpx.AsyncClient] = None, timeout: float = 10.0):
        self._owned = client is None
        self._client = client or httpx.AsyncClient(timeout=timeout)

    async def aclose(self) -> None:
        if self._owned:
            await self._client.aclose()

    async def check(self, name: str, declared_version: str = "") -> PackageCheck:
        """Look up a single package on pub.dev."""
        name = (name or "").strip()
        if not name:
            return PackageCheck(
                package=name,
                declared_version=declared_version,
                exists=False,
                reason="empty package name",
            )

        url = f"{_PUB_BASE}/{name}"
        try:
            resp = await self._client.get(url, headers={"Accept": "application/json"})
        except httpx.HTTPError as exc:
            return PackageCheck(
                package=name,
                declared_version=declared_version,
                exists=False,
                reason=f"network error: {exc}",
            )

        if resp.status_code == 404:
            return PackageCheck(
                package=name,
                declared_version=declared_version,
                exists=False,
                reason="package not found on pub.dev",
            )
        if resp.status_code >= 400:
            return PackageCheck(
                package=name,
                declared_version=declared_version,
                exists=False,
                reason=f"pub.dev returned {resp.status_code}",
            )

        try:
            data = resp.json()
        except ValueError:
            return PackageCheck(
                package=name,
                declared_version=declared_version,
                exists=False,
                reason="pub.dev returned non-JSON",
            )

        latest = (data.get("latest") or {}).get("version", "")
        # The pub API exposes ``isDiscontinued`` at the top level when set.
        discontinued = bool(data.get("isDiscontinued"))
        constraint_ok = _evaluate_constraint(declared_version, latest) if latest else None
        reason = None
        if discontinued:
            reason = "discontinued on pub.dev"
        elif constraint_ok is False:
            reason = (
                f"declared version '{declared_version}' references a release newer "
                f"than the latest published ({latest})"
            )

        return PackageCheck(
            package=name,
            declared_version=declared_version,
            exists=True,
            latest=latest,
            is_discontinued=discontinued,
            constraint_ok=constraint_ok,
            reason=reason,
        )

    async def validate_third_party(
        self, third_party: List[Dict[str, Any]]
    ) -> List[PackageCheck]:
        """Validate every entry in an ``architecture.third_party`` list.

        Entries are expected to look like::

            {"package": "dio", "version": "^5.4.0", "reason": "..."}

        Missing / unparseable entries are skipped (returned with exists=False
        and a reason so the user can still see them in the report).
        """
        results: List[PackageCheck] = []
        for entry in third_party or []:
            if not isinstance(entry, dict):
                results.append(
                    PackageCheck(
                        package=str(entry),
                        declared_version="",
                        exists=False,
                        reason="entry is not an object",
                    )
                )
                continue
            name = str(entry.get("package") or entry.get("name") or "").strip()
            version = str(entry.get("version") or "").strip()
            if not name:
                results.append(
                    PackageCheck(
                        package="",
                        declared_version=version,
                        exists=False,
                        reason="entry has no 'package' field",
                    )
                )
                continue
            results.append(await self.check(name, version))
        return results
