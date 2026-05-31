"""Pydantic models exposed by the public HTTP API."""
from __future__ import annotations

from enum import Enum
from typing import Any, Dict, List, Literal, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Skill metadata
# ---------------------------------------------------------------------------


class SkillMeta(BaseModel):
    """The YAML front-matter at the top of every SKILL.md."""

    id: str = Field(..., description="Unique skill id, matches directory name.")
    name: str
    version: str = "1.0.0"
    platforms: List[str] = Field(default_factory=list)
    tags: List[str] = Field(default_factory=list)
    applies_when: Optional[str] = None
    stage_hints: List[str] = Field(default_factory=list)


class SkillSummary(SkillMeta):
    """Skill metadata + path on disk; body is omitted to keep listings light."""

    path: str


class SkillDetail(SkillSummary):
    body: str = Field(..., description="Markdown body (everything after front-matter).")


# ---------------------------------------------------------------------------
# Refinement pipeline
# ---------------------------------------------------------------------------


class Platform(str, Enum):
    mobile = "mobile"
    desktop = "desktop"
    web = "web"
    auto = "auto"


class Stage(str, Enum):
    classify = "classify"
    spec = "spec"
    architecture = "architecture"
    breakdown = "breakdown"
    acceptance = "acceptance"
    markdown = "markdown"


class RefineRequest(BaseModel):
    """User-facing request for the /v1/refine endpoint."""

    requirement: str = Field(
        ...,
        min_length=2,
        description="The raw user requirement (one liner or paragraph).",
    )
    platforms: List[Platform] = Field(
        default_factory=lambda: [Platform.auto],
        description="Target platforms. Use ['auto'] to let the model decide.",
    )
    skills: Optional[List[str]] = Field(
        default=None,
        description=(
            "Override skill selection. If null, the classify stage decides. "
            "Pass skill ids, e.g. ['flutter-mobile','task-refinement']."
        ),
    )
    stages: List[Stage] = Field(
        default_factory=lambda: [
            Stage.classify,
            Stage.spec,
            Stage.architecture,
            Stage.breakdown,
            Stage.acceptance,
            Stage.markdown,
        ],
        description="Which pipeline stages to run, in order.",
    )
    temperature: Optional[float] = Field(
        default=None, ge=0.0, le=2.0, description="Override sampling temperature."
    )
    max_tokens: Optional[int] = Field(
        default=None, gt=0, le=32000, description="Override per-call max tokens."
    )
    extra_context: Optional[str] = Field(
        default=None,
        description="Free-form extra context to append after the user requirement.",
    )
    use_cache: bool = Field(
        default=False,
        description=(
            "If true, reuse the most recent run with an identical input "
            "(requirement+skills+stages+temperature+max_tokens+model). "
            "Cache hits are returned with cached=true and skip the upstream call."
        ),
    )
    validate_packages: bool = Field(
        default=True,
        description=(
            "If true, every entry in architecture.third_party is checked "
            "against pub.dev to catch hallucinated package names."
        ),
    )


class TokenUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0

    def add(self, other: "TokenUsage") -> None:
        self.prompt_tokens += other.prompt_tokens
        self.completion_tokens += other.completion_tokens
        self.total_tokens += other.total_tokens


class CostBreakdown(BaseModel):
    """USD cost estimate (worst-case, no cache-hit discount).

    Sourced from `flutter_agent.pricing.MODEL_PRICING`; override via the
    ``PRICING_CONFIG`` env var.
    """

    model: str
    pricing_source: str = Field(
        ..., description="Which key in the pricing table matched ('*' = fallback)."
    )
    input_cost_usd: float = 0.0
    output_cost_usd: float = 0.0
    total_cost_usd: float = 0.0


class PackageValidation(BaseModel):
    """Result of looking up a recommended package on pub.dev."""

    package: str
    declared_version: str = ""
    exists: bool
    latest: Optional[str] = None
    is_discontinued: bool = False
    constraint_ok: Optional[bool] = Field(
        default=None,
        description="True/False if the constraint could be checked; null when unparseable.",
    )
    reason: Optional[str] = None


