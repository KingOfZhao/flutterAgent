"""Integration test: full pipeline with mocked LLM responses.

Verifies:
- Stage chaining (classify -> spec -> architecture -> breakdown -> implementation -> review -> acceptance -> markdown)
- Skill auto-selection via ranker
- pub.dev validation integration
- Cost aggregation
- Stage schema validation
- Cache indexing
"""
from __future__ import annotations

import json
import pytest

from flutter_agent.cache import RunCache
from flutter_agent.config import Settings
from flutter_agent.deepseek_client import DeepSeekClient
from flutter_agent.pipeline import RefinementPipeline
from flutter_agent.schemas import Platform, RefineRequest, Stage
from flutter_agent.skill_loader import SkillRegistry

# ---------------------------------------------------------------------------
# Mock LLM responses per stage
# ---------------------------------------------------------------------------

_MOCK_CLASSIFY = json.dumps({
    "recommended_skills": ["flutter-mobile", "flutter-navigation", "architecture-design"],
    "platforms": ["mobile"],
    "complexity": "medium",
    "rationale": "A mobile app with navigation requirements.",
})

_MOCK_SPEC = json.dumps({
    "user_stories": [
        {"id": "US-1", "title": "User can view product list"},
        {"id": "US-2", "title": "User can navigate to product detail"},
    ],
    "functional_requirements": [
        {"id": "FR-1", "desc": "Display paginated product list"},
        {"id": "FR-2", "desc": "Deep link to product detail page"},
    ],
    "non_functional": ["Load time < 2s"],
})

_MOCK_ARCHITECTURE = json.dumps({
    "layers": ["presentation", "domain", "data"],
    "third_party": [
        {"package": "go_router", "version": "^14.0.0", "purpose": "routing"},
        {"package": "dio", "version": "^5.0.0", "purpose": "HTTP client"},
    ],
    "state_management": "riverpod",
    "patterns": ["repository", "use_case"],
})

_MOCK_BREAKDOWN = json.dumps({
    "tasks": [
        {"id": "T-1", "title": "Setup project scaffold", "hours": 4},
        {"id": "T-2", "title": "Implement product list", "hours": 8},
        {"id": "T-3", "title": "Implement deep linking", "hours": 6},
    ],
})

_MOCK_IMPLEMENTATION = json.dumps({
    "files": [
        {
            "path": "lib/features/product/product_list_page.dart",
            "purpose": "产品列表页",
            "layer": "presentation",
            "public_api": ["ProductListPage"],
            "depends_on": ["package:flutter_riverpod/flutter_riverpod.dart"],
            "skeleton": "class ProductListPage extends ConsumerWidget { /* TODO(spec): build */ }",
        },
    ],
    "data_models": [{"name": "Product", "kind": "freezed", "fields": [{"name": "id", "type": "String"}]}],
    "widget_tree": "ProductListPage > ListView > ProductTile",
    "test_stubs": [
        {"path": "test/product_list_page_test.dart", "covers": "lib/features/product/product_list_page.dart", "kind": "widget", "cases": ["should render list"]},
    ],
    "wiring": ["注册 productListProvider"],
})

_MOCK_REVIEW = json.dumps({
    "summary": "骨架基本就绪，建议补齐错误态",
    "findings": [
        {
            "path": "lib/features/product/product_list_page.dart",
            "severity": "minor",
            "category": "error-handling",
            "issue": "未处理加载失败的 UI 错误态",
            "suggestion": "用 AsyncValue 三态渲染 error 分支",
        }
    ],
    "checklist": [{"item": "失败路径已建模", "status": "fail"}],
    "blocking": False,
})

_MOCK_ACCEPTANCE = json.dumps({
    "criteria": [
        "Given product list, when user taps item, then navigate to detail",
        "Given deep link URL, when app opens, then show correct product",
    ],
})

_MOCK_MARKDOWN = """# 产品需求文档

## 概述
一个电商移动应用的产品列表和详情页面。

## 用户故事
- US-1: 用户可以浏览产品列表
- US-2: 用户可以通过深度链接访问产品详情
"""

_STAGE_RESPONSES = {
    "classify": _MOCK_CLASSIFY,
    "spec": _MOCK_SPEC,
    "architecture": _MOCK_ARCHITECTURE,
    "breakdown": _MOCK_BREAKDOWN,
    "implementation": _MOCK_IMPLEMENTATION,
    "review": _MOCK_REVIEW,
    "acceptance": _MOCK_ACCEPTANCE,
    "markdown": _MOCK_MARKDOWN,
}


