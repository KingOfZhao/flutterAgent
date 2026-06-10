---
name: flutter-skill-distillation
description: |
  在本项目内"造 skill"的方法论——把一位 Flutter 专家 / 一个工程主题蒸馏成可加载的 mindset skill。
  改写自"女娲 · Skill 造人术"(https://github.com/alchaincyf/nuwa-skill)的五层认知操作系统 + 三重验证,
  并对齐本项目的加载器约定(front-matter)与反幻觉规则(每条主张落到官方出处)。
  触发:当用户说「蒸馏 XX」「造一个 XX 的 skill」「把 XXX 的思维写进来」「更新 XX 的 mindset」「女娲」时使用。
id: flutter-skill-distillation
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [meta, distillation, nuwa, mindset, methodology, growability, skill-authoring, 女娲]
applies_when: 需要在本项目内新建 / 更新一个"思维型(mindset)"skill,或把某人/某主题的认知框架蒸馏入库
stage_hints: [architecture]
---
# 在本项目内蒸馏 mindset skill(女娲方法论·本地化)

> "蒸馏的是 HOW they think,不是 WHAT they said。一个不告诉你局限在哪的 skill,不值得信任。"
> —— 改写自 [女娲 · Skill 造人术](https://github.com/alchaincyf/nuwa-skill)

## Contents

- [核心理念](#核心理念)
- [何时触发](#何时触发)
- [Workflow](#workflow)
  - [Phase 1:采集(多路并行)](#phase-1采集多路并行)
  - [Phase 2:提炼(三重验证)](#phase-2提炼三重验证)
  - [Phase 3:构建(五层 + 本项目 front-matter)](#phase-3构建五层--本项目-front-matter)
  - [Phase 4:验证(质量门禁)](#phase-4验证质量门禁)
- [产物模板](#产物模板)
- [成长性约定](#成长性约定可读快速可演进)
- [Troubleshooting](#troubleshooting)
- [References](#references)

## 核心理念

女娲不复制人,**提炼认知操作系统**。一个好的 mindset skill 是一套可运行的镜片 + 直觉规则,五层:

| 层 | 问题 | 在 skill 里的体现 |
|---|---|---|
| 怎么想 | 用什么**心智模型**看世界 | `## 核心心智模型`(3–7 个,各带 一句话/依据/应用/局限) |
| 怎么判断 | 用什么**决策启发式** | `## 决策启发式`(5–10 条,各带 应用场景/案例) |
| 怎么说话 | **表达 DNA** | `## 表达 DNA` |
| 什么不做 | **反模式 / 价值观底线** | `## 价值观与反模式` |
| 知道局限 | **诚实边界** | `## 诚实边界` |

本项目额外要求(与女娲叠加):**每条工程主张都要能落到 `REFERENCES.md` 的官方出处**(反幻觉),且 front-matter 必须满足加载器(见 Phase 3)。

## 何时触发

| 用户输入 | 路径 |
|---|---|
| 明确人名/主题(「蒸馏 Remi Rousselet」「造一个状态管理 mindset」) | 直接进入 Workflow |
| 模糊需求(「我想让 AI 更懂 Flutter 性能取舍」) | 先用一句话把需求定位到一个主题,再进入 Workflow |

## Workflow

**Task Progress:**

- [ ] Phase 1 采集:六路素材已归档(著作/演讲/源码/issue/批评/时间线)
- [ ] Phase 2 提炼:每个候选心智模型过三重验证
- [ ] Phase 3 构建:五层写齐 + front-matter 合规 + 出处齐全
- [ ] Phase 4 验证:3 个已知问题方向一致 + 1 个未讨论问题表现"适度不确定"
- [ ] 入库:`pytest` 绿 + 服务 `/healthz` skill 计数 +1 + README/REFERENCES 已登记

### Phase 1:采集(多路并行)

对"人物"蒸馏,尽量覆盖六路一手/二手素材;对"主题"蒸馏,覆盖官方文档 + 权威实践 + 反面案例:

1. 一手产出:本人的书/博客/演讲/**开源源码与 commit/issue 评论**(对工程师极重要)。
2. 访谈 / 播客 / 大会 talk。
3. 社交媒体长贴(X / 知乎 / 公众号)。
4. **批评者视角**(争议、被反驳的观点)——避免只收录"粉丝叙事"。
5. 决策记录(他在真实项目里怎么取舍)。
6. 时间线(观点的演化,标注"截止日期")。

> 条件逻辑:**有本地一手语料(PDF/transcript/源码)→ 优先用它,质量高于网络搜索**;无 → 走联网检索并标注来源。

### Phase 2:提炼(三重验证)

一个观点要被收录为"心智模型",必须三条全过,否则降级为普通建议或丢弃:

1. **跨领域**:在 2+ 个不同场景/项目里出现过(不是随口一说)。
2. **有预测力**:能据此推断他对一个**新问题**的立场。
3. **有排他性**:不是所有聪明人都会这么想(有区分度)。

### Phase 3:构建(五层 + 本项目 front-matter)

把通过验证的内容填入[产物模板](#产物模板):3–7 心智模型 + 5–10 决策启发式 + 表达 DNA + 价值观/反模式 + 诚实边界。

**front-matter 必须满足本项目加载器**(否则不会被加载/排序):

- 必填:`id`(= 目录名,kebab-case)、`name`、`version`、`platforms`、`tags`、`applies_when`、`stage_hints`。
- `platforms` ⊆ `{all, mobile, desktop, web}`;`stage_hints` ⊆ `{classify, spec, architecture, breakdown, acceptance, markdown}`(无关阶段别乱填,避免被注入到不相干流水线阶段)。
- 可叠加女娲风格的多行 `description`(加载器会忽略多余字段,但利于人读与跨 runtime 复用)。
- 文件路径:`skills/<id>/SKILL.md`。

### Phase 4:验证(质量门禁)

1. **方向一致**:拿 3 个该对象/主题**公开回答过**的问题测试,skill 给出的判断方向应与其真实立场一致。
2. **适度不确定**:再拿 1 个他**没讨论过**的问题,skill 应表现出"适度不确定"而非斩钉截铁——否则就是过拟合/幻觉。
3. **可加载**:`SkillRegistry.reload()` 不报 front-matter / 重复 id 错误;`/v1/skills/<id>` 能取到。
4. **出处齐全**:每条工程主张在 `REFERENCES.md` 有对应官方链接。

## 产物模板

```markdown
---
name: <person-or-topic>-mindset
description: |
  <对象> 的思维框架……(含触发词)
id: <person-or-topic>-mindset
version: 1.0.0
platforms: [all]            # 或按平台收窄
tags: [mindset, ...]
applies_when: 需要 <对象> 视角的工程判断与取舍
stage_hints: [architecture]  # 按真实相关阶段填
---
# <对象> · 思维操作系统
> <一句最能代表其思维的话>

## 使用说明           # 这是框架不是本人;不替代实测/业务取舍
## 核心心智模型        # 3–7 个,各:一句话 / 依据(官方出处)/ 应用 / 局限
## 决策启发式          # 5–10 条,各:应用场景 / 案例
## 表达 DNA            # 语气/节奏/用词/确定性/引用习惯
## 价值观与反模式       # 我追求的 / 我拒绝的 / 我也没想清楚的
## 诚实边界            # 做不到什么 + 调研截止日期
## 参考 / References    # 一手/二手来源 + 关键引用
```

参照实现:`flutter-engineer-mindset`(通用底座),以及下面花名册里的专家 mindset skill。

## 蒸馏指定专家(按需,一等能力)

当用户说「蒸馏 XX」时,这是标准入口:

1. 定身份:是**人物**(框架作者/布道者)还是**主题/实践**(性能、架构…)。
2. 跑 Phase 1–4(见上),人物务必覆盖其**开源源码 / 演讲 / 文章 / 争议**。
3. 落地为 `skills/<name>-mindset/SKILL.md`,id = `<name>-mindset`,五层齐全 + 出处齐全。
4. 在下面花名册登记一行;在 `README.md` / `REFERENCES.md` 同步;为它加一条测试(`tests/test_distillation_and_lenses.py` 的 EXPERT 列表)。
5. 自检:`pytest` 绿 + `/healthz` skill 数 +1。

> 反幻觉红线:人物 mindset 只蒸馏**有公开出处**的"思维方式",并在`诚实边界`声明"这是镜片不是本人 + 时点快照"。无出处不写。

### 已蒸馏花名册

| 类型 | skill id | 对象 | 一句话镜片 |
|---|---|---|---|
| 通用底座 | `flutter-engineer-mindset` | 资深 Flutter 工程师 | 约束链 / UI=f(state) / 两条线程 / 状态归属 / 平台在边界 |
| 框架专家 | `remi-rousselet-mindset` | Remi Rousselet(Riverpod) | 错误前移编译期;异步三态一体;状态是可组合缓存 |
| 框架专家 | `felix-angelov-mindset` | Felix Angelov(Bloc) | event→state 单向;分层单一职责;可测试是设计目标 |
| 框架专家 | `tim-sneath-mindset` | Tim Sneath(前产品负责人) | 四支柱;一套代码处处一流体验;DX 即产品 |
| 实践专家 | `andrea-bizzotto-mindset` | Andrea Bizzotto(Code With Andrea) | 没有银弹但有分层骨架;组合;单向数据流 |
| 实践专家 | `filip-hracek-mindset` | Filip Hracek(前 DevRel) | 实用主义;状态管理是连续谱;能讲清才是好方案 |
| AI 工程师 | `devin-ai-engineer-mindset` | Devin(自治 AI 软件工程师;自蒸馏,老师即执笔者) | 验证闭环;最小改动;先复现后修复;证据优先;显式升级 |

## 成长性约定(可读、快速、可演进)

让"造 skill"这件事本身长期可维护:

- **结构即契约**:五层标题固定,测试守护(`tests/test_engineering_workflow_skills.py` 检查标题/出处/front-matter 缺失即 fail)→ 后续不会悄悄退化。
- **小而准 > 大而全**:心智模型最多 7 个、启发式最多 10 条;读者 30 秒能扫完。宁可少而每条都过三重验证。
- **版本化演进**:观点更新时 bump `version` 并在 `诚实边界` 更新"调研截止日期";旧结论若被推翻,先在 `REFERENCES.md` 补来源再改。
- **出处可点击**:每条主张一行可点链接,便于 review 与回溯。
- **遇到问题就回流**:在使用中发现 skill 给错方向 → 回到 Phase 2 复核该条是否真过三重验证,必要时降级/删除,并补一个回归用例。

## Troubleshooting

| 现象 | 原因 | 处理 |
|---|---|---|
| 新 skill 没被加载 | `id` 与目录名不一致 / front-matter 缺必填字段 | 对齐 Phase 3 规则,`SkillRegistry.reload()` 看告警 |
| 被注入到不相干的流水线阶段 | `stage_hints` 填了无关阶段 | 收窄到真实相关阶段 |
| skill 像在"复读语录" | 收录的是 WHAT they said 而非 HOW they think | 回 Phase 2,只留有预测力 + 排他性的镜片 |
| 对新问题"过度自信" | 过拟合训练素材 | 在 `诚实边界` 标注未覆盖范围;Phase 4 第 2 步必须通过 |
| 重复 id 警告 | 两个目录用了同名 id | 改名;加载器只保留第一个 |

## References

- 女娲 · Skill 造人术(方法论母本):<https://github.com/alchaincyf/nuwa-skill>
- 女娲 skill 模板:<https://github.com/alchaincyf/nuwa-skill/blob/main/references/skill-template.md>
- Agent Skills 协议(跨 runtime 复用):<https://agentskills.io>
- 本项目反幻觉规则与出处约定:`REFERENCES.md`
- 本法的首个产物:`flutter-engineer-mindset`
