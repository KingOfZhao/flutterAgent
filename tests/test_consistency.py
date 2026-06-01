"""Unit tests for the deterministic implementation consistency checker."""
from __future__ import annotations

from flutter_agent.consistency import check_implementation_consistency


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


def test_defensive_against_garbage_input():
    assert check_implementation_consistency(None, None, None) == []
    assert check_implementation_consistency("oops", [], 5) == []
    assert check_implementation_consistency({"files": "nope"}, {}, {}) == []
    # files entries that are not dicts are ignored
    assert check_implementation_consistency({"files": ["lib/a.dart"]}, {}, {}) == []
