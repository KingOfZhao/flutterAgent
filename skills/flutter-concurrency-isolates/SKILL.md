---
id: flutter-concurrency-isolates
name: Flutter 并发与隔离区 (isolate / compute / Isolate.run / 消息传递)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [concurrency, isolate, compute, async, parallelism, jank, threads, message-passing, performance]
applies_when: 有重计算/阻塞工作要挪出 UI 线程,或需要真正并行(isolate)、处理并发与竞态
stage_hints: [architecture, breakdown, implementation]
---

# Flutter 并发与隔离区

Dart 是**单线程事件循环 + isolate 模型**:`async`/`await` 让你在**同一个线程**上
交错执行(并发,不是并行),`Isolate` 才是**真正的并行**(各有独立内存,靠消息通信)。
搞混这两者,就会写出"明明 await 了还是卡 UI"的代码。本 skill 给"什么时候用谁、
怎么用对"的判断,与 `dart-language-idioms`(async 语法)、`flutter-performance`(帧预算)配合。

## 0. 核心区分:并发 vs 并行

- **`async`/`await`(并发)**:在 UI isolate 的事件循环里**等 I/O**(网络、文件)时让出,不阻塞。但 **CPU 密集计算照样在 UI 线程跑**——`await` 一个纯计算函数**不会**让它不卡。
- **`Isolate`(并行)**:开一个有独立内存的执行单元,把 CPU 密集活儿挪过去,真正与 UI 线程并行,算完用消息把结果送回。
- 一句话判断:**等外部用 async;算得久用 isolate。**

## 1. 什么该挪进 isolate

典型 CPU 密集、会撑爆 16ms 帧预算(见 `flutter-performance`)的活儿:
- 解析大 JSON / 大文件、图像处理、加解密、压缩、复杂排序或计算。
- 经验阈值:一段同步计算可能 > 几毫秒,就考虑挪走;真的久(> 一帧)就必须挪。

不该挪的:等网络/磁盘(那是 I/O,用 `async` 即可,挪进 isolate 反而多此一举)。

## 2. 首选 `Isolate.run`(Dart 2.19+,一次性计算)

```dart
final result = await Isolate.run(() => _expensiveParse(bigJsonString));
```

- 最简单:开一个短命 isolate 跑闭包,返回 `Future`,算完自动销毁。
- 传入/返回的数据会在 isolate 间**复制**(有传输成本),所以适合"输入输出不算巨大、计算才是瓶颈"的场景。

## 3. `compute`(Flutter 老牌封装)

```dart
final parsed = await compute(_parseUsers, jsonString);  // 顶层或 static 函数
```

- `compute(callback, message)` 是 Flutter 对一次性 isolate 的封装,语义同 `Isolate.run`。
- 限制:回调必须是**顶层函数或 static 方法**(因为要被发到新 isolate)。新代码可直接用 `Isolate.run`。

## 4. 长生命周期 isolate + 消息传递(高级)

一次性 `Isolate.run` 不够时(要持续往一个后台 isolate 喂任务):
- 用 `Isolate.spawn` + `SendPort`/`ReceivePort` 建双向通道,自己管理生命周期与销毁。
- 也可用 `package:isolate` 或更高层的 worker 池方案。
- 复杂度显著上升:要处理端口关闭、错误传播、isolate 泄漏——非必要不上。

## 5. 数据传递的约束

- isolate 间**不共享内存**,消息按值复制(`TransferableTypedData` 可减少大字节数组的拷贝开销)。
- 能发的对象类型有限制(基本类型、List/Map、SendPort 等);别想把带闭包/句柄的复杂对象塞过去。
- 设计上让"送过去的输入"和"送回来的输出"尽量小且可序列化。

## 6. Web 平台的不同

- **Web 没有 Dart isolate 的并行语义**(底层是 Web Worker,限制多):`compute`/`Isolate.run` 在 web 上行为受限,常常退化为在主 isolate 执行或需要特殊处理。
- web 端的重计算要结合 Web Worker / WASM 策略评估(见 `flutter-web`),别假设移动端的 isolate 写法在 web 上等价。

## 7. 并发正确性(同一 isolate 内)

- 单 isolate 事件循环内**没有抢占式并发**,但仍有**交错**:`await` 之后世界可能变了(状态被别的回调改过),别假设 `await` 前后状态不变。
- 多个异步操作竞态:用 `Future.wait` 收敛、用取消标志/最新者优先(参见 `flutter-network` 的请求竞态)避免"旧响应覆盖新结果"。

## 反模式

- ❌ 以为 `await 一个纯计算` 就不卡 UI——CPU 活儿没挪进 isolate 照样掉帧。
- ❌ 把纯 I/O(网络/磁盘)硬塞进 isolate,徒增复制开销。
- ❌ 用 `Isolate.spawn` 长 isolate 却不销毁/不关端口,造成泄漏。
- ❌ 往 isolate 发巨大的数据,复制成本盖过并行收益。
- ❌ 在 web 上照搬移动端 isolate 假设,不验证平台差异。

## 参考 / References

- 并发编程(Dart 官方,isolate 模型):<https://dart.dev/language/concurrency>
- `Isolate.run`:<https://api.dart.dev/stable/dart-isolate/Isolate/run.html>
- `Isolate.spawn` / Ports:<https://api.dart.dev/stable/dart-isolate/Isolate-class.html>
- Flutter `compute`:<https://api.flutter.dev/flutter/foundation/compute.html>
- 异步编程 futures/async-await:<https://dart.dev/libraries/async/async-await>
- 渲染性能 / 帧预算:<https://docs.flutter.dev/perf/rendering-performance>
- 帧预算与性能见 `flutter-performance`;请求竞态见 `flutter-network`;web 限制见 `flutter-web`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **等外部用 async,算得久用 isolate**:并发(交错)与并行(独立内存)是两件事,选错就白忙。
- **isolate 不共享内存,只传消息**:设计时让输入输出小而可序列化,复制成本要算进收益。
- **先量再挪**:用 DevTools 确认是 CPU 卡顿再上 isolate,别凭感觉过度工程。

**诚实边界:**

- isolate 有创建与数据复制开销;小计算挪过去可能更慢,需 profile 取舍。
- Web 的并行模型与移动端不同,这里给原则,具体以平台实测为准。
- 长生命周期 isolate 的生命周期/错误管理复杂,非高频场景不建议自造。
