---
id: flutter-ui-component-recipes
name: 组件级还原范例库 (照图找 Flutter 组件)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [ui, components, recipes, widgets, design-to-code, material, cupertino]
applies_when: 看着设计稿里的某个 UI 元素,需要快速找到对应 Flutter 组件与实现骨架
stage_hints: [breakdown, acceptance]
---

# 组件级还原范例库

一张"**看到什么 → 用哪个 widget → 骨架怎么写 → 易错点**"的查表。
配合 `flutter-design-to-code-playbook` 的 S4 使用:读图拿到组件清单后,逐项来这里对照。
原则:**优先用框架既有组件**,别一上来就 `CustomPaint` 自绘;样式走主题 token(见 `flutter-design-tokens-theming`)。

## 查表:常见 UI → 组件

| 设计稿里看到 | 首选 widget | 备注 |
|---|---|---|
| 整页脚手架(顶栏+内容+底栏) | `Scaffold` + `AppBar` + `bottomNavigationBar` | 别手搓顶栏 |
| 填充/描边/文本按钮 | `FilledButton` / `OutlinedButton` / `TextButton` | M3 语义按钮 |
| 图标按钮 | `IconButton` | 命中区 ≥48dp(见 `flutter-accessibility`) |
| 输入框 | `TextField` + `InputDecoration` | 装饰统一进 `inputDecorationTheme` |
| 卡片 | `Card` | 圆角/阴影走 `cardTheme` |
| 列表 | `ListView.builder` / `ListTile` | 长列表必用 builder(见 `flutter-performance`) |
| 网格 | `GridView` / `SliverGrid` | 复杂滚动用 Sliver |
| 标签/徽标 | `Chip` / `Badge` | |
| 顶部标签页 | `TabBar` + `TabBarView` | `TabController` 管理 |
| 底部导航 | `NavigationBar`(M3) | 旧版 `BottomNavigationBar` |
| 侧边抽屉 | `Drawer` | |
| 头像 | `CircleAvatar` | |
| 进度 | `CircularProgressIndicator` / `LinearProgressIndicator` | |
| 弹窗/底部弹层 | `showDialog` / `showModalBottomSheet` | |
| 开关/勾选/单选 | `Switch` / `Checkbox` / `Radio` | |
| 滑块 | `Slider` | |

## 骨架范例(可直接套)

### 1. 渐变按钮(框架没有现成的)

```dart
DecoratedBox(
  decoration: BoxDecoration(
    gradient: const LinearGradient(
      begin: Alignment.centerLeft, end: Alignment.centerRight,
      colors: [Color(0xFF7B61FF), Color(0xFF4D7CFE)],
    ),
    borderRadius: BorderRadius.circular(12),
  ),
  child: FilledButton(
    style: FilledButton.styleFrom(
      backgroundColor: Colors.transparent, shadowColor: Colors.transparent,
    ),
    onPressed: () {},
    child: const Text('继续'),
  ),
)
```
易错:渐变方向看 `flutter-ui-from-image` §3;别用图片当按钮背景(失真、不可缩放)。

### 2. 带角标的头像

```dart
Badge(
  label: const Text('3'),
  child: const CircleAvatar(radius: 24, backgroundImage: NetworkImage(url)),
)
```
易错:网络图要处理加载/失败占位(见 `flutter-resource-lifecycle`)。

### 3. 卡片列表项

```dart
Card(
  child: ListTile(
    leading: const Icon(Icons.folder),
    title: Text('标题', style: Theme.of(context).textTheme.titleMedium),
    subtitle: const Text('副标题'),
    trailing: const Icon(Icons.chevron_right),
    onTap: () {},
  ),
)
```
易错:文字样式取 `textTheme`,别内联 `fontSize`。

### 4. 输入框(统一装饰)

```dart
TextField(
  decoration: InputDecoration(
    labelText: '邮箱',
    prefixIcon: const Icon(Icons.mail_outline),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(8)),
  ),
)
```
易错:同一项目装饰应进 `inputDecorationTheme`,这里只覆盖差异。

### 5. 圆角图片 + 渐变遮罩(图上压文字)

```dart
ClipRRect(
  borderRadius: BorderRadius.circular(16),
  child: Stack(fit: StackFit.passthrough, children: [
    Image.network(url, fit: BoxFit.cover),
    const DecoratedBox(decoration: BoxDecoration(
      gradient: LinearGradient(
        begin: Alignment.topCenter, end: Alignment.bottomCenter,
        colors: [Colors.transparent, Colors.black54]))),
    const Positioned(left: 12, bottom: 12, child: Text('标题')),
  ]),
)
```
易错:遮罩是为了文字对比度(见 `flutter-accessibility`),方向/透明度按图调。

### 6. 骨架屏(加载态)

```dart
// 用 shimmer 包或自绘灰块;关键是给"加载态"一个占位,别白屏
```
易错:加载/空/错误三态要补齐(见 `flutter-error-handling`、playbook S6)。

## 何时才自绘(CustomPaint)

只有当**既有组件 + 组合 + 装饰都无法表达**时才上 `CustomPaint`/`CustomClipper`:
异形裁剪、复杂图表、手绘曲线、特殊进度环。自绘要注意重绘范围与性能(见 `flutter-performance`)。

## 反模式

- ❌ 能用 `FilledButton` 却用 `GestureDetector` + `Container` 手搓按钮(丢无障碍/水波/语义)。
- ❌ 用整张切图当组件背景(失真、不随主题、体积大)。
- ❌ 样式内联硬编码,不走主题 token。
- ❌ 长列表用 `Column` + `SingleChildScrollView`(应 `ListView.builder`)。
- ❌ 一遇到稍复杂的形状就 `CustomPaint`,放着组合方案不用。
- ❌ 网络图/异步组件不给加载与失败占位。

## 参考 / References

- Material 组件目录:<https://docs.flutter.dev/ui/widgets/material>
- Widget 目录总览:<https://docs.flutter.dev/ui/widgets>
- Material 3 组件(M3):<https://m3.material.io/components>
- Cupertino 组件:<https://docs.flutter.dev/ui/widgets/cupertino>
- `BoxDecoration` / 渐变:<https://api.flutter.dev/flutter/painting/BoxDecoration-class.html>
- `CustomPaint`:<https://api.flutter.dev/flutter/widgets/CustomPaint-class.html>
- 组件清单来源见 `flutter-ui-from-image`;主题见 `flutter-design-tokens-theming`;端到端见 `flutter-design-to-code-playbook`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先找现成,再组合,最后才自绘**:90% 的 UI 用既有组件 + 装饰就能还原。
- **组件是语义不只是外观**:用 `FilledButton` 不仅省事,还自带语义/无障碍/反馈。
- **样式走主题**:组件只表达"是什么",颜色字号交给主题 token。

**诚实边界:**

- 本表是常见映射的**起点**,不是穷举;特殊设计仍需查官方组件目录或自绘。
- 组件 API、Material 版本随 Flutter 演进,以当时官方文档为准。
- 范例是**骨架**,生产代码还需接状态管理、错误态、无障碍与测试(见对应 skill)。
