---
id: flutter-mobile
name: Flutter Mobile (iOS / Android) 工程规范
version: 1.0.0
platforms: [mobile, ios, android]
tags: [flutter, mobile, ios, android]
applies_when: 需求目标平台包含 Android 或 iOS
stage_hints: [spec, architecture, breakdown]
---

# Flutter Mobile 工程规范

你正在为一个 **面向 iOS / Android 的 Flutter 移动端** 项目产出工程设计。
所有产出必须遵循下列约束,不要发明不存在的库,不要给伪代码。

## 1. 技术栈基线(全部可在 pub.dev 验证)

| 类别 | 选择 | pub.dev / 文档 | 选择理由 |
|---|---|---|---|
| Flutter SDK | ≥ 3.22 | <https://docs.flutter.dev/release/release-notes> | Material 3 默认、impeller 默认、`textScaler` |
| Dart | ≥ 3.4 | <https://dart.dev/guides/language/evolution> | record / pattern matching |
| 状态管理(推荐) | **Riverpod 2.x** | <https://pub.dev/packages/flutter_riverpod> | 无 BuildContext 依赖、编译期安全 |
| 状态管理(等价路径) | BLoC 8.x | <https://pub.dev/packages/flutter_bloc> | 事件流强约束场景;Flutter 团队两者皆中立 |
| 路由 | **go_router 14.x**(Flutter team 维护) | <https://pub.dev/packages/go_router> | 支持深链 / Web URL / shell route |
| 网络 | `dio 5.x` | <https://pub.dev/packages/dio> | 拦截器 / 取消 / 重试生态最齐 |
| API 客户端生成(可选) | `retrofit 4.x` + `json_serializable` | <https://pub.dev/packages/retrofit> | 基于 dio 的注解式客户端 |
| K-V 存储 | `shared_preferences` | <https://pub.dev/packages/shared_preferences>(Flutter team) | — |
| 关系型 DB | `drift 2.x`(原名 moor) | <https://pub.dev/packages/drift> | type-safe、isolate-aware、跨平台 |
| 安全存储 | `flutter_secure_storage` | <https://pub.dev/packages/flutter_secure_storage> | iOS Keychain / Android EncryptedSharedPreferences |
| 国际化 | `flutter_localizations` + `intl` + gen-l10n | <https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization> | 见 `flutter-i18n` skill |
| 主题 | Material 3 | <https://m3.material.io> | Flutter 3.16+ 默认 |
| 测试 | `flutter_test` + `integration_test` + `mocktail` | <https://docs.flutter.dev/testing>;<https://pub.dev/packages/mocktail> | 见 `flutter-testing` skill |
| Lint | `flutter_lints` 或 `very_good_analysis` | <https://pub.dev/packages/flutter_lints>;<https://pub.dev/packages/very_good_analysis> | 后者更严格,Very Good Ventures 出品 |

## 2. 必须考虑的移动端能力

