# Claude Fable 5 与 Claude Opus 4.8:能力、方法谱系与调用实践

> 性质:论文式整理。事实部分来自 Anthropic 官方一手材料;推断部分明确标注【推断】。
> 整理时点:2026-06-10。
> 一手出处:
> - Fable 5 / Mythos 5 发布公告(2026-06-09):https://www.anthropic.com/news/claude-fable-5-mythos-5
> - Opus 4.8 产品页(2026-05-28):https://www.anthropic.com/claude/opus
> - Adaptive thinking API 文档:https://platform.claude.com/docs/en/build-with-claude/adaptive-thinking
> - Effort API 文档:https://platform.claude.com/docs/en/build-with-claude/effort
> - AWS 公告:https://aws.amazon.com/about-aws/whats-new/2026/06/claude-fable-5-aws/

## 目录

1. 模型谱系与定位
2. Claude Opus 4.8:可靠自治的日常旗舰
3. Claude Fable 5 / Mythos 5:长时程自治的质变
4. 方法谱系:这些能力站在哪些公开研究之上
5. 安全发布范式:分类器回退与双形态发布
6. API 参数与调用实践
7. 对比与选型
8. 工程集成要点:把两个模型接进生产系统
9. 失效模式与评测建议
10. 诚实边界

## 1. 模型谱系与定位

- Opus 线:Opus 4.5(2025-11)→ 4.6(2026-02)→ 4.7(2026-04)→ **4.8(2026-05-28)**,Anthropic 的"日常主力"旗舰。
- Mythos 线:Mythos Preview(定向)→ **Mythos 5**(定向,网络防御者/基础设施商,经 Project Glasswing 与美国政府合作部署)。
- **Fable 5(2026-06-09)= Mythos 5 同一底座 + 安全分类器护栏**,首个公开可用的 Mythos 级模型。
- 关键规律(官方):任务越长越复杂,Fable 5 对其他模型的领先越大。

## 2. Claude Opus 4.8:可靠自治的日常旗舰

定位:严肃编码 + AI Agent + 企业知识工作的"daily driver"。混合推理,1M 上下文。

强项(均有官方/客户证据):
- **自适应思考**:按任务复杂度自动调节思考深度,把 effort 调参负担从用户移回模型。
- **长程一致性**:跨会话记忆、多天项目推进、大代码库内可靠运行、自我纠错。Cognition 反馈其工具调用干净、指令遵循一致,可支撑无人值守自治工程负载。
- **Agent 效率**:CursorBench 全 effort 档位超过此前 Opus;Online-Mind2Web 84%(被测最强 computer-use 模型);"Super-Agent benchmark"唯一全用例端到端跑通。
- **专业工作**:Legal Agent Benchmark 最高分;金融文档引用精度提升;数据分析中会主动指出输入/输出的问题。
- **判断力**:多家客户独立强调——问对的问题、对不合理方案 push back、大改动前先建立信心。

价格:$5 / $25(每百万输入/输出 token);prompt caching 省最高 90%,batch 省 50%。API 名 `claude-opus-4-8`。

## 3. Claude Fable 5 / Mythos 5:长时程自治的质变

- **软件工程**:Stripe 在 5000 万行 Ruby 代码库一天完成原需团队两个多月的全库迁移;Cognition FrontierCode 前沿模型最高分,中等 effort 即达成(token 效率领先)。
- **知识工作**:Hebbia 金融基准最高分;IMC 交易分析评测几乎全线通过。
- **视觉**:新 SOTA;可仅凭截图重建 Web 应用源码;**仅靠原始截图、零辅助工具通关 Pokémon FireRed**(此前模型配复杂 harness 也不行)——意味着同样的 Agent 产品可以用更少脚手架做更强的事。
- **记忆与超长上下文**:数百万 token 长任务中保持专注,用自己的笔记改进产出;Slay the Spire 实验中,持久化文件记忆带来的收益是 Opus 4.8 的 3 倍。
- **科研(Mythos 5 展示)**:蛋白/药物设计流程提速约 10 倍,14 个靶点出 9 个强候选;分子生物学假说盲测约 80% 被科学家偏好,一个 E. coli 蛋白新机制假说被独立实验室佐证;一周多自主完成基因组学研究,自训 100 倍更小的模型超过《Science》近期发表模型。
- **自我验证**:最高 effort 下反思并验证自己的工作;会自建评测 harness、交付前自查、基于学习自我更新 skills(AWS 公告)。
- 对齐:自动化对齐评估中失准行为水平低,与 Opus 4.8 相当。
- 价格:$10 / $50,Amazon Bedrock 与 Claude Platform on AWS 可用。

