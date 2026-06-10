# 复盘:模型理论深读十轮(审核 / 强化 / 明确必要长期 / 推演理论依据)

> 任务:对 Opus 4.8 / Fable 5 等模型文档进行十轮深度思考——审核、强化、
> 明确"必要/长期"内容、推演其论文与模型强大的理论依据。
> 时点:2026-06-10。每轮一个 commit。

## 逐轮记录

| 轮 | 动作 | 产出 | 性质 |
|---|---|---|---|
| 1 | 审核 claude-fable5-opus48.md | §3.1 证据强度四级审计(A 可复核基准 / B 客户转述 / C 官方叙事 / D 推断);发现长时程核心卖点证据全在 B/C 级 | 审核 |
| 2 | 审核 model-capability-evolution.md | §7.1 框架自审:乘法/min 混用修正(李比希最小因子律)、量化刻度缺失明示、§9 选择效应声明 | 审核/碰撞 |
| 3 | 深读篇开篇 | `knowledge/model-theory-deepdive.md`:总纲因果链(七环节各解决上一环节的失效模式)+ 线 1 RLHF/InstructGPT/DPO + 线 2 CAI/RLAIF | 理论依据 |
| 4 | 深读续 | 线 3 scaling/Chinchilla/蒸馏即数据生产(model collapse 风险)+ 线 4 过程监督/STaR/RLVR(可判定性边界即演进边界) | 理论依据 |
| 5 | 深读续 | 线 5 长时程(错误复利数学 p^n + Reflexion/Voyager)+ 线 6 工具接口(ReAct/Toolformer/SWE-bench)+ 线 7 SAE/Constitutional Classifiers | 理论依据 |
| 6 | 综合推演 | §8 五步可证伪论证链(Fable 5 优势源于验证闭环×记忆管理而非纯 scaling)+ 三条可检验含义 + §8.1 应用层资产升贬值表 | 立论/强化 |
| 7 | 强化交叉引用 | 两份主文档 §4/§7/开篇 指向 deepdive;分层声明(主文档保持框架层) | 回写 |
| 8 | 明确必要/长期 | 路线图 v7:第 19 条交付收口、第 6 条状态审正(structured-output-reliability.md 早已存在未回填)、段位复审 + 优先级传导(8.6>4>5>2) | 回写/审核 |
| 9 | 引用回填 | REFERENCES.md §22 新增 18 行,七条线论文来源全部可点击 | 一致性 |
| 10 | 复盘 | 本文 + 全量测试 + 跨文档一致性检查 | 复盘 |

## 第二阶段:十轮完整循环(每轮跑一遍"思考→审核→强化→明确→推演"闭环)

第一阶段是分工式十轮(每轮一类动作);应需求方澄清,第二阶段改为**迭代循环式**:
每轮都对全体系做一遍完整闭环,逐轮深化。记录如下:

| 循环 | 审核发现 | 强化/推演产出 | 落点 |
|---|---|---|---|
| 1 | 总纲因果链可被读得过强(时间序误读/薄弱环节准则缺失) | §0.1 三点限定;"验证是全链公共资源"=8.6 条的理论根据 | deepdive §0.1 |
| 2 | "push back"被当作偏好学习自然产物 | 谄媚文献(2310.13548)证明其为逆梯度塑形→迁移评测必测维度 | deepdive §1.3 |
| 3 | 蒸馏保护的"制度性确认"推断过强 | 三对立假设(护城河/合规/安全外溢)并列+判别观察,降级为弱化版 | deepdive §3.2 |
| 4 | "可验证奖励"被默认不可作弊 | 代码域作弊形态;自建 harness 自欺风险;封存集=验证器隔离的训练侧依据 | deepdive §4.3 |
| 5 | "记忆 3 倍"存在混淆变量(记忆位存在 vs 使用策略) | 含义 2 升级为三臂对照(A 无读写/B 给不提示/C 给+提示) | deepdive §5.3 |
| 6 | "脚手架变薄"可能被误用为删光编排 | harness 两分法:补偿性应减薄/约束性永不减薄 + 拆层判别测试 | deepdive §6.3 |
| 7 | "越长越领先"无法判别验证闭环说 vs 纯 scaling 说 | §8.0 反方最强陈述 + 三个判别变量;推论 4 置信度下调一档 | deepdive §8.0 |
| 8 | 深读篇被默认一次性交付 | 保鲜期分层(机制长效/推断随发布过期)+ 三个维护触发条件 | 路线图第 19 条 |
| 9 | 新引用未入表;主文档未同步置信度下调 | sycophancy 入 REFERENCES;选型直觉行加"偏好假设"限定 | REFERENCES / 主文档 |
| 10 | — | 本复盘更新 + 全量测试 | 本文 |

