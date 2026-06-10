"""Multi-stage requirement refinement pipeline.

Each stage:
  1. builds a system prompt out of the selected SKILL.md bodies,
  2. injects the upstream user requirement (and prior stages' outputs),
  3. calls the upstream chat model,
  4. tries to JSON-parse the answer, attaches the result to the response.

Stages are ordered: ``classify -> spec -> architecture -> breakdown
-> acceptance -> markdown``. The final ``markdown`` stage is the only one
that asks for prose; everything else is JSON.
"""
from __future__ import annotations

import json
import logging
import re
import time
import uuid
from typing import Any, Awaitable, Callable, Dict, List, Optional

from .cache import RunCache, make_cache_key
from .config import Settings
from .consistency import check_acceptance_consistency
from .deepseek_client import DeepSeekClient, UpstreamError
from .pricing import estimate_cost
from .pub_validator import PubValidator
from .reporting import append_audit_section, prepend_validation_warnings
from .review_loop import (
    _augment_review_with_consistency,
    _format_review_feedback,
    _review_is_blocking,
    _summarize_review_pass,
)
from .run_store import RunStore
from .schemas import (
    CostBreakdown,
    PackageValidation,
    Platform,
    RefineRequest,
    RefineResponse,
    ReviewPass,
    SkillDetail,
    Stage,
    StageResult,
    TokenUsage,
)
from .skill_loader import SkillRegistry
from .skill_ranker import build_families, rank_skills, select_within_budget
from .stage_schemas import validate_stage_output

logger = logging.getLogger(__name__)

# Async callback that receives progress events while the pipeline runs.
ProgressCallback = Callable[[Dict[str, Any]], Awaitable[None]]


# Foundational skills and the signals that justify force-including them.
# When none of a skill's trigger terms appear in the requirement, it is no
# longer pinned to the top — it still competes on its own keyword relevance.
# Strong, unambiguous signals only (weak generics like 列表/数据/ui were
# dropped because they misfire on performance/ops tasks).
_STATE_TERMS = (
    "状态", "state", "交互", "数据流", "表单", "登录",
    "provider", "riverpod", "bloc", "getx", "setstate", "redux", "mobx",
)
_ARCH_TERMS = (
    "架构", "结构", "模块", "分层", "重构", "工程化", "新功能",
    "architecture", "clean", "mvvm", "mvc", "feature",
    "需求", "功能", "迁移", "重写",
)
# Narrow ops/maintenance tasks: when one of these appears and there is no
# structure/state signal, do NOT pin foundational skills — they would just
# waste token budget that the actually-relevant ops skills need.
_OPS_TERMS = (
    "打包", "签名", "混淆", "发布", "上架", "商店", "store", "公证", "归档",
    "ci", "cd", "流水线", "pipeline", "缓存", "cache", "产物", "密钥",
    "剖析", "profil", "jank", "掉帧", "卡顿", "构建", "build", "release",
    "性能", "调优", "优化", "内存", "启动", "体积",
)


def _resolve_foundational_ids(requirement: str, platforms: List[str]) -> List[str]:
    """Decide which foundational skills to force-include for this requirement.

    Narrow ops tasks (e.g. "Android 打包签名", "配置 CI 缓存", "性能剖析") that
    mention no structure/state signal get neither pinned, freeing budget for
    the skills that actually matter. Such tasks still receive arch/state skills
    if they happen to rank, just not at a forced +100.
    """
    text = (requirement or "").lower()
    ids: List[str] = []
    if any(term in text for term in _ARCH_TERMS):
        ids.append("architecture-design")
    if any(term in text for term in _STATE_TERMS):
        ids.append("state-management")
    if not ids:
        is_ops = any(term in text for term in _OPS_TERMS)
        # Generic app/feature task with no clear signal -> keep old behaviour
        # (pin both). A narrow ops task -> pin nothing.
        if not is_ops:
            ids = ["architecture-design", "state-management"]
    if {"mobile", "desktop"}.issubset(set(platforms)):
        ids.append("flutter-cross-platform")
    return ids


_REPAIR_SYSTEM = (
    "你是一个 JSON 修复器。下面会给你一段本应是合法 JSON 的文本,但里面可能混杂了 "
    "```json``` 围栏、解释性文字、尾随逗号等。你的任务是只输出一个合法的 JSON 对象 "
    "或数组,不要任何其他字符。如果原文是数组,把它包成 {\"items\": [...]} 形式。"
)


