"""Pub validator never hits the network in tests; we mock httpx."""
from __future__ import annotations

import asyncio
import sys
from pathlib import Path
from typing import Any, Dict, List

import httpx
import pytest

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from flutter_agent.pub_validator import (  # noqa: E402
    PackageCheck,
    PubValidator,
    _evaluate_constraint,
    _parse_semver,
)


def _make_client(routes: Dict[str, httpx.Response]) -> httpx.AsyncClient:
    """Tiny in-memory pub.dev: maps URL path -> Response."""

    def handler(request: httpx.Request) -> httpx.Response:
        path = request.url.path
        if path in routes:
            return routes[path]
        return httpx.Response(404, json={"error": "not found"})

    return httpx.AsyncClient(transport=httpx.MockTransport(handler))


@pytest.mark.parametrize(
    "v,expected",
    [
        ("1.2.3", (1, 2, 3)),
        ("0.0.1", (0, 0, 1)),
        ("1.2.3-pre.1", (1, 2, 3)),
        ("not-a-version", None),
        ("1.2", None),
    ],
)
def test_parse_semver(v, expected) -> None:
    assert _parse_semver(v) == expected


@pytest.mark.parametrize(
    "constraint,latest,expected",
    [
        ("^5.0.0", "5.4.1", True),
        ("^5.0.0", "4.9.9", False),
        ("^99.0.0", "5.4.1", False),  # constraint references future major
        ("any", "5.4.1", True),
        ("", "5.4.1", True),
        ("1.2.3", "1.5.0", True),  # pinned within published range
        ("9.9.9", "1.0.0", False),  # pinned beyond published
        (">=1.0.0 <2.0.0", "5.4.1", None),  # range -> not evaluated
        ("git://...", "5.4.1", None),
    ],
)
def test_evaluate_constraint(constraint, latest, expected) -> None:
    assert _evaluate_constraint(constraint, latest) is expected


def test_check_known_package_returns_exists() -> None:
    routes = {
        "/api/packages/dio": httpx.Response(
            200,
            json={
                "name": "dio",
                "latest": {"version": "5.4.0"},
                "isDiscontinued": False,
            },
        )
    }
    client = _make_client(routes)
    validator = PubValidator(client=client)

    async def go() -> PackageCheck:
        return await validator.check("dio", "^5.0.0")

    result = asyncio.run(go())
    assert result.exists
    assert result.latest == "5.4.0"
    assert result.is_discontinued is False
    assert result.constraint_ok is True
    assert result.reason is None


def test_check_unknown_package_marks_hallucinated() -> None:
    routes: Dict[str, httpx.Response] = {}  # everything 404s
    validator = PubValidator(client=_make_client(routes))

    async def go() -> PackageCheck:
        return await validator.check("super_fake_package_xyz", "^1.0.0")

    result = asyncio.run(go())
    assert result.exists is False
    assert "not found" in (result.reason or "")


def test_check_discontinued_flagged() -> None:
    routes = {
        "/api/packages/old_pkg": httpx.Response(
            200,
            json={
                "name": "old_pkg",
                "latest": {"version": "0.9.0"},
                "isDiscontinued": True,
            },
        )
    }
    validator = PubValidator(client=_make_client(routes))
    result = asyncio.run(validator.check("old_pkg", "^0.9.0"))
    assert result.exists is True
    assert result.is_discontinued is True
    assert result.reason == "discontinued on pub.dev"


def test_check_constraint_in_future_flagged() -> None:
    routes = {
        "/api/packages/dio": httpx.Response(
            200,
            json={"name": "dio", "latest": {"version": "5.4.0"}},
        )
    }
    validator = PubValidator(client=_make_client(routes))
    result = asyncio.run(validator.check("dio", "^9.0.0"))
    assert result.exists is True
    assert result.constraint_ok is False
    assert "newer than" in (result.reason or "")


def test_validate_third_party_handles_mixed_input() -> None:
    routes = {
        "/api/packages/dio": httpx.Response(
            200, json={"name": "dio", "latest": {"version": "5.4.0"}}
        ),
        "/api/packages/riverpod": httpx.Response(
            200, json={"name": "riverpod", "latest": {"version": "2.5.1"}}
        ),
    }
    validator = PubValidator(client=_make_client(routes))
    third_party: List[Dict[str, Any]] = [
        {"package": "dio", "version": "^5.0.0", "reason": "http"},
        {"package": "riverpod", "version": "^2.0.0", "reason": "state"},
        {"package": "made_up_pkg", "version": "^1.0.0", "reason": "??"},
        {"name": "no_version_field"},  # name instead of package
        "string entry",  # not a dict
        {"version": "^1.0.0"},  # missing name
    ]
    results = asyncio.run(validator.validate_third_party(third_party))
    assert len(results) == 6
    assert results[0].exists and results[0].constraint_ok
    assert results[1].exists and results[1].constraint_ok
    assert not results[2].exists  # made_up_pkg
    assert not results[3].exists  # no_version_field 404s in our mock
    assert not results[4].exists and "not an object" in (results[4].reason or "")
    assert not results[5].exists and "no 'package' field" in (results[5].reason or "")