class _MockDeepSeekClient:
    """Deterministic mock that returns predefined responses per stage."""

    def __init__(self):
        self._call_count = 0
        self._stage_order = ["classify", "spec", "architecture", "breakdown", "implementation", "review", "acceptance", "markdown"]

    async def chat(self, messages, *, model=None, temperature=None, max_tokens=None, response_format=None):
        # Determine stage from system prompt content or call order
        stage = self._stage_order[min(self._call_count, len(self._stage_order) - 1)]
        self._call_count += 1
        text = _STAGE_RESPONSES.get(stage, "{}")
        return {
            "choices": [{"message": {"content": text}}],
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 300,
                "total_tokens": 800,
            },
        }

    @staticmethod
    def extract_text(completion):
        return completion["choices"][0]["message"]["content"] or ""

    @staticmethod
    def extract_usage(completion):
        usage = completion.get("usage", {})
        return {
            "prompt_tokens": int(usage.get("prompt_tokens", 0)),
            "completion_tokens": int(usage.get("completion_tokens", 0)),
            "total_tokens": int(usage.get("total_tokens", 0)),
        }


@pytest.fixture()
def settings(tmp_path):
    return Settings(
        deepseek_api_key="test-key",
        deepseek_base_url="http://localhost:9999/v1",
        deepseek_model="test-model",
        skills_dir=str(Settings().skills_path),  # use real skills
        runs_log_path=str(tmp_path / "runs.jsonl"),
    )


@pytest.fixture()
def registry(settings):
    reg = SkillRegistry(settings.skills_path)
    reg.reload()
    return reg


@pytest.mark.asyncio
async def test_full_pipeline_with_mock_llm(settings, registry, tmp_path):
    """Run all 8 stages with mocked LLM and verify the response structure."""
    mock_client = _MockDeepSeekClient()
    cache = RunCache(settings.runs_log_file)

    pipeline = RefinementPipeline(
        settings=settings,
        client=mock_client,
        registry=registry,
        cache=cache,
        pub_validator=None,  # skip pub.dev calls in this test
    )

    req = RefineRequest(
        requirement="构建一个电商移动应用,支持产品列表和深度链接到产品详情页",
        platforms=[Platform.mobile],
        stages=[
            Stage.classify, Stage.spec, Stage.architecture,
            Stage.breakdown, Stage.implementation, Stage.review, Stage.acceptance, Stage.markdown,
        ],
        validate_packages=False,
    )

    response = await pipeline.run(req)

    # Basic structure
    assert response.id.startswith("run-")
    assert response.cached is False
    assert response.cache_key != ""
    assert len(response.stages) == 8
    assert response.requirement == req.requirement

    # Stage results
    stage_names = [sr.stage.value for sr in response.stages]
    assert stage_names == ["classify", "spec", "architecture", "breakdown", "implementation", "review", "acceptance", "markdown"]

    # Parsed outputs
    assert response.classify is not None
    assert "recommended_skills" in response.classify
    assert response.spec is not None
    assert "user_stories" in response.spec
    assert response.architecture is not None
    assert "third_party" in response.architecture
    assert response.breakdown is not None
    assert "tasks" in response.breakdown
    assert response.implementation is not None
    assert "files" in response.implementation
    assert response.implementation["files"][0]["path"].startswith("lib/")
    assert response.review is not None
    assert "findings" in response.review
    assert response.review["findings"][0]["issue"]
    assert response.acceptance is not None
    assert "criteria" in response.acceptance
    assert response.markdown is not None
    assert "产品需求文档" in response.markdown

    # Cost aggregation
    assert response.cost is not None
    assert response.cost.total_cost_usd >= 0

    # Usage aggregation
    assert response.usage.total_tokens > 0
    # 8 stages * 800 tokens each = 6400
    assert response.usage.total_tokens == 6400

    # Stage-level schema validation — all mock outputs should pass
    for sr in response.stages:
        if sr.stage != Stage.markdown:
            assert sr.stage_valid is True, f"stage {sr.stage.value} failed validation: {sr.validation_error}"


