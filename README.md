# flutter-agent

一个本地运行的 **Flutter 需求精炼器**。所有工程主张都能在 [`REFERENCES.md`](./REFERENCES.md) 里找到官方文档 / pub.dev / 行业标准的出处。

- 用 **Markdown 形式的 Skills** 描述「Mobile / Desktop / 跨端 / 动画 / 导航 / 数据持久化 / 测试 / 性能 / a11y / i18n / CI-CD / 安全」Flutter 工程规范,以及一套「修复 / 新增 / 自测 / 文档 / 交付」的工程闭环框架 + 「环境 / 打包 / 性能」实战 SOP(默认 **60 个 skill**,均附官方出处;部分 skill 采用 [flutter 官方 skill](https://github.com/flutter/skills) 的结构,并用 [女娲 Skill 造人术](https://github.com/alchaincyf/nuwa-skill) 的五层蒸馏法提炼资深工程师“思维操作系统”——`flutter-skill-distillation` 把该蒸馏法本地化为可复用能力(支持“蒸馏指定专家”),并已蒸馏 5 位 Flutter 框架/实践专家为 `*-mindset` skill;19 个领域 skill 均补有精简的“心智模型 + 诚实边界”层;另有一组**代码领域**能力:地道写法 / 评审 / 重构 / 依赖养护 / 错误处理 / 代码生成 / 并发隔离区 / API 包设计 / 静态分析 / monorepo / 领域建模(让非法状态不可表达)/ 可测试性设计 / 异步与流;以及一组**平台 + 协议**能力:原生互操作(platform channel / Pigeon / FFI)、Android / iOS / 桌面三端工程层、通信协议(HTTP/gRPC/GraphQL/WebSocket/SSE/MQTT)与认证授权协议(OAuth2/OIDC/PKCE/JWT);还有一组**UI 识别与还原**能力:从设计稿/截图取色、字号等比换算、渐变方向识别、关键信息提取 → 落成 ColorScheme/TextTheme/ThemeData 主题,并有“设计稿→代码”端到端 playbook 与组件级还原范例库;以及一组**交付与运维**能力:CI/CD 深化(矩阵/缓存/产物归档/发布自动化)与可观测性(崩溃上报/日志/指标/追踪/行为分析);以及一项**通用思维**能力:`comprehensive-thinking` 全面思考(五重审视复杂判断框架,接入自 [comprehensive-thinking-skill](https://github.com/syzkillall/comprehensive-thinking-skill),Apache-2.0),在高复杂度/高代价/高不确定性的架构、策略与根因判断中强制大师理论体系 × 关键事实 × 最强反方 × 前提辩证分析 × 可验证收束)。
- 把用户的一句话需求,经多阶段流水线(分类 → 规格 → 架构 → 任务拆解 → 实现骨架 → 代码自检 → 验收 → 汇总 PRD),交给 任何 OpenAI 兼容模型去精炼(默认 DeepSeek v4 pro;可接 `deepseek-chat` / `deepseek-reasoner` / `gpt-4o` / Ollama 本地)。
- **反幻觉层**:架构阶段产出的所有第三方包会在 pub.dev API 上被验证,不存在 / 已废弃 / 版本超前的包会被标警并在 PRD 顶部贴 warning。
- **成本透明**:按 DeepSeek / OpenAI 公布价目实时估算 USD,累计到每个 stage 、整个运行以及 run history list。
- **幂等缓存**:同一需求 + 同一 skills + 同一参数 → 内容寻址 SHA-256 命中 `logs/runs.jsonl`,跳过上游调用返回原始运行。
- 流水线带 **JSON 自修复**(脟数据一次 `temperature=0` 重试)、**指数退避重试**(429 / 5xx 带 jitter)、**token 用量累计**、**运行历史落盘**。
- 通过 **FastAPI** 在本地暴露:
  - 标准 **OpenAPI 3.x** 文档(`/docs` 与 `/openapi.json`),可被任意 OpenAPI 客户端 / Swagger Codegen 调用;
  - **OpenAI 兼容** 接口 `/v1/chat/completions`,**支持 `stream=true` SSE**,直接被 OpenAI SDK / LangChain / IDE 插件接入;
  - 运行审计 `/v1/runs` 与 `/v1/runs/{id}`,任何调用过的需求都可重读；
  - **流式精炼** `/v1/refine/stream`:逐阶段 SSE 进度事件(开始/完成/耗时/token/成本),最后给出完整结果；
  - **选用解释** `/v1/skills/rank`:不花一个 token,dry-run 整套 skill 选用(得分/钉住/族去重/预算),调 ranker 时不再黑盒；
  - **聚合指标** `/v1/metrics`：总运行次数、累计 token / 成本、各阶段成功率、高频 skill；
  - **结构化日志**：`LOG_FORMAT=json` 可输出 JSON Lines，便于接入 Datadog / Loki / CloudWatch。

## 目录结构

```
flutterAgent/
├── README.md
├── requirements.txt
├── .env.example
├── run.sh                       # 一键启动 (venv + uvicorn)
├── scripts/
│   ├── refine_cli.py            # 命令行直接调用精炼流水线
│   └── export_openapi.py        # 导出 openapi.json 到磁盘
├── skills/                      # Markdown 形式的 skill / spec(60 个)
│   ├── task-refinement/SKILL.md
│   ├── comprehensive-thinking/SKILL.md       # 通用: 全面思考(五重审视复杂判断框架,Apache-2.0 引入)
│   ├── architecture-design/SKILL.md
│   ├── state-management/SKILL.md
│   ├── flutter-mobile/SKILL.md
│   ├── flutter-desktop/SKILL.md
│   ├── flutter-cross-platform/SKILL.md
│   ├── flutter-testing/SKILL.md
│   ├── flutter-performance/SKILL.md
│   ├── flutter-accessibility/SKILL.md       # 新增,WCAG/Apple HIG/Android a11y
│   ├── flutter-i18n/SKILL.md                # 新增,intl + ARB + gen-l10n
│   ├── flutter-ci-cd/SKILL.md               # 新增,flavors + fastlane + GH Actions
│   ├── flutter-security/SKILL.md            # OWASP MASVS + pinning + Play Integrity
│   ├── flutter-animation/SKILL.md           # 新增,动画系统 + Hero + Lottie/Rive + 性能
│   ├── flutter-navigation/SKILL.md          # go_router + deep link + 嵌套导航 + Tab 保活
│   ├── flutter-data-persistence/SKILL.md    # drift/sqflite/hive + 离线优先 + 迁移
│   ├── flutter-ai-integration/SKILL.md      # 新增,Genkit/GenUI/flutter_gemma/Firebase AI/MCP
│   ├── flutter-resource-lifecycle/SKILL.md   # 新增,大图/视频/多Controller 生命周期管理
│   ├── flutter-web/SKILL.md                  # 新增,CanvasKit/WASM/PWA/SEO/字体/部署
│   ├── flutter-network/SKILL.md              # 新增,Dio拦截器/Token刷新/WebSocket/离线队列
│   ├── flutter-engineering-workflow/SKILL.md # 工程交付总框架: 理解→修复/新增→自测→文档→交付
│   ├── flutter-feature-development/SKILL.md  # 新增功能 SOP: 垂直切片→契约先行→接线→灰度
│   ├── flutter-debugging/SKILL.md            # 修复 SOP: 复现→定位→最小改动→防回归
│   ├── flutter-verification/SKILL.md         # 自测门禁: format→analyze→test→build
│   ├── flutter-documentation/SKILL.md        # 文档 SOP: dartdoc/README/CHANGELOG/ADR
│   ├── flutter-environment-setup/SKILL.md    # 环境: SDK/工具链/doctor/fvm(官方 skill 格式)
│   ├── flutter-build-and-release/SKILL.md    # 打包: APK/AAB/IPA/桌面/Web + 签名/混淆(官方 skill 格式)
│   ├── flutter-performance-profiling/SKILL.md # 性能: profile/DevTools/jank/内存/体积(官方 skill 格式)
│   ├── flutter-engineer-mindset/SKILL.md     # 思维底座: 心智模型/决策启发式(女娲五层蒸馏)
│   ├── flutter-skill-distillation/SKILL.md   # 女娲蒸馏法(本地化): 在本项目内造/更新 mindset skill(含花名册)
│   ├── remi-rousselet-mindset/SKILL.md       # 框架专家: Remi Rousselet(Riverpod)思维
│   ├── felix-angelov-mindset/SKILL.md        # 框架专家: Felix Angelov(Bloc)思维
│   ├── tim-sneath-mindset/SKILL.md           # 框架专家: Tim Sneath(产品愿景)思维
│   ├── andrea-bizzotto-mindset/SKILL.md      # 实践专家: Andrea Bizzotto(应用架构)思维
│   ├── filip-hracek-mindset/SKILL.md         # 实践专家: Filip Hracek(实用主义)思维
│   ├── dart-language-idioms/SKILL.md         # 代码: Dart 地道写法(Effective Dart + Dart3 特性)
│   ├── flutter-code-review/SKILL.md          # 代码: 评审 SOP(看什么/红线/给反馈)
│   ├── flutter-refactoring/SKILL.md          # 代码: 安全重构(小步+测试护栏+常见手法)
│   ├── flutter-dependency-maintenance/SKILL.md # 代码: 依赖养护(pub upgrade/破坏性升级/dart fix)
│   ├── flutter-error-handling/SKILL.md       # 代码: 错误处理(Result/Either/错误边界/上报)
│   ├── flutter-codegen/SKILL.md              # 代码: 代码生成(build_runner/freezed/json/riverpod)
│   ├── flutter-concurrency-isolates/SKILL.md # 代码: 并发与隔离区(isolate/compute/Isolate.run)
│   ├── dart-api-package-design/SKILL.md      # 代码: API/包设计(公共 API/SemVer/pub 发布)
│   ├── flutter-static-analysis/SKILL.md      # 代码: 静态分析自动化(analysis_options/lints/custom_lint)
│   ├── flutter-monorepo-melos/SKILL.md       # 代码: 多包/monorepo(pub workspaces + melos)
│   ├── flutter-domain-modeling/SKILL.md      # 代码: 领域建模(让非法状态不可表达/状态机/值对象)
│   ├── flutter-testability-design/SKILL.md   # 代码: 可测试性设计(DI/接缝/纯核心/控时间随机)
│   ├── dart-async-streams/SKILL.md           # 代码: 异步与流(Future 组合/Stream/取消背压/zones)
│   ├── flutter-platform-channels/SKILL.md    # 平台: 原生互操作(MethodChannel/EventChannel/Pigeon/FFI)
│   ├── flutter-android-platform/SKILL.md     # 平台: Android 工程层(Gradle/Manifest/权限/R8/Play)
│   ├── flutter-ios-platform/SKILL.md         # 平台: iOS/Apple 工程层(Xcode/Info.plist/ATS/审核)
│   ├── flutter-desktop-platform/SKILL.md     # 平台: 桌面三端(Win/macOS/Linux 打包/签名/公证)
│   ├── flutter-network-protocols/SKILL.md    # 协议: HTTP/2·3/REST/gRPC/GraphQL/WebSocket/SSE/MQTT/TLS
│   ├── flutter-auth-protocols/SKILL.md       # 协议: OAuth2/OIDC/PKCE/JWT/刷新令牌/生物识别
│   ├── flutter-ui-from-image/SKILL.md        # UI: 读图成规格(取色/字号等比换算/渐变方向/关键信息)
│   ├── flutter-design-tokens-theming/SKILL.md # UI: 设计 token 工程化主题(ColorScheme/TextTheme/亮暗)
│   ├── flutter-design-to-code-playbook/SKILL.md # UI: 设计稿→代码端到端 playbook(S0→S8)
│   ├── flutter-ui-component-recipes/SKILL.md # UI: 组件级还原范例库(照图找 widget + 骨架)
│   ├── flutter-cicd-pipelines/SKILL.md       # 交付: CI/CD 深化(矩阵/缓存/产物归档/发布自动化)
│   └── flutter-observability/SKILL.md        # 运维: 可观测性(崩溃/日志/指标/追踪/分析)
├── logs/                        # runs.jsonl 自动写入(gitignored)
├── REFERENCES.md                # 全部官方/开源出处汇总
├── src/flutter_agent/
│   ├── main.py                  # FastAPI app
│   ├── config.py                # 环境变量配置
│   ├── schemas.py               # Pydantic 数据模型(RefineResponse / CostBreakdown / PackageValidation …)
│   ├── skill_loader.py          # 解析 SKILL.md(支持 YAML front-matter)
│   ├── deepseek_client.py       # OpenAI 兼容客户端 (retry + stream)
│   ├── pipeline.py              # 多阶段精炼流水线 (JSON 修复 + cost + cache + pub 验证)
│   ├── skill_ranker.py          # 智能 skill 选择: 关键词匹配 + token 预算裁剪
│   ├── stage_schemas.py         # 各阶段 JSON 输出期望 schema (松校验)
│   ├── log_setup.py             # text / JSON 结构化日志配置
│   ├── pricing.py               # 模型 USD 价目表 + 成本估算
│   ├── pub_validator.py         # pub.dev 包名/版本/废弃校验
│   ├── cache.py                 # 内容寻址缓存(SHA-256 over runs.jsonl)
│   ├── run_store.py             # 运行历史 JSONL 持久化
│   ├── deps.py                  # FastAPI DI 工厂
│   └── routes/
│       ├── refine.py            # POST /v1/refine
│       ├── ingest.py            # POST /v1/ingest  (HF + arXiv 吸收)
│       ├── skills.py            # /v1/skills + reload
│       ├── runs.py              # GET /v1/runs[/{id}]
│       ├── openai_compat.py     # POST /v1/chat/completions  (含 SSE)
│       └── metrics.py           # GET /v1/metrics  聚合统计
└── tests/                       # 80 测试用例 (全 pass)
    ├── test_smoke.py            # 端到端 smoke(无 API key)
    ├── test_pricing.py          # 成本估算单测
    ├── test_cache.py            # 缓存键 + JSONL 索引单测
    ├── test_pub_validator.py    # pub.dev mock 测试
    ├── test_retry.py            # 429/503 重试 + 400 不重试 monkeypatch
    ├── test_skill_ranker.py     # 关键词匹配 + token budget 裁剪
    ├── test_stage_schemas.py    # 阶段输出 schema 校验
    └── test_pipeline_integration.py  # 全流水线集成测试 (mock LLM)
```

## 快速开始

```bash
# 1. 克隆 / 进入目录
cd flutterAgent

# 2. 编辑环境变量
cp .env.example .env
# 在 .env 里填入 DEEPSEEK_API_KEY、DEEPSEEK_BASE_URL、DEEPSEEK_MODEL

# 3. 启动(自动建 venv、装依赖、起服务)
bash run.sh
```

启动后访问:

- Swagger UI:   <http://127.0.0.1:8765/docs>
- ReDoc:        <http://127.0.0.1:8765/redoc>
- OpenAPI JSON: <http://127.0.0.1:8765/openapi.json>

## 调用方式

### 1. 用 curl 直接调用精炼接口

```bash
curl -X POST http://127.0.0.1:8765/v1/refine \
  -H 'Content-Type: application/json' \
  -d '{
    "requirement": "做一个跨端的待办清单 App,支持本地存储和云同步",
    "platforms": ["mobile", "desktop"],
    "skills": ["flutter-cross-platform", "task-refinement", "state-management"]
  }'
```

返回结构化 JSON(规格 / 架构 / 任务树 / 验收标准 / 风险) + Markdown PRD + `validations[]`(pub.dev 校验结果) + `cost`(USD 估算)。

主要 flags:
- `use_cache: true` — 命中内容寻址缓存时跳过上游调用。
- `validate_packages: true` (默认) — 在 architecture 阶段后用 pub.dev API 验证每个推荐包。
- `review_max_iterations: 1` (默认) — **评审闭环**:当 review 阶段判定为 blocking 时,把 findings 回灌给 implementation 重产一版骨架并再次 review,最多迭代这么多次;`0` 关闭闭环(review 仅作建议)。实际迭代次数见返回的 `review_iterations`。
- `review_block_severity: "major"` (默认) — 触发闭环的最低严重度阈值:`major` 拦 blocker+major;`blocker` 只拦 blocker(最松);`minor` 连 minor 也拦(最严)。模型显式 `blocking=true` 不受此阈值影响,始终拦截。

**review findings 的两个来源**:除 LLM 自查外,review 还叠加一层**确定性结构自检**(纯 Python,不依赖模型),finding 带 `source: "static"`,即使模型自查漏了也能据此触发闭环:
- 每个 `lib/` 文件是否有测试桩(major)、breakdown 声明 `files_touched` 的文件是否都产出骨架(major)、文件路径是否落在 `architecture.directory_tree` 内(minor)
- 重复文件路径(major)、测试桩 `covers` 指向不存在文件(minor)、`depends_on` 悬空内部依赖(minor)

**审计与可观测**:
- `review_iterations` / `review_history[]` — 闭环每轮的 findings 计数(按严重度、按 llm/static 来源)与 blocking 标记。
- `acceptance_gaps[]` — acceptance 阶段的确定性交叉校验(任务缺验收标准、测试桩未被 test_plan 引用),仅作建议、不驱动闭环。
- 最终 Markdown PRD 末尾自动追加「闭环与自检审计」表格,无需依赖模型生成。

CLI 对应 flag:`--review-max-iterations`、`--review-block-severity`。

### 2. 用 OpenAI SDK 调用(OpenAI 兼容,支持流式)

```python
from openai import OpenAI
client = OpenAI(base_url="http://127.0.0.1:8765/v1", api_key="local")

# 阻塞模式
resp = client.chat.completions.create(
    model="flutter-agent",
    messages=[{"role": "user", "content": "做一个 PC 端的串口调试助手"}],
)
print(resp.choices[0].message.content)
print("usage:", resp.usage)

# SSE 流式
stream = client.chat.completions.create(
    model="flutter-agent",
    messages=[{"role": "user", "content": "做一个跨端待办 App"}],
    stream=True,
)
for chunk in stream:
    delta = chunk.choices[0].delta.content or ""
    print(delta, end="", flush=True)
```

> 把 `model` 换成 `deepseek-v4-pro` 等具体模型名,会绕过流水线直接透传到上游 — 同一个端口,既是「PRD 工厂」也是普通 chat 代理。

### 3. 命令行直接跑

```bash
# 普通调用
python scripts/refine_cli.py "做一个跨端的待办清单 App" \
    --platforms mobile,desktop --out out/todo-spec.md

# 把每个阶段的产物分别落盘 (out_dir/classify.json, spec.json, …, prd.md)
python scripts/refine_cli.py "做一个串口助手" -p desktop --out-dir out/serial/

# 只想看会发出哪些 prompt,不真正调上游
python scripts/refine_cli.py "做一个跨端 App" --dry-run
```

### 4. 由其他工具按 OpenAPI 自动生成 SDK

```bash
# 任何 openapi-generator-cli 即可
openapi-generator-cli generate \
  -i http://127.0.0.1:8765/openapi.json \
  -g typescript-fetch -o ./gen-sdk
```

## Skill 文件格式

每个 skill 是一个目录,内含一个 `SKILL.md`,顶部带 YAML front-matter:

```markdown
---
id: flutter-mobile
name: Flutter Mobile (iOS / Android) 工程规范
version: 1.0.0
platforms: [mobile]
tags: [flutter, mobile, android, ios]
applies_when: "需求目标平台包含 Android 或 iOS"
stage_hints: [spec, architecture, breakdown]
extends: []                                   # 本 skill 深化/特化了谁(可选)
see_also: [flutter-android-platform]          # 相关 skill 交叉引用(可选)
---

# Flutter Mobile 工程规范

## 目录结构
...

## 强制约束
...

## 输出要求
...
```

加载器会扫描 `skills/**/SKILL.md`,front-matter 进入 metadata,正文进入 system prompt。

### skill 之间的关系字段(`extends` / `see_also`)

随着 skill 增多,会出现**职责相邻**的 skill(如 `flutter-performance` 规则 vs
`flutter-performance-profiling` 工具)。两个关系字段让 ranker 和读者都知道分工:

- **`extends: [parent-id]`** — 声明"我是 parent 的深化/特化"。ranker 把
  `self + parent`(及传递闭包)视为**同一族**,在 token 预算内**只选族内最相关的那个**,
  避免父子两条一起挤占上下文。当前两族:`flutter-performance-profiling → flutter-performance`、
  `flutter-cicd-pipelines → flutter-ci-cd`。
- **`see_also: [other-id, ...]`** — 纯交叉引用(互补但不去重),如
  `flutter-network`(客户端实现)↔ `flutter-network-protocols`(协议选型)、
  `flutter-mobile` ↔ `flutter-android-platform`/`flutter-ios-platform`。
- 每个重叠 skill 的正文顶部都带一行 **「分工:本 skill 负责 X;Y 见 \`other\`」**,人和模型都不踩重复。

> 设计动机见 [`REFLECTION_redundancy_and_leverage.md`](REFLECTION_redundancy_and_leverage.md)。

### ranker 选用机制(`skill_ranker.py`)

1. **关键词打分**:在原有 unigram(CJK 单字 + 拉丁词)基础上,新增 **CJK bigram(双字)**
   评分——`协议`/`性能`/`打包` 作为整体匹配,不再因共享单字而误命中无关 skill;
   bigram 只取 `tags / applies_when / name` 等**策划过的元数据**,正文不参与,降噪更彻底。
2. **族去重**:见上,`extends` 同族在预算内只进最相关的一个。
3. **基础 skill 条件注入**:`architecture-design` / `state-management` 不再无条件置顶——
   仅当需求含**结构/状态信号**时才强制注入;**纯运维任务**(打包/签名/CI/性能剖析)不注入,
   把预算让给真正相关的 skill;完全无信号的通用需求才回退到注入两者(见 `pipeline._resolve_foundational_ids`)。

## 配置项(.env)

| 变量 | 说明 | 默认 |
|---|---|---|
| `DEEPSEEK_API_KEY` | API key | 必填 |
| `DEEPSEEK_BASE_URL` | OpenAI 兼容 base url | `https://api.deepseek.com/v1` |
| `DEEPSEEK_MODEL` | 主模型 | `deepseek-v4-pro` |
| `DEEPSEEK_PLANNER_MODEL` | 规划阶段模型 | 同上 |
| `LOCAL_API_KEY` | 本地 API 鉴权 token,空则关闭 | (空) |
| `HOST` / `PORT` | 监听地址 | `127.0.0.1` / `8765` |
| `SKILLS_DIR` | skills 目录 | `skills` |

## 流水线阶段

```
requirement
  └── [cache lookup]               — 命中则返回 cached=true,不动上游
  └── stage 1  classify              (识别目标平台 + 自适应选 skills)
       └── stage 2  spec               (用户故事 / 功能点 / 数据模型 / 接口)
            └── stage 3  architecture   (模块划分 / 状态管理 / 依赖选型)
                 └── [pub.dev validation]  — 对 architecture.third_party 逐个查 latest / discontinued
                 └── stage 4  breakdown      (Epic → Story → Task,带工时和验收)
                      └── stage 5  implementation (逼近代码的骨架:文件/接口签名/widget 树/数据模型/测试桩)
                           └── stage 6  review       (代码自检:LLM 按 code-review/static-analysis 红线 + 确定性结构自检 → findings + checklist)
                                └── [review 闭环]   — review blocking 时把 findings 回灌 implementation 重产并再 review(≤ review_max_iterations)
                                └── stage 7  acceptance (测试用例 + 风险清单)
                                     └── stage 8  markdown    (汇总人类阅读的 PRD,顶部 prepend 依赖告警)
  └── [cost & cache index]         — 写入 runs.jsonl + 增量索引 cache key
```

每一阶段把上一阶段的 JSON 输出 + 选中的 SKILL.md 作为 system prompt 喂给上游模型。

### 稳健性与工程机制

- **指数退避重试**:网络 / 408 / 425 / 429 / 5xx 自动重试,默认 3 次,base 0.6s + jitter。
- **JSON 自修复**:非 markdown 阶段若解析失败,自动用 `temperature=0` + JSON repair prompt 重调,`StageResult.repaired=true` 留痕。
- **幂等缓存**:`sha256(requirement ⋄ sorted(skill_ids) ⋄ stages ⋄ temperature ⋄ max_tokens ⋄ extra_context ⋄ model)`,命中不动上游。需求请求带 `use_cache: true` 才启用;默认 off,避免意外复用。
- **pub.dev 校验**:`architecture.third_party` 中每个 `{package, version}` 被 `GET https://pub.dev/api/packages/<name>` 验证;`exists=false` / `is_discontinued` / `constraint_ok=false` 会在 markdown 顶部加 warning块。关闭:请求带 `validate_packages: false`。
- **成本估算**:依据 [DeepSeek pricing](https://api-docs.deepseek.com/quick_start/pricing) 与 [OpenAI pricing](https://openai.com/api/pricing/),在 `src/flutter_agent/pricing.py` 里维护;可用 `PRICING_CONFIG=/path/to/pricing.json` 覆盖。运行结果包含 `cost.total_cost_usd`。
- **运行历史**:全量运行追加 `logs/runs.jsonl`,`GET /v1/runs?limit=N` 列表,`GET /v1/runs/{id}` 取详情。
- **流式**:`/v1/chat/completions` 支持 `stream=true`(SSE);agent 模式先跑完流水线再分块吐出最终 PRD。

### 诚实声明(不回避)

- **DEEPSEEK_MODEL=`deepseek-v4-pro`**:作为占位,在本仓库不被验证是实际可调型号;请根据你的账号换为 `deepseek-chat` / `deepseek-reasoner` / `gpt-4o` 等。估价默认按 V3 chat 价。
- **估价是 worst-case**:上游返回的 cache-hit 折扣未被计入(`prompt_tokens` 里不区分 cached / fresh),原因是 OpenAI 兼容接口不必然返回 cache_hit 字段。
- **pub.dev constraint 检查是轻量版**:只检 `^x.y.z` 与 pinned;纯范围 / git / path 依赖返回 `constraint_ok=null` 表示未评估。需要 full SemVer solver 请接 `pub_semver`。
- **所有 skill 里的「推荐」都是工程选型**,不是官方指定。Flutter 团队对 state mgmt / DI / 网络库保持中立;具体理由见 `REFERENCES.md`。

### 全部端点

| 方法 | 路径 | 用途 |
|---|---|---|
| `POST` | `/v1/refine` | 强类型流水线,返回 `RefineResponse`(含 `cost` / `validations` / `cache_key`) |
| `POST` | `/v1/refine/stream` | 同一条流水线,但以 **SSE** 推送进度:`pipeline_start` / `stage_start` / `stage_complete`(耗时/token/成本)/ `cache_hit` / `done`(完整 `RefineResponse`)/ `error`,以 `data: [DONE]` 结束 |
| `POST` | `/v1/ingest` | 持续吸收开源:发现 HF 模型 + arXiv 论文,可选 `scaffold`/`distill`,返回 `IngestResponse` |
| `POST` | `/v1/chat/completions` | OpenAI 兼容;agent / passthrough 双模;支持 SSE |
| `GET` | `/v1/skills` | 列出已加载 skill |
| `POST` | `/v1/skills/rank` | **选用 dry-run**(零模型调用):对给定需求返回每个 skill 的得分、是否入选、是否被基础 skill 钉住、族根与 token 估算,解释 ranker 为什么选了这些 |
| `GET` | `/v1/skills/{id}` | 取单个 skill(含 markdown body) |
| `POST` | `/v1/skills/reload` | 热重载磁盘上的 SKILL.md |
| `GET` | `/v1/runs?limit=N` | 列出最近 N 次运行(每项带 `cost` + `bad_packages`) |
| `GET` | `/v1/runs/{id}` | 取某次运行的完整 `RefineResponse` |
| `GET` | `/v1/metrics` | 聚合统计(总 runs、tokens、cost、阶段成功率、高频 skill) |
| `GET` | `/healthz` | 健康检查 |
| `GET` | `/openapi.json` | OpenAPI 3.x 规范 |
| `GET` | `/docs` / `/redoc` | Swagger UI / ReDoc |

## 蒸馏方法(女娲五层造 skill 法)

本项目用 [女娲 · Skill 造人术](https://github.com/alchaincyf/nuwa-skill) 的方法论,把"一位专家 / 一个主题怎么**想**"蒸馏成可加载的 **mindset skill**——蒸馏的是 *HOW they think*(认知操作系统),不是 *WHAT they said*(语录)。方法本身被封装进 `flutter-skill-distillation`,所以项目能**持续自我成长**:说一句"蒸馏 XX"就能按统一规范产出。

### 五层认知操作系统

每个 mindset skill 必须写齐五层:

| 层 | 回答的问题 | 在 SKILL.md 里的标题 |
|---|---|---|
| 怎么想 | 用什么**心智模型**看世界 | `## 核心心智模型`(3–7 个,各带 一句话 / 依据 / 应用 / 局限) |
| 怎么判断 | 用什么**决策启发式** | `## 决策启发式`(5–10 条,各带 应用场景 / 案例) |
| 怎么说话 | **表达 DNA** | `## 表达 DNA` |
| 什么不做 | **反模式 / 价值观底线** | `## 价值观与反模式` |
| 知道局限 | **诚实边界** | `## 诚实边界`(做不到什么 + 调研截止日期) |

### 三重验证(决定一个观点能否被收录为"心智模型")

1. **跨领域**:在 2+ 个不同场景出现过,不是随口一说。
2. **有预测力**:能据此推断该专家对一个**新问题**的立场。
3. **有排他性**:不是所有聪明人都会这么想(有区分度)。

### 蒸馏一位指定专家(Phase 1–4)

1. **Phase 1 采集**:对人物,覆盖其开源源码 / 演讲 / 文章 / 争议;对主题,覆盖官方文档 + 权威实践 + 反面案例。
2. **Phase 2 提炼**:候选观点过三重验证,不过则降级或丢弃。
3. **Phase 3 构建**:填入五层 + 本项目加载器所需 front-matter(`id` = 目录名 = `<name>-mindset`,`platforms` ⊆ {all,mobile,desktop,web},`stage_hints` ⊆ {classify,spec,architecture,breakdown,implementation,review,acceptance,markdown}),落地 `skills/<name>-mindset/SKILL.md`。
4. **Phase 4 验证**:用 3 个该专家公开回答过的问题测方向一致;用 1 个他没讨论过的问题测"适度不确定"(防过拟合)。
5. **登记 + 自检**:在 `flutter-skill-distillation` 花名册、`README.md`、`REFERENCES.md` 同步,并在 `tests/test_distillation_and_lenses.py` 的 `EXPERT_SKILLS` 加一行;`pytest` 绿 + `/healthz` skill 数 +1。

> **反幻觉红线**:人物 mindset 只蒸馏**有公开出处**的"思维方式",`诚实边界` 必须声明"这是镜片不是本人 + 时点快照"。无出处不写。

### 已蒸馏花名册

| 类型 | skill | 对象 | 一句话镜片 |
|---|---|---|---|
| 通用底座 | `flutter-engineer-mindset` | 资深 Flutter 工程师 | 约束链 / UI=f(state) / 两条线程 / 状态归属 / 平台在边界 |
| 框架专家 | `remi-rousselet-mindset` | Remi Rousselet(Riverpod) | 错误前移编译期;异步三态一体;状态是可组合缓存 |
| 框架专家 | `felix-angelov-mindset` | Felix Angelov(Bloc) | event→state 单向;分层单一职责;可测试是设计目标 |
| 框架专家 | `tim-sneath-mindset` | Tim Sneath(前产品负责人) | 四支柱;一套代码处处一流体验;DX 即产品 |
| 实践专家 | `andrea-bizzotto-mindset` | Andrea Bizzotto(Code With Andrea) | 没有银弹但有分层骨架;组合;单向数据流 |
| 实践专家 | `filip-hracek-mindset` | Filip Hracek(前 DevRel) | 实用主义;状态管理是连续谱;能讲清才是好方案 |

此外,19 个领域 skill 均补有精简的"心智模型(镜片)+ 诚实边界"层,与上述底座交叉链接。方法论与全部出处见 [`REFERENCES.md` §13](./REFERENCES.md)。

## 持续吸收开源(ingestion)

让 skill 库能持续从开源生态学习——抓取**开发/代码方向**的开源信号,而不是把一切塞进来。

- **来源(自行查询公开 API)**:Hugging Face Hub 模型、arXiv 论文。纯 HTTP,关键词过滤到 code/agent/flutter/dart 等开发主题;对 429/5xx 有退避重试,单源失败不影响其余(arXiv 对云 IP 限流较严,失败会标 `sources: arxiv=FAIL` 并继续)。
- **只报新增**:`data/ingestion_seen.json` 记录已见条目,每次运行只高亮新出现的(`is_new`)。
- **脚手架而非成品**:命中可一键生成**带出处**的 `SKILL.md` 草稿(front-matter + 来源 + 五层 TODO),供后续按 `flutter-skill-distillation` 填充。
- **诚实边界**:抓取+脚手架**不花模型 token**;把草稿蒸馏成成熟 skill 的"认知内容"那一步**需要一次模型运行(算力/token)**。"持续"需把命令挂到定时任务,服务本身不会自动后台轮询。

```bash
# 用默认 watch-list 发现并记录已见
python scripts/ingest_cli.py discover

# 自定义查询、只看新增、写 JSON、不更新 seen-store(干跑)
python scripts/ingest_cli.py discover -q "code agent" -q "dart" \
    --json out/digest.json --only-new --no-commit

# 把新增条目生成草稿到 skills/(草稿目录已 gitignore,需人工填充+登记后才纳入)
python scripts/ingest_cli.py discover --only-new --scaffold-dir skills

# 一键调底层模型把草稿填成成熟 skill(★会花 token,需 DEEPSEEK_API_KEY;--max-distill 限流)
python scripts/ingest_cli.py discover --only-new --scaffold-dir skills \
    --distill --max-distill 3

# 持续(cron 每天一次,落每日 digest)
# 0 7 * * *  cd /path/to/flutterAgent && .venv/bin/python scripts/ingest_cli.py \
#            discover --only-new --json data/digests/$(date +\%F).json
```

也可走 HTTP(同一能力,接进服务):`POST /v1/ingest`。**发现 + 草稿 0 token**;`distill=true` 才调底层模型(花 token,需 `DEEPSEEK_API_KEY`,模型出错回 502)。

```bash
# 只发现(返回 IngestResponse.digest;不写盘、不动 seen-store)
curl -X POST http://127.0.0.1:8765/v1/ingest \
  -H 'Content-Type: application/json' \
  -d '{"queries":["code generation"],"sources":["hf","arxiv"],"limit":5}'

# 发现 + 生成草稿到指定目录 + 持久化 seen-store(下次只报新增)
curl -X POST http://127.0.0.1:8765/v1/ingest \
  -H 'Content-Type: application/json' \
  -d '{"only_new":true,"scaffold":true,"scaffold_dir":"skills","commit":true}'

# ★ 调模型把草稿填成成熟 skill(花 token;max_distill 限流;无 key 返回 400)
curl -X POST http://127.0.0.1:8765/v1/ingest \
  -H 'Content-Type: application/json' \
  -d '{"only_new":true,"distill":true,"max_distill":3,"scaffold_dir":"skills"}'
```

请求字段:`queries`(默认内置 watch-list)、`sources`(`hf`/`arxiv`)、`limit`、`only_new`、`scaffold`、`distill`、`max_distill`、`scaffold_dir`(默认服务 skills 目录,不覆盖已存在文件)、`commit`(默认 `false`,只读)。

## 所有 Skills

| ID | 主题 | 依据主要源 |
|---|---|---|
| `task-refinement` | 需求精炼流水线的元 SOP | Atlassian / BDD / INVEST |
| `comprehensive-thinking` | 通用·全面思考:五重审视 / 大师理论体系 / 最强反方 / 前提辩证分析 / 可验证收束 | github.com/syzkillall/comprehensive-thinking-skill(Apache-2.0) |
| `architecture-design` | Clean Architecture / feature-first | docs.flutter.dev/app-architecture |
| `state-management` | Riverpod vs BLoC 选型 | docs.flutter.dev/data-and-backend/state-mgmt |
| `flutter-mobile` | iOS / Android 工程规范 | flutter.dev + pub.dev |
| `flutter-desktop` | Windows / macOS / Linux | docs.flutter.dev/platform-integration/desktop |
| `flutter-cross-platform` | 跨端适配 / `flutter_adaptive_scaffold` | docs.flutter.dev/ui/adaptive-responsive + M3 |
| `flutter-testing` | 测试金字塔 / `flutter_test` / `mocktail` | docs.flutter.dev/testing |
| `flutter-performance` | 帧预算 / Impeller / `--analyze-size` | docs.flutter.dev/perf |
| `flutter-accessibility` | WCAG AA / Semantics / a11y guideline | docs.flutter.dev/ui/.../accessibility |
| `flutter-i18n` | `flutter_localizations` + ARB + gen-l10n | docs.flutter.dev/ui/.../internationalization |
| `flutter-ci-cd` | flavors / fastlane / GitHub Actions / 隐私清单 | docs.flutter.dev/deployment |
| `flutter-security` | OWASP MASVS / pinning / Play Integrity / GDPR | flutter.dev + OWASP + Apple/Google |
| `flutter-animation` | 隐式/显式动画 / Hero / Lottie / Rive / 性能 | docs.flutter.dev/ui/animations + M3 motion |
| `flutter-navigation` | go_router / deep link / 嵌套导航 / Tab 保活 | docs.flutter.dev/ui/navigation |
| `flutter-data-persistence` | drift / sqflite / hive_ce / 离线优先 / 迁移 | docs.flutter.dev/cookbook/persistence + drift.simonbinder.eu |
| `flutter-ai-integration` | Genkit Dart / GenUI / flutter_gemma / Firebase AI / Agentic Hot Reload | pub.dev + github.com/flutter/skills |
| `flutter-resource-lifecycle` | 大图内存 / 视频 Controller 切换 / 多 TextController / dispose / leak_tracker | docs.flutter.dev/tools/devtools/memory + perf |
| `flutter-web` | CanvasKit / SkWasm / PWA / SEO / 字体加载 / --base-href / CORS | docs.flutter.dev/deployment/web + renderers |
| `flutter-network` | Dio 拦截器链 / Token 刷新竞态 / WebSocket 重连 / 离线队列 / GraphQL / gRPC | docs.flutter.dev/networking + pub.dev/dio |
| `flutter-engineering-workflow` | 工程交付总框架:理解→修复/新增→自测→文档→交付 | docs.flutter.dev/testing + Conventional Commits |
| `flutter-feature-development` | 新增功能 SOP:垂直切片 / 契约先行 / 接线 / 灰度 | docs.flutter.dev/app-architecture |
| `flutter-debugging` | 修复 SOP:复现→定位根因→最小改动→防回归 | docs.flutter.dev/testing/debugging + DevTools |
| `flutter-verification` | 自测门禁:format → analyze → test → build | dart.dev/tools + docs.flutter.dev/testing |
| `flutter-documentation` | 文档 SOP:dartdoc / README / CHANGELOG / ADR | dart.dev/effective-dart/documentation + Keep a Changelog |
| `flutter-environment-setup` | 环境:SDK / 平台工具链 / `flutter doctor` / fvm | docs.flutter.dev/get-started/install + fvm.app |
| `flutter-build-and-release` | 打包:APK/AAB/IPA/桌面/Web + 签名 / flavors / 混淆 | docs.flutter.dev/deployment + obfuscate |
| `flutter-performance-profiling` | 性能:profile 模式 / DevTools / jank / 内存 / 体积 | docs.flutter.dev/perf + tools/devtools |
| `flutter-engineer-mindset` | 思维底座:7 心智模型 + 8 决策启发式 + 反模式 + 诚实边界 | docs.flutter.dev + nuwa-skill 五层蒸馏 |
| `flutter-skill-distillation` | 女娲蒸馏法本地化:五层 + 三重验证,造/更新 mindset skill(含花名册) | nuwa-skill + 本项目加载器约定 |
| `remi-rousselet-mindset` | 框架专家·Remi Rousselet:错误前移编译期 / 异步三态 / 可组合缓存 | riverpod.dev + nuwa-skill |
| `felix-angelov-mindset` | 框架专家·Felix Angelov:event→state 单向 / 分层 / 可测 | bloclibrary.dev + nuwa-skill |
| `tim-sneath-mindset` | 框架专家·Tim Sneath:四支柱 / 一套代码处处一流 / DX 即产品 | Flutter keynote + nuwa-skill |
| `andrea-bizzotto-mindset` | 实践专家·Andrea Bizzotto:分层骨架 / 组合 / 单向数据流 | codewithandrea.com + nuwa-skill |
| `filip-hracek-mindset` | 实践专家·Filip Hracek:实用主义 / 状态管理连续谱 / 能讲清 | Google I/O talks + nuwa-skill |
| `dart-language-idioms` | 代码·Dart 地道写法:Effective Dart + records/patterns/sealed/extension types | dart.dev/effective-dart + dart.dev/language |
| `flutter-code-review` | 代码·评审 SOP:看什么 / 红线清单 / 怎么给反馈 | google.github.io/eng-practices/review |
| `flutter-refactoring` | 代码·安全重构:小步 + 测试护栏 + 常见手法 + 绞杀者模式 | refactoring.com + martinfowler.com |
| `flutter-dependency-maintenance` | 代码·依赖养护:pub outdated/upgrade / 破坏性升级 / dart fix / SemVer | dart.dev/tools/pub + semver.org |
| `flutter-error-handling` | 代码·错误处理:Result/Either vs 异常 / 错误边界 / 日志上报 | docs.flutter.dev/testing/errors + dart.dev |
| `flutter-codegen` | 代码·代码生成:build_runner / freezed / json_serializable / riverpod_generator | pub.dev + docs.flutter.dev/.../serialization/json |
| `flutter-concurrency-isolates` | 代码·并发与隔离区:isolate / compute / Isolate.run / 消息传递 / 避免卡 UI | dart.dev/language/concurrency + api.flutter.dev/.../compute |
| `dart-api-package-design` | 代码·API/包设计:公共 API 稳定性 / SemVer / pub 发布 | dart.dev/effective-dart/design + dart.dev/tools/pub/publishing |
| `flutter-static-analysis` | 代码·静态分析自动化:analysis_options / lint 规则集 / custom_lint | dart.dev/tools/analysis + dart.dev/tools/linter-rules |
| `flutter-monorepo-melos` | 代码·多包/monorepo:pub workspaces + melos 编排与发版 | dart.dev/tools/pub/workspaces + melos.invertase.dev |
| `flutter-domain-modeling` | 代码·领域建模:让非法状态不可表达 / sealed 状态机 / 值对象与不变量 | dart.dev/language/class-modifiers + dart.dev/language/patterns |
| `flutter-testability-design` | 代码·可测试性设计:依赖注入 / 接缝 / 纯函数核心 / 控时间与随机 | docs.flutter.dev/testing/overview + pub.dev/packages/clock |
| `dart-async-streams` | 代码·异步与流:Future 组合 / Stream / async* / 取消与背压 / zones | dart.dev/libraries/async/async-await + dart.dev/libraries/async/using-streams |
| `flutter-platform-channels` | 平台·原生互操作:MethodChannel / EventChannel / Pigeon / dart:ffi | docs.flutter.dev/platform-integration/platform-channels + pub.dev/packages/pigeon |
| `flutter-android-platform` | 平台·Android 工程层:Gradle / Manifest / 权限 / R8 / Play | developer.android.com/build/shrink-code + developer.android.com/google/play/requirements/target-sdk |
| `flutter-ios-platform` | 平台·iOS/Apple 工程层:Xcode / Info.plist / ATS / 权限串 / 审核 | docs.flutter.dev/deployment/ios + developer.apple.com/app-store/review/guidelines |
| `flutter-desktop-platform` | 平台·桌面三端:Win/macOS/Linux 打包 / 签名 / 公证 | docs.flutter.dev/platform-integration/desktop + developer.apple.com notarization |
| `flutter-network-protocols` | 协议·通信协议全景:HTTP/2·3 / REST / gRPC / GraphQL / WebSocket / SSE / MQTT / TLS | grpc.io + graphql.org + mqtt.org + developer.mozilla.org |
| `flutter-auth-protocols` | 协议·认证授权:OAuth2 / OIDC / PKCE / JWT / 刷新令牌 / 生物识别 | oauth.net/2 + openid.net + datatracker.ietf.org/doc/html/rfc7636 |
| `flutter-ui-from-image` | UI·读图成规格:取色 / 字号等比换算 / 渐变方向 / 关键信息提取 | api.flutter.dev/.../MediaQuery + docs.flutter.dev/ui/adaptive-responsive + api.flutter.dev/.../Gradient |
| `flutter-design-tokens-theming` | UI·设计 token 主题:ColorScheme / TextTheme / ThemeData / 亮暗双主题 | docs.flutter.dev/cookbook/design/themes + m3.material.io/styles/color |
| `flutter-design-to-code-playbook` | UI·设计稿→代码端到端 SOP:S0 对齐 → S8 比对交付 | docs.flutter.dev/cookbook/testing/widget + matchesGoldenFile |
| `flutter-ui-component-recipes` | UI·组件还原范例:常见 UI → widget + 代码骨架 + 易错点 | docs.flutter.dev/ui/widgets/material + m3.material.io/components |
| `flutter-cicd-pipelines` | 交付·CI/CD 深化:构建矩阵 / 缓存 / 产物归档 / 发布自动化 | docs.github.com/actions + docs.flutter.dev/deployment/cd + docs.fastlane.tools |
| `flutter-observability` | 运维·可观测性:崩溃上报 / 结构化日志 / 指标 / 追踪 / 行为分析 | firebase.google.com/docs/crashlytics + docs.sentry.io/platforms/flutter + opentelemetry.io |

> 标「官方 skill 格式」的 skill 采用 [flutter/skills](https://github.com/flutter/skills) 的结构(`Contents / Core Concepts / Workflow + Task Progress / Conditional Logic / Examples / Troubleshooting`),同时保留本项目加载器所需的 front-matter 字段。

完整出处列表见 [`REFERENCES.md`](./REFERENCES.md)。

## 许可

MIT.