### 3.1 证据强度审计【第 1 轮审核新增,2026-06-10】

§2/§3 的能力主张并非同一证据等级。按"读者能否独立复核"分四级,逐条归位——
引用本文做选型时,**B/C 级主张不应单独作为决策依据**,需配合自建评测(`claude-eval-methodology.md`):

| 级别 | 含义 | 本文中的主张 |
|---|---|---|
| A:可复核基准 | 公开基准 + 公开数字,第三方可重跑 | Online-Mind2Web 84%;CursorBench 档位对比;FrontierCode 分数(Cognition 公布) |
| B:客户/厂商转述 | 有具体数字但出自客户引语或厂商内部评测,无法独立复核 | Stripe 5000 万行迁移提速;Hebbia/IMC 基准;Slay the Spire 记忆 3 倍;蛋白设计 10 倍提速、14 靶点 9 候选 |
| C:官方叙事 | 定性描述,无数字 | "任务越长领先越大";"判断力/push back";"自建评测 harness";Pokémon FireRed 通关(有事实但无量化口径) |
| D:推断 | 本文作者外推 | §4 全部谱系映射;§6.1/§7.1/§8/§9 的【我的理解】段 |

审计结论:本文 A 级主张集中在 Agent/computer-use 轴;**长时程优势——两模型差异化的核心卖点——
证据全部落在 B/C 级**。这不构成否定,但意味着 §7.1 决策树中"天级任务 → Fable 5"分支的
真实置信度低于表面;在自己的长任务样本上做一次对照(哪怕 n=5)的信息价值极高。

## 4. 方法谱系:这些能力站在哪些公开研究之上

(内部细节未公开;以下为基于 Anthropic 公开论文/文档的谱系定位,标注【推断】处为合理外推。
逐论文精读与完整推演已展开为独立文档:`model-theory-deepdive.md`——含每条线的
机制/贡献/天花板三段式精读,以及"为什么 Fable 5 强"的五步可证伪论证链。)

