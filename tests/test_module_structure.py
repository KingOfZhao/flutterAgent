"""Guard the pipeline module split so it cannot silently re-bloat.

The closed-loop helpers live in ``review_loop`` and the markdown decorations
in ``reporting``. ``pipeline`` orchestrates and re-exports the helpers for
backward-compatible imports. These tests fail if the separation regresses.
"""
from pathlib import Path

import flutter_agent.pipeline as pipeline
import flutter_agent.reporting as reporting
import flutter_agent.review_loop as review_loop

_SRC = Path(__file__).resolve().parents[1] / "src" / "flutter_agent"


def _loc(name: str) -> int:
    return len((_SRC / name).read_text(encoding="utf-8").splitlines())


def test_closed_loop_helpers_live_in_review_loop():
    for fn in (
        "_blocking_severities",
        "_review_is_blocking",
        "_augment_review_with_consistency",
        "_summarize_review_pass",
        "_format_review_feedback",
    ):
        assert hasattr(review_loop, fn), f"{fn} should live in review_loop"


def test_markdown_decorations_live_in_reporting():
    assert hasattr(reporting, "append_audit_section")
    assert hasattr(reporting, "prepend_validation_warnings")


def test_pipeline_reexports_helpers_for_back_compat():
    # Existing call sites / tests import these straight from pipeline.
    assert pipeline._review_is_blocking is review_loop._review_is_blocking
    assert pipeline._format_review_feedback is review_loop._format_review_feedback
    # The class still exposes the static wrappers used by tests.
    assert pipeline.RefinementPipeline._append_audit_section("# x", [], []) == "# x"
    assert pipeline.RefinementPipeline._prepend_validation_warnings("# x", []) == "# x"


def test_pipeline_module_stays_lean():
    # Anti-bloat tripwire: the orchestrator must not absorb helper logic again.
    # Headroom above current size; tighten if it keeps shrinking.
    assert _loc("pipeline.py") < 820, "pipeline.py is bloating — extract helpers"
    assert _loc("review_loop.py") < 220
    assert _loc("reporting.py") < 160
