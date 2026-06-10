# 多 AI 协作协议 (Agent Collaboration Protocol)

> 实现:`src/flutter_agent/collaboration.py` + `src/flutter_agent/providers.py`
> 接口:`POST /v1/agents/collaborate`、`GET /v1/agents/providers`
> 设计依据:`knowledge/model-theory-deepdive.md` §4.3(验证器/策略隔离)、§6.3(补偿性/约束性两分法)

## 1. 设计原则

1. **约束性层永不省略**:所有 AI 间通信走统一结构化消息并全程留痕(transcript),
   预算上限(`COLLAB_MAX_AGENTS`、`COLLAB_MAX_ROUNDS`)由配置硬性约束——这些是
   两分法中的"约束性"层,不随模型变强而减薄。
2. **编排保持薄**:协作拓扑只有四种最小原语(solo/debate/committee/peer_review),
   不做复杂的工作流引擎——"补偿性"编排应随模型代际减薄,厚编排会被框架/模型收编
   (deepdive §10.2 两级吸收律)。
3. **验证器与策略隔离**:评审/打分的 Agent 应配置在与提案者**不同的提供商**上,
   避免同一模型自我确认(self-confirmation)。协议不强制但通过 `@reviewer`/`@judge`
   角色路由使之成为默认做法;隔离弱化不隐藏——裁判与被评者落在同一提供商时,
   该条打分附 `same_provider=true` 显式暴露。
4. **容错降级而非整体失败**:并行提案中单个提供商故障只剩下者继续,故障记入
   `failures`;全员失败才返回 502。peer_review 仅剩一个存活提案时其默认胜出
   (`votes=0`,不伪造分数)。
5. **并发受约束**:协作扇出(N 提案 + N×(N-1) 互评)与流水线共用全局
   `MAX_CONCURRENT_UPSTREAM` 信号量,不会无界爆发。
6. **运行级留痕**:每次协作运行追加一行 JSONL 审计摘要到
   `logs/collaborations.jsonl`(`COLLAB_LOG_PATH`,置空可关):时间/模式/参与者/
   提供商/胜者/失败/总用量。

## 2. 消息格式 (TranscriptEntry)

每条 AI 间消息的统一结构:

| 字段 | 类型 | 含义 |
|---|---|---|
| `agent` | str | 发言 Agent 名 |
| `role` | str | `proposer` / `reviewer` / `judge` |
| `round` | int | 所属轮次(从 1 起) |
| `content` | str | 消息正文 |
| `provider` | str | 实际解析到的提供商名(审计身份) |
| `model` | str | 实际使用的模型名(优先取上游回报) |
| `usage` | dict | token 用量(prompt/completion/total) |
| `elapsed_ms` | int | 该次调用耗时 |

所有模式的结果(`CollaborationResult`)都包含完整 transcript 与聚合用量
`total_usage`,并附 `failures`(被降级参与者),保证可审计。

**提示注入防护**:任何 Agent 输出被回注到评审/裁判/打分提示词前,都被统一
围栏标记包裹(内嵌同名标记会被剥离)并声明为待评估数据而非指令,降低
"在提案里写入给我打 10 分"一类跨 Agent 注入的成功率(缓解非根治)。

## 3. 互评判优 (peer_review):AI 间互相判断谁更具优势

流程:

1. **并行提案**:N(≥2)个 Agent 各自独立解答任务;
2. **匿名化**:提案被重标为 `候选方案 A/B/...`,打分提示词中不出现作者名;
3. **交叉打分**:每个 Agent 给**其他所有** Agent 的提案打分(从不给自己打分),
   按统一评分准则输出严格 JSON:

   ```json
   {"correctness": 0-10, "completeness": 0-10, "risk_control": 0-10,
    "justification": "一句话理由"}
   ```

   分值在解析时被截断到 [0,10];无法解析的打分记 `parse_ok=false` 并**从聚合中剔除**
   (而非按 0 分计入,避免格式失败惩罚被评者);
4. **聚合判优**:每个候选的聚合分 = 有效打分 total 的平均;打分调用固定
   `temperature=0` 以提高可复现性;排序为确定性三级键(聚合分降序→票数降序→
   名字升序),最高者为 `winner`,前两级打平时 `winner_tied=true` 显式标注;
   其原始提案作为 `final_answer` 返回;
5. **全量回传**:`scoreboard`(聚合分+有效票数)与 `peer_scores`(每条原始打分
   及理由)全部返回,便于人工复核与离线分析。

防偏置措施小结:匿名化(防名声偏好)、禁自评(防自我偏好)、跨提供商路由(防
模型家族自相似偏好)、原始分全留痕(防黑箱聚合)。已知局限:互评衡量的是
"评审者眼中的优势",非客观正确性;对有可执行验证器的任务(如代码),应优先用
真实验证(测试/编译)而非互评——互评是无验证器领域的退而求其次(deepdive §4.3)。
各防偏置措施的文献依据见 `REFERENCES.md` §23(位置偏差、自我偏好偏差、LLM-as-a-judge 局限)。

## 4. 其他协作模式

| 模式 | 拓扑 | 适用 |
|---|---|---|
| `solo` | 单 Agent 直答 | 基线/简单任务 |
| `debate` | 提案者↔评审者迭代修订,评审输出 `APPROVE` 即收敛 | 需要质量闸门的产出 |
| `committee` | N 提案并行 → 裁判综合 | 需要融合多视角的产出 |
| `peer_review` | N 提案并行 → 匿名交叉打分 → 判优 | 需要在候选间**选优**而非融合 |

## 5. 多提供商配置 (providers)

提供商在 `data/providers.json` 或环境变量 `MODEL_PROVIDERS`(JSON)中声明;
无任何配置时只有 `default`(由 `DEEPSEEK_*` 合成),完全向后兼容。

```json
{"providers": [
  {"name": "openai", "base_url": "https://api.openai.com/v1",
   "api_key_env": "OPENAI_API_KEY", "model": "gpt-5.2", "roles": ["reviewer"]},
  {"name": "local", "base_url": "http://localhost:11434/v1",
   "api_key": "x", "model": "qwen3", "roles": ["judge"]}
]}
```

路由引用语法(在任何接受 model 的地方可用,包括 pipeline 的 `DEEPSEEK_PLANNER_MODEL`):

| 引用 | 含义 |
|---|---|
| `openai:gpt-5.2-mini` | 指定提供商 + 指定模型 |
| `openai:` 或 `openai` | 指定提供商,用其配置的默认模型 |
| `@reviewer` | 第一个声明该角色的提供商 |
| 其他任意字符串 | 默认提供商,原样作为模型名(兼容旧行为) |

密钥优先从 `api_key_env` 指向的环境变量读取;`GET /v1/agents/providers` 的
视图不含任何密钥,仅含 `has_api_key` 布尔。

## 6. 调用示例

```bash
curl -X POST http://127.0.0.1:8765/v1/agents/collaborate \
  -H 'Content-Type: application/json' \
  -d '{
    "task": "为 Flutter 应用设计离线优先的同步层",
    "mode": "peer_review",
    "agents": [
      {"name": "deepseek", "role": "proposer", "provider": "default"},
      {"name": "gpt", "role": "proposer", "provider": "openai:"}
    ]
  }'
```

返回:`winner`(及 `winner_tied`)、`final_answer`、`scoreboard`、`peer_scores`
(含 `same_provider`)、`failures`、`total_usage`、完整 `transcript`。