- **RLHF / 偏好学习**:Christiano et al. 2017(https://arxiv.org/abs/1706.03741);InstructGPT(https://arxiv.org/abs/2203.02155)。指令遵循与"有帮助性"的底座方法。
- **Constitutional AI / RLAIF**:Bai et al. 2022(https://arxiv.org/abs/2212.08073)。用一组明文原则让 AI 自我批评与改写,替代大量人工标注——Claude 系对齐方法的标志性路线;Fable/Mythos 的低失准行为水平是这条线持续迭代的结果【推断:具体配方未公开】。
- **Scaling laws 与计算最优**:Kaplan et al. 2020(https://arxiv.org/abs/2001.08361)、Chinchilla(https://arxiv.org/abs/2203.15556)。"Mythos 级"作为能力代际命名,本质是更大有效计算量 + 更优数据配比的产物【推断】。
- **可解释性**:Anthropic 的 transformer-circuits 系列(https://transformer-circuits.pub),如 Scaling Monosemanticity(SAE 特征字典)。这是其"先理解再放权"的安全发布能力基础之一【推断:与分类器工程相互支撑】。
- **长时程 Agent 评测**:METR 关于"任务时长视角的能力测量"(https://metr.org/blog/2025-03-19-measuring-ai-ability-to-complete-long-tasks/)。Fable 5"任务越长领先越大"正是该维度上的代际跃迁。
- **过程监督与自我验证**:Let's Verify Step by Step(https://arxiv.org/abs/2305.20050)等过程奖励研究;Fable 5 的"反思并验证自己的工作 / 自建评测 harness"是这一思想产品化的形态【推断】。
- **记忆增强 Agent**:外置文件记忆 + 笔记自改进(官方 Slay the Spire 实验)呼应 Reflexion(https://arxiv.org/abs/2303.11366)等"语言反馈即学习信号"路线【推断:实现细节未公开】。

## 5. 安全发布范式:分类器回退与双形态发布

官方公开机制(Fable 5 发布公告):
- **安全分类器**:独立的 AI 系统检测潜在滥用(含越狱尝试),在主模型响应前拦截。
- **回退而非拒绝**:命中网络安全、生物/化学、**蒸馏(distillation)**相关请求时,自动改由 Opus 4.8 代答,并告知用户。>95% 的会话完全不触发回退——这些会话里 Fable 5 ≈ Mythos 5。
- **双形态发布**:同一底座,公开版(Fable,带护栏)+ 定向版(Mythos,部分护栏解除,仅限可信网络防御方)。
- 护栏刻意调保守(宁可误伤),随后续迭代降误报。

值得注意:把"模型蒸馏"列为受保护类别,说明前沿厂商已把"能力被竞品/恶意方蒸馏"视为与生化、网安并列的风险面。

**回退机制的工程含义**(对接入方的实际影响):
- 你的应用必须容忍**同一个 model id 下能力不是常量**:同一会话里某些轮次可能是 Opus 4.8 在答。若业务逻辑假设"调的一定是 Fable 5",在 <5% 的触发会话里会出现难以复现的质量抖动——监控上应把"是否被回退"作为一个显式维度记录(响应中会告知)。
- 误伤是设计预期而非 bug:安全/生物/蒸馏邻域的合法请求(如安全研究、模型压缩论文复现)可能被保守拦截。重试不会绕过分类器;正确姿势是改写表述或直接降级到 Opus 4.8。
  检测清单与误伤处理决策流的可操作细则已单独成篇:`claude-fallback-playbook.md`。
- 这是一个可复用的范式:**"强模型 + 独立守门员 + 可接受的回退体"**比"拒答"保留了可用性,比"不设门"保留了可发布性——应用层做自己的敏感能力分级时可以照搬这个结构。

## 6. API 参数与调用实践

(出处:platform.claude.com 文档,见文首链接。)

- **思考模式**:
  - Fable 5 / Mythos 5:adaptive thinking **永远开启**,不可关闭(`thinking: {type: "disabled"}` 报错),无需配置。
  - Opus 4.8:`thinking: {type: "adaptive"}` 显式开启;手动 `{type: "enabled", budget_tokens: N}` 直接 400。不传则不思考。
  - `budget_tokens` 在 Opus/Sonnet 4.6 已弃用,由 effort 取代。
- **effort 档位**(`output_config.effort`,软性引导思考预算):`max`(无约束,Fable 5/Mythos 5/Opus 4.6+ 可用)> `xhigh`(深思 + 扩展探索)> `high`(默认,几乎总是思考)> `medium`(简单题可跳过思考)> `low`(最小思考)。
  - 官方建议:复杂 Agent 任务用 `xhigh`,多数智力敏感负载用 `high`,只有评测确认质量不掉再降档。
- 示例:

```bash
curl https://api.anthropic.com/v1/messages \
  -H "x-api-key: $ANTHROPIC_API_KEY" \
  -H "anthropic-version: 2023-06-01" \
  -H "content-type: application/json" \
  -d '{
    "model": "claude-opus-4-8",
    "max_tokens": 16000,
    "thinking": {"type": "adaptive"},
    "output_config": {"effort": "high"},
    "messages": [{"role": "user", "content": "..."}]
  }'
```

- **token 效率即真实成本**:Opus 4.5 时代起,medium effort 可匹配上代最佳分数且省约 76% 输出 token;Fable 5 在 FrontierCode 上中等 effort 即最高分。单价高 ≠ 总成本高。

### 6.1 adaptive thinking 与 effort 的取舍模型【我的理解】

两个机制解决的是同一个问题的两半:**思考预算的分配权归谁**。
- adaptive thinking 把"逐题分配"交还模型——模型比调用方更清楚哪道题难。这是对 `budget_tokens` 手动调参路线的否定:固定预算在简单题上浪费、在难题上不够,是一个必然被淘汰的中间状态(所以 4.6+ 直接弃用)。
- effort 保留的是"全局风险偏好"这一层:调用方仍然比模型更清楚**这笔调用的错误代价**(生产事故 vs 草稿生成)。正确心智模型:effort = 你告诉模型"错了多疼",adaptive = 模型决定"这题多难"。
- 实践规则:默认 `high`;只有**自己的评测集**证明降档不掉分才降(官方同样建议);`xhigh/max` 留给"错一次的代价 ≫ 多思考的 token 费"的场景。不要用 effort 控制延迟或限流——那是 max_tokens 与路由的职责。
- "自己的评测集"怎么建、model × effort 怎么扫、前沿图怎么读:见 `claude-eval-methodology.md`。

## 7. 对比与选型

| 维度 | Opus 4.8 | Fable 5 |
|---|---|---|
| 定位 | 日常主力旗舰 | 最强公开模型(Mythos 级) |
| 价格(入/出,每百万) | $5 / $25 | $10 / $50 |
| 思考 | adaptive(需显式开启) | adaptive(强制开启) |
| 长时程任务 | 强 | 显著更强,任务越长领先越大 |
| 视觉 | computer-use SOTA 之一 | 新 SOTA,几乎无需脚手架 |
| 记忆利用 | 跨会话记忆 | 笔记自改进,记忆收益约 3 倍 |
| 安全角色 | Fable 5 的护栏回退模型 | Mythos 5 + 分类器 |

选型直觉:日常开发、生产 Agent、成本敏感 → Opus 4.8;一次性硬骨头(全库迁移、深度研究、复杂多 Agent、纯视觉自动化)→ Fable 5。
两者差距的机制性解释(为什么是长任务而不是所有轴均匀拉开):`model-theory-deepdive.md` §8。

### 7.1 选型决策树【我的理解】

```
任务可机器判定成败吗?(测试/编译/可执行验收)
├─ 是 → 任务预计多长?
│   ├─ 小时级以内、可重跑 → Opus 4.8 + high(失败了重跑比升级模型便宜)
│   └─ 天级、重跑成本高(全库迁移/长程研究) → Fable 5 + xhigh
│      (长任务里验证闭环的复利优势被放大,正是 Fable 5 领先最大的轴)
├─ 否,但有人在环路审核 → Opus 4.8(人是验证器,模型差距被审核压缩)
└─ 否,且无人审核(全自动决策) → Fable 5,且必须要求它自建验证
   (没有外部验证器时,模型自身的自检能力就是唯一门禁——这正是两者差距最大处)
视觉主导(截图→代码 / computer-use 重负载) → 直接 Fable 5:脚手架省下的工程成本通常超过差价
```

## 8. 工程集成要点:把两个模型接进生产系统【我的理解】

1. **双模型路由是默认架构,不是优化**:把 Fable 5 当"升级通道"而非默认通道。入口先用 Opus 4.8 分流(它本身就擅长"判断任务难度、对不合理方案 push back"),只把被判为长/难/视觉重的任务送 Fable 5。这与本仓库 skill ranker 的思想同构:预算只花在别处买不到的地方。
2. **prompt caching 改变架构选择**:省最高 90% 意味着"大而稳定的 system prompt + 小而多变的 user 尾部"是成本最优形状——把 skill/知识库这类稳定内容前置、会话状态后置,缓存命中率直接决定账单;batch 50% 适用于离线评测与批量生成。
3. **跨会话记忆要主动设计**:Fable 5 的记忆收益来自"用自己的笔记"——应用层应提供可读写的持久化笔记位(文件/DB),而不是只靠塞满上下文。给模型"记忆权"比给它"更长上下文"收益曲线更陡。
4. **把回退事件纳入可观测性**(见 §5):记录实际应答模型、effort 档位、思考 token 数;否则质量回归无法归因。

## 9. 失效模式与评测建议【我的理解】

可预期的失效模式(基于公开机制推导,非官方清单):
- **回退引起的质量抖动**:同 prompt 不同轮次分数不同——先查是否被回退到 Opus 4.8,再怀疑模型。
- **过度自主**:强自主模型在指令欠约束时会"把活做完"而不是"把你要的活做完";长任务必须给出验收标准(definition of done),否则它会自己发明一个。
- **评测饱和**:公开基准对这一代模型区分度下降,厂商引用的多是私有/客户基准。结论:**自建评测集是选型的唯一可靠依据**——用自己的真实任务样本,同时扫 model × effort 两个轴,看质量-成本前沿而非单点分数(实操手册:`claude-eval-methodology.md`)。
- **时效失真**:这个领域以周为单位演进,本文任何"最强/最佳"表述都隐含"截至 2026-06-10"。

## 10. 诚实边界

- 架构、参数量、训练数据与具体训练配方均未公开;第 4 节的谱系映射是基于公开文献的【推断】,不是官方声明。
- 基准引语多来自厂商与早期客户,存在选择性呈现的可能;生产采用前应在自己的评测集上复核。
- 本文时点为 2026-06-10;该领域以周为单位演进,引用前注意时效。
