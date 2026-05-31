---
id: state-management
name: Flutter 状态管理选型与规范
version: 1.0.0
platforms: [all]
tags: [state, riverpod, bloc, provider]
applies_when: 出现表单 / 列表 / 实时数据 / 跨页面状态
stage_hints: [architecture, breakdown]
---

# 状态管理规范

> 重要声明:**Flutter 官方对 state management 中立**,同时列出 Provider / Riverpod / BLoC / GetX / Redux 等选项(参考 <https://docs.flutter.dev/data-and-backend/state-mgmt/options>)。本 skill 推荐 Riverpod 是**工程考量后的竞品**,不是官方指定。遵循 BLoC 的项目使用**等价路径**,不需要迁移。

## 1. 选型参数(供架构阶段取舍)

| 维度 | Riverpod 2.x | BLoC 8.x | Provider 6.x |
|---|---|---|---|
| 项目主页 | <https://pub.dev/packages/flutter_riverpod> | <https://pub.dev/packages/flutter_bloc> | <https://pub.dev/packages/provider> |
| 维护方 | Remi Rousselet(Flutter core team) | Felix Angelov | Flutter team |
| BuildContext 耦合 | 无 | 低 | 高 |
| codegen | `@riverpod` 高度类型安全 | `flutter_bloc` 原生 Stream | 无 |
| 本地生态 | `riverpod_lint` + `riverpod_generator` | `bloc_test` + `bloc_concurrency` | 轻 |
| 适合 | 中大型、多状态跨页面 | 事件驱动、机状态多、企业代码库 | 必刚需 / DI |

**本项目使用准则**:
- 项目从 0 启动 → **Riverpod 2.x**;理由:编译期安全 + 无 BuildContext + `AsyncValue` 三态 + provider override 便于测试
- 项目已有大量 BLoC 代码 → **沿用 BLoC**,不要迁移;`bloc_test` 表现同样优秀
- 极简 demo / 单一表单 → `ValueNotifier` + `ListenableBuilder` 均可

参考采访记录(三位本领域作者):
- Remi Rousselet 谈 Riverpod 2 理念:<https://github.com/rrousselGit/riverpod/blob/master/RATIONALE.md>
- Felix Angelov 谈 BLoC 8 事件模型:<https://bloclibrary.dev/architecture/>
- Flutter team 状态管理选项总览:<https://docs.flutter.dev/data-and-backend/state-mgmt/options>

## 2. Provider 分类约定

| 类型 | 用途 | 例 |
|---|---|---|
| `Provider` | 不可变值 / DI | `dioProvider`, `repoProvider` |
| `FutureProvider` | 一次性异步读 | `userProfileProvider` |
| `StreamProvider` | 持续流 | `chatMessagesProvider` |
| `NotifierProvider` | 可写状态 | `loginFormController` |
| `AsyncNotifierProvider` | 异步可写 | `todoListController` |

命名规范:
- 数据型 provider 用名词:`todoListProvider`
- controller / notifier 用 `xxxController` 或 `xxxNotifier`
- 一次性可丢:加 `.autoDispose`
- 带参数:`.family<T, Param>`

## 3. State 模型

页面级状态用 immutable class + `copyWith`(`freezed` 推荐):

```dart
@freezed
class LoginState with _$LoginState {
  const factory LoginState({
    @Default('') String email,
    @Default('') String password,
    @Default(false) bool submitting,
    Failure? error,
  }) = _LoginState;
}
```

异步数据用 `AsyncValue<T>`(loading/data/error 三态),禁止自己造 `isLoading` 布尔。

## 4. 何时不选 Riverpod

- 团队已有大量 BLoC 代码 → 沿用 BLoC,但仍要遵守 state 三态
- 极简 demo / 单一表单 → `ValueNotifier` + `ListenableBuilder` 也行,但不要混用

## 5. 状态作用域

| 作用域 | 实现 |
|---|---|
| Widget local | `useState` (flutter_hooks) 或 `StatefulWidget` |
| Page | `autoDispose` Notifier |
| Feature | 普通 Notifier |
| App-wide | 顶层 Provider(谨慎,数量 ≤ 10) |

## 6. 红线

- 不要把 BuildContext 存进 state
- 不要在 build() 里 `ref.read`(应该 `ref.watch`)
- 不要在 Notifier 里直接 push 路由(返回 Result,让 UI 决定跳转)
- 不要让两个 Notifier 互相 listen 形成环
- 长列表必须用 `select` 精确订阅,避免整张表 rebuild

## 参考 / References

- Flutter 官方 state management 总览:<https://docs.flutter.dev/data-and-backend/state-mgmt/options>
- Riverpod 官方文档:<https://riverpod.dev>
- BLoC 官方文档:<https://bloclibrary.dev>
- Effective Dart — Style:<https://dart.dev/effective-dart/style>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **状态=UI 的真相源**:UI=f(state),改状态而非改 widget(见 mindset 模型 3)。
- **状态有归属与作用域**:就近持有,跨域才上提;一仓库一套方案。
- **副作用与状态分离**:异步/IO 收敛在明确层,UI 只声明依赖。

**诚实边界:**

- 没有“最好”的方案,Riverpod/BLoC 取决于团队与规模;本 skill 给取舍维度,非定论。
- 不替你设计领域状态模型本身。
