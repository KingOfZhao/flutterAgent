---
id: flutter-cross-platform
name: Flutter 跨端(移动 + 桌面 + Web)适配规范
version: 1.0.0
platforms: [mobile, desktop, web, all]
tags: [flutter, cross-platform, responsive, adaptive]
applies_when: 需求同时覆盖移动端与 PC(或包含 Web)
stage_hints: [spec, architecture]
---

# Flutter 跨端适配规范

当目标平台 ≥ 2 个时启用本 skill。核心思路:**一套业务 + 自适应 shell**。

> 直接依据:
> * Flutter 官方 Adaptive UI 指南:**[docs.flutter.dev/ui/adaptive-responsive](https://docs.flutter.dev/ui/adaptive-responsive)**
> * Material 3 Window size classes:<https://m3.material.io/foundations/layout/applying-layout/window-size-classes>
> * `flutter_adaptive_scaffold`(Flutter team 官方发布):<https://pub.dev/packages/flutter_adaptive_scaffold>
> * Flutter Samples → adaptive_app_demos:<https://github.com/flutter/samples/tree/main/experimental/web_dashboard>
> * Wonderous(跨端参考应用,同一套代码跑 mobile + desktop):<https://github.com/gskinnerTeam/flutter-wonderous-app>

## 1. 分层

```
┌──────────────────────────────────────┐
│  presentation (adaptive widgets)     │  ← 平台差异隔离在这里
├──────────────────────────────────────┤
│  domain (entity / usecase)           │  ← 100% 平台无关
├──────────────────────────────────────┤
│  data   (repository / api / db)      │  ← 通过抽象隔离平台 IO
├──────────────────────────────────────┤
│  platform (file / window / push ...) │  ← 接口在此,实现按平台注入
└──────────────────────────────────────┘
```

`domain` 与 `data` 99% 共享;`presentation` 用 **adaptive widget**;`platform` 用接口 + 工厂。

## 2. Adaptive 设计断点(与 Material 3 spec 完全一致)

数据源:Material Design 3 “window size classes” — <https://m3.material.io/foundations/layout/applying-layout/window-size-classes>

| 断点名 | dp 区间 | 典型形态 |
|---|---|---|
| compact | 0 – 599 | 手机竖屏 |
| medium | 600 – 839 | 手机横屏 / 小平板 |
| expanded | 840 – 1199 | 大平板 / 小桌面 |
| large | 1200 – 1599 | 桌面 |
| extra-large | ≥ 1600 | 大桌面 / 多面板 |

布局规则(与 Material 3 layout guidance 一致):
- compact / medium → 底部 tab 导航 + 单列
- expanded / large → `NavigationRail`(侧导) + 双列(list-detail)
- extra-large → 三列(`NavigationDrawer` + list + detail)

**推荐直接使用 `flutter_adaptive_scaffold`**(Flutter team 官方发布):

```dart
AdaptiveScaffold(
  selectedIndex: idx,
  onSelectedIndexChange: (i) => setState(() => idx = i),
  destinations: const [
    NavigationDestination(icon: Icon(Icons.inbox), label: 'Inbox'),
    NavigationDestination(icon: Icon(Icons.article), label: 'Articles'),
    NavigationDestination(icon: Icon(Icons.settings), label: 'Settings'),
  ],
  smallBody:  (_) => InboxList(...),     // compact
  body:       (_) => InboxList(...),     // medium
  smallSecondaryBody: AdaptiveScaffold.emptyBuilder,
  secondaryBody: (_) => InboxDetail(...),// expanded 以上
);
```

手动控制的场景用 `LayoutBuilder` + `MediaQuery.sizeOf`。**禁止** 用 `Platform.isAndroid` 决定 UI — 官方明语:“do not use `Platform` to decide layout, use input + size”(<https://docs.flutter.dev/ui/adaptive-responsive>)。

## 3. 平台能力差异表

| 能力 | mobile | desktop | web |
|---|---|---|---|
| 推送 | FCM/APNs | local_notifier | Web Push |
| 文件系统 | 沙盒 | 任意路径(需 picker) | 仅下载/上传 |
| 后台任务 | WorkManager/BGTaskScheduler | 常驻进程 | Service Worker |
| 深链接 | App Links / Universal Links | 自定义 URL scheme | URL 路由 |
| 鼠标右键 | 无 | 有 | 有 |
| 摄像头 | 原生 | 部分 (UVC) | getUserMedia |

对每个被需求用到的能力,**必须**在产出里给出三端实现策略,缺一不可。

## 4. 输入差异

- 触摸 vs 鼠标 vs 键盘 — 所有交互必须能纯键盘完成
- hover 效果只在 desktop / web 启用
- 长按 vs 右键 — 同义但需要分别监听
- 滚动条 — desktop 默认 always-visible,mobile 滑动隐藏

## 5. 产出必须包含

- 断点表 + 每个主页面的 compact / expanded 两版骨架
- platform 接口列表(`PlatformFiles`, `PlatformNotifier`, `PlatformWindow` 等)
- 每个接口在 mobile / desktop (/ web) 的实现策略
- 共享代码占比估算(domain + data + 共享 widget)
- 平台特有页面清单(如「设置 → 系统托盘」仅 desktop 可见)

## 6. 红线

- 不要用 `dart:io` 的 Platform 决定 UI 形态,要用尺寸 / 输入模式(官方要求)
- 不要在 domain 层直接 import `dart:io` 或平台插件
- 不要假设 web 有文件系统
- 不要假设 mobile 有键盘

## 参考 / References

- Flutter 官方 adaptive guide:<https://docs.flutter.dev/ui/adaptive-responsive>
- `flutter_adaptive_scaffold`:<https://pub.dev/packages/flutter_adaptive_scaffold>
- Material 3 layout:<https://m3.material.io/foundations/layout>
- Pointer / input 适配:<https://docs.flutter.dev/ui/interactivity>
- Flutter desktop 提示:<https://docs.flutter.dev/platform-integration/desktop>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **平台差异收敛到边界**:core/UI 平台无关,差异藏在 adapter(见 mindset 模型 6)。
- **响应式按断点不按设备**:用 Material 3 断点,而非 isPhone/isTablet 硬判。
- **输入是多元的**:同时设计触摸 / 鼠标 / 键盘 / 手势。

**诚实边界:**

- 后台/窗口/文件系统等能力天然平台特异,无法完全抽象。
- 不替代各平台的真机/真窗口实测。
