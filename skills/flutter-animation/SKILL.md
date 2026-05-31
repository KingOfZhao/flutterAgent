---
id: flutter-animation
name: Flutter 动画与运动设计规范
version: 1.0.0
platforms: [all]
tags: [animation, motion, transition, hero, lottie, rive, implicit, explicit, curve]
applies_when: 需求涉及动画、过渡、运动效果、微交互或动效设计
stage_hints: [spec, architecture, breakdown]
---

# Flutter 动画与运动设计规范

> 直接依据:
> * Flutter 官方:**[docs.flutter.dev/ui/animations](https://docs.flutter.dev/ui/animations)**
> * Material 3 Motion:**[m3.material.io/styles/motion/overview](https://m3.material.io/styles/motion/overview)**
> * Flutter Cookbook — Animations:**[docs.flutter.dev/cookbook/animation](https://docs.flutter.dev/cookbook/animation)**

---

## 1. 隐式动画 (Implicit Animations)

适用于只需声明目标值、由框架自动补间的场景。

| Widget | 用途 | 关键属性 |
|--------|------|----------|
| `AnimatedContainer` | 尺寸/颜色/边距等组合变化 | `duration`, `curve` |
| `AnimatedOpacity` | 淡入淡出 | `opacity`, `duration` |
| `AnimatedPositioned` | Stack 内定位动画 | `left/top/...`, `duration` |
| `AnimatedSwitcher` | 子 Widget 切换过渡 | `transitionBuilder` |
| `AnimatedCrossFade` | 两子 Widget 交叉淡入淡出 | `crossFadeState` |
| `AnimatedDefaultTextStyle` | 文字样式过渡 | `style`, `duration` |
| `AnimatedPadding` | 内边距过渡 | `padding`, `duration` |

```dart
// 官方示例: AnimatedContainer
AnimatedContainer(
  duration: const Duration(milliseconds: 300),
  curve: Curves.easeInOut,
  width: _expanded ? 200 : 100,
  height: _expanded ? 200 : 100,
  color: _expanded ? Colors.blue : Colors.red,
)
```

**规则: 简单属性过渡优先使用隐式动画,避免手动管理 AnimationController。**

---

## 2. 显式动画 (Explicit Animations)

当需要精确控制进度、组合多个动画、监听状态时使用。

### 2.1 AnimationController 生命周期

```dart
class _MyAnimState extends State<MyAnim> with SingleTickerProviderStateMixin {
  late final AnimationController _ctrl;
  late final Animation<double> _scale;

  @override
  void initState() {
    super.initState();
    _ctrl = AnimationController(
      vsync: this,          // SingleTickerProviderStateMixin
      duration: const Duration(milliseconds: 400),
    );
    _scale = CurvedAnimation(parent: _ctrl, curve: Curves.elasticOut);
  }

  @override
  void dispose() {
    _ctrl.dispose();        // 必须 dispose 防止泄漏
    super.dispose();
  }
}
```

### 2.2 常用 Tween 类型

| Tween | 泛型 | 场景 |
|-------|------|------|
| `Tween<double>` | double | 缩放、透明度 |
| `ColorTween` | Color | 颜色渐变 |
| `RectTween` | Rect | Hero-like 矩形变换 |
| `IntTween` | int | 离散值动画 |
| `AlignmentTween` | Alignment | 对齐偏移 |

### 2.3 AnimatedBuilder vs AnimatedWidget

- **`AnimatedBuilder`**: 通用; 将动画逻辑与渲染 Widget 解耦。
- **`AnimatedWidget`**: 继承基类, 适合封装可复用的动画组件。

```dart
AnimatedBuilder(
  animation: _ctrl,
  builder: (context, child) => Transform.scale(
    scale: _scale.value,
    child: child,
  ),
  child: const Icon(Icons.star),   // child 不随 build 重建
)
```

---

## 3. Hero 动画

跨页面共享元素过渡, Flutter 内置 `Hero` Widget。

```dart
// 源页面
Hero(
  tag: 'product-${item.id}',
  child: Image.network(item.imageUrl),
)

// 目标页面
Hero(
  tag: 'product-${item.id}',
  child: Image.network(item.imageUrl, fit: BoxFit.cover),
)
```

**规则:**
1. `tag` 在同一个 Navigator 层级下必须唯一。
2. 避免在 Hero child 中使用 `ClipRRect` 等可能导致布局跳变的 Widget — 改用 `flightShuttleBuilder`。
3. 对列表→详情场景, `tag` 使用业务唯一 ID 而非 index。

---

## 4. 页面过渡 (Page Transitions)

```dart
// 使用 PageRouteBuilder 自定义过渡
PageRouteBuilder(
  transitionDuration: const Duration(milliseconds: 350),
  pageBuilder: (_, __, ___) => const DetailPage(),
  transitionsBuilder: (_, animation, __, child) {
    return FadeTransition(
      opacity: CurvedAnimation(parent: animation, curve: Curves.easeIn),
      child: child,
    );
  },
)
```

| 内置 Transition Widget | 效果 |
|------------------------|------|
| `FadeTransition` | 淡入/淡出 |
| `SlideTransition` | 平移 |
| `ScaleTransition` | 缩放 |
| `RotationTransition` | 旋转 |
| `SizeTransition` | 尺寸变化 |

---

## 5. 物理/弹簧动画

使用 `SpringSimulation` 或 `physics_model` 插件实现物理真实感:

```dart
final spring = SpringDescription(
  mass: 1,
  stiffness: 100,
  damping: 10,
);
_ctrl.animateWith(SpringSimulation(spring, 0, 1, 0));
```

---

## 6. 第三方动效集成

| 包 | pub.dev | 适用 |
|----|---------|------|
| `lottie` | [pub.dev/packages/lottie](https://pub.dev/packages/lottie) | After Effects 导出 JSON 动画 |
| `rive` | [pub.dev/packages/rive](https://pub.dev/packages/rive) | 交互式矢量动画 (状态机) |
| `flutter_animate` | [pub.dev/packages/flutter_animate](https://pub.dev/packages/flutter_animate) | 声明式链式动画 API |
| `animations` | [pub.dev/packages/animations](https://pub.dev/packages/animations) | Material motion (container transform 等) |

```dart
// lottie 示例
Lottie.asset(
  'assets/animations/loading.json',
  width: 120,
  height: 120,
  repeat: true,
);
```

---

## 7. 性能注意事项

1. **RepaintBoundary**: 将频繁动画区域用 `RepaintBoundary` 包裹, 避免整个子树重绘。
2. **shouldRebuild**: 自定义 `CustomPainter.shouldRepaint()` 只在值变化时返回 true。
3. **addPostFrameCallback**: 避免在 `build()` 中触发动画启动; 使用 `SchedulerBinding.instance.addPostFrameCallback`。
4. **GPU 线程**: 使用 DevTools Performance overlay 监控 raster 线程; 复杂路径动画考虑 `saveLayer` 成本。
5. **帧率**: 对 60fps 目标, 每帧预算 ≤ 16ms; 120Hz 设备 ≤ 8ms。

---

## 8. 动画测试

```dart
testWidgets('fade in animation completes', (tester) async {
  await tester.pumpWidget(const MyFadeWidget());
  expect(find.byType(FadeTransition), findsOneWidget);

  // 推进动画到一半
  await tester.pump(const Duration(milliseconds: 150));
  final fade = tester.widget<FadeTransition>(find.byType(FadeTransition));
  expect(fade.opacity.value, greaterThan(0));
  expect(fade.opacity.value, lessThan(1));

  // 推进到动画完成
  await tester.pumpAndSettle();
  expect(fade.opacity.value, equals(1.0));
});
```

---

## 9. Flutter 3.44 动画与组件更新

### Material / Cupertino 解耦

自 Flutter 3.44 起,`Material` 和 `Cupertino` 库框架内更新**已冻结**,后续将迁移为独立包 `material_ui` 和 `cupertino_ui`。动画相关组件需注意迁移。

### MenuAnchor 灵动微动效

`MenuAnchor` 新增 Material 3 原生微动效(需手动 `animated: true` 开启),提升菜单展开流畅度。`SubmenuButton` 新增 `hoverOpenDelay` 控制桌面端悬停延迟。

### CupertinoMenuAnchor

全新 iOS 风格菜单锚点组件,基于 `RawMenuAnchor` 重构,解决旧版 Cupertino 菜单在复杂布局下的定位与层级问题。

### CupertinoSheetRoute

iOS 底部半屏弹窗路由,实现了"滚动组件"与"手势下拉关闭"的平滑协同,消除滑动冲突。

### reduceMotion 自动适配

引擎自动响应系统"减弱动态效果"设置,Flutter Web/桌面端自动禁用非必要动效。详见 `flutter-accessibility` skill。

### ShapedInputBorder

`TextField` 现在接受任意 `ShapeBorder` 自定义边框,可传入 `RoundedSuperellipseBorder` 实现 iOS 风格丝滑圆角。

### CarouselView 无限循环

`CarouselView` 解锁无限循环滚动能力,控制器新增 `onIndexChanged` 回调和 `leadingItem` 属性。

### ExpansionTile 增强

`ExpansibleController` 新增 `toggle()` 方法;`RadioListTile` / `CheckboxListTile` / `SwitchListTile` 支持 `WidgetStatesController`。

## 参考

- Flutter 官方 Animations overview: <https://docs.flutter.dev/ui/animations>
- Flutter 官方 Animations tutorial: <https://docs.flutter.dev/ui/animations/tutorial>
- Flutter 官方 Implicit animations: <https://docs.flutter.dev/ui/animations/implicit-animations>
- Flutter 官方 Hero animations: <https://docs.flutter.dev/ui/animations/hero-animations>
- Material 3 Motion: <https://m3.material.io/styles/motion/overview>
- `animations` package (Google): <https://pub.dev/packages/animations>
- `flutter_animate` package: <https://pub.dev/packages/flutter_animate>
- `lottie` package: <https://pub.dev/packages/lottie>
- `rive` package: <https://pub.dev/packages/rive>
- Flutter Performance profiling: <https://docs.flutter.dev/perf/ui-performance>
