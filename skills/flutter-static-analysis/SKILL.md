---
id: flutter-static-analysis
name: Flutter 静态分析自动化 (analysis_options / lint 规则集 / custom_lint)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [static-analysis, lint, analysis-options, flutter_lints, very_good_analysis, custom_lint, quality-gate, ci]
applies_when: 配置/收紧静态分析、统一 lint 规则、写自定义 lint 把团队约定自动化
stage_hints: [acceptance, architecture]
---

# Flutter 静态分析自动化

最好的质量约定是**机器自动执行的**——靠人记、靠评审盯都会漏。`dart analyze` +
`analysis_options.yaml` + lint 规则集让"该报错的自动报错",`custom_lint` 还能把
团队特有约定写成可执行规则。本 skill 把质量门禁前移到"写代码当下",是
`flutter-verification`(门禁链)与 `flutter-code-review`(人评审)之间的自动化层。

## 0. 心智:能自动化的别靠人

- 风格、命名、空安全误用、`print` 残留、未使用导入……这些应由分析器拦,不该消耗评审注意力。
- 评审的注意力留给"设计/正确性"(见 `flutter-code-review`),机器能查的交给 `analyze`。

## 1. `analysis_options.yaml` 骨架

```yaml
include: package:flutter_lints/flutter.yaml   # 或更严的 very_good_analysis

analyzer:
  language:
    strict-casts: true
    strict-raw-types: true
  errors:
    # 把重要 lint 从 info/warning 升级为 error(CI 会 fail)
    invalid_annotation_target: error
    todo: ignore
  exclude:
    - "**/*.g.dart"        # 生成物不参与分析(见 flutter-codegen)
    - "**/*.freezed.dart"

linter:
  rules:
    - prefer_const_constructors
    - avoid_print
    - require_trailing_commas
```

- `include` 引入一个规则集做基线;`linter.rules` 在其上增删。
- `analyzer.errors` 可把任意 lint 的**严重级别**改成 `error`/`warning`/`info`/`ignore`——这是"把建议变成硬门禁"的关键。
- `exclude` 排除生成物,避免对 `*.g.dart` 报一堆无意义警告。

## 2. 选规则集(lint ruleset)

- **`flutter_lints`**:Flutter 官方推荐基线,`flutter create` 默认带,温和。
- **`very_good_analysis`**(Very Good Ventures):明显更严格,适合想要高一致性的团队。
- **`lints`**:纯 Dart(非 Flutter)package 的官方基线(`core` / `recommended`)。
- 全部 lint 规则查表见官方 linter rules 页;按团队接受度增量收紧,别一次开满导致海量告警没人理。

## 3. 跑分析

```bash
dart analyze            # 或 flutter analyze
dart analyze --fatal-infos   # 把 info 也当失败(最严)
dart fix --apply        # 自动修可修的 lint(见 dart-language-idioms)
```

- 目标 **0 error**;`// ignore: rule_name` / `// ignore_for_file:` 仅在确有理由时用,并写明原因——别拿它当消警工具。

## 4. `custom_lint`:把团队约定写成规则

通用规则集覆盖不到的项目特有约定(如"禁止在 widget 里直接 import data 层""所有
provider 必须带文档"),可用 `custom_lint` + `analyzer` API 写自定义 lint 插件:
- 依赖 `custom_lint` / `custom_lint_builder`,实现 `DartLintRule`,在 `analysis_options.yaml` 启用 `custom_lint` 插件。
- 很多生态库(如 Riverpod 的 `riverpod_lint`)就是基于它分发专属 lint。
- 成本不低,适合"反复出现、靠评审挡不住"的约定才值得自动化。

## 5. 接进 CI(本地绿 == CI 绿)

- CI 顺序:`dart format --set-exit-if-changed` → `dart analyze`(必要时 `--fatal-infos`)→ test(见 `flutter-ci-cd` / `flutter-verification`)。
- 分析失败即 fail fast,别让风格/lint 问题流到测试阶段才发现。
- 生成物若不提交,要在 analyze 前先 `build_runner build`(见 `flutter-codegen`),否则会对缺失的 part 报错。

## 反模式

- ❌ 项目无 `analysis_options.yaml` 或只用默认却从不收紧,放任坏味道。
- ❌ 用 `// ignore_for_file:` 大面积消警,把红变绿掩盖真问题。
- ❌ 一次性开满最严规则集,产生几千条告警,团队直接无视。
- ❌ 对生成物不 `exclude`,被一堆 `*.g.dart` 噪音淹没真告警。
- ❌ 本地不 analyze 就提 PR,把静态问题甩给 CI / 评审。

## 参考 / References

- 自定义静态分析(`analysis_options.yaml`):<https://dart.dev/tools/analysis>
- `dart analyze`:<https://dart.dev/tools/dart-analyze>
- Linter rules 全表:<https://dart.dev/tools/linter-rules>
- `flutter_lints`:<https://pub.dev/packages/flutter_lints>
- `lints`(Dart 官方):<https://pub.dev/packages/lints>
- `very_good_analysis`:<https://pub.dev/packages/very_good_analysis>
- `custom_lint`:<https://pub.dev/packages/custom_lint>
- `riverpod_lint`(custom_lint 实例):<https://pub.dev/packages/riverpod_lint>
- 门禁链见 `flutter-verification`;CI 固化见 `flutter-ci-cd`;自动修复见 `dart-language-idioms`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **能自动化的约定才能长期执行**:写进 `analysis_options.yaml` 的规则不会累、不会忘、不看人情。
- **严重级别是杠杆**:把关键 lint 升成 `error` 才有强制力,停留在 info 等于没有。
- **增量收紧**:规则一次开满会被无视;按团队接受度逐步加,保持告警可处理。

**诚实边界:**

- 静态分析查不出逻辑/设计错误,只是质量网的一层,不替代测试与人评审。
- `custom_lint` 维护成本高,只有高频且评审挡不住的约定才值得写。
- 规则集的取舍因团队而异,这里给框架不替团队定规则清单。
