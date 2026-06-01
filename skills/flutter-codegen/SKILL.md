---
id: flutter-codegen
name: Flutter 代码生成 (build_runner / freezed / json_serializable / riverpod_generator)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [codegen, build_runner, freezed, json_serializable, riverpod_generator, source_gen, generated, maintenance]
applies_when: 维护/排查基于 build_runner 的代码生成(数据类、JSON 序列化、provider、路由等)
stage_hints: [breakdown, implementation, acceptance]
---

# Flutter 代码生成

Dart 没有运行时反射(尤其 release/AOT/web),所以序列化、不可变数据类、provider
等大量样板靠**编译期代码生成**完成。维护 Flutter 项目绕不开 `build_runner` 生态。
本 skill 给"怎么跑、生成物怎么管、出错怎么排查"的套路,与 `dart-language-idioms`
(语言层)、`flutter-feature-development`(新增功能)配合。

## 0. 心智:生成物是"产物"不是"源码"

- `*.g.dart` / `*.freezed.dart` 是**生成产物**,由源文件 + 注解推导而来。
- **永远不要手改生成文件**——下次生成会覆盖。要改就改源文件里的注解/定义,再重新生成。
- 源文件用 `part 'xxx.g.dart';` 声明与生成物的 part 关系。

## 1. build_runner 基本命令

```bash
# 一次性生成(CI / 改完一批后)
dart run build_runner build --delete-conflicting-outputs

# 开发时持续监听,改了源文件自动重生成
dart run build_runner watch --delete-conflicting-outputs

# 生成物与源文件冲突/脏了,先清再生成
dart run build_runner clean
```

- `--delete-conflicting-outputs` 几乎是常备参数,解决"上次的生成物挡路"。
- 生成是**项目级**的:多个 generator(freezed/json/riverpod)共用一次 `build`。

## 2. 常见 generator 及用途

- **freezed**:不可变数据类 + `copyWith` + `==`/`hashCode` + sealed union(配合 pattern matching,见 `dart-language-idioms`)。省掉大量样板,且 union 类型利于状态建模。
- **json_serializable**:`fromJson`/`toJson`,常与 freezed 一起用(`@freezed` + `@JsonSerializable`)。DTO 放 data 层(见 `architecture-design`)。
- **riverpod_generator**:用 `@riverpod` 注解声明 provider,生成类型安全的 provider 与 ref(见 `state-management` / `remi-rousselet-mindset`)。
- **go_router_builder / auto_route**:类型安全路由(见 `flutter-navigation`)。
- **retrofit / chopper**:声明式网络客户端(见 `flutter-network`)。
- **mockito**(`@GenerateMocks`):生成 mock(也可改用零代码生成的 `mocktail`,见 `flutter-testing`)。

## 3. 生成物要不要提交?

- 两种策略,**团队统一一种**:
  1. **提交生成物**:clone 后无需生成即可编译,CI 简单;代价是 diff 噪音大、易冲突。
  2. **不提交**(`.gitignore` 掉 `*.g.dart`/`*.freezed.dart`):仓库干净,但 CI/clone 后**必须先 `build_runner build`** 才能编译。
- 不提交时,把 `dart run build_runner build` 放进 CI 的依赖安装之后、analyze/test 之前(见 `flutter-ci-cd`)。

## 4. 排查清单(生成报错/不更新时)

1. **改了源文件没重生成** → 跑 `build watch` 或重跑 `build`。
2. **冲突产物** → 加 `--delete-conflicting-outputs`,还不行 `clean` 后重来。
3. **缺 `part` 声明 / part 路径写错** → 生成器找不到落点,补 `part 'x.g.dart';`。
4. **注解包与 builder 包版本不匹配**(如 `freezed` 与 `freezed_annotation`)→ 对齐版本(见 `flutter-dependency-maintenance`)。
5. **analyze 报"未生成"错** → 先生成再 analyze;CI 顺序要对。
6. 看 `build_runner` 输出的具体 generator 报错行,定位是哪个注解/字段触发。

## 5. 依赖位置约定

- generator 与 `build_runner` 放 **`dev_dependencies`**(只编译期用,不进运行时包)。
- 注解包(`freezed_annotation` / `json_annotation` / `riverpod_annotation`)放普通 `dependencies`(运行时需要)。

## 6. 与流程衔接

- 新增带数据类/序列化/provider 的功能时,先写源 + 注解,再生成,再接线(见 `flutter-feature-development`)。
- 验证门禁前确保生成物是最新的,否则 analyze/test 可能基于过期产物(见 `flutter-verification`)。

## 反模式

- ❌ 手改 `*.g.dart` / `*.freezed.dart`,下次生成被覆盖。
- ❌ 注解包放 `dev_dependencies` 导致运行时缺类,或 builder 放普通 deps 增大包体。
- ❌ CI 不提交生成物又不在 CI 里生成,导致编译失败。
- ❌ 注解包与 builder 包版本错配,生成出诡异错误还以为是业务代码问题。
- ❌ 滥用代码生成做本可简单手写的东西,增加构建时间与认知负担。

## 参考 / References

- `build_runner`:<https://pub.dev/packages/build_runner>
- `source_gen`(生成器基础):<https://pub.dev/packages/source_gen>
- freezed:<https://pub.dev/packages/freezed>
- `json_serializable`:<https://pub.dev/packages/json_serializable>
- JSON & 序列化(官方指南):<https://docs.flutter.dev/data-and-backend/serialization/json>
- Riverpod 代码生成:<https://riverpod.dev/docs/concepts/about_code_generation>
- `go_router_builder`:<https://pub.dev/packages/go_router_builder>
- 版本对齐见 `flutter-dependency-maintenance`;CI 顺序见 `flutter-ci-cd`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **生成物是产物不是源码**:改注解/源文件,绝不手改生成文件。
- **Dart 无运行时反射,所以编译期生成**:理解了"为什么要生成",就不会乱用或畏惧它。
- **注解包 vs builder 包分清依赖位置**:运行时需要的进 deps,只编译期用的进 dev_deps。

**诚实边界:**

- 代码生成增加构建时间与一层"魔法",小项目要权衡是否值得引入。
- 生成物提交与否各有取舍,这里给策略不替团队决策。
- 各 generator 的具体注解用法以其 pub.dev 文档为准,版本间可能有差异。
