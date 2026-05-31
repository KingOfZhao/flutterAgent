---
id: flutter-navigation
name: Flutter 导航与路由规范
version: 1.0.0
platforms: [all]
tags: [navigation, routing, deeplink, go_router, navigator, tabs, nested]
applies_when: 需求涉及页面跳转、深度链接、嵌套导航、Tab 页面保活或路由守卫
stage_hints: [spec, architecture, breakdown]
---

# Flutter 导航与路由规范

> 直接依据:
> * Flutter 官方:**[docs.flutter.dev/ui/navigation](https://docs.flutter.dev/ui/navigation)**
> * go_router package:**[pub.dev/packages/go_router](https://pub.dev/packages/go_router)**
> * Flutter 官方 Deep linking:**[docs.flutter.dev/ui/navigation/deep-linking](https://docs.flutter.dev/ui/navigation/deep-linking)**

---

## 1. 路由方案选型

| 方案 | 推荐场景 | 官方态度 |
|------|----------|----------|
| Navigator 1.0 (imperative) | 简单 App、少量页面 | 内置 API, 始终可用 |
| Navigator 2.0 (declarative) | 需要完全控制路由栈 | 官方 API, 但 API 复杂 |
| **go_router** | 中大型 App, deep link, web | **Flutter 官方推荐** (flutter.dev team 维护) |
| auto_route | 代码生成路由 | 社区流行, 类型安全 |

> go_router 是 Flutter 团队维护的官方路由包 (在 flutter/packages 仓库下)。
> 源码: <https://github.com/flutter/packages/tree/main/packages/go_router>

---

## 2. go_router 标准用法

### 2.1 路由声明

```dart
final router = GoRouter(
  initialLocation: '/',
  debugLogDiagnostics: true,  // 开发阶段开启路由日志
  routes: [
    GoRoute(
      path: '/',
      name: 'home',
      builder: (context, state) => const HomeScreen(),
      routes: [
        GoRoute(
          path: 'product/:id',
          name: 'product-detail',
          builder: (context, state) {
            final id = state.pathParameters['id']!;
            return ProductDetailScreen(productId: id);
          },
        ),
      ],
    ),
  ],
);
```

### 2.2 MaterialApp.router 集成

```dart
MaterialApp.router(
  routerConfig: router,
  // 不再使用 home 或 routes 参数
)
```

### 2.3 编程式导航

```dart
// push (加入栈)
context.push('/product/42');

// go (替换栈)
context.go('/product/42');

// 带 extra 数据
context.push('/product/42', extra: myObject);

// pop
context.pop();

// 命名路由
context.pushNamed('product-detail', pathParameters: {'id': '42'});
```

---

## 3. Deep Linking (深度链接)

### 3.1 平台配置

**Android** — `AndroidManifest.xml`:
```xml
<intent-filter android:autoVerify="true">
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="example.com" />
</intent-filter>
```

**iOS** — Associated Domains (Runner.entitlements):
```xml
<key>com.apple.developer.associated-domains</key>
<array>
  <string>applinks:example.com</string>
</array>
```

### 3.2 go_router 自动处理

go_router 内置 deep link 支持, 无需额外配置:
- `GoRouter` 自动监听平台 deep link 事件
- URL 路径直接映射到声明的 `GoRoute.path`
- Web 端自动同步浏览器 URL

---

## 4. 嵌套导航 (Nested Navigation)

### 4.1 ShellRoute — Tab 页面保活

```dart
final router = GoRouter(
  routes: [
    ShellRoute(
      builder: (context, state, child) => ScaffoldWithNavBar(child: child),
      routes: [
        GoRoute(path: '/feed', builder: (_, __) => const FeedScreen()),
        GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
        GoRoute(path: '/profile', builder: (_, __) => const ProfileScreen()),
      ],
    ),
  ],
);
```

### 4.2 StatefulShellRoute — Tab 状态保活

```dart
StatefulShellRoute.indexedStack(
  builder: (context, state, navigationShell) {
    return ScaffoldWithNavBar(navigationShell: navigationShell);
  },
  branches: [
    StatefulShellBranch(routes: [
      GoRoute(path: '/feed', builder: (_, __) => const FeedScreen()),
    ]),
    StatefulShellBranch(routes: [
      GoRoute(path: '/search', builder: (_, __) => const SearchScreen()),
    ]),
  ],
)
```

> `StatefulShellRoute` 通过 `IndexedStack` 保持每个 branch 的状态, 切换 Tab 不会重建页面。

---

## 5. 路由守卫 (Redirect)

```dart
GoRouter(
  redirect: (context, state) {
    final loggedIn = AuthProvider.of(context).isLoggedIn;
    final isLoginPage = state.matchedLocation == '/login';

    if (!loggedIn && !isLoginPage) return '/login';
    if (loggedIn && isLoginPage) return '/';
    return null;  // null = 不重定向
  },
  // ...
)
```

**规则:**
1. `redirect` 应为纯函数, 不产生副作用。
2. 避免在 `redirect` 中执行异步操作 — 登录状态应已预加载。
3. 使用 `refreshListenable` 监听认证状态变化, 自动触发重新检查。

---

## 6. 类型安全路由 (go_router_builder)

```yaml
# pubspec.yaml
dependencies:
  go_router: ^14.0.0
dev_dependencies:
  go_router_builder: ^2.7.0
  build_runner: ^2.4.0
```

```dart
// 声明类型安全路由
@TypedGoRoute<HomeRoute>(path: '/')
class HomeRoute extends GoRouteData {
  const HomeRoute();
  @override
  Widget build(BuildContext context, GoRouterState state) => const HomeScreen();
}

// 使用
const HomeRoute().go(context);
```

---

## 7. 导航测试

```dart
testWidgets('navigates to product detail', (tester) async {
  final router = GoRouter(
    initialLocation: '/',
    routes: testRoutes,
  );

  await tester.pumpWidget(MaterialApp.router(routerConfig: router));
  await tester.tap(find.text('Product 42'));
  await tester.pumpAndSettle();
  expect(find.byType(ProductDetailScreen), findsOneWidget);
});

// 测试 redirect
test('unauthenticated user redirected to login', () {
  final router = GoRouter(
    initialLocation: '/profile',
    redirect: (_, __) => '/login',
    routes: [...],
  );
  expect(router.state?.matchedLocation, '/login');  // 概念性验证
});
```

---

## 8. 常见反模式

| 反模式 | 正确做法 |
|--------|----------|
| 使用全局 `GlobalKey<NavigatorState>` 传递上下文 | 使用 `GoRouter` + `context.push/go` |
| 在 `build` 中调用 `Navigator.push` | 使用按钮回调或 `onTap` 触发导航 |
| deep link 路径硬编码字符串散落各处 | 集中定义路由常量或使用 `go_router_builder` |
| Tab 页面每次切换都重建 | 使用 `StatefulShellRoute` 保活 |
| `WillPopScope` (deprecated) | 使用 `PopScope` (Flutter 3.16+) |

---

## 9. Flutter 3.44 导航更新

### CupertinoSheetRoute

iOS 底部半屏弹窗路由,实现了滚动组件与手势下拉关闭动画的平滑协同:

```dart
Navigator.of(context).push(
  CupertinoSheetRoute(
    builder: (context) => const BottomSheetPage(),
  ),
);
```

### Web `--base-href` 本地调试

Flutter 3.44 支持 `flutter run -d chrome --base-href /app/`,本地即可模拟生产环境子目录部署,避免路由 404:

```bash
flutter run -d chrome --base-href /myapp/
```

### iOS 26 Safari Autofill

Web 端新增 iOS 26 Safari 自动填充支持,提升表单类页面的移动端体验。

## 参考

- Flutter 官方 Navigation overview: <https://docs.flutter.dev/ui/navigation>
- Flutter 官方 Deep linking: <https://docs.flutter.dev/ui/navigation/deep-linking>
- go_router package: <https://pub.dev/packages/go_router>
- go_router migration guide: <https://docs.flutter.dev/ui/navigation/url-strategies>
- go_router_builder: <https://pub.dev/packages/go_router_builder>
- StatefulShellRoute docs: <https://pub.dev/documentation/go_router/latest/go_router/StatefulShellRoute-class.html>
- Flutter Navigator 2.0 解析: <https://docs.flutter.dev/ui/navigation#using-the-router>
- auto_route package: <https://pub.dev/packages/auto_route>
- Flutter PopScope (WillPopScope replacement): <https://api.flutter.dev/flutter/widgets/PopScope-class.html>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **路由是声明式状态**:URL/路由表是真相源,别命令式堆栈乱 push。
- **深链/守卫从一开始设计**:鉴权重定向、未登录回跳是路由职责。
- **类型安全优先**:用 go_router_builder 让路由参数编译期可查。

**诚实边界:**

- 复杂嵌套/保活场景边界多,需按真实导航图实测回退行为。
- 不替你做信息架构(哪些是页面、层级如何)。