class StageResult(BaseModel):
    stage: Stage
    model: str
    elapsed_ms: int
    attempts: int = Field(
        default=1,
        description="How many upstream calls this stage took (>1 means JSON repair was triggered).",
    )
    repaired: bool = Field(
        default=False,
        description="True if the stage's JSON was rescued by a repair retry.",
    )
    stage_valid: bool = Field(
        default=True,
        description="Whether the parsed JSON conforms to the expected stage schema.",
    )
    validation_error: Optional[str] = Field(
        default=None,
        description="Human-readable schema validation error, null when valid.",
    )
    usage: TokenUsage = Field(default_factory=TokenUsage)
    cost: Optional[CostBreakdown] = Field(
        default=None, description="USD cost estimate for this stage."
    )
    raw_output: str = Field(..., description="Raw model text for this stage.")
    parsed: Optional[Dict[str, Any]] = Field(
        default=None,
        description="Best-effort JSON parse of raw_output. Null if not JSON.",
    )


class RefineResponse(BaseModel):
    id: str = Field(..., description="Unique run id, also written to logs/runs.jsonl.")
    created_at: int = Field(..., description="Epoch seconds when the run finished.")
    cache_key: str = Field(
        default="",
        description="SHA-256 of the deterministic inputs; key used by the run cache.",
    )
    cached: bool = Field(
        default=False,
        description="True if this response was served from the run cache.",
    )
    requirement: str
    selected_skills: List[str]
    usage: TokenUsage = Field(
        default_factory=TokenUsage,
        description="Aggregated upstream token usage across all stages.",
    )
    cost: Optional[CostBreakdown] = Field(
        default=None, description="Aggregated USD cost estimate across all stages."
    )
    stages: List[StageResult]
    classify: Optional[Dict[str, Any]] = None
    spec: Optional[Dict[str, Any]] = None
    architecture: Optional[Dict[str, Any]] = None
    breakdown: Optional[Dict[str, Any]] = None
    acceptance: Optional[Dict[str, Any]] = None
    markdown: Optional[str] = Field(
        default=None, description="Final human-readable PRD in Markdown."
    )
    validations: List[PackageValidation] = Field(
        default_factory=list,
        description="pub.dev validation results for architecture.third_party packages.",
    )


class RunSummary(BaseModel):
    """Compact view of a past refinement run, returned by GET /v1/runs."""

    id: str
    created_at: int
    cached: bool = False
    cache_key: str = ""
    requirement: str
    selected_skills: List[str]
    usage: TokenUsage
    cost: Optional[CostBreakdown] = None
    elapsed_ms_total: int
    stages: List[str]
    bad_packages: int = Field(
        default=0,
        description="How many recommended packages failed pub.dev validation.",
    )


# ---------------------------------------------------------------------------
# OpenAI-compatible chat completions
# ---------------------------------------------------------------------------


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str


class ChatCompletionRequest(BaseModel):
    model: str = Field(
        default="flutter-agent",
        description="Model alias. 'flutter-agent' runs the refinement pipeline.",
    )
    messages: List[ChatMessage]
    temperature: Optional[float] = None
    max_tokens: Optional[int] = None
    stream: bool = False  # accepted for SDK compatibility; we always reply non-stream


class ChatCompletionChoice(BaseModel):
    index: int = 0
    message: ChatMessage
    finish_reason: str = "stop"


class ChatCompletionUsage(BaseModel):
    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


class ChatCompletionResponse(BaseModel):
    id: str
    object: Literal["chat.completion"] = "chat.completion"
    created: int
    model: str
    choices: List[ChatCompletionChoice]
    usage: ChatCompletionUsage = Field(default_factory=ChatCompletionUsage)


# ---------------------------------------------------------------------------
# Health & errors
# ---------------------------------------------------------------------------


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    version: str
    skills_loaded: int
    upstream_base_url: str
    upstream_model: str


class MetricsResponse(BaseModel):
    """Aggregate statistics from run history."""

    total_runs: int = Field(0, description="Total refinement runs recorded.")
    cached_runs: int = Field(0, description="Runs served from cache.")
    total_tokens: int = Field(0, description="Cumulative tokens consumed.")
    total_cost_usd: float = Field(0.0, description="Cumulative estimated cost in USD.")
    avg_elapsed_ms: float = Field(0.0, description="Average wall-clock time per run (ms).")
    bad_packages_total: int = Field(0, description="Total packages that failed pub.dev validation.")
    skills_loaded: int = Field(0, description="Number of skills currently loaded.")
    top_skills: List[str] = Field(
        default_factory=list,
        description="Most frequently selected skill ids (top 10).",
    )
    stage_success_rate: Dict[str, float] = Field(
        default_factory=dict,
        description="Fraction of stages where stage_valid=True, keyed by stage name.",
    )


class ErrorResponse(BaseModel):
    error: str
    detail: Optional[str] = None
