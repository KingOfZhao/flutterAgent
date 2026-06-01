---
id: flutter-feature-development
name: Flutter 新增功能 SOP (垂直切片→契约先行→接线→灰度)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [feature, development, new, scaffold, vertical-slice, feature-flag]
applies_when: 需求是在已有 Flutter 项目中新增功能 / 页面 / 模块
stage_hints: [architecture, breakdown, implementation]
---

# Flutter 新增功能 SOP

在一个**已有仓库**里加功能,目标是"加得进、不破坏、可回滚"。
按**垂直切片**交付:一个 feature 自带 data → domain → presentation → test,不要横向铺一层再铺一层。
本 skill 是总框架 `flutter-engineering-workflow` 阶段 1B 的展开。

## 1. 落位与脚手架

按 feature-first 目录组织(对齐 `architecture-design` 的 Clean Architecture 三层):

```
lib/
└── features/
    └── <feature_name>/
        ├── data/          # repository 实现、datasource、dto/mapper
        ├── domain/        # entity、usecase、repository 抽象接口
        └── presentation/  # widget、page、state(provider/bloc)
```

- 先建目录与空骨架文件,再逐层填实现。
- 复用 `core/` / `shared/` 里已有的网络、存储、主题、路由能力,**不要重复造轮子**。

## 2. 契约先行(domain 层最先写)

- 先定义 **entity**(纯 Dart 数据类,`==`/`hashCode` 用 `equatable` 或 record)与 **usecase** 的输入输出契约。
- 定义 **repository 抽象接口**放 domain,**实现**放 data —— 依赖倒置,便于测试时 mock。
- domain 不依赖 Flutter / 第三方 IO,保证可纯单测。

## 3. 数据层(data)

- repository 实现抽象接口;datasource 负责真实 IO(dio / drift / secure storage,见 `flutter-network`、`flutter-data-persistence`)。
- dto ↔ entity 用显式 mapper,别让网络模型泄漏到 UI。
- 错误转换:把底层异常映射成 domain 可理解的 failure 类型,不要把 `DioException` 直接抛到 UI。

## 4. 状态管理(presentation)

- **遵循仓库既有方案**:仓库用 Riverpod 就用 Riverpod,用 BLoC 就用 BLoC——**同一仓库不要混用两套**(见 `state-management`)。
- 三态必须显式建模:`loading` / `data` / `error`(可加 `empty`);UI 对每种状态都要有渲染。
- widget 只读 state、发 intent,**不写业务逻辑**;逻辑下沉到 usecase / notifier。

## 5. 接线(wiring)

- **路由**:用 `go_router` 注册新页面/深链(见 `flutter-navigation`)。
- **依赖注入**:在既有 DI 容器/provider 树里注册新依赖,保持作用域正确。
- **国际化**:用户可见文案进 ARB,不要硬编码字符串(见 `flutter-i18n`)。
- **无障碍**:交互元素给 `Semantics` / label,达标 `meetsGuideline`(见 `flutter-accessibility`)。

## 6. 依赖选型(反幻觉)

- 新引入的包必须 **pub.dev 可查、活跃维护、版本约束合理**;在 PR 写明"为什么选它"。
- 优先 Flutter team / 知名维护者的包;避免长期未更新或已 `discontinued` 的包。
- 能用现有依赖实现就不新增依赖。

## 7. 灰度与可回滚

- 有风险/未完全验证的功能加 **feature flag**(编译期常量或远程开关),默认关,可快速回滚。
- 涉及本地数据结构变化要写迁移且可回退(见 `flutter-data-persistence`)。

## 8. 自带测试(随功能一起交付)

每个垂直切片至少包含:

- **unit**:usecase / repository 逻辑(mock datasource)。
- **widget**:页面三态渲染 + 关键交互。
- **integration**(关键路径):端到端走一遍主流程。

测试写法见 `flutter-testing`;交付前跑完自测门禁见 `flutter-verification`。

## 反模式

- ❌ 把业务逻辑写进 widget 的 `build`。
- ❌ 网络 dto 直接当 UI model 用,字段一变全线崩。
- ❌ 同仓库混用 Riverpod + BLoC + setState 三套状态方案。
- ❌ 新功能不带测试 / 硬编码文案 / 漏掉 error 与 empty 态。

## 参考 / References

- Flutter 架构与状态管理总览:<https://docs.flutter.dev/app-architecture>
- 状态管理选项:<https://docs.flutter.dev/data-and-backend/state-mgmt/options>
- `go_router`:<https://pub.dev/packages/go_router>
- 国际化:<https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization>
- 分层/选型/测试细节见 `architecture-design`、`state-management`、`flutter-network`、`flutter-data-persistence`、`flutter-testing`。
