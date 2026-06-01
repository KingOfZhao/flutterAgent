---
id: flutter-testability-design
name: Flutter 可测试性设计(依赖注入 / 接缝 / 纯函数核心 / 控制时间与随机)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [testability, dependency-injection, seams, pure-functions, fake, mock, determinism, clock, design-for-test]
applies_when: 代码"能跑但很难测"时——重新设计接缝与依赖方向,让单元可在无网络/无设备/可控时间下被测
stage_hints: [architecture, implementation, review]
see_also: [flutter-testing, flutter-domain-modeling, flutter-error-handling, state-management]
---

# Flutter 可测试性设计

本 skill 负责**怎么设计代码,让它好测**(design for testability):依赖注入、接缝、
把副作用推到边界、控制时间/随机/IO。它和 `flutter-testing` 分工明确——
`flutter-testing` 讲**怎么写各类测试**(unit/widget/golden/集成)与模板,
本 skill 讲**怎么把代码改造成可测的形状**,是写测试之前的设计前提。
领域类型设计见 `flutter-domain-modeling`,失败路径见 `flutter-error-handling`。

## 0. 核心命题:可测试性是设计属性,不是测试技巧

测不了的代码,八成是设计问题:依赖是硬编码 new 出来的、副作用和逻辑搅在一起、
依赖了"现在几点/随机数/真实网络"。解决靠**改设计**,而不是堆 mock。

## 1. 依赖注入(DI):别在内部 `new` 协作者

```dart
// ❌ 难测:内部直接造依赖,测试无法替换
class LoginService {
  final _api = AuthApi();          // 硬编码,测试会打真网络
}
// ✅ 可测:依赖从构造函数传入(接缝),测试传 fake
class LoginService {
  LoginService(this._api);
  final AuthApi _api;
}
```

- 依赖以**抽象**(abstract class / 接口)注入,生产传真实现、测试传 fake。
- 用 provider/get_it 等做装配(见 `state-management`),但**核心类不该知道容器存在**。

## 2. 纯函数核心 + 副作用边界(Functional Core, Imperative Shell)

- 把业务计算抽成**纯函数**(无 IO、无全局、同输入同输出)——这是最容易测的代码。
- 把 IO/网络/磁盘/时钟推到**最外层薄壳**,壳尽量无逻辑。
- 测试集中火力测纯核心(快、稳、无需 mock),壳用少量集成测试覆盖。

## 3. 控制不确定性:时间、随机、ID

- **时间**:别直接 `DateTime.now()`/`Future.delayed`;注入 `Clock`(`clock` 包)或时间函数,
  widget 测试用 `tester.pump(duration)` / `fakeAsync` 推进时间。
- **随机**:注入 `Random(seed)`,测试用固定种子可复现。
- **ID/UUID**:注入生成器,测试可固定。
- 原则:凡"每次运行结果不同"的来源,都做成可注入的依赖。

## 4. 接缝(Seam):留出替换点

- 网络层抽 `ApiClient` 接口;持久化抽 `Repository` 接口(见 `flutter-data-persistence`)。
- 平台能力(权限/通道,见 `flutter-platform-channels`)包一层可替换的封装,别让 UI 直接调静态平台 API。
- 全局单例是测试之敌:能注入就别单例;必须单例也留一个测试可重置的入口。

## 5. Fake 优先于 Mock

- **Fake**(可用的轻量实现,如内存版 repo)比 **Mock**(录制期望)更稳、更接近真实、重构时不易碎。
- 只在"验证交互本身就是需求"(如确实调用了上报)时才用 mock 断言调用。
- 避免过度 mock 到"测的是 mock 而不是代码"。

## 6. 与测试金字塔对齐

- 设计良好 → 大量便宜的单元测试(纯核心)+ 适量 widget 测试 + 少量集成测试。
- 具体测试类型、模板、CI 集成见 `flutter-testing`;修 bug 的回归测试见 `flutter-debugging`。

## 反模式

- ❌ 在类内部 `new` 出网络/数据库依赖,测试只能打真实环境。
- ❌ 业务逻辑写在 `build()`/事件回调里,和 UI 死绑,无法单测。
- ❌ 直接用 `DateTime.now()`/`Random()`,导致测试随时间/运气而抖。
- ❌ 满屏 mock 且断言一堆调用顺序,重构一点就红一片(脆弱测试)。
- ❌ 靠全局单例共享状态,测试间相互污染、无法并行。

## 参考 / References

- Flutter 测试(整体):<https://docs.flutter.dev/testing/overview>
- `tester.pumpWidget` / 推进时间:<https://api.flutter.dev/flutter/flutter_test/WidgetTester-class.html>
- `fake_async`:<https://pub.dev/packages/fake_async>
- `clock`(可注入时钟):<https://pub.dev/packages/clock>
- `mocktail`(fake/mock):<https://pub.dev/packages/mocktail>
- Effective Dart(设计):<https://dart.dev/effective-dart/design>
- 测试类型与模板见 `flutter-testing`;领域建模见 `flutter-domain-modeling`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **测不了通常是设计问题**:先改接缝,再写测试,别用 mock 硬怼。
- **把不确定性赶到边界**:纯核心可测,副作用薄壳少测。
- **依赖朝抽象注入**:能替换才能测,硬编码即锁死。

**诚实边界:**

- 可测试性不是免费的:抽象/注入有样板成本,简单脚本别过度设计。
- Fake 也要维护,且可能与真实实现漂移;关键路径仍需集成/端到端测试兜底。
- 100% 覆盖率不是目标;测对地方(核心逻辑、失败路径)比测全更重要。
