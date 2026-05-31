---
id: flutter-debugging
name: Flutter 缺陷修复与排错 SOP (复现→定位→修复→防回归)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [debug, bugfix, fix, troubleshooting, devtools, regression, crash]
applies_when: 需求是修复 bug、崩溃、异常行为、性能回退或线上故障
stage_hints: [breakdown, acceptance]
---

# Flutter 修复 SOP

修 bug 的铁律:**先复现,再定位根因,后做最小改动,最后用测试锁死防回归。**
跳过任何一步都会留坑。本 skill 是总框架 `flutter-engineering-workflow` 阶段 1A 的展开。

## 1. 稳定复现(没有复现就没有修复)

- 写出**最小可复现步骤**:设备/平台、构建模式(debug/profile/release)、输入数据、操作序列。
- 区分构建模式很重要:很多 bug 只在 release(AOT + tree-shaking)出现,debug 看不到。
- 复现不了时:补日志、加埋点、问清环境;不要凭猜改代码。
- 把复现步骤记下来——阶段 4 它会变成回归测试用例。

## 2. 收集证据 & 定位根因

按"成本从低到高"排查:

1. **静态分析**:先跑 `flutter analyze`,很多问题(null、类型、未 await 的 Future)这里就暴露。
2. **读栈与日志**:用 `debugPrint` / `dart:developer` 的 `log()` 打点;Crash 看完整 stack trace,定位到具体 `.dart:line`。
3. **DevTools**:
   - **Inspector** 查 widget tree / 布局溢出(`RenderFlex overflowed`)。
   - **CPU / Performance** 查掉帧、jank、`build()` 过频。
   - **Memory** 查泄漏(未 dispose 的 controller / listener,见 `flutter-resource-lifecycle`)。
   - **Network** 查请求/响应、超时、401(见 `flutter-network`)。
4. **二分法缩小范围**:`git bisect` 找到引入提交;或注释/隔离代码块定位最小触发面。
5. **明确根因**:能用一句话说清"因为 X 所以 Y";区分**症状**和**根因**,只压症状会复发。

## 3. 常见根因清单(Flutter 特有)

| 现象 | 高频根因 | 方向 |
|---|---|---|
| `setState() called after dispose` | 异步回调在 widget 卸载后写状态 | 检查 `mounted`,取消订阅 |
| `RenderFlex overflowed` | 无界约束下放可变内容 | `Expanded` / `Flexible` / 滚动容器 |
| 列表卡顿 | `build` 内建重对象 / 没用 `const` / 大 widget 未拆 | 见 `flutter-performance` |
| 内存持续上涨 | `AnimationController` / `StreamSubscription` / `TextEditingController` 未 dispose | 见 `flutter-resource-lifecycle` |
| release 崩溃 debug 正常 | tree-shaking 掉了反射用到的符号 / 平台通道差异 | 加 `@pragma('vm:entry-point')`、查 release log |
| 平台行为不一致 | `dart:io` 在 web 不可用 / 权限差异 | 平台判断,见 `flutter-cross-platform` |
| 状态不刷新 | provider 作用域错 / 没 `notifyListeners` / 比较相等跳过 | 见 `state-management` |

## 4. 最小改动修复

- **只改根因相关代码**;顺手发现的其它问题记 TODO 或单独开 PR,不要混进本次修复。
- 修复要对齐架构分层(见 `architecture-design`):数据问题改 data 层,别在 UI 里打补丁。
- 错误处理要"显式":别用空 `catch {}` 吞异常;该向上抛/该降级要写清。
- 涉及并发/异步:确认 `await`、`mounted`、取消逻辑齐全。

## 5. 防回归(修复必须配测试)

- **先写失败测试**:写一个能复现该 bug 的测试,确认它在旧代码下 **fail**(red)。
- **再改代码**:让该测试转 **pass**(green)。这保证你真的修在了根因上。
- 测试层级按 bug 性质选(见 `flutter-testing`):
  - 逻辑/数据 → unit test;
  - UI/交互 → widget test;
  - 跨页面/真实链路 → `integration_test`。
- 跑全量自测门禁(见 `flutter-verification`),确认没引入新红。

## 6. 收尾

- 提交信息用 `fix: <一句话根因与现象>`,正文引用复现步骤与关联 issue。
- 若属用户可见行为变化或回退,更新 `CHANGELOG`(见 `flutter-documentation`)。
- 同类代码路径做一次"姊妹 bug"扫描,避免同一坑反复踩。

## 参考 / References

- Flutter 调试总览:<https://docs.flutter.dev/testing/debugging>
- DevTools 总览:<https://docs.flutter.dev/tools/devtools/overview>
- DevTools 性能视图:<https://docs.flutter.dev/tools/devtools/performance>
- DevTools 内存视图:<https://docs.flutter.dev/tools/devtools/memory>
- `dart:developer` `log()`:<https://api.flutter.dev/flutter/dart-developer/log.html>
- `dart analyze`:<https://dart.dev/tools/dart-analyze>
- `git bisect`:<https://git-scm.com/docs/git-bisect>
- 测试/性能/生命周期细节见 `flutter-testing`、`flutter-performance`、`flutter-resource-lifecycle`。