# ---------------------------------------------------------------------------
# Prompts
# ---------------------------------------------------------------------------

_BASE_SYSTEM = """你是一个资深的 Flutter 解决方案架构师 + 产品经理。
你将依据下列 **SKILL** 文档以及流水线阶段定义,把用户的需求精炼成可执行的工程产出。

总则:
1. 严格遵守 SKILL 中的目录结构、技术栈、红线。
2. 阶段为 JSON 时,**只**输出合法的 JSON,不要 ```json``` 围栏外的任何解释。
3. 阶段为 markdown 时,输出干净的 markdown,使用合适的标题层级,不要包 ``` 围栏。
4. 任何 ID 字段全用英文 ID;描述性字段保留用户使用的语言(默认中文)。
5. 估算不确定时给区间,如 "estimate_hours": {"min": 3, "max": 6}。
6. 如果用户需求与 SKILL 冲突,以 SKILL 为准并在 "assumptions" 字段里说明。
"""


_STAGE_INSTRUCTIONS: Dict[Stage, str] = {
    Stage.classify: """# 当前阶段: classify

请只输出 JSON,字段如 task-refinement SKILL 阶段 0 所定义:
{
  "title": "...",
  "one_liner": "...",
  "platforms": ["mobile" | "desktop" | "web", ...],
  "primary_users": [...],
  "core_value": "...",
  "non_goals": [...],
  "recommended_skills": [...],   // 从可用 skill id 中选
  "complexity": "S|M|L|XL",
  "confidence": 0.0~1.0,
  "open_questions": [...]
}

可用 skill id 列表:
{available_skills}
""",
    Stage.spec: """# 当前阶段: spec (PRD)

输入: 用户需求 + 上一步 classify 的 JSON。
任务: 产出 PRD,字段如 task-refinement SKILL 阶段 1。**仅输出 JSON**。
""",
    Stage.architecture: """# 当前阶段: architecture

输入: 上一步的 spec JSON。
任务: 给出技术架构,字段如 task-refinement SKILL 阶段 2;务必符合 architecture-design SKILL 的分层与依赖方向。
**仅输出 JSON**。
""",
    Stage.breakdown: """# 当前阶段: breakdown

输入: spec + architecture JSON。
任务: 按 Epic→Story→Task 拆解,字段如 task-refinement SKILL 阶段 3。
约束:
- 每个 task 工时 ≤ 8h,否则继续拆。
- files_touched 路径必须符合 architecture.directory_tree。
- 每个 task 至少 1 条 acceptance。
**仅输出 JSON**。
""",
    Stage.implementation: """# 当前阶段: implementation (代码骨架)

输入: spec + architecture + breakdown JSON。
任务: 把任务清单落成**逼近代码**的实现骨架,让下游(编码 Agent / 人)可以照着直接写。
严格遵守 architecture.directory_tree 与分层/依赖方向;遵守 dart-language-idioms / flutter-error-handling
等代码领域 SKILL 的写法约定。**只给签名/骨架,不写完整业务实现**,未完成处用 `// TODO(spec):` 标注。

**仅输出 JSON**,结构:
{
  "files": [
    {
      "path": "lib/...",                 // 必须落在 architecture.directory_tree 内
      "purpose": "这个文件负责什么",
      "language": "dart",
      "layer": "presentation|application|domain|data|...",
      "public_api": ["ClassName", "ClassName.method(Args) -> Return", ...],
      "depends_on": ["lib/...dart", "package:xxx/xxx.dart"],
      "skeleton": "类/方法签名 + import + // TODO 占位的 Dart 代码骨架(不写完整实现)"
    }
  ],
  "data_models": [
    {"name": "User", "kind": "freezed|class|enum|sealed", "fields": [{"name":"id","type":"String"}], "notes":"..."}
  ],
  "widget_tree": "关键页面的 widget 树(缩进文本),标出状态来源与回调",
  "test_stubs": [
    {"path": "test/...", "covers": "lib/...dart", "kind": "unit|widget|golden|integration", "cases": ["should ...", ...]}
  ],
  "wiring": ["把上述文件接起来的步骤,如 注册 provider / 路由 / DI"],
  "assumptions": ["从需求无法确定、此处所做的假设"]
}
约束:
- 每个 task(来自 breakdown)至少映射到一个 file 或 test_stub。
- skeleton 只放签名与结构,业务逻辑用 // TODO(spec): 占位,避免编造未确认的实现。
- 不引入 architecture.third_party 之外的新依赖;若确需新依赖,写进 assumptions 待确认。
""",
    Stage.review: """# 当前阶段: review (代码自检 / 评审)

输入: architecture + breakdown + implementation JSON。
任务: 站在评审者视角,对 implementation 产物做一次**自查**,按 flutter-code-review 的红线清单
与 flutter-static-analysis 的规则,找出问题并给出**可执行的修复建议**(对位到具体 file/path)。
这是质量反馈环:发现问题就回填,让下游(编码 Agent / 人)拿到的是已自审过的骨架。

**仅输出 JSON**,结构:
{
  "summary": "一句话总体评价(骨架是否就绪、主要风险)",
  "findings": [
    {
      "path": "lib/...",                 // 对位 implementation.files 的某个 path(全局问题用 \"<general>\")
      "severity": "blocker|major|minor|nit",
      "category": "architecture|error-handling|testability|naming|null-safety|performance|security|style|other",
      "issue": "问题是什么(具体、可核对)",
      "suggestion": "怎么改(给出方向或签名级示例,不必整段重写)"
    }
  ],
  "checklist": [
    {"item": "分层与依赖方向正确(无反向依赖)", "status": "pass|fail|na"},
    {"item": "失败路径已建模(可预期失败/未预期异常)", "status": "pass|fail|na"},
    {"item": "资源可释放(订阅/控制器有 dispose)", "status": "pass|fail|na"},
    {"item": "纯核心可测、依赖可注入", "status": "pass|fail|na"},
    {"item": "无明显 lint/红线违规(吞异常/print/裸 any)", "status": "pass|fail|na"}
  ],
  "blocking": true
}
约束:
- findings 的 path 必须能在 implementation.files 中找到(或用 "<general>")。
- 没有问题时 findings 给空数组,blocking=false;不要编造问题凑数。
- severity=blocker 至少要在 summary 点明;blocking 取决于是否存在 blocker/major。
""",
    Stage.acceptance: """# 当前阶段: acceptance

输入: breakdown(+ implementation / review,若有) JSON。
任务: 产出 acceptance_matrix / test_plan / risks / milestones,如 task-refinement SKILL 阶段 4。
若已有 implementation.test_stubs,test_plan 应与其对齐(同一文件/同一用例不重复造)。
**仅输出 JSON**。
""",
    Stage.markdown: """# 当前阶段: markdown

输入: 前面所有阶段的 JSON。
任务: 汇总成一份给人类阅读的 **Markdown PRD**,顶层结构:
1. 项目概览
2. 用户与场景
3. 功能列表
4. 数据模型与接口
5. 技术架构(含目录树)
6. 任务清单(Epic 表 + Story 表)
7. 实现骨架(若有 implementation:文件清单 + 关键签名/widget 树 + 测试桩;代码用 ```dart 围栏)
8. 自检与评审(若有 review:总体结论 + findings 表[path/severity/issue/suggestion] + checklist)
9. 测试与验收
10. 风险与里程碑

要求:中文输出;使用表格;除第 7 节内嵌代码外,不要包代码围栏在最外层。
""",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


_JSON_FENCE_RE = re.compile(r"```(?:json)?\s*(?P<body>\{.*\}|\[.*\])\s*```", re.DOTALL)
_LOOSE_JSON_RE = re.compile(r"(?P<body>\{.*\}|\[.*\])", re.DOTALL)


def _try_parse_json(text: str) -> Optional[Dict[str, Any]]:
    """Best-effort JSON extraction; tolerates ``` fences and leading prose."""
    text = (text or "").strip()
    if not text:
        return None
    # 1. direct
    try:
        v = json.loads(text)
        return v if isinstance(v, dict) else {"_list": v}
    except json.JSONDecodeError:
        pass
    # 2. fenced
    m = _JSON_FENCE_RE.search(text)
    if m:
        try:
            v = json.loads(m.group("body"))
            return v if isinstance(v, dict) else {"_list": v}
        except json.JSONDecodeError:
            pass
    # 3. greedy biggest object
    m = _LOOSE_JSON_RE.search(text)
    if m:
        try:
            v = json.loads(m.group("body"))
            return v if isinstance(v, dict) else {"_list": v}
        except json.JSONDecodeError:
            return None
    return None


def _stage_complete_event(
    sr: StageResult, *, review_iteration: Optional[int] = None
) -> Dict[str, Any]:
    event: Dict[str, Any] = {
        "type": "stage_complete",
        "stage": sr.stage.value,
        "elapsed_ms": sr.elapsed_ms,
        "attempts": sr.attempts,
        "repaired": sr.repaired,
        "stage_valid": sr.stage_valid,
        "usage": {
            "prompt_tokens": sr.usage.prompt_tokens,
            "completion_tokens": sr.usage.completion_tokens,
            "total_tokens": sr.usage.total_tokens,
        },
        "cost_usd": sr.cost.total_cost_usd if sr.cost else None,
    }
    if review_iteration is not None:
        event["review_iteration"] = review_iteration
    return event


def _platforms_to_strs(platforms: List[Platform]) -> List[str]:
    out = [p.value for p in platforms if p != Platform.auto]
    return out or ["mobile", "desktop"]  # safe default


# ---------------------------------------------------------------------------
# Pipeline
# ---------------------------------------------------------------------------


class RefinementPipeline:
    def __init__(
        self,
        settings: Settings,
        client: DeepSeekClient,
        registry: SkillRegistry,
        cache: Optional[RunCache] = None,
        pub_validator: Optional[PubValidator] = None,
        run_store: Optional[RunStore] = None,
    ):
        self._settings = settings
        self._client = client
        self._registry = registry
        self._cache = cache
        self._pub_validator = pub_validator
        self._run_store = run_store

    # ------------------------------------------------------------------ API

    @staticmethod
    async def _emit(progress: Optional[ProgressCallback], event: Dict[str, Any]) -> None:
        if progress is None:
            return
        try:
            await progress(event)
        except Exception:  # noqa: BLE001 - progress must never break the run
            logger.exception("progress callback failed for event %s", event.get("type"))

    async def run(
        self,
        req: RefineRequest,
        progress: Optional[ProgressCallback] = None,
    ) -> RefineResponse:
        # ---- Decide which skills are in play -----------------------------
        if req.skills:
            picked = self._registry.get_many(req.skills)
        else:
            picked = self._initial_skill_guess(req)

        # task-refinement is always included as the meta SOP
        if not any(s.id == "task-refinement" for s in picked):
            meta = self._registry.get("task-refinement")
            if meta is not None:
                picked.insert(0, meta)

        selected_ids = [s.id for s in picked]

        # ---- Cache lookup ------------------------------------------------
        cache_key = make_cache_key(
            requirement=req.requirement,
            skill_ids=selected_ids,
            stages=[s.value for s in req.stages],
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            extra_context=req.extra_context,
            model=self._settings.deepseek_model,
        )
        if req.use_cache and self._cache and self._run_store:
            hit_id = await self._cache.lookup(cache_key)
            if hit_id:
                cached_obj = self._run_store.get(hit_id)
                if cached_obj is not None:
                    cached_response = RefineResponse.model_validate(cached_obj)
                    cached_response.cached = True
                    cached_response.cache_key = cache_key
                    logger.info("cache hit: %s -> %s", cache_key[:12], hit_id)
                    await self._emit(progress, {
                        "type": "cache_hit",
                        "run_id": hit_id,
                        "cache_key": cache_key,
                    })
                    return cached_response

        run_id = f"run-{uuid.uuid4().hex[:16]}"
        logger.info(
            "pipeline start id=%s skills=%s stages=%s",
            run_id,
            selected_ids,
            [s.value for s in req.stages],
        )

        await self._emit(progress, {
            "type": "pipeline_start",
            "run_id": run_id,
            "skills": selected_ids,
            "stages": [s.value for s in req.stages],
        })

        stage_results: List[StageResult] = []
        prior: Dict[Stage, Dict[str, Any]] = {}
        markdown_out: Optional[str] = None
        total_usage = TokenUsage()
        review_iterations = 0
        review_history: List[ReviewPass] = []

        for stage in req.stages:
            await self._emit(progress, {"type": "stage_start", "stage": stage.value})
            stage_result = await self._run_stage(
                stage=stage,
                req=req,
                skills=picked,
                prior=prior,
            )
            stage_results.append(stage_result)
            total_usage.add(stage_result.usage)
            await self._emit(progress, _stage_complete_event(stage_result))

            if stage == Stage.markdown:
                markdown_out = stage_result.raw_output.strip()
            elif stage_result.parsed is not None:
                prior[stage] = stage_result.parsed

                # After classify, refine selected skills if the model suggested some.
                if stage == Stage.classify:
                    suggested = stage_result.parsed.get("recommended_skills") or []
                    if req.skills is None and isinstance(suggested, list):
                        merged: List[SkillDetail] = []
                        seen = set()
                        for sid in suggested:
                            sd = self._registry.get(str(sid))
                            if sd and sd.id not in seen:
                                merged.append(sd)
                                seen.add(sd.id)
                        meta = self._registry.get("task-refinement")
                        if meta and meta.id not in seen:
                            merged.insert(0, meta)
                        if merged:
                            picked = merged
                            selected_ids = [s.id for s in picked]
                            logger.info("classify refined skills -> %s", selected_ids)

                # Closed loop: if the review blocks, re-implement with the
                # findings as feedback and re-review, bounded by the request.
                elif stage == Stage.review and Stage.implementation in req.stages:
                    threshold = req.review_block_severity
                    _augment_review_with_consistency(prior)
                    review_history.append(
                        _summarize_review_pass(prior.get(Stage.review), 0, threshold)
                    )
                    while (
                        review_iterations < req.review_max_iterations
                        and _review_is_blocking(prior.get(Stage.review), threshold)
                    ):
                        feedback = _format_review_feedback(prior[Stage.review], threshold)
                        logger.info(
                            "review blocking -> re-implement pass %d/%d",
                            review_iterations + 1,
                            req.review_max_iterations,
                        )
                        await self._emit(progress, {
                            "type": "stage_start",
                            "stage": Stage.implementation.value,
                            "review_iteration": review_iterations + 1,
                        })
                        impl_again = await self._run_stage(
                            stage=Stage.implementation,
                            req=req,
                            skills=picked,
                            prior=prior,
                            feedback=feedback,
                        )
                        stage_results.append(impl_again)
                        total_usage.add(impl_again.usage)
                        await self._emit(
                            progress,
                            _stage_complete_event(
                                impl_again, review_iteration=review_iterations + 1
                            ),
                        )
                        if impl_again.parsed is not None:
                            prior[Stage.implementation] = impl_again.parsed

                        await self._emit(progress, {
                            "type": "stage_start",
                            "stage": Stage.review.value,
                            "review_iteration": review_iterations + 1,
                        })
                        review_again = await self._run_stage(
                            stage=Stage.review,
                            req=req,
                            skills=picked,
                            prior=prior,
                        )
                        stage_results.append(review_again)
                        total_usage.add(review_again.usage)
                        await self._emit(
                            progress,
                            _stage_complete_event(
                                review_again, review_iteration=review_iterations + 1
                            ),
                        )
                        if review_again.parsed is not None:
                            prior[Stage.review] = review_again.parsed
                            _augment_review_with_consistency(prior)

                        review_iterations += 1
                        review_history.append(
                            _summarize_review_pass(
                                prior.get(Stage.review), review_iterations, threshold
                            )
                        )

        # ---- acceptance cross-check (deterministic, advisory) -----------
        acceptance_gaps: List[Dict[str, Any]] = []
        if Stage.acceptance in prior:
            acceptance_gaps = check_acceptance_consistency(
                prior.get(Stage.acceptance),
                prior.get(Stage.breakdown),
                prior.get(Stage.implementation),
            )

        # ---- pub.dev package validation ---------------------------------
        validations: List[PackageValidation] = []
        if req.validate_packages and self._pub_validator is not None:
            arch = prior.get(Stage.architecture) or {}
            third_party = arch.get("third_party")
            if isinstance(third_party, list) and third_party:
                logger.info("validating %d package(s) against pub.dev", len(third_party))
                checks = await self._pub_validator.validate_third_party(third_party)
                validations = [PackageValidation(**c.to_dict()) for c in checks]

        # ---- Aggregate cost ---------------------------------------------
        aggregated_cost = self._aggregate_cost(stage_results)

        response = RefineResponse(
            id=run_id,
            created_at=int(time.time()),
            cache_key=cache_key,
            cached=False,
            requirement=req.requirement,
            selected_skills=selected_ids,
            usage=total_usage,
            cost=aggregated_cost,
            stages=stage_results,
            classify=prior.get(Stage.classify),
            spec=prior.get(Stage.spec),
            architecture=prior.get(Stage.architecture),
            breakdown=prior.get(Stage.breakdown),
            implementation=prior.get(Stage.implementation),
            review=prior.get(Stage.review),
            review_iterations=review_iterations,
            review_history=review_history,
            acceptance=prior.get(Stage.acceptance),
            acceptance_gaps=acceptance_gaps,
            markdown=self._prepend_validation_warnings(
                self._append_audit_section(markdown_out, review_history, acceptance_gaps),
                validations,
            ),
            validations=validations,
        )

        if self._cache is not None:
            await self._cache.index(cache_key, run_id)

        return response

    # -------------------------------------------------------------- helpers

    def _initial_skill_guess(self, req: RefineRequest) -> List[SkillDetail]:
        """Pick skills using keyword relevance ranking + token budget.

        Strategy:
        1. Collect all skills that platform-match *or* score > 0 via keyword.
        2. Rank by relevance to req.requirement.
        3. Trim to fit token budget so the system prompt stays within the
           model context window.
        """
        platforms = _platforms_to_strs(req.platforms)
        all_skills = [s for _, s in enumerate(self._registry._skills.values())]

        # Foundational skills are force-included only when the requirement is
        # actually about app structure / state — not for narrow ops tasks
        # (packaging / CI / profiling), where pinning them wastes budget.
        always_ids = _resolve_foundational_ids(req.requirement, platforms)

        ranked = rank_skills(
            requirement=req.requirement,
            skills=all_skills,
            platforms=platforms,
            always_include=always_ids,
        )
        families = build_families(all_skills)
        picked = select_within_budget(
            ranked,
            always_include=set(always_ids),
            families=families,
        )
        logger.info(
            "skill ranker: %d/%d skills selected (top scores: %s)",
            len(picked),
            len(all_skills),
            [(s.id, round(sc, 2)) for s, sc in ranked[:5]],
        )
        return picked

    async def _run_stage(
        self,
        *,
        stage: Stage,
        req: RefineRequest,
        skills: List[SkillDetail],
        prior: Dict[Stage, Dict[str, Any]],
        feedback: Optional[str] = None,
    ) -> StageResult:
        sys_prompt = self._build_system_prompt(stage, skills)
        user_prompt = self._build_user_prompt(stage, req, prior, feedback=feedback)
        model = (
            self._settings.planner_model
            if stage == Stage.classify
            else self._settings.deepseek_model
        )

        messages = [
            {"role": "system", "content": sys_prompt},
            {"role": "user", "content": user_prompt},
        ]

        response_format = (
            {"type": "json_object"} if stage != Stage.markdown else None
        )

        t0 = time.perf_counter()
        completion = await self._client.chat(
            messages,
            model=model,
            temperature=req.temperature,
            max_tokens=req.max_tokens,
            response_format=response_format,
        )
        text = self._client.extract_text(completion)
        usage = TokenUsage(**self._client.extract_usage(completion))
        attempts = 1
        repaired = False

        parsed: Optional[Dict[str, Any]] = None
        if stage != Stage.markdown:
            parsed = _try_parse_json(text)
            if parsed is None:
                # JSON repair: ask the model to extract a clean JSON from the
                # bad output. One repair attempt only — keeps cost bounded.
                logger.warning(
                    "stage %s: JSON parse failed, attempting repair", stage.value
                )
                repair_completion = await self._client.chat(
                    [
                        {"role": "system", "content": _REPAIR_SYSTEM},
                        {"role": "user", "content": text},
                    ],
                    model=model,
                    temperature=0.0,
                    max_tokens=req.max_tokens,
                    response_format={"type": "json_object"},
                )
                attempts += 1
                repair_text = self._client.extract_text(repair_completion)
                usage.add(TokenUsage(**self._client.extract_usage(repair_completion)))
                parsed = _try_parse_json(repair_text)
                if parsed is not None:
                    repaired = True
                    # surface repaired text alongside original for debugging
                    text = (
                        text
                        + "\n\n--- REPAIRED JSON ---\n"
                        + repair_text
                    )
                else:
                    logger.error("stage %s: JSON repair also failed", stage.value)

        # ---- Schema validation ----
        stage_valid: bool = True
        validation_error: Optional[str] = None
        if parsed is not None:
            validation_error = validate_stage_output(stage.value, parsed)
            if validation_error:
                stage_valid = False
                logger.warning(
                    "stage %s: output schema validation failed: %s",
                    stage.value,
                    validation_error[:200],
                )

        elapsed_ms = int((time.perf_counter() - t0) * 1000)
        cost_est = estimate_cost(
            model=model,
            prompt_tokens=usage.prompt_tokens,
            completion_tokens=usage.completion_tokens,
        )
        cost = CostBreakdown(**cost_est.to_dict())
        return StageResult(
            stage=stage,
            model=model,
            elapsed_ms=elapsed_ms,
            attempts=attempts,
            repaired=repaired,
            stage_valid=stage_valid,
            validation_error=validation_error,
            usage=usage,
            cost=cost,
            raw_output=text,
            parsed=parsed,
        )

    def _aggregate_cost(self, stage_results: List[StageResult]) -> Optional[CostBreakdown]:
        if not stage_results:
            return None
        # All stages should hit the same pricing source unless mixed planner +
        # main models are in play. We label the breakdown with the *main* model
        # but accumulate every stage's USD.
        models = {sr.model for sr in stage_results}
        source = sorted({sr.cost.pricing_source for sr in stage_results if sr.cost})
        input_total = sum(sr.cost.input_cost_usd for sr in stage_results if sr.cost)
        output_total = sum(sr.cost.output_cost_usd for sr in stage_results if sr.cost)
        return CostBreakdown(
            model="+".join(sorted(models)) if len(models) > 1 else next(iter(models)),
            pricing_source="+".join(source) if source else "*",
            input_cost_usd=round(input_total, 6),
            output_cost_usd=round(output_total, 6),
            total_cost_usd=round(input_total + output_total, 6),
        )

    # Thin wrappers kept for call-site/test ergonomics; logic lives in
    # ``reporting`` so the markdown decorations stay model-independent.
    _prepend_validation_warnings = staticmethod(prepend_validation_warnings)
    _append_audit_section = staticmethod(append_audit_section)

    def _build_system_prompt(self, stage: Stage, skills: List[SkillDetail]) -> str:
        available = ", ".join(sorted(s.id for s in self._registry.list())) or "(empty)"
        instr = _STAGE_INSTRUCTIONS[stage].replace("{available_skills}", available)

        # Filter skills by stage_hints: only inject those relevant to current
        # stage. Skills with no stage_hints are treated as universal (always
        # included). This cuts ~30-40% off the system prompt for late stages.
        stage_value = stage.value
        relevant: List[SkillDetail] = []
        for sk in skills:
            if not sk.stage_hints or stage_value in sk.stage_hints:
                relevant.append(sk)

        blocks = [_BASE_SYSTEM, instr, "# 已加载的 Skill 文档"]
        for sk in relevant:
            blocks.append(f"\n## SKILL: {sk.id}  —  {sk.name}\n\n{sk.body}\n")
        logger.debug(
            "stage %s: injected %d/%d skills (filtered by stage_hints)",
            stage_value,
            len(relevant),
            len(skills),
        )
        return "\n".join(blocks)

    def _build_user_prompt(
        self,
        stage: Stage,
        req: RefineRequest,
        prior: Dict[Stage, Dict[str, Any]],
        feedback: Optional[str] = None,
    ) -> str:
        chunks: List[str] = []
        chunks.append("## 用户原始需求")
        chunks.append(req.requirement.strip())
        if req.extra_context:
            chunks.append("\n## 额外上下文")
            chunks.append(req.extra_context.strip())
        if feedback:
            chunks.append("\n## 评审反馈(必须逐条修复后重新产出)")
            chunks.append(feedback.strip())

        platforms = _platforms_to_strs(req.platforms)
        chunks.append("\n## 目标平台")
        chunks.append(", ".join(platforms))

        if prior:
            chunks.append("\n## 已完成阶段输出 (JSON)")
            for s, v in prior.items():
                chunks.append(f"\n### {s.value}\n")
                chunks.append(json.dumps(v, ensure_ascii=False, indent=2))

        chunks.append(f"\n## 请输出当前阶段({stage.value})的产物")
        return "\n".join(chunks)
