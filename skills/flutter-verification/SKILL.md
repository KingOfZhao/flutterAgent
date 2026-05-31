---
id: flutter-verification
name: Flutter 自测与本地验证门禁 (format→analyze→test→build)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [verify, self-test, gate, analyze, format, coverage, ci, golden, build]
applies_when: 任何 Flutter 改动在提交 / 交付前的自测与验证环节
stage_hints: [acceptance]
---

# Flutter 自测门禁

"自测"不是"跑一下 app 看看",而是一条**可复制、可在 CI 复跑**的门禁链。
任何修复或新增,交付前都要本地把这条链跑绿。本 skill 是总框架
`flutter-engineering-workflow` 阶段 2 的展开;它讲"怎么验证",测试**怎么写**见 `flutter-testing`。

## 0. 标准门禁链(按顺序,红了就停)

```bash
# 1) 依赖一致
flutter pub get

# 2) 格式(CI 会用 --set-exit-if-changed 卡住未格式化代码)
dart format --output=none --set-exit-if-changed .

# 3) 静态分析:必须 0 error(warning 按仓库 lint 策略处理)
flutter analyze

# 4) 单元 + widget 测试 + 覆盖率
flutter test --coverage

# 5) 集成测试(若仓库有 integration_test/)
flutter test integration_test

# 6) 可编译性冒烟:至少编出目标平台的 debug 包
flutter build apk --debug          # Android
# flutter build ios --no-codesign  # iOS
# flutter build windows|macos|linux --debug   # 桌面
# flutter build web                # Web
```

> 原则:**任何一步失败都先修,不要带着红往下走,也不要把验证甩给 CI。**

## 1. 格式 & 分析

- `dart format`:统一风格,消除"格式 diff 噪音"。CI 用 `--set-exit-if-changed` 强制。
- `flutter analyze`:基于 `analysis_options.yaml`(`flutter_lints` 或 `very_good_analysis`)。
  目标 **0 error**;不要用 `// ignore:` 掩盖真实问题,确需忽略要写明理由。

## 2. 测试与覆盖率

- `flutter test` 跑 `test/` 下全部 unit + widget 测试。
- `--coverage` 产出 `coverage/lcov.info`;可用 `genhtml` 看报告。
  - 覆盖率**关注增量**:新增/改动的代码要有测试覆盖,而非只看总数字。
- 修 bug 必带**回归测试**(先红后绿,见 `flutter-debugging` §5)。
- 不稳定(flaky)测试要定位根因(时间/随机/异步竞态),不要简单 `skip` 掩盖。

## 3. Golden(像素回归)测试

- UI 视觉回归用 `matchesGoldenFile`;首次或确认是预期变更时,用 `flutter test --update-goldens` 生成/刷新基线。
- golden 对字体/平台敏感,建议固定渲染环境或用 `golden_toolkit` 之类约束,避免跨机抖动。

## 4. 集成测试

- `integration_test` 包跑真实设备/模拟器上的端到端流程(启动、登录、核心路径)。
- 桌面端可在 CI 的对应 OS runner 上跑;移动端用模拟器/真机。

## 5. 性能与体积(性能敏感改动追加)

- 用 `--profile` + DevTools 看掉帧/jank(见 `flutter-performance`)。
- 包体积:`flutter build apk --analyze-size`,对比改动前后,异常增长要解释。

## 6. 依赖健康

- `flutter pub outdated` 看过时依赖;升级要看 changelog 与破坏性变更。
- `dart pub deps` 排查冲突;新依赖确认 pub.dev 活跃、非 `discontinued`。

## 7. 把门禁固化进 CI

- 上面 0–4 步应 1:1 映射到 CI(见 `flutter-ci-cd`),保证"本地绿 == CI 绿"。
- 建议顺序:`format → analyze → test --coverage → build`,任一失败即 fail fast。

## 反模式

- ❌ 只手动点 app,不跑 `analyze` / `test` 就提 PR。
- ❌ 用 `// ignore:` / `skip` 把红变绿。
- ❌ golden 抖动就无脑 `--update-goldens` 覆盖基线(先确认是真实 UI 变更)。
- ❌ 本地与 CI 用不同命令,导致"本地过、CI 挂"。

## 参考 / References

- Flutter 测试总览:<https://docs.flutter.dev/testing/overview>
- `flutter test` / 覆盖率:<https://docs.flutter.dev/cookbook/testing/unit/introduction>
- 集成测试:<https://docs.flutter.dev/testing/integration-tests>
- golden 测试 `matchesGoldenFile`:<https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html>
- `dart format`:<https://dart.dev/tools/dart-format>
- `dart analyze`:<https://dart.dev/tools/dart-analyze>
- `flutter pub outdated`:<https://dart.dev/tools/pub/cmd/pub-outdated>
- 包体积分析:<https://docs.flutter.dev/perf/app-size>
- CI 固化见 `flutter-ci-cd`;测试写法见 `flutter-testing`。
