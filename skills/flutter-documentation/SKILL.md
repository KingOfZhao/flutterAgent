---
id: flutter-documentation
name: Flutter 文档与交付说明 SOP (dartdoc/README/CHANGELOG/ADR)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [doc, documentation, dartdoc, readme, changelog, adr, api]
applies_when: 改动涉及公共 API、用户可见行为、依赖或重要架构决策,需要同步文档
stage_hints: [markdown, acceptance]
---

# Flutter 文档 SOP

文档的唯一目的是**让下一个人(包括三个月后的你)用更短时间做对事**。
核心原则:**文档跟着改动走**——代码行为变了,文档同一个 PR 内同步,不留"以后补"。
本 skill 是总框架 `flutter-engineering-workflow` 阶段 3 的展开。

## 1. 改了什么 → 该动哪类文档

| 改动 | 必须更新 |
|---|---|
| 新增/修改**公共 API**(public class/method) | `///` dartdoc 注释 |
| **用户可见行为 / 配置 / 依赖**变化 | `README` + `CHANGELOG` |
| 引入/移除**第三方包** | `README`(依赖说明)+ `pubspec` + `CHANGELOG` |
| 重要**架构/选型决策** | 一条 ADR |
| **破坏性变更** | `CHANGELOG` 顶部 `BREAKING` + 迁移指引 + PR 显著标注 |
| 新增**功能模块** | 模块 README / 用法示例 |

> 反过来:只改私有实现、不影响行为的小重构,通常不需要动 README/CHANGELOG,但 PR 描述要说清。

## 2. 代码级文档:dartdoc

- 公共 API 用 `///` 文档注释(不是 `//`);第一句是**摘要**,会出现在 API 列表。
- 遵循 Effective Dart 文档规范:写"做什么/为什么",而非复述代码"怎么写"。
- 用方括号引用标识符(如 `[MyClass]`、`[doThing]`)生成交叉链接。
- 复杂用法附最小代码示例(放 ```` ```dart ```` 块);示例应可编译。
- 本地预览:`dart doc .` 生成静态 API 文档。

```dart
/// 把原始需求精炼为可执行任务清单。
///
/// 当 [requirement] 为空时抛 [ArgumentError]。返回的 [Prd] 已包含
/// 验收标准与风险清单。
Prd refine(String requirement, {List<String> platforms = const []}) { ... }
```

## 3. README

仓库 / 模块 README 应能回答:

1. **这是什么 / 给谁用**(一句话)。
2. **快速开始**:环境要求(Flutter / Dart 版本)、`flutter pub get`、运行命令。
3. **目录结构**:核心 feature / layer 在哪。
4. **配置**:环境变量、flavor、平台前置条件(权限、签名)。
5. **测试与门禁**:怎么跑 `analyze` / `test` / `build`(指向 `flutter-verification`)。

改了上述任一项就要同步 README,保持"照着 README 能从零跑起来"。

## 4. CHANGELOG(Keep a Changelog + SemVer)

- 每次用户可见变化追加条目,分组 `Added` / `Changed` / `Fixed` / `Removed` / `Deprecated` / `Security`。
- 版本号遵循 SemVer:破坏性 → major,新功能向后兼容 → minor,修复 → patch。
- 破坏性变更在条目前加 **BREAKING**,并给迁移步骤。
- 维护 `[Unreleased]` 段,发版时再归档到具体版本号。

## 5. ADR(架构决策记录)

重要决策(选 Riverpod 还是 BLoC、本地库选 drift 还是 hive、是否引入某 SDK)写一条轻量 ADR:

```
# ADR-000X: <决策标题>
- Status: Accepted | Proposed | Superseded by ADR-00YY
- Context: 我们面对什么问题/约束
- Decision: 我们决定怎么做
- Consequences: 好处、代价、被放弃的方案
```

放 `docs/adr/`,文件名带递增编号。ADR 是**只追加**的历史,不回头改旧的,改了就新开一条并标 Superseded。

## 6. PR 描述(交付的"门面")

- **What / Why**:改了什么、为什么;关联 issue。
- **How verified**:贴自测门禁结果(见 `flutter-verification`)。
- **Risk / Rollback**:风险点、feature flag、回滚方式。
- 破坏性变更显著标注。

## 反模式

- ❌ 改了行为却写"文档以后补"。
- ❌ dartdoc 复述代码("set the name to name");应写意图与边界条件。
- ❌ CHANGELOG 写成 git log 流水账;应是面向用户/调用方的变化。
- ❌ 把已 Accepted 的旧 ADR 直接改写,丢失决策历史。

## 参考 / References

- Effective Dart — Documentation:<https://dart.dev/effective-dart/documentation>
- `dart doc` 工具:<https://dart.dev/tools/dart-doc>
- dartdoc 写法指南:<https://dart.dev/tools/doc-comments>
- Keep a Changelog:<https://keepachangelog.com/>
- Semantic Versioning:<https://semver.org/>
- ADR(Michael Nygard 原始格式):<https://github.com/joelparkerhenderson/architecture-decision-record>
- 自测门禁见 `flutter-verification`;CI 见 `flutter-ci-cd`。
