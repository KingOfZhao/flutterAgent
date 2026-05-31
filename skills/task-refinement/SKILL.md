---
id: task-refinement
name: 需求到任务的精炼方法
version: 1.0.0
platforms: [all]
tags: [process, prd, task, breakdown]
applies_when: 任何阶段都启用
stage_hints: [classify, spec, breakdown, acceptance]
---

# 需求精炼 SOP

你的目标:把用户一句话需求 → 可执行的 Flutter 工程任务清单。

## 阶段 0:分类 (classify)

读完用户需求,输出一个 JSON:

```json
{
  "title": "<≤ 20 字的项目名>",
  "one_liner": "<一句话产品定义>",
  "platforms": ["mobile" | "desktop" | "web", ...],
  "primary_users": ["..."],
  "core_value": "<对用户最大的 1 件事>",
  "non_goals": ["<刻意不做的事>", "..."],
  "recommended_skills": ["flutter-mobile", "flutter-desktop", ...],
  "complexity": "S" | "M" | "L" | "XL",
  "confidence": 0.0 ~ 1.0,
  "open_questions": ["<必须澄清才能继续的问题>", "..."]
}
```

判定平台优先看用户原文里的关键词:
- 出现「App / 手机 / iOS / Android / 微信」→ mobile
- 出现「PC / 桌面 / Windows / Mac / 客户端 / 工具软件 / 串口 / 蓝牙(BLE 桌面)」→ desktop
- 出现「网页 / H5 / 后台管理」→ web
- 无明显倾向时默认 mobile,但 `open_questions` 必须问清楚

## 阶段 1:规格 (spec)

产出标准 PRD,字段:

```json
{
  "overview": {
    "background": "...",
    "goals": ["..."],
    "success_metrics": [{"name": "...", "target": "..."}]
  },
  "personas": [{"name": "...", "needs": "..."}],
  "user_stories": [
    {"id": "US-001", "as_a": "...", "i_want": "...", "so_that": "...", "priority": "P0|P1|P2"}
  ],
  "features": [
    {
      "id": "F-001",
      "name": "...",
      "stories": ["US-001"],
      "description": "...",
      "ui_sketch": "<文字描述 wireframe>",
      "edge_cases": ["..."]
    }
  ],
  "data_model": [
    {"entity": "Todo", "fields": [{"name": "id", "type": "String", "notes": "uuid"}]}
  ],
  "apis": [
    {"method": "POST", "path": "/todos", "req": {...}, "resp": {...}, "errors": ["401","409"]}
  ]
}
```

要求:
- 每个 user story 都至少链到一个 feature
- 每个 feature 都至少有 1 个 edge case
- 不发明用户没提的功能;若有强假设,放入 `assumptions` 数组
- 数据模型字段必须给类型和约束

## 阶段 2:架构 (architecture)

```json
{
  "tech_stack": {"flutter": "3.22", "dart": "3.4", "state": "riverpod", ...},
  "modules": [
    {"name": "auth", "responsibility": "...", "depends_on": ["core/network"]}
  ],
  "state_management": "<策略,引用 state-management skill>",
  "directory_tree": "<ASCII tree>",
  "platform_adapters": [
    {"capability": "notification", "mobile": "...", "desktop": "..."}
  ],
  "third_party": [{"package": "dio", "version": "^5.4.0", "reason": "..."}]
}
```

每个第三方库必须给「为什么选它」。

## 阶段 3:任务拆解 (breakdown)

按 Epic → Story → Task 三级:

```json
{
  "epics": [
    {
      "id": "E-001",
      "name": "账号体系",
      "stories": [
        {
          "id": "S-001",
          "name": "邮箱注册登录",
          "feature_ref": "F-002",
          "tasks": [
            {
              "id": "T-001",
              "name": "实现 AuthRepository (dio + secure storage)",
              "type": "code" | "test" | "design" | "infra" | "doc",
              "estimate_hours": 4,
              "depends_on": [],
              "acceptance": ["登录成功后 token 写入 secure storage", "401 自动跳登录页"],
              "files_touched": ["lib/features/auth/data/auth_repository.dart"]
            }
          ]
        }
      ]
    }
  ]
}
```

要求:
- 任何一个 task 工时 ≤ 8h,超出必须再拆
- `files_touched` 用真实路径,符合 architecture 阶段定义的目录树
- 每个 task **必须** 有 ≥ 1 条 `acceptance`(可被测试验证)
- `depends_on` 用 task id,不能成环

## 阶段 4:验收与风险 (acceptance)

```json
{
  "acceptance_matrix": [
    {"story_id": "S-001", "scenario": "...", "given": "...", "when": "...", "then": "..."}
  ],
  "test_plan": {
    "unit": [{"target": "AuthRepository.login", "cases": ["..."]}],
    "widget": [...],
    "integration": [...]
  },
  "risks": [
    {"id": "R-001", "desc": "...", "likelihood": "L|M|H", "impact": "L|M|H", "mitigation": "..."}
  ],
  "milestones": [
    {"name": "M1: MVP", "stories": ["S-001","S-002"], "weeks": 2}
  ]
}
```

## 通用规则

- 输出 **必须** 是合法 JSON(除非显式要求 markdown);不要包 ```json``` 围栏外的解释
- 中文需求 → 字段值中文,字段 key 始终英文
- 不要省略字段,空值用 `[]` 或 `""`
- 一切估算给区间也接受,如 `"estimate_hours": 4` 或 `{"min":3,"max":6}`

## 参考 / References

- Atlassian 用户故事写法(`as a / I want / so that`):<https://www.atlassian.com/agile/project-management/user-stories>
- Mike Cohn《User Stories Applied》— 行业标准用户故事方法
- Behavior-driven Development(BDD,Given/When/Then):<https://cucumber.io/docs/bdd/>
- Scaled Agile Epic → Capability → Feature → Story 层级:<https://scaledagileframework.com/epic/>
- 估算技术(Planning Poker、T-shirt sizing):<https://www.mountaingoatsoftware.com/agile/planning-poker>
- INVEST 原则(用户故事质量):<https://en.wikipedia.org/wiki/INVEST_(mnemonic)>
- 验收标准模板(Given/When/Then):<https://www.agilealliance.org/glossary/acceptance/>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **需求要可证伪**:用 Given/When/Then 把“做完”写成可断言句子。
- **INVEST 切分**:每个故事独立、可测、小到能在一个迭代完成。
- **不确定性显式化**:估算带区间与假设,而非单点承诺。

**诚实边界:**

- 估算是概率不是承诺;范围/优先级最终是产品决策。
- 本 skill 规范“怎么写需求”,不替你做需求取舍。