- **权限**: 相机、相册、定位、通知、麦克风,使用 `permission_handler`,需要逐平台说明 `Info.plist` 与 `AndroidManifest` 配置
- **生命周期**: 前后台切换 (`AppLifecycleState`) 的副作用要明确(轮询暂停、socket 断开);iOS 13+ 使用 UIScene 生命周期,Flutter 3.44 已支持
- **推送**: APNs(iOS) + FCM(Android),要求列出 token 获取流程、payload 结构、点击落地路由
- **离线优先**: 列表类页面默认有本地缓存 → swr 策略,弱网降级方案要写出来
- **包体积**:必须跑 `flutter build apk --analyze-size` / `--analyze-size` for iOS,产出 size report 并在 PRD 中给目标值与降级路径。Flutter 官方不强制具体上限,目标由产品决定(参考 <https://docs.flutter.dev/perf/app-size>)
- **首屏**:无统一官方目标,实测口径采用 `--trace-startup --profile` 的 `engineEnterTimestampMicros → firstFrameRasterizedMicros`(参考 <https://docs.flutter.dev/perf/best-practices#startup-latency>);典型中端机 < 2s 是可达目标
- **无障碍**:见 `flutter-accessibility` skill;widget 测试必须跑 `meetsGuideline(...)` 四套官方断言
- **屏幕圆角**: Flutter 3.44 支持通过 `MediaQuery` 获取设备屏幕圆角半径,避免全面屏 UI 裁剪
- **iOS 预测文本(实验性)**: `TextField(enableInlinePrediction: true)` 启用 iOS 内联预测文本

## 2.1 Flutter 3.44 平台要点

### Android — Hybrid Composition++ (HCPP)

HCPP 是嵌入原生视图(Google Maps / WebView / 视频播放器)的最新方案,解决画面撕裂、文本输入错误和 CPU 占用过高问题。通过 Vulkan + SurfaceControl 将图层合成委托给 Android OS:

```xml
<!-- AndroidManifest.xml -->
<meta-data
  android:name="io.flutter.embedding.android.EnableHcpp"
  android:value="true" />
```

> HCPP 对 Android API 版本和 Vulkan 硬件有要求,需要做好降级兼容。

### Android — AGP 9.0 + 内置 Kotlin

Android Gradle 插件 9.0 内置 Kotlin 支持,解决了 AGP 与 KGP 版本兼容性问题。新项目应直接采用 AGP 9.0+。

### iOS — Swift Package Manager 默认

Flutter 3.44 起,**SwiftPM 彻底取代 CocoaPods** 成为 iOS/macOS 默认依赖管理器:
- `flutter build ios` 会自动将 Xcode 工程升级为 SwiftPM 架构
- 不再需要安装 Ruby 和 CocoaPods
- 新项目直接使用 SwiftPM;存量项目 CLI 自动迁移

### iOS — UIScene 支持

Flutter 已支持 iOS 13+ 基于 Scene 的生命周期机制,为未来多窗口体验做好准备。

### Material / Cupertino 包解耦(迁移预警)

自 Flutter 3.44 起,`Material` 和 `Cupertino` 库的框架内更新已**冻结**,下一个稳定版将被弃用。应提前规划迁移到独立包:
- `package:material_ui`(替代 `package:flutter/material.dart`)
- `package:cupertino_ui`(替代 `package:flutter/cupertino.dart`）

## 3. 目录结构(必须遵守)

```
lib/
  app/                # AppWidget、MaterialApp、router、theme
  core/
    config/           # env、feature flags
    network/          # dio、interceptors、error mapping
    storage/          # drift schema、prefs
    utils/            # 纯函数工具
    error/            # AppException、failure 模型
  features/
    <feature_name>/
      data/           # dto、api、repository_impl
      domain/         # entity、repository(抽象)、usecase
      presentation/   # widget、page、controller(riverpod)
  l10n/
  main.dart           # runZonedGuarded + Bloc/Provider observer
test/
integration_test/
```

每个 feature 必须自包含,跨 feature 通信走 `core` 暴露的端口,严禁横向 import。

## 4. 产出必须包含

- 完整的 `pubspec.yaml` 依赖块(含版本号)
- 关键页面的 widget 树骨架(伪 Dart 即可,但类名 / 文件名要真实)
- 数据流图(API → repository → controller → widget)
- 至少 1 个 widget test + 1 个 integration test 用例描述
- iOS 与 Android 各自需要修改的原生配置清单
- 发布渠道:TestFlight、内测分发、Google Play 内测,需要列出包名 / 证书 / 签名规则

## 5. 红线

- 不要使用 `setState` 管理跨页面状态
- 不要直接在 widget 里写 `dio.get`
- 不要把 token 放在 `shared_preferences`(用 `flutter_secure_storage`,见 `flutter-security` skill)
- 不要使用 `print`,用 `package:logging` (<https://pub.dev/packages/logging>) 或自定义 logger
- 不要引入 GPL / AGPL / SSPL 协议依赖

## 参考 / References

- Flutter 官方架构指南:<https://docs.flutter.dev/app-architecture>
- Flutter 性能最佳实践:<https://docs.flutter.dev/perf/best-practices>
- Flutter Samples(包含官方 Adaptive App 演示):<https://github.com/flutter/samples>
- Very Good Ventures — Flutter 工程规范开源参考:<https://github.com/VeryGoodOpenSource/very_good_cli>
- 知名开源 Flutter 应用对照:
  - Wonderous (gskinner):<https://github.com/gskinnerTeam/flutter-wonderous-app>
  - Reflectly:<https://github.com/oleksandrkirichenko/clock-challenge>(布局/动画参考)
  - Cake Wallet (含钱包逻辑):<https://github.com/cake-tech/cake_wallet>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **移动能力即约束**:权限/生命周期/后台/省电/深链在设计期就纳入。
- **平台特性走通道**:业务逻辑保持 Dart 侧平台无关。
- **包体与启动是第一印象**:从一开始预算(见 flutter-performance)。

**诚实边界:**

- iOS/Android 权限与商店策略各异且常变,以官方与商店政策为准。
- 不替代真机(尤其低端机/老系统)实测。
