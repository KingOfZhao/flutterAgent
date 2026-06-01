# 自我反省:56 个 skill 的冗余 & 实际可用性诊断

> 结论先行:**机制是能跑的,但有真实冗余在"互抢预算",而且选用精度被三处设计稀释。**
> 下面每条都附了可复现的实测证据,不是空谈。

---

## 一、它到底有没有"被真正应用"?——先看选用链路

请求进来后的实际链路(`pipeline.py` + `skill_ranker.py`):

1. `rank_skills()` 用**关键词重叠(CJK 单字 + 拉丁词)的 Jaccard** 给每个 skill 打分,平台命中加分。
2. `select_within_budget()` 在 **40k token 预算**内贪心装入。
3. 之后每个 stage 再用 `stage_hints` 二次过滤。

**关键数字(实测):**
- 56 个 SKILL.md 正文合计 ≈ **137,589 token**,而预算只有 **40,000**。
- → 每次请求**只有约一半 skill 能进上下文**(实测 26–31/56)。

**含义:** 预算是真的会裁的,所以"重叠的两个 skill"不是"反正都注入无所谓",而是**会互相挤掉对方、也挤掉真正相关的 skill**。冗余在这里是有代价的。

---

## 二、真实冗余:6 对/簇职责重叠

| 重叠簇 | 旧 skill | 新 skill | 重叠点 | 判断 |
|---|---|---|---|---|
| 性能 | `flutter-performance`(预算+优化规则) | `flutter-performance-profiling`(DevTools 工具流) | jank/重建/启动 | **互补为主**(规则 vs 工具),但 tags 高度重合 |
| 网络 | `flutter-network`(dio/拦截器/重试客户端实现) | `flutter-network-protocols`(协议选型) | tags 几乎全同(http/grpc/graphql/ws) | 边界清晰,但 ranker 上**互抢** |
| CI/CD | `flutter-ci-cd`(发布管线/flavors/版本/回滚) | `flutter-cicd-pipelines`(矩阵/缓存/密钥/产物/自动化) | 发布自动化 + 版本策略 | **真重叠**,且同名极易混 |
| 移动平台 | `flutter-mobile`(综述) | `flutter-android-platform`+`flutter-ios-platform`(深入) | 平台配置/权限/签名 | 综述 vs 深入,可接受但需声明分工 |
| 桌面平台 | `flutter-desktop`(综述) | `flutter-desktop-platform`(打包/签名/公证) | 打包分发 | 同上 |
| 打包 | `flutter-build-and-release` | android/ios/desktop-platform 的打包签名 + `flutter-cicd-pipelines` 的发布自动化 | 签名/混淆/产物 | **三方重叠**最严重 |

另有 **meta/编排三件套** 职责交叠:`task-refinement`(恒定注入)/`flutter-engineering-workflow`(总编排)/`flutter-skill-distillation`(造 skill)——都在"讲流程",边界靠读者自己分辨。

---

## 三、稀释"实际选用精度"的三处设计问题(实测证据)

### 问题 1:`always_include` 太粗暴
`architecture-design` + `state-management` 被**无条件 +100 分**恒定注入。

实测「优化列表滚动卡顿」性能任务的排名:
```
state-management  101.91   ← 排第 1,但和性能调优几乎无关
architecture-design 101.0  ← 排第 2
flutter-performance 4.18   ← 真正该用的排第 3
```
→ 纯打包 / 纯 UI 还原任务里,这两个也强行挤占预算。

### 问题 2:CJK 单字 Jaccard 带来关键词噪声
实测「接入后端 API,选择通信协议」任务:
```
flutter-documentation        3.91  ← 冲到第 6,与协议无关
flutter-design-to-code-playbook 2.82 ← 第 8,无关
```
→ "协议/选型"等被拆成单字,和大量 skill 的常用字误命中。

### 问题 3:front-matter 没有"关系字段",ranker 看不到分工
`SkillMeta` 只有 `id/name/version/platforms/tags/applies_when/stage_hints`,**没有 `extends`/`supersedes`/`see_also`**。
- 重叠的两个 skill 无法告诉 ranker "我俩同族,选一个主、一个辅"。
- 正文里写的交叉链接(prose)**ranker 根本读不到**——它只取正文前 300 字。
→ 所以同族 skill 只能盲目竞争,无法去重/降权。

---

## 四、建议(分两层,均不破坏"成长性",待你拍板)

### A. 低风险机制增强(推荐先做,不删任何 skill)
1. **front-matter 加可选 `extends` / `see_also` 字段** + 让 ranker 对"同族"做去重/降权:一对重叠 skill 不再同时挤进预算,只进最相关那个 + 一句指针。
2. **`always_include` 改为按 stage/平台/关键词触发**:纯 UI / 纯打包任务不再硬塞 `state-management`。
3. **降关键词噪声**:CJK 改用 bigram(双字),或给 `tags` 命中更高权重、正文片段降权,挡掉 `flutter-documentation` 这类误入。

### B. 内容层(可选,关乎"文字冗余")
4. 给 6 对重叠各加一行**明确分工声明**("本 skill 负责 X;深入 Y 见 `<other>`"),人和模型都不踩重。
5. 或更激进:把同名的 `ci-cd`↔`cicd-pipelines`、`performance`↔`performance-profiling` 各自**合并成一个分章节的 skill**(减少互抢,但会变大;需权衡可读性)。

---

## 五、诚实边界
- 以上排名实测基于当前 `skill_ranker` 的关键词算法;真实部署若接了更强的 embedding ranker,噪声问题会缓解,但**预算互抢和缺关系字段的问题依然存在**。
- "合并 skill"会提升选用精度,但牺牲单一职责的可读性;我倾向**先做 A 类机制增强**(保留所有 skill,加关系字段 + 修 always_include + 降噪),这是性价比最高、最符合你要的"成长性 + 可读性"。
