---
id: flutter-testing
name: Flutter 测试规范(unit / widget / integration / golden)
version: 1.0.0
platforms: [all]
tags: [testing, unit, widget, integration, golden, ci]
applies_when: 任何包含 features 的产物都必须配测试计划
stage_hints: [breakdown, acceptance]
---

# Flutter 测试规范

## 1. 测试金字塔

```
           ┌──────────┐
           │ e2e (5%)  │   integration_test, 真机/模拟器
        ┌──┴──────────┴──┐
        │ widget (25%)    │   golden + interactive
   ┌────┴─────────────────┴────┐
   │ unit (70%)                 │   pure Dart, mocktail
   └────────────────────────────┘
```

> 任何 PR 必须给出对应层级的测试,**禁止仅靠人工 QA**。

## 2. 测试类型清单

| 类型 | 工具 | 覆盖目标 | 命名 |
|---|---|---|---|
| unit | `flutter_test` + `mocktail` | usecase / repository / mapper / 纯函数 | `<name>_test.dart` |
| widget | `flutter_test` + `WidgetTester` | 单页面或单组件,含交互 | `<page_name>_widget_test.dart` |
| golden | `flutter_test` + `--update-goldens` | UI 视觉回归 | `<page_name>_golden_test.dart` |
| integration | `integration_test` | 端到端关键链路 | `<flow_name>_integration_test.dart` |

## 3. 强制约束

- **覆盖率**: domain ≥ 90%,data ≥ 75%,presentation ≥ 50%(由 widget test 兜底)
- **禁止** mock domain 层之外的实体类(用真对象)
- **禁止** 在测试里依赖 `await Future.delayed`,使用 `tester.pump()` / `pumpAndSettle()`
- **禁止** 让 widget test 直接发起网络请求,`dio` 必须被 `MockDio` 替换
- 所有 Repository 抽象至少有 1 个针对成功 + 1 个针对每种 Failure 的 unit test
- Riverpod 测试用 `ProviderContainer`,**禁止** 全局状态泄漏

## 4. 测试模板

### 4.1 unit (mocktail)

```dart
class _MockApi extends Mock implements AuthApi {}

void main() {
  late _MockApi api;
  late AuthRepositoryImpl repo;

  setUp(() { api = _MockApi(); repo = AuthRepositoryImpl(api); });

  test('login success returns User', () async {
    when(() => api.login(any(), any())).thenAnswer((_) async => userJson);
    final result = await repo.login('a@b.c', 'pw');
    expect(result.isRight, true);
  });

  test('login 401 returns AuthFailure', () async {
    when(() => api.login(any(), any())).thenThrow(DioException(...));
    final result = await repo.login('a@b.c', 'bad');
    expect(result.left, isA<AuthFailure>());
  });
}
```

### 4.2 widget

```dart
testWidgets('LoginPage shows error on bad creds', (tester) async {
  final container = ProviderContainer(overrides: [
    authRepoProvider.overrideWithValue(_StubRepo.failing()),
  ]);
  addTearDown(container.dispose);
  await tester.pumpWidget(UncontrolledProviderScope(
    container: container,
    child: const MaterialApp(home: LoginPage()),
  ));
  await tester.enterText(find.byKey(const Key('email')), 'a@b.c');
  await tester.enterText(find.byKey(const Key('pwd')), 'bad');
  await tester.tap(find.byKey(const Key('submit')));
  await tester.pump();
  expect(find.text('账号或密码错误'), findsOneWidget);
});
```

### 4.3 golden

- 命名: `goldens/<page>/<state>.png`
- 必须在三种屏幕宽度跑一次:`compact`(360)、`expanded`(1024)、`extraLarge`(1600)
- 字体使用 `loadAppFonts()`,避免 CI 上字体不一致
- 更新规则:UI 改动必须随 PR 一起 `flutter test --update-goldens` 并人审

### 4.4 integration

- 必须能在 CI 跑:Android emulator + iOS simulator + (PC 用例) macos / windows headless
- 至少覆盖:登录链路、主页面渲染、核心 CRUD 一条
- 数据用 in-memory 假后端,**不要** 打线上

## 5. CI 集成(必须列出)

```yaml
- flutter analyze
- dart format --set-exit-if-changed .
- flutter test --coverage
- genhtml coverage/lcov.info -o coverage/html
- flutter test integration_test --device-id=emulator-5554
```

每个产出需包含:
1. 工时分配中,测试任务 ≥ 30% 实现工时
2. 必须列出 ≥ 1 个 unit、≥ 1 个 widget、≥ 1 个 integration 用例
3. 失败率监控:CI 上出现 flake 必须 24h 内修或暂时跳过(标 TODO)

## 6. 红线

- 不要把日志里的 secret 留在测试 fixture
- 不要把测试用例写成「能跑就行」,必须断言可观测后果
- 不要让一个测试覆盖 > 1 个行为
- golden 失败不能直接 `--update-goldens` 不审查

## 参考 / References

- Flutter 官方测试文档总览:<https://docs.flutter.dev/testing>
- `flutter_test` API:<https://api.flutter.dev/flutter/flutter_test/flutter_test-library.html>
- `integration_test` API:<https://api.flutter.dev/flutter/integration_test/integration_test-library.html>
- `mocktail`(零代码生成的 mock):<https://pub.dev/packages/mocktail>
- `bloc_test`(BLoC 专用测试工具):<https://pub.dev/packages/bloc_test>
- `golden_toolkit`(多设备多分辨率 golden):<https://pub.dev/packages/golden_toolkit>
- `patrol`(更强的端到端测试):<https://pub.dev/packages/patrol>
- Very Good Ventures `very_good_workflows` (CI 模板):<https://github.com/VeryGoodOpenSource/very_good_workflows>
- 覆盖率工具 `lcov` / `genhtml`:<https://github.com/linux-test-project/lcov>
- 官方 Sample test 写法参照:<https://github.com/flutter/samples>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **测试金字塔**:多单元、适量 widget、少而关键的集成,按成本/价值分配。
- **测行为不测实现**:断言用户可见结果与契约,别绑死内部结构。
- **可测性是设计产物**:依赖注入 / 纯函数让代码天然好测。

**诚实边界:**

- 覆盖率是信号不是目标;高覆盖 ≠ 无 bug。
- 不替代探索性测试与真机/真用户验证。
