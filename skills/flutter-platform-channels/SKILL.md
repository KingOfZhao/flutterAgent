---
id: flutter-platform-channels
name: Flutter 原生互操作 (MethodChannel / EventChannel / Pigeon / dart:ffi)
version: 1.0.0
platforms: [all, mobile, desktop]
tags: [platform-channel, method-channel, event-channel, pigeon, ffi, native, interop, jni, objc, swift, kotlin]
applies_when: 需要调用平台原生能力(iOS/Android/桌面),或与 C/C++ 库互操作
stage_hints: [architecture, breakdown]
---

# Flutter 原生互操作

Flutter 自带的能力覆盖不到的平台特性(蓝牙、传感器、原生 SDK、系统 API、C/C++ 库)
要靠**原生互操作**:Dart 与平台原生代码(Kotlin/Java、Swift/Obj-C、C++)互相调用。
本 skill 给"选哪种通道、怎么用对、怎么不踩线程坑"的判断,是 `flutter-mobile` /
`flutter-desktop` 在"打通原生"这件事上的专用 skill。具体平台工程配置见
`flutter-android-platform` / `flutter-ios-platform` / `flutter-desktop-platform`。

## 0. 先问:真的需要原生吗?

- 先在 **pub.dev** 找现成插件(很多原生能力已有维护良好的 plugin,见 `flutter-dependency-maintenance` 的选包判据)。
- 自己写原生只在"没有合适插件 / 要包装公司私有 SDK / 性能敏感的 C/C++"时才做——它带来跨平台维护成本。

## 1. 选择互操作方式

| 方式 | 适用 | 特点 |
|---|---|---|
| **MethodChannel** | 一次性请求-响应调用原生方法 | 异步、按名字调用、手写编解码易出错 |
| **EventChannel** | 原生持续推流给 Dart(传感器/位置/电量) | 单向 stream |
| **BasicMessageChannel** | 双向自由消息 | 自定义 codec |
| **Pigeon** | 结构化、类型安全的 Dart↔原生接口 | **推荐**:代码生成,免手写字符串与编解码 |
| **dart:ffi** | 直接调 C/C++(无需写平台胶水) | 同步、零拷贝、适合原生库;不经平台线程 |
| **JNI / native interop(`jnigen`/`ffigen`)** | 直接从 Dart 调 Java/Kotlin/Obj-C | 新兴,免写 channel 胶水 |

一句话:**和原生平台 API 打交道首选 Pigeon(类型安全);和 C/C++ 库打交道用 dart:ffi。** 裸 MethodChannel 用于简单/临时场景。

## 2. MethodChannel 基本形 + 线程坑

```dart
const channel = MethodChannel('com.example/battery');
final level = await channel.invokeMethod<int>('getBatteryLevel');
```

- **通道名全局唯一**:用反向域名前缀,避免插件间撞名。
- **类型要对齐**:Dart 与原生两端的参数/返回类型映射要一致(`int`/`double`/`String`/`List`/`Map`),错了运行时才炸——这正是 Pigeon 的价值。
- **线程**:平台侧的 channel 回调默认在**平台主线程(UI 线程)**;原生里做重活要切到后台线程,算完再回主线程回 `result`,否则卡住原生 UI。Dart 侧调用是异步的,但别假设瞬时返回。

## 3. Pigeon(推荐:类型安全 + 免编解码)

- 用一个 Dart 文件定义 `@HostApi()`(Dart 调原生)/`@FlutterApi()`(原生调 Dart)接口,Pigeon **生成** Dart 与各平台的强类型胶水代码。
- 改接口只改定义文件 + 重新生成,杜绝"两端字符串/类型对不上"的运行时错误。
- 生成属于代码生成范畴,纳入 `flutter-codegen` 的管理(产物不手改、版本对齐)。

## 4. dart:ffi(调 C/C++)

- `ffigen` 从 C 头文件**生成** Dart 绑定;`DynamicLibrary.open` 加载 `.so`/`.dylib`/`.dll`。
- 同步调用、无消息复制,适合性能敏感与现成 C 库。
- 注意:内存要手动管理(`malloc`/`free`、`Pointer`),跨 isolate 使用有约束;长耗时 FFI 调用仍会阻塞调用它的 isolate(配合 `flutter-concurrency-isolates`)。

## 5. 插件化(把原生能力封装成可复用 plugin)

- 要在多个 app 复用,做成 **federated plugin**:平台接口包 + 各平台实现包 + app-facing 包(见 `dart-api-package-design`)。
- 单 app 用,放在 app 的 `android/`、`ios/`、`windows/` 等目录里直接实现即可。

## 6. 错误与可测性

- 原生侧用 `result.error(code, message, details)` 回错误;Dart 侧 catch `PlatformException` 并翻译成领域错误(见 `flutter-error-handling`)。
- 把 channel 调用封装在一个 Dart 抽象后面,业务层依赖抽象——便于 mock 测试(见 `flutter-testing`),也隔离平台差异(平台在边界,见 `flutter-engineer-mindset`)。

## 反模式

- ❌ 凡事自己写 channel,无视 pub.dev 已有的成熟插件。
- ❌ 裸 MethodChannel 手写大量字符串方法名 + 手编解码,类型对不上到运行时才炸(应上 Pigeon)。
- ❌ 在平台 channel 回调里跑重活,卡住原生主线程。
- ❌ FFI 不管内存,`Pointer` 泄漏 / use-after-free。
- ❌ 业务代码直接散落 `MethodChannel` 调用,无法 mock、无法测、平台耦合。

## 参考 / References

- 编写平台特定代码(platform channels):<https://docs.flutter.dev/platform-integration/platform-channels>
- Pigeon:<https://pub.dev/packages/pigeon>
- C 互操作 dart:ffi:<https://dart.dev/interop/c-interop>
- `ffigen`:<https://pub.dev/packages/ffigen>
- Objective-C/Swift 互操作:<https://dart.dev/interop/objective-c-interop>
- Java/Kotlin 互操作(`jnigen`):<https://dart.dev/interop/java-interop>
- 开发 packages & plugins:<https://docs.flutter.dev/packages-and-plugins/developing-packages>
- 平台工程配置见 `flutter-android-platform` / `flutter-ios-platform` / `flutter-desktop-platform`;代码生成见 `flutter-codegen`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先找插件,再写原生**:原生互操作是跨平台维护负债,能复用就别自造。
- **类型安全优先**:和平台 API 打交道用 Pigeon、和 C 用 ffigen,让生成器消灭"字符串/类型对不上"。
- **平台在边界**:channel 调用封装在抽象后面,业务依赖抽象,平台差异不渗进核心。

**诚实边界:**

- 原生代码要分别在各平台用真机/真环境验证,Dart 侧测试覆盖不到原生实现。
- 线程模型(平台主线程 vs 后台、isolate 与 FFI)易踩坑,需按平台文档实测。
- 新兴的 jnigen/objc interop 仍在演进,API 可能变化,以官方文档为准。
