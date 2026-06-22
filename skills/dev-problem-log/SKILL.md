---
id: dev-problem-log
name: 开发问题记录与 skill 孵化 (问题捕获格式 / 孵化判据 / 整理成 skill 的时机)
version: 1.0.0
platforms: [all]
tags: [process, problem-log, lessons-learned, postmortem, knowledge, incubation, 问题记录, 经验沉淀]
applies_when: 实际开发中遇到值得沉淀的问题/坑/教训时,先按统一格式记录;积累到模式成立后整理成新 skill 或强化已有 skill
stage_hints: [implementation, review, acceptance]
see_also: [flutter-skill-distillation, scope-and-impact-analysis]
---

# 开发问题记录与 skill 孵化

> 分工:本 skill 负责**捕获**——开发中遇到的问题怎么记、记什么、何时升级成 skill。
> 把素材**蒸馏成 skill**的方法论见 `flutter-skill-distillation`(女娲蒸馏法)。

> 核心原则:**当场记原始事实,事后提炼模式**。
> 问题刚发生时上下文最全但最没空写;所以捕获格式必须轻(2 分钟内写完),提炼留给整理时机。

---

## 1. 记录什么(捕获判据)

满足任一条就值得记:

- **踩坑**:符合直觉的做法是错的(如"只扫 Figma Page 顶层会漏 Section 里的画板")。
- **误判**:表象指向 A,根因其实是 B(如"控制台丢 CJK 字形,误以为数据损坏")。
- **重复**:同类问题第二次出现——重复本身就是要沉淀的信号。
- **绕路**:官方文档/常规路径走不通,最终靠某个非显然手段解决。
- **边界**:工具/API/框架的能力边界或版本差异第一次被实测确认。

不记:一次性笔误、纯环境抖动、已有 skill 明确覆盖且无新增信息的问题。

## 2. 捕获格式(轻量,当场写)

记录到 `knowledge/problem-log.md`(追加式,一条一段):

```markdown
## P-YYYYMMDD-NN <一句话标题>
- 场景: <在做什么任务时遇到>
- 现象: <观察到的事实,贴关键报错/数据>
- 根因: <最终确认的原因;未确认就写"未定位"并说排除了什么>
- 解法: <怎么解决/绕过的,关键命令或代码点>
- 教训: <下次怎么避免;一句话>
- 标签: [figma] [network] [build] ...   ← 用于聚类
- 关联 skill: <已有相关 skill id,或"无 → 候选新 skill">
```

要求:

- **现象与根因分开写**——记录时往往只有现象,根因后补;不要把猜测写成结论。
- 必须有可检索标签,孵化判断靠标签聚类。
- 引用已有 skill 时用准确 id(有完整性测试守护)。

## 3. 孵化判据(何时升级成 skill)

定期(或每次新增记录时)按标签聚类回看:

| 信号 | 动作 |
|------|------|
| 同标签 ≥ 3 条且指向同一类方法 | 孵化新 skill,按 `flutter-skill-distillation` 蒸馏 |
| 1–2 条但与已有 skill 强相关 | **强化**该 skill:补"实战教训/反模式"小节,不另立新 skill |
| 多条同标签但各自孤立无模式 | 继续积累,不强行归纳 |
| 根因仍是"未定位" | 不孵化——没有根因的教训是迷信 |

孵化后在原记录条目末尾标注 `→ 已孵化: <skill-id>` 或 `→ 已并入: <skill-id> §x`,问题日志保持只增不删(它同时是孵化审计轨迹)。

## 4. 升级成 skill 时的质量门槛

- 走 `flutter-skill-distillation` 的流程:front-matter 完整、每条主张有出处或实测依据、写明诚实边界。
- 教训要**泛化到方法**,不是复述事故:"递归遍历全树按尺寸筛画板" ✓;"上次那个文件里画板在 1848:9423" ✗。
- 新 skill 必须与已有 skill 划清分工(见 `scope-and-impact-analysis` 的重叠判定),宁可并入已有 skill 也不造重叠的新 skill。

## 反模式

- ❌ 问题解决了就翻篇,不留记录——同一个坑三个月后再踩一次。
- ❌ 记录写成小作文:超过十行的捕获写不动,格式就废了。
- ❌ 把猜测当根因写进记录,污染后续孵化。
- ❌ 每条记录都立刻造一个新 skill——单点事故 ≠ 可复用方法,skill 库被噪声稀释。
- ❌ 孵化后删掉原始记录,丢失审计轨迹。
- ❌ 新 skill 与已有 skill 大面积重叠,组合注入时互相挤占 token 预算。

## 参考 / References

- 蒸馏方法论见 `flutter-skill-distillation`;重叠/分工判定见 `scope-and-impact-analysis`。
- Blameless postmortem 文化(Google SRE):<https://sre.google/sre-book/postmortem-culture/>
- Architecture Decision Records(同类"轻捕获重提炼"思想):<https://adr.github.io/>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **捕获与提炼分离**:当场只记事实,模式靠日后聚类——两件事混做就两件都做不好。
- **重复是信号**:一个坑值不值得沉淀,最可靠的判据是它出现第二次。
- **根因是孵化门票**:没定位根因的教训只能是待办,不能是方法。
- **强化优先于新建**:能并入已有 skill 的就不造新的,控制 skill 库的关联复杂度。

**诚实边界:**

- 问题日志是个人/团队工作流约定,格式可按团队习惯调整;本 skill 给默认模板与判据。
- 孵化判据(≥3 条)是经验阈值非硬性规则;高价值单条(如安全事故)可直接孵化。
- 日志文件位置(`knowledge/problem-log.md`)依本仓库结构,其他项目自行约定。
