---
id: dart-async-streams
name: Dart 异步与流编程(Future 组合 / Stream / async* / 取消与背压 / zones)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [async, future, stream, async-await, generator, broadcast, backpressure, cancellation, completer, event-loop]
applies_when: 需要编排异步流程、处理连续事件流、组合/取消多个异步任务,或排查"异步执行顺序/丢事件"问题时
stage_hints: [architecture, breakdown, implementation]
see_also: [flutter-concurrency-isolates, flutter-error-handling, flutter-resource-lifecycle, dart-language-idioms]
---

# Dart 异步与流编程

本 skill 负责**单个隔离区内的异步编排**:`Future` 组合、`Stream` 处理、`async*` 生成、
取消与背压、事件循环顺序。它和 `flutter-concurrency-isolates` 分工明确——
本 skill 管"等待 IO / 编排事件"(并发,不并行);**CPU 密集、需要真并行**的重计算
(跨隔离区、`Isolate.run`/`compute`)见 `flutter-concurrency-isolates`。
异步里的错误处理见 `flutter-error-handling`,订阅的生命周期清理见 `flutter-resource-lifecycle`。

## 0. 心智模型:单线程事件循环 + 协作式让步

Dart 单隔离区是**单线程**的。`async`/`await` 不开线程,只是在 `await` 处把控制权
交回事件循环,等 `Future` 完成再续跑。所以"异步"≠"并行":两个 `await` 的网络请求
是**交错**进行,不是用两个 CPU 核跑。

```
微任务队列(microtask)优先于事件队列(event);
scheduleMicrotask / Future.value 进微任务,Timer / IO 进事件队列。
```

## 1. Future:组合与并行等待

- 串行依赖用顺序 `await`;**互不依赖**的多个请求用 `Future.wait([...])` 并行等待,显著省时。
- `Future.any` 取最先完成;超时用 `.timeout(Duration)`(并处理 `TimeoutException`)。
- `Completer` 用于把"回调式 API"桥接成 `Future`,但能用 `async` 就别手搓 Completer。
- 异常变成 `Future` 的 error:**必须** `await` + try/catch 才能捕获;fire-and-forget(`unawaited`)会丢异常(见 `flutter-error-handling` §5)。

## 2. Stream:连续事件

- **single-subscription**(默认,只能监听一次,如文件读取)vs **broadcast**(可多监听,如按钮事件)。别把 single 当 broadcast 用。
- 变换用 `map`/`where`/`expand`/`asyncMap`;**别在 `listen` 回调里手动堆状态**能用算子就用算子。
- 用 `StreamController` 暴露事件源时,记得 `close()`;`onListen`/`onCancel` 管理资源。
- `async*` + `yield` 写生成器流;`yield*` 委托子流。

## 3. 取消与背压(容易踩的坑)

- **订阅必须取消**:`StreamSubscription` 不取消 = 内存泄漏 + 回调打到已 dispose 的对象(见 `flutter-resource-lifecycle`)。
- `await for` 会一直消费到流结束;在 widget 里慎用,优先 `listen` + 在 `dispose` 取消。
- **背压**:生产快于消费时,`asyncMap`/`pause`/缓冲策略控制速率;`StreamController` 默认会缓冲未消费事件(可能涨内存)。
- 防抖/节流(搜索框等)用 `rxdart` 的 `debounceTime`/`throttleTime`,或自己用 `Timer` 实现。

## 4. 与 Flutter 的衔接

- UI 消费流优先用 `StreamBuilder`,或状态管理的封装(Riverpod `StreamProvider`/`AsyncValue`,见 `state-management`)——别手动 `setState`。
- `FutureBuilder`/`StreamBuilder` 必处理 加载/数据/错误 三态。

## 5. zones(谨慎使用)

- `runZonedGuarded` 可捕获 zone 内未捕获的异步错误,常用于 `main` 兜底上报(与 `PlatformDispatcher.onError` 别重复,见 `flutter-error-handling` §3)。
- zone 还能覆盖 `print`/注入上下文,但属高级用法;**绝大多数业务代码不该碰 zone**。

## 反模式

- ❌ 把独立的多个 `await` 串行写,本可 `Future.wait` 并行(白白变慢)。
- ❌ fire-and-forget 异步调用,异常无声丢失(用 `unawaited` 也要先想清楚错误去哪)。
- ❌ `StreamController`/`StreamSubscription` 不 `close`/`cancel`,泄漏 + 回调打到死对象。
- ❌ 在 `listen` 回调里堆命令式状态机,能用流算子表达却不用。
- ❌ 把异步当并行,以为 `async` 能加速 CPU 密集计算(那是 isolate 的活,见 `flutter-concurrency-isolates`)。
- ❌ 滥用 zone 做控制流,徒增理解成本。

## 参考 / References

- Dart 异步编程(async/await):<https://dart.dev/libraries/async/async-await>
- `Future` API:<https://api.dart.dev/stable/dart-async/Future-class.html>
- `Stream` 教程:<https://dart.dev/libraries/async/using-streams>
- 创建流(`async*` / StreamController):<https://dart.dev/libraries/async/creating-streams>
- 事件循环:<https://dart.dev/articles/archive/event-loop>
- `StreamBuilder`:<https://api.flutter.dev/flutter/widgets/StreamBuilder-class.html>
- `rxdart`:<https://pub.dev/packages/rxdart>
- 并行/隔离区见 `flutter-concurrency-isolates`;订阅清理见 `flutter-resource-lifecycle`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **异步是交错不是并行**:单线程让步,别指望 `await` 用上多核。
- **凡订阅必取消**:流的生命周期要和持有者绑定,否则泄漏。
- **能用算子表达就别手写状态机**:`map/where/asyncMap` 比一堆回调清晰。

**诚实边界:**

- `Stream` 算子组合能力不如 RxDart 丰富;复杂事件编排可引入 `rxdart`,但增依赖与认知成本。
- 背压策略没有银弹,取决于生产/消费速率与可丢失性,需按场景权衡。
- 跨隔离区通信只能传可序列化消息,不能共享对象引用——重计算并行见 `flutter-concurrency-isolates`。
