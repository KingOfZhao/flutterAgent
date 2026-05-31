---
name: flutter-environment-setup
description: 在 Linux / macOS / Windows 上配置 Flutter 开发与构建环境。Use when 需要从零搭建 Flutter SDK、平台工具链(Android/iOS/桌面),或修复 `flutter doctor` 报错、统一团队/CI 的 SDK 版本。
metadata:
  model: distilled-by-devin
  last_modified: Sun, 31 May 2026 02:00:00 GMT
id: flutter-environment-setup
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [environment, setup, toolchain, sdk, doctor, fvm, android, ios, ci]
applies_when: 需要搭建 / 校验 / 统一 Flutter 开发或 CI 构建环境
stage_hints: [breakdown, acceptance]
---
# 配置 Flutter 开发与构建环境

> 采用 Flutter 官方 skill 结构(Contents / Core Concepts / Workflow + Task Progress / Conditional Logic / Examples / Troubleshooting)。本 skill 是 `flutter-engineering-workflow` 阶段 0/4 中"环境"维度的展开。

## Contents
- [Core Concepts](#core-concepts)
- [Workflow: 安装 Flutter SDK](#workflow-安装-flutter-sdk)
- [Workflow: 配置平台工具链](#workflow-配置平台工具链)
- [Workflow: 统一 SDK 版本 (fvm)](#workflow-统一-sdk-版本-fvm)
- [Workflow: 校验环境](#workflow-校验环境)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Core Concepts
- **`flutter doctor` 是唯一事实源**:任何"能不能开发某平台"的判断都以 `flutter doctor -v` 输出为准,不要凭记忆假设。
- **目标平台决定工具链**:Android 需 Android SDK + JDK;iOS/macOS 需 Xcode + CocoaPods(仅 macOS);Linux 桌面需 GTK/clang/ninja;Web 无需额外原生工具链。
- **版本要可复现**:团队与 CI 必须锁定同一 Flutter/Dart 版本,避免"本地能跑、CI 挂"。用 fvm 或 CI 的 setup-action 固定版本。
- **PATH 与缓存**:`flutter` 必须在 `PATH`;首次运行会下载 Dart SDK 与平台 artifact,CI 要缓存 `~/.pub-cache` 与 Flutter 缓存以加速。

## Workflow: 安装 Flutter SDK

**Task Progress:**
- [ ] 确认操作系统与架构(x64 / Apple Silicon)。
- [ ] 按官方方式安装 SDK(归档解压、`git clone`,或包管理器)。
- [ ] 把 `flutter/bin` 加入当前 shell 的 `PATH`。
- [ ] 运行 `flutter --version` 确认可执行,记录版本号。
- [ ] 运行一次 `flutter precache` 预热目标平台 artifact(可选,CI 推荐)。

**Conditional Logic:**
- **若 Linux**:可用归档安装或 `git clone https://github.com/flutter/flutter.git -b stable`;桌面构建还需系统依赖(见下个 workflow)。
- **若 macOS**:支持 Apple Silicon;确保 Rosetta 对个别工具可用。
- **若 Windows**:解压到无空格、无中文、当前用户可写的路径(如 `C:\src\flutter`),避免权限与路径问题。

## Workflow: 配置平台工具链

**Task Progress:**
- [ ] **Android**:安装 Android Studio 或 cmdline-tools;用 `sdkmanager` 装 platform-tools / 对应 API platform / build-tools;运行 `flutter doctor --android-licenses` 接受全部许可。
- [ ] **iOS / macOS(仅 macOS)**:安装 Xcode → `sudo xcode-select -s /Applications/Xcode.app/Contents/Developer && sudo xcodebuild -runFirstLaunch`;`sudo xcodebuild -license`;`sudo gem install cocoapods`。
- [ ] **Linux 桌面**:安装 `clang cmake ninja-build pkg-config libgtk-3-dev`(以发行版包管理器为准)。
- [ ] **Windows 桌面**:安装 Visual Studio(含 "Desktop development with C++" 工作负载)。
- [ ] **Web**:无需额外原生工具链;新版 Flutter 默认启用 web,必要时 `flutter config --enable-web`。

**Conditional Logic:**
- **若只做某一平台**:只装该平台工具链,`flutter doctor` 其它平台的 warning 可暂时忽略,但要在文档里写明。
- **若 CI 环境**:用对应 runner(Android→linux、iOS/macOS→macOS runner),并用官方 setup-action 固定 Flutter 版本。

## Workflow: 统一 SDK 版本 (fvm)

**Task Progress:**
- [ ] 安装 fvm(Flutter Version Management)。
- [ ] 在仓库根运行 `fvm use <version>` 生成 `.fvmrc` / `.fvm/`,提交到 git。
- [ ] 团队成员/CI 用 `fvm flutter ...` 代替 `flutter ...`,保证版本一致。
- [ ] 在 `README` 写明锁定版本与 `fvm` 用法(见 `flutter-documentation`)。

**Conditional Logic:**
- **若不用 fvm**:在 CI 用 `subosito/flutter-action`(或等价)显式 pin `flutter-version`,并在 README 标注本地需安装的版本。

## Workflow: 校验环境

**Task Progress:**
- [ ] 运行 `flutter doctor -v`,逐段消除 error(warning 按目标平台决定是否处理)。
- [ ] 运行 `flutter devices` 确认目标设备/模拟器/桌面被识别。
- [ ] 在样例工程跑 `flutter pub get && flutter run -d <device>` 冒烟一次。
- [ ] **Success Criteria**:`flutter doctor` 目标平台段无 error;`flutter run` 能启动到首帧。

## Examples

### Linux 桌面系统依赖(Debian/Ubuntu)
```bash
sudo apt-get update && sudo apt-get install -y \
  clang cmake ninja-build pkg-config libgtk-3-dev
flutter config --enable-linux-desktop
flutter doctor -v
```

### 用 fvm 锁定并使用版本
```bash
dart pub global activate fvm
fvm install 3.24.0
fvm use 3.24.0        # 生成 .fvmrc,提交到仓库
fvm flutter doctor -v # 之后所有命令都加 fvm 前缀
```

## Troubleshooting
- **`flutter: command not found`**:`flutter/bin` 未进 `PATH`;在 shell profile 里持久化导出。
- **Android licenses not accepted**:运行 `flutter doctor --android-licenses` 全部 `y`。
- **`cmdline-tools component is missing`**:在 Android Studio SDK Manager 勾选 "Android SDK Command-line Tools",或用 `sdkmanager "cmdline-tools;latest"`。
- **CocoaPods not installed/out of date(macOS)**:`sudo gem install cocoapods` 后确认 gem bin 在 `PATH`。
- **CI 与本地版本不一致**:用 fvm 或 setup-action 固定同一版本,清缓存后重试。

## 参考 / References
- 安装指南:<https://docs.flutter.dev/get-started/install>
- `flutter doctor`(诊断):<https://docs.flutter.dev/resources/faq#what-tools-can-i-use-to-build-apps-with-flutter>
- Linux 桌面构建依赖:<https://docs.flutter.dev/platform-integration/linux/building>
- Windows 桌面构建依赖:<https://docs.flutter.dev/platform-integration/windows/building>
- macOS 工具链(Xcode/CocoaPods):<https://docs.flutter.dev/platform-integration/macos/building>
- fvm(Flutter Version Management):<https://fvm.app>
- CI setup-action:<https://github.com/subosito/flutter-action>
- 官方 skill 格式参考:<https://github.com/flutter/skills>
