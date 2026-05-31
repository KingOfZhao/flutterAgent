---
name: flutter-build-and-release
description: 为 Android / iOS / 桌面 / Web 构建、签名、混淆并发布 Flutter 应用。Use when 需要出 release 包(APK/AAB/IPA/msix/dmg/web)、配置签名与 flavors、做代码混淆,或提交到应用商店。
metadata:
  model: distilled-by-devin
  last_modified: Sun, 31 May 2026 02:00:00 GMT
id: flutter-build-and-release
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [build, release, packaging, signing, flavors, obfuscate, deploy, store, 打包]
applies_when: 需要构建 / 签名 / 混淆 / 发布 Flutter 各平台产物
stage_hints: [architecture, breakdown, acceptance]
---
# 构建、签名与发布 Flutter 应用

> 采用 Flutter 官方 skill 结构。本 skill 是 `flutter-engineering-workflow` 阶段 4"交付"的打包维度展开,CI 自动化见 `flutter-ci-cd`,体积优化见 `flutter-performance-profiling`。

## Contents
- [Core Concepts](#core-concepts)
- [Workflow: Android 打包与签名](#workflow-android-打包与签名)
- [Workflow: iOS 打包与上架](#workflow-ios-打包与上架)
- [Workflow: 桌面端打包](#workflow-桌面端打包)
- [Workflow: Web 构建与部署](#workflow-web-构建与部署)
- [Workflow: 多环境 flavors 与混淆](#workflow-多环境-flavors-与混淆)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Core Concepts
- **Release ≠ Debug**:发布一律用 `--release`(AOT + tree-shaking);debug 包体积/性能不代表线上。
- **AAB 是 Android 首选上传格式**:Google Play 要求 App Bundle(`.aab`),由 Play 按设备下发拆分 APK;`.apk` 仅用于侧载/测试。
- **签名是发布前置**:Android 用 keystore + `key.properties`;iOS 用证书 + provisioning profile(Xcode 自动/手动管理)。**密钥永不进仓库**。
- **符号要留存**:开启 `--obfuscate` 必须 `--split-debug-info` 导出符号表并归档,否则线上崩溃栈无法还原。
- **版本号**:`pubspec.yaml` 的 `version: x.y.z+build`,`+` 后是 build number(Android versionCode / iOS CFBundleVersion)。

## Workflow: Android 打包与签名

**Task Progress:**
- [ ] 生成 keystore(`keytool -genkey -v -keystore ... -keyalg RSA -keysize 2048 -validity 10000 -alias upload`)。
- [ ] 创建 `android/key.properties`(storeFile/storePassword/keyAlias/keyPassword),并加入 `.gitignore`。
- [ ] 在 `android/app/build.gradle(.kts)` 读取 `key.properties`,配置 `signingConfigs.release` 并应用到 `buildTypes.release`。
- [ ] 构建:`flutter build appbundle --release`(上架)或 `flutter build apk --release`(侧载)。
- [ ] 核对产物位置:`build/app/outputs/bundle/release/*.aab` 或 `build/app/outputs/flutter-apk/*.apk`。

**Conditional Logic:**
- **若要分架构 APK**:`flutter build apk --split-per-abi` 产出 arm64/armeabi-v7a/x64 分包。
- **若上架 Google Play**:用 `appbundle`,并启用 Play App Signing。

## Workflow: iOS 打包与上架

**Task Progress:**
- [ ] 在 Xcode 配置 Bundle ID、Team、签名(自动或手动 provisioning)。
- [ ] 设置 `version`/build number(`pubspec.yaml` 或 Xcode）。
- [ ] 构建归档:`flutter build ipa`(产出 `build/ios/archive/*.xcarchive` 与 `build/ios/ipa/*.ipa`)。
- [ ] 用 Xcode Organizer 或 `xcrun altool`/Transporter 上传到 App Store Connect / TestFlight。

**Conditional Logic:**
- **若仅本地分发/CI 构建**:`flutter build ipa --export-method development|ad-hoc|enterprise`。
- **若无 macOS**:iOS 构建必须在 macOS(本地或 CI macOS runner),无法在 Linux/Windows 完成。

## Workflow: 桌面端打包

**Task Progress:**
- [ ] 确认对应桌面平台已 enable 且系统依赖齐全(见 `flutter-environment-setup`)。
- [ ] 构建:`flutter build windows|macos|linux --release`。
- [ ] 打分发包:Windows → MSIX(`msix` 包)或安装器(Inno Setup);macOS → 签名 + 公证(notarize)`.app`/`.dmg`;Linux → AppImage/deb/snap。

**Conditional Logic:**
- **若 macOS 分发到 Gatekeeper 之外的用户**:必须 codesign + `notarytool` 公证,否则会被拦截。
- **若 Windows 上架 Microsoft Store**:用 `msix` 包配置发布者信息。

## Workflow: Web 构建与部署

**Task Progress:**
- [ ] 构建:`flutter build web --release`(产物在 `build/web/`)。
- [ ] 若部署到子路径,设置 `--base-href "/subpath/"`。
- [ ] 部署静态资源到 CDN/静态托管;配置缓存与正确的 MIME(`.wasm`/`.js`)。
- [ ] 验证 SPA 路由回退(404 → index.html)与 CORS。

**Conditional Logic:**
- **若需更高保真渲染**:选择 CanvasKit/SkWasm renderer(见 `flutter-web`),注意首屏体积权衡。

## Workflow: 多环境 flavors 与混淆

**Task Progress:**
- [ ] 定义 flavors(dev/staging/prod),分别配置 applicationId/bundleId、图标、API base。
- [ ] 用 `--flavor <name>` + `--dart-define` 注入环境变量(不要把密钥硬编码进源码)。
- [ ] 发布构建加固:`--obfuscate --split-debug-info=build/symbols/<flavor>`,并归档 `build/symbols`。
- [ ] 把符号表与版本号、commit 关联存档,便于线上崩溃还原。

## Examples

### Android 上架包 + 混淆 + 符号留存
```bash
flutter build appbundle --release \
  --obfuscate --split-debug-info=build/symbols/prod \
  --dart-define=API_BASE=https://api.example.com
# 产物: build/app/outputs/bundle/release/app-release.aab
# 符号: build/symbols/prod (务必归档)
```

### iOS 归档并导出 IPA
```bash
flutter build ipa --release --export-method app-store
# 归档: build/ios/archive/Runner.xcarchive
# IPA:  build/ios/ipa/*.ipa  → 上传 App Store Connect
```

### Web 部署到子路径
```bash
flutter build web --release --base-href "/app/"
# 部署 build/web/ 到 https://host/app/
```

## Troubleshooting
- **`Keystore file not found` / 签名失败**:确认 `key.properties` 路径与 `storeFile` 指向正确,且未被 `.gitignore` 漏配导致缺失。
- **iOS `No profiles for '<bundleId>' were found`**:在 Xcode 用正确 Team 重新生成/下载 provisioning profile。
- **release 崩溃但 debug 正常**:多为 tree-shaking 移除了反射符号——给入口加 `@pragma('vm:entry-point')`,并用归档的 `--split-debug-info` 符号表还原栈。
- **Web 部署后白屏/资源 404**:`--base-href` 与实际部署路径不一致;检查静态托管的 SPA 回退与 `.wasm` MIME。
- **桌面包在他人机器打不开(macOS)**:未签名/未公证,需 codesign + notarize。

## 参考 / References
- Android 发布:<https://docs.flutter.dev/deployment/android>
- iOS 发布:<https://docs.flutter.dev/deployment/ios>
- macOS 发布:<https://docs.flutter.dev/deployment/macos>
- Windows 发布:<https://docs.flutter.dev/deployment/windows>
- Linux 发布:<https://docs.flutter.dev/deployment/linux>
- Web 发布:<https://docs.flutter.dev/deployment/web>
- flavors(多环境):<https://docs.flutter.dev/deployment/flavors>
- 代码混淆与符号:<https://docs.flutter.dev/deployment/obfuscate>
- 官方 skill 格式参考:<https://github.com/flutter/skills>
