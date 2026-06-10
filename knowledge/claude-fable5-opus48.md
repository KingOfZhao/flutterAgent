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
8. 诚实边界

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

## 4. 方法谱系:这些能力站在哪些公开研究之上

(内部细节未公开;以下为基于 Anthropic 公开论文/文档的谱系定位,标注【推断】处为合理外推。)

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

## 8. 诚实边界

- 架构、参数量、训练数据与具体训练配方均未公开;第 4 节的谱系映射是基于公开文献的【推断】,不是官方声明。
- 基准引语多来自厂商与早期客户,存在选择性呈现的可能;生产采用前应在自己的评测集上复核。
- 本文时点为 2026-06-10;该领域以周为单位演进,引用前注意时效。
