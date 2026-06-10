# Flutter 可观测性与线上诊断(向量库优质语料·轮10)

> 反思缺口:发布语料以"看崩溃率"收尾,但崩溃只是线上问题的最响亮一种——
> 非致命错误、性能劣化、行为漏斗的观测无语料。来源见 REFERENCES §27。

## 1. 错误捕获的完整面(只接 Crashlytics 默认还不够)

Flutter 应用有四个错误出口,漏接任何一个都会出现"用户说崩了但后台没记录":

1. `FlutterError.onError`:框架层错误(build/layout 异常);
2. `PlatformDispatcher.instance.onError`:Dart 层未捕获异步错误(返回 true
   表示已处理)——**最常被漏接**,async 异常默认不走 FlutterError;
3. 原生层崩溃:由 Crashlytics/Sentry 的原生 SDK 捕获(Dart 侧接不到);
4. isolate 内错误:不冒泡,需 onError 端口显式回传(flutter-concurrency §3)。

非致命错误用 `recordError(fatal: false)` 主动上报(如解析失败走了降级),
否则"静默降级"在线上等于不可见劣化。

## 2. 让错误可诊断的三件事

- **符号化**:`--obfuscate` 构建必须同发布版本一致地上传符号/映射文件,
  否则堆栈是乱码(flutter-release-engineering §3 / flutter-mobile-security §4);
- **面包屑与上下文**:错误发生前的导航路径、关键操作、自定义 key
  (用户分群/AB 桶)——没有上下文的堆栈只能修"是什么",修不了"为什么";
- **分版本/分灰度桶看**:崩溃率必须按版本+灰度阶段切片,全量均值会掩盖
  新版本回归(flutter-release-engineering §3 的爬坡决策依赖这一切片)。

## 3. 性能与行为观测

- 线上性能:Firebase Performance / Sentry 采集冷启动、首帧、慢帧/冻结帧率,
  与 DevTools 本地画像互补——本地 profile 找原因,线上指标定优先级
  (flutter-performance §1 是本地侧,本篇是线上侧);
- 行为漏斗:Analytics 事件命名要先定 schema(事件表入库评审),散弹式
  `logEvent` 半年后无人能解释字段含义;
- 结构化日志:开发期 `dart:developer log`,线上日志分级采样上报,
  `print` 在 release 下不可靠且 logcat 全局可读(flutter-mobile-security §2)。

## 4. 告警的工程纪律

- 告警绑定可执行动作:崩溃率超灰度门槛 → 暂停爬坡;无动作的告警很快被静音;
- 周期性看"非致命错误 top N"——它们是下一个崩溃的前身,也是用户流失的
  无声原因。

## 5. 与本仓库其他语料的衔接

- 灰度爬坡门槛 ← flutter-release-engineering §3;
- isolate 错误回传 ← flutter-concurrency §3;
- 本地性能画像 ← flutter-performance §1。