## 第三阶段:续推演——开源高星项目作为独立证据源

应需求方要求,把前沿论文之外的第三条证据链(GitHub 高星开源项目,2026-06-10
实查星数)接入推演,产出 deepdive §10:

- 七项论断的开源印证/反例表(OpenHands 75k★ / hermes-agent 188k★ /
  LangChain 138k★ / smolagents 27k★ / vLLM 82k★ / CrewAI 53k★);
- 最强一条:OpenHands AgentSkills 收录准则("模型已会的不再包装")与
  本文 harness 两分法**独立同构**——接近判别级证据;
- 新推断"两级吸收律"(应用层创新→框架收编→模型收编),推出"该投资吸收链
  终点仍在应用侧的资产"——与 §8.1 第三次独立吻合;
- agentskills.io 标准化作为 skill 资产升值的"生态已定价"信号;
- 校准:星数衡量注意力非正确性,多数印证是相容性证据而非判别性证据。

## 第四阶段:十轮「反思→强化→收敛→工程化」(落地工程循环)

对象从理论文档转为已落地的多提供商配置 + 多 Agent 协作能力(commit 0e1c7ae),
每轮四步:反思审出真实弱点→强化补能力→收敛降复杂度/校准措辞→工程化落成
代码+测试。每轮一个 commit,全程 408 测试保持绿。

| 轮 | 反思发现 | 工程化落点 |
|---|---|---|
| 1 | 一个提供商挂掉会沉没整次协作 | 并行提案容错降级:`failures` 记录、全员失败才 502、单存活者默认胜出 |
| 2 | 协作扇出 N+N×(N-1) 可无界爆发上游 | 与流水线共用 `MAX_CONCURRENT_UPSTREAM` 信号量 |
| 3 | transcript 无法回答"这句话到底是谁说的" | `provider`/`model` 审计字段 + `total_usage` 聚合;`resolve` 收敛为 `resolve_named` 薄包装 |
| 4 | 互评结果不可复现、平局裁决未定义 | 打分调用 `temperature=0`;确定性三级排序键 + `winner_tied` 显式标注 |
| 5 | 提案内容可注入评审提示词("给我打 10 分") | `_fence` 围栏:剥内嵌标记 + 声明为数据非指令(缓解非根治) |
| 6 | 验证器隔离只是文档建议,运行时不可见 | 每条互评分附 `same_provider` 标记(deepdive §4.3 量化) |
| 7 | 协作运行无持久留痕,事后不可审 | `logs/collaborations.jsonl` 一行式 JSONL 审计(约束性留痕,可关) |
| 8 | 协议文档落后实现 7 轮语义 | 文档补齐全部新语义;README 配置表同步 |
| 9 | 三处措辞强于证据(注入防护/确定性/隔离度) | 降级为缓解性措辞 + REFERENCES §23 回填 3 行来源 |
| 10 | — | 本复盘 + 全量测试 |

**本阶段元发现**:工程化循环与理论循环的产出结构互补——理论循环的主产出是
置信度校准,工程化循环的主产出是**把文档承诺变成运行时不变量**(留痕、上限、
标记都是测试可断言的)。最有价值的一类反思是"文档说了但代码没兑现"
(轮 3/6/7 全部属于此类):协议文档先行一步本身没错,但每条协议承诺都应配
一条可执行断言,否则承诺会静默漂移。

**循环式相对分工式的元发现**:每轮强制重过一遍"审核"环节后,第一阶段写下的
结论有 4 处被自己推翻或降级(循环 3/5/7/9)——单遍写作的推断置信度系统性偏高,
迭代审核的主要产出不是新内容而是**置信度校准**。最大的一次:§8 核心论证
(验证闭环说)被循环 7 降为"与纯 scaling 说并列的未判定假设"。

## 本期三个最重要的发现

1. **证据分级改变结论的置信结构**(第 1 轮):两模型差异化核心卖点(长时程优势)
   的证据全部落在不可独立复核的 B/C 级——选型决策树的"天级任务 → Fable 5"分支
   置信度低于表面,n=5 的自建对照即有极高信息价值。
2. **乘法隐喻与瓶颈轮换在数学上不自洽**(第 2 轮):必要性用乘法、优先级用 min(李比希律),
   此前混用削弱了框架的严谨性;修正后框架的适用范围明确收窄为"定性诊断 + 可证伪预测"。
