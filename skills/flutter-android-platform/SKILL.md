---
id: flutter-android-platform
name: Android 平台工程 (Gradle / Manifest / 权限 / R8 / 嵌入 / Play)
version: 1.0.0
platforms: [mobile]
tags: [android, gradle, manifest, permissions, r8, proguard, intent, flutteractivity, play, kotlin]
applies_when: 需要配置 Android 工程层(Gradle/清单/权限/混淆规则/原生嵌入)或排查 Android 专属问题
stage_hints: [architecture, breakdown, acceptance]
see_also: [flutter-mobile, flutter-build-and-release]
---

# Android 平台工程

> 分工:本 skill 负责 **Android 专属工程层**(Gradle/清单/权限/R8/原生嵌入/Play)。
> 移动端**通用约定**见 `flutter-mobile`;**打包签名混淆的通用流程**见 `flutter-build-and-release`。

Flutter 的 Android 部分本质是一个**标准 Android 工程**(`android/` 目录里是 Gradle 项目)。
要配权限、改 Gradle、写 keep 规则、嵌入原生、上 Play,就得懂 Android 工程层。本 skill
聚焦**工程配置与平台约定**;签名/打包发布的命令链见 `flutter-build-and-release`,
原生互操作见 `flutter-platform-channels`,移动端通用基线见 `flutter-mobile`。

## 0. `android/` 目录地图

- `android/app/build.gradle(.kts)`:app 模块配置——`applicationId`、`minSdk`/`targetSdk`/`compileSdk`、`signingConfigs`、`buildTypes`、flavor。
- `android/app/src/main/AndroidManifest.xml`:权限、组件(activity/service/receiver)、intent-filter、`application` 标签。
- `android/build.gradle(.kts)` + `settings.gradle(.kts)`:项目级仓库与插件(含 AGP / Kotlin / Flutter Gradle plugin)。
- `gradle/wrapper/gradle-wrapper.properties`:Gradle 版本(与 AGP 配套,见 `flutter-dependency-maintenance`)。
- `src/main/kotlin/.../MainActivity.kt`:`FlutterActivity` 宿主。

## 1. SDK 版本与 Gradle

- `compileSdk` / `targetSdk` 跟随 Play 政策(Play 定期抬高 `targetSdk` 下限);`minSdk` 决定能装的最低系统。
- AGP(Android Gradle Plugin)与 Gradle wrapper、Kotlin 版本要**配套**;升级看官方兼容表,一次一项(见 `flutter-dependency-maintenance`)。
- Flutter 3.x 新工程用**声明式 plugins{} 块**管理 Flutter Gradle 插件(旧的 `apply` 写法已迁移)。

## 2. AndroidManifest 与权限

- 权限在 Manifest 声明 `<uses-permission>`;**危险权限**(相机、定位、麦克风等)还要**运行时请求**(用 `permission_handler` 等插件)。
- `targetSdk` 越高,权限/后台/存储(分区存储 scoped storage)等政策约束越严——升级 targetSdk 必读对应行为变更。
- intent-filter 用于 deep link / App Links(深链细节见 `flutter-navigation`)、分享、自定义 scheme。
- `android:exported` 在高版本必须显式声明,漏了会编译/安装失败。

## 3. R8 / ProGuard(混淆与裁剪)

- release 默认用 **R8** 做收缩+混淆;第三方原生 SDK 常需 **keep 规则**(`proguard-rules.pro`)防止被裁掉导致运行时 `ClassNotFound`。
- Flutter 引擎相关 keep 规则一般由插件提供;你引入的反射型库要按其文档加 keep。
- 混淆 Dart 层符号、保留 split-debug-info 的命令见 `flutter-build-and-release`;原生层裁剪是这里的关注点。

## 4. 原生嵌入与启动

- `MainActivity` 继承 `FlutterActivity`;要在已有 Android app 里嵌 Flutter,用 `FlutterFragment` / `FlutterEngine`(add-to-app)。
- 启动图(splash)、自适应图标(adaptive icon)、应用名在 Manifest / 资源目录配置。
- 原生方法调用走 platform channel(见 `flutter-platform-channels`)。

## 5. 多环境(flavors)

- 用 Gradle `productFlavors` 定义 dev/staging/prod,配合 `--flavor` 构建;每个 flavor 可有不同 `applicationId` 后缀、图标、配置(见 `flutter-build-and-release`)。

## 6. 排查清单

- 构建失败先看 **Gradle/AGP/Kotlin 版本是否配套**、`compileSdk` 是否够新。
- 运行时崩在 release 不崩在 debug → 多半是 R8 裁掉了反射类,补 keep 规则。
- 装不上 / 组件不生效 → 检查 `android:exported`、权限、`minSdk`。
- `flutter doctor` 看 Android toolchain / 许可(`flutter doctor --android-licenses`,见 `flutter-environment-setup`)。

## 反模式

- ❌ 把所有权限一股脑塞进 Manifest(违反最小权限,Play 审核/隐私风险,见 `flutter-security`)。
- ❌ 升 `targetSdk` 不读行为变更,上线后后台/存储/权限崩。
- ❌ release 崩了就关掉 R8(`minifyEnabled false`)了事,而非补 keep 规则。
- ❌ 手改 `build/` 生成产物或乱动 Flutter 托管的 Gradle 段。
- ❌ 在 Dart 里硬编码只适用于 Android 的假设,不做平台分支(见 `flutter-cross-platform`)。

## 参考 / References

- Android 平台集成 / add-to-app:<https://docs.flutter.dev/add-to-app>
- Flutter Android 构建配置(build & release):<https://docs.flutter.dev/deployment/android>
- Android 权限(官方):<https://developer.android.com/guide/topics/permissions/overview>
- 运行时权限请求:<https://developer.android.com/training/permissions/requesting>
- R8 / 收缩混淆:<https://developer.android.com/build/shrink-code>
- `targetSdk` 与 Play 政策:<https://developer.android.com/google/play/requirements/target-sdk>
- App Links(深链):<https://developer.android.com/training/app-links>
- Android Gradle plugin 版本兼容:<https://developer.android.com/build/releases/gradle-plugin>
- 签名/发布命令链见 `flutter-build-and-release`;原生互操作见 `flutter-platform-channels`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **`android/` 就是个标准 Gradle 工程**:用 Android 的方式理解它,Flutter 只是宿主在 `FlutterActivity` 里。
- **targetSdk 是政策开关**:抬高它=接受一批新行为约束,必须读变更而不是盲升。
- **release ≠ debug**:R8 裁剪让 release 才暴露的问题成为常态,keep 规则是解药不是关混淆。

**诚实边界:**

- Android 版本/AGP/Gradle 政策变化快,具体版本与行为以官方文档当时版本为准。
- 这里聚焦工程配置;UI 适配、Material 规范见 `flutter-mobile`,签名发布见 `flutter-build-and-release`。
- 原生 SDK 的 keep 规则因库而异,需以各 SDK 文档为准。
