# 全项目反思 v2:向量库是"孤岛",检索没有进决策链

> 时点:合并 comprehensive-thinking / devin-ai-engineer-mindset / 向量数据库三个增量之后。
> 结论先行:**项目最大的问题不再是 skill 冗余(上一轮已修),而是新建的向量库与核心选用链路脱节——花了成本建索引,真正决定"注入哪些 skill"的 ranker 却一个字节都没用上。** 本次反思附带把它修掉。

---

## 一、逐模块体检

| 模块 | 状态 | 发现 |
|---|---|---|
| skill 语料(61 个) | 健康 | 上一轮的 extends/see_also + 家族去重 + 条件化 always_include 已落地,六对重叠簇有分工声明 |
| skill_ranker | 可用但停滞 | 关键词 unigram + 中文 bigram + tags 加权;同义改写(如"通信链路怎么选"→ network-protocols)仍然漏召回 |
| vector_store(上一增量新建) | **孤岛** | 只服务 `/v1/vector/search` 端点和 CLI;pipeline 选 skill 时完全不经过它 |
| /v1/skills/reload | 有陈旧性缺陷 | 热重载 skill 后向量索引不重建 → 语义检索返回旧内容 |
| 应用生命周期 | 小漏 | lifespan 关闭了 http client / validator,但向量库连接从不关闭 |
| /v1/skills/rank(dry-run) | 即将漂移 | 文档承诺"和 pipeline 用同一个 ranker",一旦 pipeline 接入语义分而 dry-run 不接,承诺就失效 |
| 测试 | 良好 | 317 个,但向量↔ranker 的接缝处为零覆盖(因为接缝原本不存在) |

## 二、根因

这是典型的**"加法式成长"反模式**:每个增量(skill、向量库、知识库)都各自闭环、各自有测试,但没有人回头问"新能力应该改变哪条既有决策链"。向量库被当作"又一个端点"交付,而它真正的价值位是 ranker 的召回层。

## 三、本次编辑(全部随本反思落地)

1. **语义分进 ranker**:`vector_store.semantic_skill_scores()` 取每个 skill 的最佳 chunk 余弦分;`rank_skills(..., semantic_scores=)` 以 `SEMANTIC_WEIGHT=8.0` 加性混入(典型余弦 0.1–0.45 → 0.8–3.6 分,与 1–2 个精确 bigram 命中同量级:语义只做"补召回",不会盖过精确关键词命中)。
2. **pipeline 接入,失败即降级**:lifespan 打开磁盘索引(为空则自动构建)注入 pipeline;任何异常仅记日志并退回纯关键词排名——语义召回是增强,不是单点依赖。
3. **`/v1/skills/rank` dry-run 同步接入**,继续与 pipeline 行为一字不差。
4. **reload 联动重建索引**:`POST /v1/skills/reload` 现在返回 `{"loaded": n, "reindexed_chunks": m}`,消除陈旧性。
5. **生命周期补漏**:lifespan 退出时关闭向量库连接;测试预置的 store 不被 lifespan 覆盖或误关。
6. 新增 3 个接缝测试(语义分聚合、ranker 混排可比性、reload 重建)。

## 四、有意不做的(及理由)

- **不用语义分替代关键词分**:哈希 embedding 没有语义先验,只有词面+字组泛化;让它做主排序会放大噪声。正确位置是加性补召回。
- **不在每个请求时重建索引**:索引持久化于 SQLite,只在显式 rebuild / reload / 启动时为空才构建。
- **不合并重叠 skill**(上一轮 B5 方案):家族去重已让重叠簇不再互抢预算,合并只剩可读性代价。

## 五、诚实边界

- `SEMANTIC_WEIGHT=8.0` 基于哈希 embedder 的实测分布手工标定;若将来替换为真 embedding API(余弦普遍 0.6+),该权重必须重新标定。
- 语义召回的上限受 embedder 上限约束:它解决"同词不同形",解决不了"同义不同词"(如"卡顿"↔"掉帧"若无共字仍难命中)。换可学习 embedding 是下一级阶梯。
- 本反思只覆盖代码与机制;skill 正文的内容质量(是否过时、是否互相矛盾)需要另一轮人工/模型审读。
