---
id: flutter-desktop
name: Flutter Desktop (Windows / macOS / Linux) 工程规范
version: 1.0.0
platforms: [desktop, windows, macos, linux, pc]
tags: [flutter, desktop, windows, macos, linux]
applies_when: 需求目标平台包含 PC / Windows / macOS / Linux
stage_hints: [spec, architecture, breakdown]
---

# Flutter Desktop 工程规范

你正在为一个 **面向 Windows / macOS / Linux 的 Flutter 桌面端** 项目产出工程设计。

## 1. 技术栈基线

- Flutter SDK ≥ 3.22(必须启用 desktop support)
- 窗口管理: **window_manager** 或 **bitsdojo_window**,必须支持自定义 title bar、多窗口、最大化/最小化/全屏
- 状态管理: Riverpod 2.x(默认)
- 路由: go_router 14.x,菜单和快捷键需要与路由联动
- 网络: dio 5.x;对于本地服务请使用 `http_proxy` 透传系统代理
- 本地存储: `path_provider` 拿到正确的 AppData / Application Support 路径,DB 用 drift,文件用平台原生路径
- 文件系统: `file_picker`(用户主动选择)+ `desktop_drop`(拖拽)
- 系统集成: `tray_manager`(系统托盘)、`hotkey_manager`(全局快捷键)、`local_notifier`(原生通知)、`screen_retriever`(多显示器)
- 自动更新: macOS 用 Sparkle 或自实现,Windows 用 MSIX/Squirrel
- 打包: Windows MSIX、macOS dmg/pkg(需公证 notarize)、Linux AppImage/deb/rpm/snap

## 2. 必须考虑的桌面端能力

- **窗口**: 初始尺寸、最小尺寸、是否记忆位置;无标题栏方案需要自己实现拖拽区域
- **键鼠**: 右键菜单、双击行为、键盘焦点遍历(Tab)、快捷键表(Ctrl/Cmd 区分)
- **多窗口**: 是否支持开多个文档窗口,窗口间通信走 isolate 或共享 provider
- **菜单栏**: macOS 必须有原生菜单(File/Edit/View/Help),Windows 用 MenuBar widget
- **系统托盘**: 关闭按钮是退出还是最小化到托盘,要明确
- **多显示器 & DPI**: 不同缩放下 UI 不能错位,使用 LayoutBuilder 而非硬编码尺寸
- **沙箱与权限**: macOS 需要在 entitlements 中开启网络/文件读写
- **代码签名 & 公证**: macOS Apple Developer ID + notarytool;Windows EV 证书
- **多语言**: 桌面端常需中英日三语,字体需考虑 CJK fallback
- **性能**: 大列表使用 `ListView.builder` + `RepaintBoundary`,长任务必须放 isolate

## 3. 目录结构

```
lib/
  app/
    app.dart
    router.dart
    theme.dart
    shortcuts.dart       # 全局快捷键映射
    menu.dart            # 原生菜单
    window.dart          # 窗口初始化
  core/
    config/
    platform/            # 平台差异适配 (Windows/macOS/Linux)
    storage/
    ipc/                 # 多窗口或主子进程通信
  features/
    <feature_name>/
      data/
      domain/
      presentation/
  main.dart              # 必须含 window_manager 初始化
windows/  macos/  linux/  # 各自原生工程
```

## 4. 产出必须包含

- 三个平台分别的入口初始化代码片段
- 窗口初始尺寸 / 最小尺寸 / 标题栏方案
- 完整的快捷键表(action → key combo,平台差异要标)
- 菜单栏树状结构
- 打包脚本路径与命令(`flutter build windows`、`build macos`、`build linux`)以及签名/公证步骤
- 自动更新方案(URL、版本号策略、回滚)
- 至少 1 个针对桌面特性的测试(窗口、文件拖拽、快捷键)

## 5. 红线

- 不要硬编码用户目录,必须用 `path_provider`
- 不要在 UI 线程做文件/网络重活
- macOS 严禁绕过 entitlements
- Windows 不要假定路径用 `/`,使用 `path` 包
- 不要使用仅在 Android/iOS 可用的插件(检查 plugin 的 platforms 字段)

## Flutter 3.44 桌面端重大变化

### Canonical 接管桌面端维护

Ubuntu 母公司 **Canonical 正式成为 Flutter 桌面端的首席维护者和战略管家**,全面负责 Windows / macOS / Linux 三端的维护与发展。

### Windowing APIs（实验性）

多窗口 API 仍处于实验阶段,尚未发布稳定版。如需多窗口支持,当前继续使用 `window_manager` 包。

### 新增能力

- **Windows 手写笔支持**: 原生支持 Surface Pen 等触控笔输入
- **嵌入式平台扩展**: 丰田 RAV4 车机系统、LG webOS SDK 均已采用 Flutter,支持热重载 + Riverpod 状态管理
- **Apple Silicon 原生**: 所有工具链完成 ARM64 重编,无需 Rosetta;未来将**停止支持 Intel Mac 主机**

## 参考 / References

- Flutter 官方 Desktop 支持:<https://docs.flutter.dev/platform-integration/desktop>
- Desktop 部署文档:<https://docs.flutter.dev/deployment/desktop>
- Flutter 官方桌面端 codelab:<https://codelabs.developers.google.com/codelabs/flutter-github-graphql-client>
- 桌面端 window 管理:`window_manager` <https://pub.dev/packages/window_manager>;`bitsdojo_window` <https://pub.dev/packages/bitsdojo_window>
- 系统集成:`tray_manager` <https://pub.dev/packages/tray_manager>;`hotkey_manager` <https://pub.dev/packages/hotkey_manager>;`local_notifier` <https://pub.dev/packages/local_notifier>;`screen_retriever` <https://pub.dev/packages/screen_retriever>
- 自动更新:`auto_updater` <https://pub.dev/packages/auto_updater>(基于 macOS Sparkle / Windows WinSparkle)
- 打包多格式:`flutter_distributor` <https://pub.dev/packages/flutter_distributor>
- 跨端参考应用:Wonderous <https://github.com/gskinnerTeam/flutter-wonderous-app>;Rive Desktop;Bluesky desktop
- Microsoft 推荐的 MSIX 打包:<https://pub.dev/packages/msix>
- Apple Notarization:<https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution>