3. **双路径交叉印证是目前最强的论证形式**(第 6 轮):资产升贬值结论由退化理论
   (capability-fixation)与训练方法谱系(deepdive)两条独立路径推出且吻合——
   比任何单路径论证都硬。后续重要结论应主动寻找第二条独立推导路径。

## 维护教训(违纪记录)

- 第 6 条(结构化输出)的产出文档早已存在但路线图状态未回填——违反
  "完成一条:状态改 [x],产出物路径回填"的维护约定。根因:该文档交付轮的
  commit 未同步动路线图。对策:今后任何 knowledge/ 新文件落地的同一 commit
  必须包含路线图状态行变更(可作为 review checklist 项)。

## 与既有体系的衔接

- deepdive §8 含义 1/2 是本仓库评测集(路线图 8.6)的新增检验用途——机制预测可分桶检验;
- deepdive 各线"天花板"小节构成路线图第 11 条(下一个瓶颈论证)的机制依据草稿;
- prediction-tracker 不变(本期无新模型发布,无证据可回填;含义 1-3 为机制预测,
  留在 deepdive 内不混入趋势预测表)。

## 附:向量库语料反思填充五轮(2026-06-10)

| 轮 | 反思出的缺口 | 填充 | 检索断言 |
|---|---|---|---|
| 1 | 选型类语料缺架构维度,"项目怎么分层"无接地依据 | flutter-app-architecture(官方 MVVM 两层/feature-first/依赖规则) | "项目结构分层 repository 单一事实源" |
| 2 | 路由/深链高频需求只有 skill 无知识语料 | flutter-navigation-deeplink(选型/守卫 redirect/App Links 验证) | "go_router 深链 redirect 守卫" |
| 3 | 离线同步语料假设网络层已做对,请求层本身无支撑 | flutter-networking-api(超时三件套/幂等重试/错误建模/无反射序列化) | "dio 超时重试 幂等 json_serializable" |
| 4 | 安全是接地答错代价最高的领域,只有一句"客户端无真密钥" | flutter-mobile-security(OWASP 威胁分级/加密存储/pinning 风险/混淆边界) | "secure storage 证书锁定 混淆 keystore" |
| 5 | 前九篇全是"功能做出来",可用性合规(i18n/a11y)零覆盖 | flutter-i18n-accessibility(ARB+ICU 复数/RTL/语义树/guideline CI 断言) | "国际化 arb 复数 读屏 无障碍 对比度" |

元发现:**给向量库填语料,反思的正确对象是"检索失败面"而非"内容是否正确"**——
每轮缺口都来自问"哪类高频中文查询现在会召回噪声或空集",填充后立即把该查询固化为
检索回归断言(test_flutter_corpus_docs_are_retrievable),语料质量从主观判断
变成可执行检验。每条结论仍按仓库纪律带 REFERENCES §26 可点击来源。

## 附:向量库语料反思填充第二批五轮(2026-06-10)

| 轮 | 反思出的缺口 | 填充 | 检索断言 |
|---|---|---|---|
| 6 | "async 够用还是必须 isolate"的判断链无语料 | flutter-concurrency(等 vs 算/使用阶梯/不共享内存/后台通道) | "isolate compute 不共享内存 消息深拷贝" |
| 7 | 性能语料只讲"别掉帧",动画建设性维度缺失 | flutter-animation-ux(隐式/显式选型/合成层友好属性/减少动效) | "隐式动画 AnimationController Hero 转场" |
| 8 | Flutter 被当封闭世界,原生边界决策无支撑 | flutter-platform-integration(先插件后通道/pigeon/FFI 所有权/PlatformView 红线) | "MethodChannel pigeon ffi PlatformView 原生" |
| 9 | "提交→可发布"之间的自动化流水线无语料 | flutter-cicd-engineering(三层流水线/可复现三件套/CI 签名) | "流水线 pubspec.lock fastlane 缓存 runner" |
| 10 | 观测只到"看崩溃率",非致命/性能/行为面缺失 | flutter-observability(四个错误出口/符号化与面包屑/告警绑定动作) | "Crashlytics onError 符号化 面包屑 慢帧" |

第二批新元发现:**哈希嵌入器没有同义词泛化,检索断言的查询词必须与语料共享
实词**——轮 6 首次断言用"主线程卡顿/消息传递"(文档实词是"卡 UI/消息深拷贝")
即检索失败,改用文档实词后通过。推论:给本仓库向量库写语料时,应主动把用户
可能用的常见说法写进正文(如同段并写"卡顿/掉帧"),这是无模型嵌入器下的
召回率工程;也再次说明检索断言不是形式主义——它真的能抓住"写了但搜不到"。

