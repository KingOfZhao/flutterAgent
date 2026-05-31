---
id: architecture-design
name: Flutter Clean Architecture 设计规范
version: 1.0.0
platforms: [all]
tags: [architecture, clean, ddd, layering]
applies_when: 架构阶段始终启用
stage_hints: [architecture]
---

# Flutter Clean Architecture

## 1. 三层模型

```
presentation  ──▶  domain  ◀──  data
   (UI)            (业务规则)       (IO)
```

- **domain**: 纯 Dart,无 Flutter 依赖,无 IO。包含 `Entity` / `Repository(抽象)` / `UseCase` / `Failure`
- **data**: 实现 `Repository`,包含 `DataSource(remote/local)` / `DTO` / `Mapper`
- **presentation**: Widget / Controller(Riverpod Notifier 或 Bloc)/ ViewModel

依赖方向只能 **由外向内**:presentation 和 data 都依赖 domain,domain 不依赖任何人。

## 2. Feature-first

按 feature 切片,而非按类型切片:

```
lib/features/auth/
  data/
    datasource/
    dto/
    repository/auth_repository_impl.dart
  domain/
    entity/user.dart
    repository/auth_repository.dart        # 抽象
    usecase/login_usecase.dart
  presentation/
    page/login_page.dart
    widget/
    controller/login_controller.dart       # Riverpod Notifier
```

跨 feature 不允许直接 import,要走 `core` 暴露的服务或事件总线。

## 3. 错误模型

domain 层定义 `Failure` sealed class:

```dart
sealed class Failure { final String code; final String message; ... }
final class NetworkFailure extends Failure { ... }
final class AuthFailure    extends Failure { ... }
final class ValidationFailure extends Failure { final Map<String,String> fields; ... }
final class UnknownFailure extends Failure { ... }
```

usecase 返回 `Result<T, Failure>`(使用 `fpdart` 或自定义 sealed)。
data 层捕获异常 → 翻译为 Failure,**禁止把 dio 异常透传到 presentation**。

## 4. DI

用 Riverpod 的 provider 树即可:

```dart
final dioProvider = Provider((ref) => buildDio(ref));
final authApiProvider = Provider((ref) => AuthApi(ref.read(dioProvider)));
final authRepoProvider = Provider<AuthRepository>(
  (ref) => AuthRepositoryImpl(ref.read(authApiProvider)),
);
```

测试时直接 `overrideWithValue` 即可 mock。

## 5. 模块边界检查清单

回答需求时,对每个 feature 都要给出:
- 它在哪一层有代码?
- 它依赖了哪些其他 feature / core?(画 ASCII 依赖图)
- 它的 public 接口是什么?(只导出 entity 与 usecase,impl 不导出)

## 6. 反模式(立即拒绝)

- Widget 里直接 new Repository
- domain 层 import `package:flutter/*`
- 全局可变单例(get_it 当成全局变量用)
- 跨 feature 共享 mutable provider
- service locator 满天飞,无类型安全

## 参考 / References

- Flutter 官方架构指南(2024 重写,含 Clean Architecture 推荐):<https://docs.flutter.dev/app-architecture>
- Flutter 官方架构 Sample(`compass_app`,展示 Clean + Riverpod):<https://github.com/flutter/samples/tree/main/compass_app>
- Robert C. Martin "The Clean Architecture":<https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html>
- DDD-Lite for Flutter(社区参考):<https://github.com/ResoCoder/flutter-tdd-clean-architecture-course>
- Bob Martin 演讲 "Architecture: The Lost Years":<https://www.youtube.com/watch?v=WpkDN78P884>
- Very Good Ventures Flutter 工程模板:<https://github.com/VeryGoodOpenSource/very_good_core>
- `freezed`(密封类 + immutable model):<https://pub.dev/packages/freezed>
- `fpdart`(`Either<L,R>` / `Option`,函数式错误模型):<https://pub.dev/packages/fpdart>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **依赖指向内层**:presentation→domain←data,domain 不依赖框架/IO/具体三方包。
- **错误是值不是异常**:用 `Either`/`Result` 让失败显式、可测,而不是到处 try-catch。
- **边界即契约**:跨层只经接口(repository/usecase),换实现不动调用方。

**诚实边界:**

- 这是组织代码的骨架规范,不替你做具体业务建模与领域划分。
- 小项目过度分层会徒增成本;按规模裁剪,不是层越多越好。