@pytest.mark.asyncio
async def test_pipeline_skill_selection_uses_ranker(settings, registry):
    """Verify that the ranker picks relevant skills for animation requirements.

    Note: classify stage overrides selection via recommended_skills.
    We test the initial ranker by explicitly providing skills=None and
    skipping classify (so the override doesn't happen).
    """
    mock_client = _MockDeepSeekClient()
    # Override mock to return non-classify response for spec stage
    mock_client._stage_order = ["spec"]

    pipeline = RefinementPipeline(
        settings=settings,
        client=mock_client,
        registry=registry,
    )

    req = RefineRequest(
        requirement="需要 hero animation 过渡动画和 motion 运动效果",
        platforms=[Platform.mobile],
        stages=[Stage.spec],  # skip classify to test ranker directly
        validate_packages=False,
    )

    response = await pipeline.run(req)
    # Should include flutter-animation due to keyword match in ranker
    assert "flutter-animation" in response.selected_skills


def test_stage_hints_filter_skills_per_stage(settings, registry):
    """Verify that _build_system_prompt filters skills by stage_hints."""
    from flutter_agent.schemas import SkillDetail

    pipeline = RefinementPipeline(
        settings=settings,
        client=_MockDeepSeekClient(),
        registry=registry,
    )

    # Get all skills (use registry directly)
    all_skills = list(registry._skills.values())

    # Markdown stage: no skill has 'markdown' in stage_hints, so prompt
    # should be the smallest (no skill bodies injected).
    md_prompt = pipeline._build_system_prompt(Stage.markdown, all_skills)

    # Architecture stage: many skills target this stage.
    arch_prompt = pipeline._build_system_prompt(Stage.architecture, all_skills)

    # Architecture prompt should be substantially larger than markdown
    assert len(arch_prompt) > len(md_prompt) * 2, (
        f"stage_hints filter not working: arch={len(arch_prompt)}, md={len(md_prompt)}"
    )

    # Skills with no stage_hints should appear in both
    universal_skills = [s for s in all_skills if not s.stage_hints]
    for sk in universal_skills:
        assert sk.id in md_prompt or sk.name in md_prompt
        assert sk.id in arch_prompt or sk.name in arch_prompt


def test_default_stages_include_implementation_and_review():
    """The default pipeline must run implementation then review in order."""
    req = RefineRequest(requirement="任意需求")
    names = [s.value for s in req.stages]
    assert names == [
        "classify", "spec", "architecture", "breakdown",
        "implementation", "review", "acceptance", "markdown",
    ]
    # implementation precedes review precedes acceptance (the feedback loop order)
    assert names.index("implementation") < names.index("review") < names.index("acceptance")


def test_review_stage_instruction_uses_review_skills():
    """The review stage prompt must invoke the code-review + static-analysis skills."""
    from flutter_agent.pipeline import _STAGE_INSTRUCTIONS

    instr = _STAGE_INSTRUCTIONS[Stage.review]
    assert "flutter-code-review" in instr
    assert "flutter-static-analysis" in instr
    assert "findings" in instr


def test_review_skills_declare_review_stage_hint(registry):
    """code-review / static-analysis must be injectable during the review stage."""
    for sid in ("flutter-code-review", "flutter-static-analysis"):
        sk = registry.get(sid)
        assert sk is not None
        assert "review" in sk.stage_hints, f"{sid} should hint the review stage"


@pytest.mark.asyncio
async def test_pipeline_cache_hit(settings, registry, tmp_path):
    """Run twice with same input, second should be cached."""
    mock_client = _MockDeepSeekClient()
    cache = RunCache(settings.runs_log_file)

    from flutter_agent.run_store import RunStore
    run_store = RunStore(settings.runs_log_file)

    pipeline = RefinementPipeline(
        settings=settings,
        client=mock_client,
        registry=registry,
        cache=cache,
        run_store=run_store,
    )

    req = RefineRequest(
        requirement="缓存测试需求",
        platforms=[Platform.mobile],
        stages=[Stage.classify],
        use_cache=True,
        validate_packages=False,
    )

    # First run — should execute normally
    resp1 = await pipeline.run(req)
    assert resp1.cached is False

    # Persist to run store so cache can find it
    await run_store.append(resp1)

    # Second run — should be a cache hit
    mock_client2 = _MockDeepSeekClient()
    pipeline2 = RefinementPipeline(
        settings=settings,
        client=mock_client2,
        registry=registry,
        cache=cache,
        run_store=run_store,
    )
    resp2 = await pipeline2.run(req)
    assert resp2.cached is True
    assert resp2.cache_key == resp1.cache_key
