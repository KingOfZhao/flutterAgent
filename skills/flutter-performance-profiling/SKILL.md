---
name: flutter-performance-profiling
description: 用 profile 模式与 DevTools 定位并修复 Flutter 性能问题(掉帧/jank、过度重建、内存、启动、体积)。Use when 出现卡顿、滚动不顺、内存增长、启动慢,或需要在发布前建立性能基线。
metadata:
  model: distilled-by-devin
  last_modified: Sun, 31 May 2026 02:00:00 GMT
id: flutter-performance-profiling
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [performance, profiling, devtools, jank, frame, memory, startup, raster, 性能]
applies_when: 需要测量 / 诊断 / 优化 Flutter 运行时性能或包体积
stage_hints: [breakdown, acceptance]
extends: [flutter-performance]
see_also: [flutter-performance]
---
# 性能剖析与优化工作流

> 分工:本 skill 负责**测量与定位**(profile 模式、DevTools、jank/过度重建/内存/启动剖析的工作流)。
> 具体**优化规则与性能预算**(列表/图片/动画该怎么写)见 `flutter-performance`。本 skill 是它的**工具深化**。

> 采用 Flutter 官方 skill 结构。本 skill 给"性能"维度的可执行流程;工程选型与帧预算原则见 `flutter-performance`,资源生命周期/泄漏见 `flutter-resource-lifecycle`,体积优化的发布侧见 `flutter-build-and-release`。

## Contents
- [Core Concepts](#core-concepts)
- [Workflow: 建立性能基线](#workflow-建立性能基线)
- [Workflow: 诊断掉帧 / jank](#workflow-诊断掉帧--jank)
- [Workflow: 定位过度重建](#workflow-定位过度重建)
- [Workflow: 内存与启动剖析](#workflow-内存与启动剖析)
- [Examples](#examples)
- [Troubleshooting](#troubleshooting)

## Core Concepts
- **只在 profile 模式测**:`flutter run --profile`。debug 有 VM/断言开销,release 不带 profiling 信息;两者都不能用来量性能。
- **两条线程**:**UI 线程**(Dart 构建/布局)和 **Raster 线程**(GPU 光栅化)。掉帧要先判断瓶颈在哪条线程,优化方向完全不同。
- **帧预算**:60Hz ≈ 16.6ms/帧,120Hz ≈ 8.3ms/帧。单帧(UI+Raster)超预算就会丢帧(jank)。
- **先测量后优化**:用 DevTools 数据定位最大瓶颈,不要凭直觉改;每次改动后重测对比(feedback loop)。
- **Impeller**:新渲染后端,减少首次着色器编译卡顿(shader jank);确认目标平台是否启用。

## Workflow: 建立性能基线

**Task Progress:**
- [ ] 用真机/目标设备,`flutter run --profile`(模拟器性能不代表真机)。
- [ ] 打开 DevTools 的 Performance 视图,录制核心场景(冷启动、首屏、关键滚动列表)。
- [ ] 记录:平均帧时、最差帧、UI vs Raster 占比、启动时延。
- [ ] 把基线写进文档/PR,作为后续对比与回归门槛(见 `flutter-documentation`)。

## Workflow: 诊断掉帧 / jank

**Task Progress:**
- [ ] 在 Performance 视图复现卡顿,定位红色超预算帧。
- [ ] 点开该帧的 Frame Analysis,判断瓶颈在 **UI** 还是 **Raster** 线程。
- [ ] 启用辅助开关:`performance overlay`、`Track Widget Rebuilds`、必要时 `debugProfileBuildsEnabled`。
- [ ] 按瓶颈定向优化,改完重录对比同一场景。

**Conditional Logic:**
- **若瓶颈在 UI 线程**:多为 `build()` 太重/重建过频/同步大计算。→ 拆 widget、加 `const`、把重计算移到 isolate(见 `flutter-concurrency-isolates` 思路 / `compute`)。
- **若瓶颈在 Raster 线程**:多为复杂裁剪/阴影/`Opacity`/`saveLayer`/大图。→ 减少 `saveLayer`、用 `RepaintBoundary` 隔离重绘、降图层复杂度。
- **若仅首次出现卡顿(shader jank)**:确认 Impeller 是否启用;必要时做 shader 预热。

## Workflow: 定位过度重建

**Task Progress:**
- [ ] 开启 DevTools "Track Widget Rebuilds",找出高频重建的 widget。
- [ ] 检查 setState/Provider 作用域是否过大,把状态下沉到最小子树。
- [ ] 给静态子树加 `const`;用 `const` 构造避免重建。
- [ ] 列表用 `ListView.builder` 懒构建,避免一次性构造全部 item。
- [ ] **Success Criteria**:目标 widget 重建次数显著下降,滚动帧回到预算内。

## Workflow: 内存与启动剖析

**Task Progress:**
- [ ] 用 DevTools Memory 视图观察堆增长、监测泄漏(未 dispose 的 controller/subscription,见 `flutter-resource-lifecycle`)。
- [ ] 启动时延:`flutter run --profile --trace-startup`,读 `start_up_info` 的关键时间戳。
- [ ] 体积:`flutter build <platform> --analyze-size`,在 DevTools App Size 工具看 treemap,对比改前改后(详见 `flutter-build-and-release`)。

## Examples

### profile 模式 + 启动追踪
```bash
flutter run --profile --trace-startup -d <device>
# 启动时间戳输出: build/start_up_info.json
```

### 用 RepaintBoundary 隔离频繁重绘区域
```dart
RepaintBoundary(
  child: CustomPaint(painter: ChartPainter(data)), // 频繁重绘的图表
)
```

### 把重计算移出 UI 线程
```dart
// 解析大 JSON 不阻塞 UI 线程
final parsed = await compute(parseBigPayload, rawJsonString);
```

## Troubleshooting
- **"性能在 debug 很差"**:debug 本就慢,务必 `--profile` 重测后再下结论。
- **overlay 看不出问题但用户喊卡**:用真机而非模拟器;模拟器 raster 行为差异大。
- **DevTools 连不上**:确认 `flutter run` 仍在前台运行并输出了 DevTools URL;同一网络/端口可达。
- **首次进入页面卡一下**:典型 shader jank;确认 Impeller 启用或做着色器预热。
- **内存只增不减**:检查 `dispose()` 是否覆盖所有 controller/animation/stream(见 `flutter-resource-lifecycle`)。

## 参考 / References
- 性能总览与最佳实践:<https://docs.flutter.dev/perf>
- 性能最佳实践清单:<https://docs.flutter.dev/perf/best-practices>
- DevTools Performance 视图:<https://docs.flutter.dev/tools/devtools/performance>
- DevTools Memory 视图:<https://docs.flutter.dev/tools/devtools/memory>
- 渲染瓶颈分析:<https://docs.flutter.dev/perf/rendering-performance>
- Impeller 渲染后端:<https://docs.flutter.dev/perf/impeller>
- 应用体积:<https://docs.flutter.dev/perf/app-size>
- `compute` / isolate:<https://docs.flutter.dev/cookbook/networking/background-parsing>
- 官方 skill 格式参考:<https://github.com/flutter/skills>
