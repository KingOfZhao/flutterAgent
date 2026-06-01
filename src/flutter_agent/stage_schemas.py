"""Expected JSON output schemas for each pipeline stage.

These are *validation* schemas — they do not affect the LLM prompt.
If the parsed JSON from a stage fails validation, we log a warning and
attach ``stage_valid=False`` to the StageResult. This lets callers
decide whether to trust the output or re-run.

Schemas are intentionally loose (``extra = "allow"``) because different
skills and requirements can produce varying extra fields. We only
enforce the minimal set of keys that downstream stages depend on.
"""
from __future__ import annotations

from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field


class _Permissive(BaseModel):
    """Base that allows extra keys silently."""

    model_config = {"extra": "allow"}


# ---- classify ---------------------------------------------------------------

class ClassifyOutput(_Permissive):
    """Classify stage should identify platforms and recommend skills."""
    recommended_skills: List[str] = Field(
        default_factory=list,
        description="Skill IDs the model recommends for this requirement.",
    )
    platforms: List[str] = Field(
        default_factory=list,
        description="Detected target platforms.",
    )
    complexity: Optional[str] = Field(
        default=None,
        description="Estimated project complexity (low/medium/high).",
    )


# ---- spec -------------------------------------------------------------------

class SpecOutput(_Permissive):
    """Spec stage should produce user stories and functional requirements."""
    user_stories: List[Any] = Field(
        default_factory=list,
        description="List of user stories.",
    )
    functional_requirements: List[Any] = Field(
        default_factory=list,
        description="List of functional requirements.",
    )


# ---- architecture -----------------------------------------------------------

class ThirdPartyEntry(_Permissive):
    package: str
    version: str = ""
    purpose: str = ""


class ArchitectureOutput(_Permissive):
    """Architecture stage should define layers, patterns, and dependencies."""
    layers: List[Any] = Field(
        default_factory=list,
        description="Architectural layers.",
    )
    third_party: List[Any] = Field(
        default_factory=list,
        description="Third-party packages to use.",
    )
    state_management: Optional[str] = None
    patterns: List[str] = Field(default_factory=list)


# ---- breakdown --------------------------------------------------------------

class BreakdownOutput(_Permissive):
    """Breakdown stage decomposes work into tasks/modules."""
    tasks: List[Any] = Field(
        default_factory=list,
        description="Development tasks or modules.",
    )


# ---- implementation ---------------------------------------------------------

class ImplementationFile(_Permissive):
    """A single file skeleton produced by the implementation stage."""
    path: str = Field(..., description="File path within architecture.directory_tree.")


class ImplementationOutput(_Permissive):
    """Implementation stage turns the breakdown into code skeletons.

    Only ``files`` is enforced (it is what makes this stage useful); the rest
    (data_models / widget_tree / test_stubs / wiring) are optional and loose.
    """
    files: List[ImplementationFile] = Field(
        default_factory=list,
        description="Per-file skeletons: path, signatures, TODO placeholders.",
    )


# ---- review -----------------------------------------------------------------

class ReviewFinding(_Permissive):
    """A single self-review finding against the implementation skeleton."""
    issue: str = Field(..., description="What is wrong (concrete, checkable).")


class ReviewOutput(_Permissive):
    """Review stage self-checks the implementation and reports findings.

    Only ``findings`` shape is enforced (each must carry an ``issue``); the
    rest (summary / checklist / blocking) are optional and loose.
    """
    findings: List[ReviewFinding] = Field(
        default_factory=list,
        description="Self-review findings, each with a fix suggestion.",
    )


# ---- acceptance -------------------------------------------------------------

class AcceptanceOutput(_Permissive):
    """Acceptance stage defines testable criteria."""
    criteria: List[Any] = Field(
        default_factory=list,
        description="Acceptance test criteria.",
    )


# ---------------------------------------------------------------------------
# Registry
# ---------------------------------------------------------------------------

STAGE_SCHEMAS: Dict[str, type] = {
    "classify": ClassifyOutput,
    "spec": SpecOutput,
    "architecture": ArchitectureOutput,
    "breakdown": BreakdownOutput,
    "implementation": ImplementationOutput,
    "review": ReviewOutput,
    "acceptance": AcceptanceOutput,
    # "markdown" has no JSON schema — it's prose.
}


def validate_stage_output(stage_name: str, data: Dict[str, Any]) -> Optional[str]:
    """Validate parsed JSON against the stage's expected schema.

    Returns None on success, or a human-readable error string on failure.
    """
    schema_cls = STAGE_SCHEMAS.get(stage_name)
    if schema_cls is None:
        return None  # no validation for this stage
    try:
        schema_cls.model_validate(data)
        return None
    except Exception as exc:
        return str(exc)
