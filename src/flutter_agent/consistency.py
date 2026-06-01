"""Deterministic structural self-check for the implementation skeleton.

The ``review`` stage already runs an LLM self-review. This module adds a
*mechanical* layer that does not depend on the model: it cross-checks the
implementation skeleton against the breakdown and architecture, and returns
findings shaped exactly like review findings (path/severity/category/issue/
suggestion) so they can be merged into the review output and participate in
the blocking decision.

Everything here is defensive against loose / missing fields — the upstream
JSON is model-generated and only loosely validated.
"""
from __future__ import annotations

from typing import Any, Dict, List


def _file_paths(implementation: Dict[str, Any]) -> List[str]:
    files = implementation.get("files")
    if not isinstance(files, list):
        return []
    out: List[str] = []
    for f in files:
        if isinstance(f, dict) and isinstance(f.get("path"), str) and f["path"].strip():
            out.append(f["path"].strip())
    return out


def _covered_paths(implementation: Dict[str, Any]) -> set[str]:
    stubs = implementation.get("test_stubs")
    covered: set[str] = set()
    if isinstance(stubs, list):
        for s in stubs:
            if isinstance(s, dict) and isinstance(s.get("covers"), str):
                covered.add(s["covers"].strip())
    return covered


def _collect_files_touched(node: Any, acc: set[str]) -> None:
    """Recursively gather every ``files_touched`` path anywhere in the breakdown
    tree (tasks may be nested under epics/stories)."""
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "files_touched" and isinstance(val, list):
                for p in val:
                    if isinstance(p, str) and p.strip():
                        acc.add(p.strip())
            else:
                _collect_files_touched(val, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_files_touched(item, acc)


def _collect_tree_paths(architecture: Dict[str, Any]) -> List[str]:
    """Pull comparable path strings out of architecture.directory_tree, which
    may be a list, a nested dict, or a single multiline string."""
    tree = architecture.get("directory_tree")
    out: List[str] = []

    def walk(node: Any) -> None:
        if isinstance(node, str):
            for line in node.splitlines():
                s = line.strip().strip("│├└─ ").strip()
                if s:
                    out.append(s)
        elif isinstance(node, list):
            for item in node:
                walk(item)
        elif isinstance(node, dict):
            for key, val in node.items():
                if isinstance(key, str) and key.strip():
                    out.append(key.strip())
                walk(val)

    walk(tree)
    return out


def _within_tree(path: str, tree_paths: List[str]) -> bool:
    """Lenient containment: a file is considered in-tree if its path or parent
    directory is referenced by any tree entry. Keeps false positives low when
    the tree format is unpredictable."""
    parent = path.rsplit("/", 1)[0] if "/" in path else path
    for t in tree_paths:
        if path in t or t in path:
            return True
        if parent and parent in t:
            return True
    return False


def check_implementation_consistency(
    implementation: Any,
    breakdown: Any,
    architecture: Any,
) -> List[Dict[str, str]]:
    """Return deterministic structural findings about the implementation
    skeleton. Empty list means no mechanical issues were found."""
    findings: List[Dict[str, str]] = []
    if not isinstance(implementation, dict):
        return findings

    file_paths = _file_paths(implementation)
    fileset = set(file_paths)

    # 1. Every lib/ source file should have a covering test stub.
    covered = _covered_paths(implementation)
    for p in file_paths:
        if p.startswith("lib/") and p not in covered:
            findings.append({
                "path": p,
                "severity": "major",
                "category": "testability",
                "issue": "该实现文件没有对应测试桩(test_stubs.covers 未覆盖)",
                "suggestion": "在 test_stubs 增加针对该文件的 unit/widget 测试桩",
                "source": "static",
            })

    # 2. Files the breakdown says it will touch must get a skeleton.
    touched: set[str] = set()
    if isinstance(breakdown, dict):
        _collect_files_touched(breakdown, touched)
    for p in sorted(touched):
        if p not in fileset:
            findings.append({
                "path": p,
                "severity": "major",
                "category": "architecture",
                "issue": "breakdown 声明要改动的文件未在 implementation.files 中产出骨架",
                "suggestion": "为该文件补一个 file 骨架,或在 assumptions 说明为何不需要",
                "source": "static",
            })

    # 3b. Duplicate file paths.
    seen: set[str] = set()
    for p in file_paths:
        if p in seen:
            findings.append({
                "path": p,
                "severity": "major",
                "category": "architecture",
                "issue": "同一文件路径在 implementation.files 中重复出现",
                "suggestion": "合并为单个 file 条目,避免下游写入冲突",
                "source": "static",
            })
        seen.add(p)

    # 3c. Test stub covering a file that has no skeleton.
    for p in sorted(covered):
        if p.startswith("lib/") and p not in fileset:
            findings.append({
                "path": p,
                "severity": "minor",
                "category": "testability",
                "issue": "test_stubs.covers 指向的源文件没有对应骨架",
                "suggestion": "补该文件的 file 骨架,或修正 covers 指向",
                "source": "static",
            })

    # 3d. Internal (lib/) dependency that points at a missing skeleton.
    files = implementation.get("files")
    if isinstance(files, list):
        for f in files:
            if not isinstance(f, dict):
                continue
            deps = f.get("depends_on")
            if not isinstance(deps, list):
                continue
            owner = f.get("path") if isinstance(f.get("path"), str) else "<general>"
            for dep in deps:
                if not isinstance(dep, str):
                    continue
                d = dep.strip()
                if d.startswith("lib/") and d not in fileset:
                    findings.append({
                        "path": owner,
                        "severity": "minor",
                        "category": "architecture",
                        "issue": f"depends_on 引用了不存在的内部文件: {d}",
                        "suggestion": "为被依赖文件补骨架,或修正依赖路径",
                        "source": "static",
                    })

    # 3. File paths should live inside architecture.directory_tree.
    if isinstance(architecture, dict):
        tree_paths = _collect_tree_paths(architecture)
        if tree_paths:
            for p in file_paths:
                if not _within_tree(p, tree_paths):
                    findings.append({
                        "path": p,
                        "severity": "minor",
                        "category": "architecture",
                        "issue": "文件路径不在 architecture.directory_tree 内",
                        "suggestion": "调整路径以符合既定目录树,或在架构中补登该目录",
                        "source": "static",
                    })

    return findings


def _collect_tasks(node: Any, acc: List[Dict[str, Any]]) -> None:
    """Gather every task dict found under any ``tasks`` list in the breakdown."""
    if isinstance(node, dict):
        for key, val in node.items():
            if key == "tasks" and isinstance(val, list):
                for t in val:
                    if isinstance(t, dict):
                        acc.append(t)
                        _collect_tasks(t, acc)
            else:
                _collect_tasks(val, acc)
    elif isinstance(node, list):
        for item in node:
            _collect_tasks(item, acc)


def _collect_strings(node: Any, acc: List[str]) -> None:
    if isinstance(node, str):
        if node.strip():
            acc.append(node.strip())
    elif isinstance(node, list):
        for item in node:
            _collect_strings(item, acc)
    elif isinstance(node, dict):
        for val in node.values():
            _collect_strings(val, acc)


def check_acceptance_consistency(
    acceptance: Any,
    breakdown: Any,
    implementation: Any,
) -> List[Dict[str, str]]:
    """Deterministic cross-check between acceptance, breakdown and the
    implementation test stubs. Returns gaps shaped like findings."""
    gaps: List[Dict[str, str]] = []
    if not isinstance(acceptance, dict):
        return gaps

    # A. Every breakdown task should declare at least one acceptance criterion.
    if isinstance(breakdown, dict):
        tasks: List[Dict[str, Any]] = []
        _collect_tasks(breakdown, tasks)
        for t in tasks:
            crit = t.get("acceptance")
            has_crit = isinstance(crit, list) and any(
                isinstance(c, str) and c.strip() for c in crit
            )
            if not has_crit:
                label = t.get("id") or t.get("title") or "<task>"
                gaps.append({
                    "path": str(label),
                    "severity": "minor",
                    "category": "acceptance",
                    "issue": "breakdown 任务缺少验收标准(acceptance)",
                    "suggestion": "为该任务补至少一条可验证的验收标准",
                    "source": "static",
                })

    # B. Each implementation test stub should be referenced by the test plan.
    if isinstance(implementation, dict):
        stub_paths: List[str] = []
        stubs = implementation.get("test_stubs")
        if isinstance(stubs, list):
            for s in stubs:
                if isinstance(s, dict) and isinstance(s.get("path"), str) and s["path"].strip():
                    stub_paths.append(s["path"].strip())
        plan_strings: List[str] = []
        _collect_strings(acceptance.get("test_plan"), plan_strings)
        if stub_paths and plan_strings:
            blob = "\n".join(plan_strings)
            for sp in stub_paths:
                if sp not in blob:
                    gaps.append({
                        "path": sp,
                        "severity": "minor",
                        "category": "testability",
                        "issue": "implementation 的测试桩未被 acceptance.test_plan 覆盖",
                        "suggestion": "在 test_plan 引用该测试文件,避免实现与验收脱节",
                        "source": "static",
                    })

    return gaps