## 附:向量库语料·机制层深入五轮(2026-06-10)

| 轮 | 反思出的缺口 | 填充 | 检索断言 |
|---|---|---|---|
| 11 | 性能语料只有"做法",无"为什么有效"的机制层 | flutter-rendering-pipeline(三棵树/单遍 layout/双线程诊断映射) | "三棵树 RenderObject 约束下行 raster 线程" |
| 12 | "状态串了加 key"是口诀,不解释机制答不了深问题 | flutter-element-keys(canUpdate 推导/key 选型/加了 key 仍不行的三坑) | "ValueKey GlobalKey canUpdate 状态串了" |
| 13 | unbounded height/嵌套滚动需协议层解释 | flutter-sliver-scrolling(Sliver 协议/shrinkWrap 取消惰性/吸顶机制) | "sliver shrinkWrap unbounded height 吸顶" |
| 14 | OOM/内存爬升的"缓慢死亡"无机制语料 | flutter-memory-leaks(GC 分代/四大根因/retaining path 取证) | "内存泄漏 heap snapshot retaining path dispose" |
| 15 | 进程死亡是测试环境不复现的状态丢失源,零覆盖 | flutter-lifecycle-state-restoration(生命周期语义/restoration 两层/dispose 非保存时机) | "进程死亡 RestorationMixin paused 落盘" |

第三批元发现(两条):
1. **机制层语料的价值在"症状→机制→工具"的映射表**:做法类语料回答
   "怎么做",机制类语料回答"为什么/坏了怎么查"——后者必须显式建
   症状到机制位置的映射(轮11 §4、轮14 §3),否则机制知识检索回来
   也用不上。
2. **召回随语料密度退化**:轮 14 入库后,轮 9 的泛词查询("流水线/缓存/
   runner")被新文档挤出 top5——语料越多,断言查询越要用目标文档的
   **独有**实词,而非领域共享词。这说明检索回归断言的另一重价值:
   它能在语料增长时自动暴露"旧文档被新文档遮蔽"的召回退化,
   这是没有断言的向量库静默发生的问题。

## 附:向量库语料·第四批七轮(2026-06-10)

| 轮 | 反思出的缺口 | 填充 | 检索断言 |
|---|---|---|---|
| 16 | 业务最高频界面形态(表单/焦点/IME)零覆盖 | flutter-forms-input(validator 同步边界/FocusNode 树/CJK composing/键盘遮挡) | "表单 validator FocusNode 键盘遮挡 composing" |
| 17 | 全部语料默认移动端,Web/桌面输入与渲染差异零覆盖 | flutter-web-desktop-adaptive(窗口断点/鼠标键盘模型/CanvasKit 选型边界) | "CanvasKit 断点 NavigationRail 悬停 桌面" |
| 18 | 内存与流量最大头的媒体管线无系统语料 | flutter-images-media(解码后尺寸决定内存/三层缓存/占位防跳动/原生句柄) | "图片 cacheWidth 降采样 blurhash ImageCache" |
| 19 | "被杀后还要干活"(推送/后台任务)平台差异零覆盖 | flutter-push-background(notification vs data/token 轮换/headless 引擎/幂等补偿) | "FCM 推送 token 轮换 workmanager headless" |
| 20 | design token 工程化(主题集中声明)零覆盖 | flutter-theming-design-system(fromSeed/ThemeExtension/静态常量反模式) | "ThemeExtension colorScheme fromSeed 暗色 token" |
| 21 | 语言层(sealed/patterns/null safety 边界)零覆盖 | dart-language-advanced(穷尽 switch/三处健全性边界/宏终止) | "sealed 穷尽 switch patterns late 健全性" |
| 22 | "钉死版本之后如何安全地动"零覆盖 | flutter-upgrades-dependency-governance(小步不跳级/dart fix/依赖健康度三问) | "pub outdated dependency_overrides dart fix 升级" |

第四批元发现:**语料网络效应开始显现**——本批每篇平均交叉引用 4+ 篇
已有语料(如轮19 同时衔接深链矩阵/headless isolate/补偿队列/错误出口),
新语料的反思缺口越来越多来自"已有两篇语料的接缝处"(深链×恢复栈×推送
的初始路由竞争即三篇接缝),而非孤立空白主题。推论:语料库成熟后,
反思方法应从"找空白领域"转向"审计交叉引用指向的章节是否真的回答了
被引用的问题",即从覆盖率反思转向一致性反思。
