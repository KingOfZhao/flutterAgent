# Flutter 平台集成与原生互操作(向量库优质语料·轮8)

> 反思缺口:语料把 Flutter 当封闭世界,"需要调原生能力/嵌原生视图/接 FFI"
> 这条边界线上的决策无支撑。来源见 REFERENCES §27。

## 1. 先找插件,再写通道

优先级:pub.dev 现成插件(看维护活跃度/平台覆盖/issue 健康度)→ 自写
platform channel → FFI。**自写原生代码是维护负债**(每个平台一份),
只有插件缺失或质量不可接受时才下场。

## 2. Platform Channel 要点

- **MethodChannel**:一次性调用(取电量、拉起原生页);通道名用域名反写
  唯一化;方法名/参数结构是隐式契约,平台两端各写一份,容易漂移——
  跨端消息结构复杂时用 **pigeon** 代码生成类型安全的双端接口,消灭手写
  序列化错配。
- **EventChannel**:原生→Dart 的持续流(传感器/扫码结果);记得在
  onCancel 释放原生侦听器,否则页面退出后原生侧还在采集。
- **线程规则**:平台通道默认必须在平台主线程收发(Android main thread /
  iOS main queue);原生侧耗时操作要自己切后台线程再回主线程应答,
  在通道回调里做磁盘/网络是原生侧 ANR 的常见来源。
- 错误传递:原生侧用 `result.error(code, message, details)` 结构化返回,
  Dart 侧捕 `PlatformException` 按 code 分支——把原生异常吞成 null 会让
  线上问题不可诊断(对应 flutter-networking-api §2 的错误建模原则)。

## 3. dart:ffi(C 互操作)

- 适用:已有 C/C++/Rust 库(编解码、加密、算法核)——FFI 是同步直调,
  没有通道的序列化开销;但**FFI 同步调用发生在当前 isolate**,耗时计算
  仍需配 isolate(flutter-concurrency §1 判断标准同样适用)。
- 工具链:`ffigen` 从头文件生成绑定;内存所有权要明确(谁分配谁释放),
  `NativeFinalizer` 兜底,泄漏与 double-free 是 FFI 两大事故源。

## 4. 嵌入原生视图(PlatformView)

- 地图/WebView/广告 SDK 等只能嵌原生视图;PlatformView 有真实合成成本
  (Android 上历经多种合成模式演进),**一屏多个 PlatformView 是性能红线**,
  列表里逐项嵌原生视图基本不可行——能用纯 Flutter 替代(如 flutter_map)
  时优先替代。
- 手势分发需显式声明 gestureRecognizers,否则原生视图内滑动与 Flutter
  滚动冲突(与 flutter-animation-ux §3 手势竞技场同一机制)。

## 5. 与本仓库其他语料的衔接

- 后台 isolate 调通道需 BackgroundIsolateBinaryMessenger ← flutter-concurrency §3;
- 原生依赖引入的供应链审计 ← flutter-mobile-security §4;
- 含原生代码的构建/签名影响 ← flutter-release-engineering §1。
