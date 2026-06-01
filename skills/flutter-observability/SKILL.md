---
id: flutter-observability
name: 可观测性 (崩溃上报 / 结构化日志 / 指标 / 追踪 / 行为分析)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [observability, crash-reporting, logging, metrics, tracing, analytics, crashlytics, sentry, opentelemetry]
applies_when: 需要在线上"看见"应用——崩溃、错误、性能、用户行为,并能定位与告警
stage_hints: [architecture, breakdown, acceptance]
---

# 可观测性

线上"看不见"等于盲飞。可观测性 = 让应用**对外可解释**:出了什么错、慢在哪、用户怎么用。
本 skill 管"**采什么信号、怎么落地、红线是什么**";失败的**建模**见 `flutter-error-handling`,
不泄露敏感信息见 `flutter-security`,符号文件归档见 `flutter-cicd-pipelines`,UI 卡顿剖析见 `flutter-performance-profiling`。

## 0. 三大支柱 + 两类信号

经典三支柱:**Logs(日志)/ Metrics(指标)/ Traces(追踪)**;客户端再加两类:**Crashes(崩溃)** 与 **Analytics(行为)**。
先想清楚"我要回答什么问题",再决定采什么——不是采得越多越好(成本、隐私、噪声)。

## 1. 崩溃与错误上报(客户端第一优先)

- 接崩溃平台:**Firebase Crashlytics** 或 **Sentry**;捕获三类:
  - Flutter 框架错误:`FlutterError.onError`。
  - 未捕获异步错误:`PlatformDispatcher.instance.onError`(或 `runZonedGuarded` 包 `runApp`)。
  - 原生崩溃:平台 SDK 自动捕获。
- **符号化**:发布构建会混淆/裁剪(R8、Dart obfuscation),必须上传 **mapping.txt / dSYM / Dart symbols**,否则栈不可读(归档见 `flutter-cicd-pipelines` §4)。
- 给错误带**上下文**:用户匿名 id、路由、版本、自定义键;但**绝不带 PII/令牌/密码**(见 §5 红线)。
- 区分**致命**(崩溃)与**非致命**(`recordError` 上报但不崩),把可预期失败(见 `flutter-error-handling`)按非致命上报。

## 2. 结构化日志

- 用 `logging` 包或封装,**结构化**(级别 + 事件名 + 字段 map),别只 `print`。
- 级别分明:`finest/fine/info/warning/severe`;**生产降噪**(只留 warning 以上 + 关键业务事件)。
- `debugPrint` 仅开发用;`print` 在生产会拖慢且泄露——CI lint 拦掉(见 `flutter-static-analysis`)。
- 日志要可被崩溃平台当**面包屑(breadcrumbs)**串起来:崩溃前发生了什么。

## 3. 指标(Metrics)

- 客户端关心:**启动时长**、**帧/jank**(见 `flutter-performance-profiling`)、网络成功率/时延、关键流程转化、内存。
- 工具:Firebase Performance Monitoring、自定义打点上报到后端、或 OpenTelemetry metrics。
- 指标是**聚合**信号(看趋势/分位数 p50/p95),不是单条日志;配告警阈值(如崩溃率突增、p95 时延上升)。

## 4. 分布式追踪(Traces)

- 一次用户操作跨"客户端 → 网关 → 多个后端服务"时,用 **trace id** 串起来定位瓶颈。
- 标准:**OpenTelemetry**(厂商中立);客户端在请求头注入 trace context(配合 `flutter-network-protocols`),后端续传。
- 移动端全量 trace 成本高,常用**采样**(按比例/按错误)。

## 5. 行为分析(Analytics)

- 工具:Firebase Analytics / 自建埋点;事件命名规范统一(动词_对象),建"事件字典"避免脏数据。
- **隐私合规**:采集前取得同意(GDPR/CCPA、App Store/Play 数据申报,见 `flutter-ios-platform` 隐私清单);提供关闭开关。
- 分析数据用于产品决策,与崩溃/性能分开看板。

## 红线(隐私与安全)

- ❌ **绝不**把密码、令牌、密钥、完整手机号/邮箱/身份证、精确定位写进日志/上报/分析(见 `flutter-security`)。
- ❌ 不在未取得同意时采集可识别个人的数据;遵守平台数据申报。
- 必要时对用户标识做**匿名化/哈希**;日志做敏感字段脱敏。

## 落地顺序(务实)

1. 先接**崩溃上报 + 符号上传**(投入小、回报最大)。
2. 再加**结构化日志 + 面包屑**。
3. 按需加**关键指标 + 告警**(启动/崩溃率/p95)。
4. 有跨服务排障需求再上**追踪**。
5. 行为分析按产品需要,合规先行。

## 反模式

- ❌ 线上只靠用户截图反馈,无崩溃上报(盲飞)。
- ❌ 上了 Crashlytics 但没传 dSYM/mapping,栈全是地址。
- ❌ 用 `print` 满地打日志,生产不降级,泄露还拖慢。
- ❌ 把敏感信息塞进日志/上报/分析。
- ❌ 把指标当日志采(每条都存),成本爆炸还看不出趋势。
- ❌ 采集行为数据不取同意、不做平台数据申报。
- ❌ 有信号没**告警**,出事还得人工翻看板。

## 参考 / References

- Flutter 错误处理(onError):<https://docs.flutter.dev/testing/errors>
- `PlatformDispatcher.onError`:<https://api.flutter.dev/flutter/dart-ui/PlatformDispatcher/onError.html>
- Firebase Crashlytics(Flutter):<https://firebase.google.com/docs/crashlytics/get-started?platform=flutter>
- Sentry for Flutter:<https://docs.sentry.io/platforms/flutter/>
- Firebase Performance Monitoring:<https://firebase.google.com/docs/perf-mon/get-started-flutter>
- Firebase Analytics(Flutter):<https://firebase.google.com/docs/analytics/get-started?platform=flutter>
- `logging` 包:<https://pub.dev/packages/logging>
- OpenTelemetry:<https://opentelemetry.io/docs/> · Dart:<https://pub.dev/packages/opentelemetry>
- Dart 混淆与符号:<https://docs.flutter.dev/deployment/obfuscate>
- 错误建模见 `flutter-error-handling`;安全红线见 `flutter-security`;符号归档见 `flutter-cicd-pipelines`;性能见 `flutter-performance-profiling`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先问要回答什么问题**,再决定采什么信号——可观测性是为"定位与决策"服务,不是数据越多越好。
- **崩溃上报性价比最高**:线上稳定性的第一道眼睛,优先接。
- **符号化是上报的前提**:没传符号的崩溃栈等于没上报。
- **隐私是硬约束**:任何信号采集都先过"会不会泄露个人信息/密钥"这关。

**诚实边界:**

- 各 SDK(Crashlytics/Sentry/OTel)接入与配置随版本演进,以当时官方文档为准。
- 采样率、保留期、告警阈值依业务与成本权衡,无通用最优值,需实测。
- 客户端可观测性能看到"现象",根因常需结合后端追踪/日志联合排查。
- 合规要求(GDPR/CCPA/各地法规、平台数据申报)因地区与品类而异,需法务/合规确认,本 skill 仅提示红线。
