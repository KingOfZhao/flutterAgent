---
id: flutter-error-handling
name: Flutter 错误处理策略 (Result/Either vs 异常 / 错误边界 / 日志上报)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [error-handling, exceptions, result, either, failure, crash, logging, reporting, resilience]
applies_when: 设计失败路径——可预期失败怎么建模、未预期异常怎么兜底、错误怎么记录上报
stage_hints: [architecture, breakdown]
---

# Flutter 错误处理策略

代码质量的分水岭往往在**失败路径**:happy path 谁都会写,健壮性体现在
"出错时会怎样"。本 skill 给一套"可预期失败用类型建模、未预期异常用边界兜底、
全程可观测"的策略,是 `flutter-engineering-workflow` 实现阶段的横切关注点。
异步语言机制见 `dart-language-idioms`,资源清理见 `flutter-resource-lifecycle`。

## 0. 第一刀:可预期失败 vs 未预期异常

- **可预期失败(expected)**:网络超时、404、表单校验失败、文件不存在——这些是**业务流程的一部分**,应当作"正常返回值"建模,让调用方**被迫处理**。
- **未预期异常(unexpected / bug)**:空指针、状态非法、断言失败——这些是**程序错误**,应快速失败 + 上报,而不是吞掉假装没事。

> 区分清楚,才不会"该处理的没处理、该崩的没崩"。

## 1. 可预期失败:用类型建模(Result / Either)

把"成功或失败"编码进**返回类型**,而不是靠抛异常 + 调用方记得 try/catch:

```dart
sealed class Result<T> {
  const Result();
}
class Ok<T> extends Result<T> {
  final T value;
  const Ok(this.value);
}
class Err<T> extends Result<T> {
  final Failure failure;
  const Err(this.failure);
}
```

- 配合 Dart 3 的 **sealed + switch 穷尽**(见 `dart-language-idioms`),编译器逼调用方处理每种结果。
- 也可用社区包 `fpdart`(`Either<L,R>` / `TaskEither`)或 `result_dart`,但**全仓库统一一种**,别混用。
- 在 **domain 层**用 `Failure` 表达业务失败(纯 Dart,可单测),在 **data 层**把底层异常(`DioException`/`SocketException`…)翻译成 `Failure`。

## 2. 用自定义异常类型,别裸抛字符串

- 抛领域明确的异常类(`PaymentDeclinedException`),不要 `throw 'error'` 或裸 `Exception('...')`。
- 异常携带足够上下文(发生位置、关键参数,但**不含敏感数据**)。
- 区分 `Exception`(可预期、可处理)与 `Error`(程序 bug,通常不该 catch)。

## 3. 边界兜底:别让一处错误炸穿整个 app

- **UI 三态**:每个异步视图都要有 加载 / 数据 / **错误** 三态;错误态给用户可读信息 + 重试入口(配合 Riverpod `AsyncValue`,见 `remi-rousselet-mindset` / `state-management`)。
- **Widget 错误边界**:用 `ErrorWidget.builder` 自定义构建期错误展示(release 别暴露堆栈)。
- **全局兜底**:
  ```dart
  void main() {
    FlutterError.onError = (details) { /* 记录 + 上报 framework 错误 */ };
    PlatformDispatcher.instance.onError = (error, stack) {
      // 兜未捕获的异步错误,返回 true 表示已处理
      return true;
    };
    runApp(const MyApp());
  }
  ```
- `runZonedGuarded` 可兜 zone 内未捕获错误(按需,与上面机制别重复上报)。

## 4. 日志与上报(可观测性)

- 用 `dart:developer` 的 `log()` 或 `logging` 包做结构化日志,**别用 `print`** 进生产。
- 接入崩溃/错误上报(Crashlytics / Sentry 等),把未预期异常 + 堆栈送上去,带版本/平台维度。
- **绝不**把密钥、token、个人敏感信息写进日志或上报(见 `flutter-security`)。
- 区分日志级别;release 与 debug 的日志详尽程度不同。

## 5. 异步与资源的错误

- `async` 函数的异常会变成 `Future` 的 error,**必须** `await` + try/catch 或 `.catchError` 才能捕获;fire-and-forget 会丢异常。
- `Stream` 错误通过 `onError` 处理;订阅记得取消(见 `flutter-resource-lifecycle`)。
- `try/finally`(或 `Future` 的 `whenComplete`)确保清理一定执行。

## 6. 测试失败路径

- 失败路径和成功路径一样要测:mock 出错误,断言返回 `Err`/抛对应异常/UI 显示错误态(见 `flutter-testing`)。
- 修 bug 必带能复现该异常的回归测试(见 `flutter-debugging`)。

## 反模式

- ❌ `catch (e) {}` 静默吞异常,错误无声消失(评审红线,见 `flutter-code-review`)。
- ❌ `catch (e) { print(e); }` 当处理——既没恢复也没上报。
- ❌ 用异常控制正常业务流程(可预期失败应建模为返回值)。
- ❌ 把底层异常(`DioException`)直接泄漏到 UI 层,耦合且信息无用。
- ❌ 错误信息/堆栈在 release 直接弹给用户,或把敏感数据写进日志。

## 参考 / References

- Flutter 错误处理(handling errors):<https://docs.flutter.dev/testing/errors>
- `PlatformDispatcher.onError`:<https://api.flutter.dev/flutter/dart-ui/PlatformDispatcher/onError.html>
- `FlutterError.onError`:<https://api.flutter.dev/flutter/foundation/FlutterError/onError.html>
- Dart 异常(Exception/Error):<https://dart.dev/language/error-handling>
- 异步错误处理:<https://dart.dev/libraries/async/async-await>
- `logging` 包:<https://pub.dev/packages/logging>
- `fpdart`(Either/TaskEither):<https://pub.dev/packages/fpdart>
- 状态层错误态见 `state-management`;安全见 `flutter-security`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **失败路径是一等公民**:happy path 谁都会,质量在于出错时的行为。
- **可预期失败建模为值,未预期异常快速失败 + 上报**:别让这两类混在一起。
- **错误必须可观测**:吞掉的异常等于没发生过,debug 时无从查起。

**诚实边界:**

- Result/Either vs 异常无绝对优劣;关键是**全仓库一致**,别两套混用。
- 全局兜底能防"白屏崩溃",但不能替代在正确层级处理具体错误。
- 上报方案(Sentry/Crashlytics)涉及隐私合规,接入前确认数据脱敏与用户同意。
