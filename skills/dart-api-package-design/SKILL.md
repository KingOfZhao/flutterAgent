---
id: dart-api-package-design
name: Dart API 与包设计 (公共 API / 稳定性 / SemVer / pub 发布)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [api-design, package, pub, semver, public-api, library, stability, breaking-change, modularity]
applies_when: 设计可复用的 package / 模块的公共 API、规划版本与稳定性、向 pub.dev 发布或内部共享
stage_hints: [architecture, breakdown]
---

# Dart API 与包设计

把代码抽成可复用的 package/模块,门槛不在"能跑",而在**公共 API 的形状与稳定性**——
一旦别人依赖你,改 API 就是破坏性变更。本 skill 给"怎么设计好用、好维护、可演进的
公共 API"与发布约定,是 `architecture-design`(分层)在"库边界"上的延伸,语言层见
`dart-language-idioms`,依赖与版本治理见 `flutter-dependency-maintenance`。

## 0. 心智:公共 API 是契约,不是实现细节

- 凡是 `export` 出去、不带下划线的东西,都是**对外承诺**;改它 = 影响所有调用方。
- 设计时先问:**最小暴露面是什么?** 能私有(`_`)就私有,能不导出就不导出——暴露越少,未来越自由。
- "好加难删":加 API 容易,删/改 API 是破坏性变更,所以**宁可一开始少暴露**。

## 1. 控制可见性与导出

- 用 `library` + `part`/`src/` 约定:实现放 `lib/src/`,在 `lib/<pkg>.dart` 里只 `export` 真正的公共面。
- `show`/`hide` 精确控制再导出的符号,别 `export 'src/everything.dart';` 把内部全漏出去。
- 用 class modifiers(`final`/`base`/`interface`/`sealed`,见 `dart-language-idioms`)显式声明"是否允许被继承/实现",别让扩展性靠默契。

## 2. 设计好用的 API(Effective Dart · Design)

- **命名即文档**:类型/方法名表达意图;遵循 Dart 命名规范。
- **命名参数 + `required`** 表达可选/必填,避免布尔位置参数当开关。
- 构造器:用命名构造器(`X.fromJson`)、工厂构造器表达不同创建方式。
- 优先**组合**而非继承暴露;回调/接口用函数类型或抽象类,别强迫调用方继承你的基类。
- 异步 API 一致返回 `Future`/`Stream`;错误用文档化的异常或 Result(见 `flutter-error-handling`)。
- 每个公共成员写 `///` dartdoc(见 `flutter-documentation`),含用法示例。

## 3. 版本与稳定性(SemVer)

- pub 遵循 **SemVer**:`MAJOR.MINOR.PATCH`。
  - PATCH:修 bug,API 不变。
  - MINOR:**向后兼容**地加功能。
  - MAJOR:**破坏性变更**(改/删公共 API、改行为契约)。
- 破坏性变更要:bump major、写 migration guide、在 `CHANGELOG.md` 顶部标 `BREAKING`(见 `flutter-documentation`)。
- `0.x` 阶段语义更宽松,但仍建议谨慎对待公共面。
- 用 `@Deprecated('用 X 替代,将在 2.0 移除')` 给迁移缓冲,而不是直接删。

## 4. 包的元数据与结构

- `pubspec.yaml`:`name` / `description`(60–180 字利于评分)/ `version` / `homepage`/`repository` / `environment`(SDK 约束)/ `topics`。
- 标准结构:`lib/`(`src/` 放实现)、`example/`(强烈建议,影响 pub 评分)、`test/`、`README.md`、`CHANGELOG.md`、`LICENSE`。
- 声明**平台支持**(移动/桌面/web)与最低 SDK;插件类用 federated plugin 结构分平台实现。

## 5. 发布到 pub.dev(或私有)

```bash
dart pub publish --dry-run   # 先校验:缺文件 / 元数据 / 体积 / 警告
dart pub publish             # 正式发布(不可撤销,只能 retract)
dart doc                     # 本地生成 API 文档预览
```

- 发布前过一遍 **pub 评分维度**:有 example、通过 `dart analyze`、`dart format`、有文档、平台声明齐全。
- 发布**不可逆**(只能 `retract` 标记不可用,不能真删);发错版本影响所有人,先 `--dry-run`。
- 内部共享可用 git 依赖 / 私有 pub 仓库,不一定上公网。

## 6. API 演进而不破坏

- 加可选命名参数(带默认值)是兼容的;改必填、改类型、删成员不是。
- 要换实现:先加新 API、`@Deprecated` 旧的、一个大版本后再删。
- 行为契约也是 API:别在 PATCH 里悄悄改返回语义。

## 反模式

- ❌ 把 `lib/src/` 全 `export`,内部实现变成对外承诺,日后寸步难行。
- ❌ 破坏性改动只 bump PATCH/MINOR,坑下游构建。
- ❌ 公共 API 无 dartdoc / 无 example,调用方只能猜。
- ❌ 直接删/改公共成员而不给 `@Deprecated` 过渡。
- ❌ `dart pub publish` 不 `--dry-run` 就发,版本/文件错了无法回收。

## 参考 / References

- Effective Dart · Design(API 设计):<https://dart.dev/effective-dart/design>
- 创建 package:<https://dart.dev/tools/pub/create-packages>
- package 布局约定:<https://dart.dev/tools/pub/package-layout>
- 发布 package(`dart pub publish`):<https://dart.dev/tools/pub/publishing>
- pubspec 格式:<https://dart.dev/tools/pub/pubspec>
- pub.dev 评分维度:<https://pub.dev/help/scoring>
- Semantic Versioning:<https://semver.org/>
- `@Deprecated`:<https://api.dart.dev/stable/dart-core/Deprecated-class.html>
- dartdoc 写法见 `flutter-documentation`;版本治理见 `flutter-dependency-maintenance`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **公共 API 是契约**:暴露即承诺,最小暴露面换取最大演进自由。
- **好加难删**:加 API 便宜、删/改昂贵,所以默认少暴露、宁缺毋滥。
- **版本号会说话**:MAJOR=破坏、MINOR=兼容加、PATCH=修复,别用错号坑下游。

**诚实边界:**

- pub 评分是参考信号不是质量真相;高分包也可能不适合你的场景。
- 发布不可逆,这里给流程,组织的私有发布策略以内部规范为准。
- API 设计有审美与取舍空间,团队既有约定优先。
