"""Unit tests for the deterministic implementation consistency checker."""
from __future__ import annotations

from flutter_agent.consistency import (
    check_acceptance_consistency,
    check_implementation_consistency,
)


def _impl(files, test_stubs=None):
    return {"files": files, "test_stubs": test_stubs or []}


def test_no_findings_when_everything_consistent():
    impl = _impl(
        files=[{"path": "lib/a.dart"}],
        test_stubs=[{"covers": "lib/a.dart", "kind": "unit"}],
    )
    breakdown = {"tasks": [{"id": "T-1", "files_touched": ["lib/a.dart"]}]}
    architecture = {"directory_tree": ["lib/a.dart"]}
    assert check_implementation_consistency(impl, breakdown, architecture) == []


def test_file_without_test_stub_is_major():
    impl = _impl(files=[{"path": "lib/a.dart"}], test_stubs=[])
    findings = check_implementation_consistency(impl, {}, {})
    assert len(findings) == 1
    assert findings[0]["severity"] == "major"
    assert findings[0]["category"] == "testability"
    assert findings[0]["path"] == "lib/a.dart"
    assert findings[0]["source"] == "static"


def test_non_lib_file_does_not_require_test():
    impl = _impl(files=[{"path": "bin/tool.dart"}], test_stubs=[])
    assert check_implementation_consistency(impl, {}, {}) == []


def test_breakdown_touched_file_missing_skeleton_is_major():
    impl = _impl(
        files=[{"path": "lib/a.dart"}],
        test_stubs=[{"covers": "lib/a.dart"}],
    )
    breakdown = {
        "epics": [
            {"stories": [{"tasks": [{"files_touched": ["lib/a.dart", "lib/b.dart"]}]}]}
        ]
    }
    findings = check_implementation_consistency(impl, breakdown, {})
    paths = {f["path"]: f for f in findings}
    assert "lib/b.dart" in paths
    assert paths["lib/b.dart"]["severity"] == "major"
    assert paths["lib/b.dart"]["category"] == "architecture"
    # lib/a.dart is implemented + covered -> not flagged
    assert "lib/a.dart" not in paths


def test_path_outside_directory_tree_is_minor():
    impl = _impl(
        files=[{"path": "lib/a.dart"}, {"path": "weird/elsewhere.dart"}],
        test_stubs=[{"covers": "lib/a.dart"}, {"covers": "weird/elsewhere.dart"}],
    )
    architecture = {"directory_tree": "lib/\n  a.dart\n"}
    findings = check_implementation_consistency(impl, {}, architecture)
    minor = [f for f in findings if f["severity"] == "minor"]
    assert any(f["path"] == "weird/elsewhere.dart" for f in minor)
    # lib/a.dart's parent 'lib' is referenced by the tree -> not flagged
    assert not any(f["path"] == "lib/a.dart" for f in minor)


def test_directory_tree_skipped_when_absent():
    impl = _impl(
        files=[{"path": "anywhere/x.dart"}],
        test_stubs=[{"covers": "anywhere/x.dart"}],
    )
    # no directory_tree -> no architecture findings at all
    findings = check_implementation_consistency(impl, {}, {})
    assert findings == []


def test_duplicate_file_paths_is_major():
    impl = _impl(
        files=[{"path": "lib/a.dart"}, {"path": "lib/a.dart"}],
        test_stubs=[{"covers": "lib/a.dart"}],
    )
    findings = check_implementation_consistency(impl, {}, {})
    dupes = [f for f in findings if "重复" in f["issue"]]
    assert len(dupes) == 1
    assert dupes[0]["severity"] == "major"


def test_test_stub_covering_missing_file_is_minor():
    impl = _impl(
        files=[{"path": "lib/a.dart"}],
        test_stubs=[{"covers": "lib/a.dart"}, {"covers": "lib/ghost.dart"}],
    )
    findings = check_implementation_consistency(impl, {}, {})
    ghosts = [f for f in findings if f["path"] == "lib/ghost.dart"]
    assert len(ghosts) == 1
    assert ghosts[0]["severity"] == "minor"
    assert ghosts[0]["category"] == "testability"


def test_dangling_internal_dependency_is_minor():
    impl = _impl(
        files=[
            {"path": "lib/a.dart", "depends_on": ["lib/missing.dart", "package:flutter/material.dart"]},
        ],
        test_stubs=[{"covers": "lib/a.dart"}],
    )
    findings = check_implementation_consistency(impl, {}, {})
    dangling = [f for f in findings if "depends_on" in f["issue"]]
    assert len(dangling) == 1
    assert dangling[0]["path"] == "lib/a.dart"
    assert dangling[0]["severity"] == "minor"
    # package: imports are never flagged
    assert all("package:" not in f["issue"] for f in findings)


def test_acceptance_task_without_criteria_is_flagged():
    acceptance = {"test_plan": []}
    breakdown = {
        "epics": [{"stories": [{"tasks": [
            {"id": "T-1", "acceptance": ["given/when/then"]},
            {"id": "T-2", "acceptance": []},
            {"id": "T-3"},
        ]}]}]
    }
    gaps = check_acceptance_consistency(acceptance, breakdown, {})
    labels = {g["path"] for g in gaps if g["category"] == "acceptance"}
    assert labels == {"T-2", "T-3"}


def test_acceptance_test_plan_must_reference_stubs():
    acceptance = {"test_plan": ["跑 test/a_test.dart 验证渲染"]}
    implementation = {
        "test_stubs": [
            {"path": "test/a_test.dart"},
            {"path": "test/b_test.dart"},
        ]
    }
    gaps = check_acceptance_consistency(acceptance, {}, implementation)
    uncovered = [g["path"] for g in gaps if g["category"] == "testability"]
    assert uncovered == ["test/b_test.dart"]


def test_acceptance_consistency_defensive():
    assert check_acceptance_consistency(None, {}, {}) == []
    assert check_acceptance_consistency("oops", {}, {}) == []


def test_defensive_against_garbage_input():
    assert check_implementation_consistency(None, None, None) == []
    assert check_implementation_consistency("oops", [], 5) == []
    assert check_implementation_consistency({"files": "nope"}, {}, {}) == []
    # files entries that are not dicts are ignored
    assert check_implementation_consistency({"files": ["lib/a.dart"]}, {}, {}) == []
