---
id: flutter-design-tokens-theming
name: 设计 token 工程化主题 (ColorScheme / TextTheme / ThemeData / 亮暗双主题)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [theme, design-tokens, colorscheme, texttheme, material3, dark-mode, theme-extension, styling]
applies_when: 把提取/约定好的设计 token(色/字/间距/圆角/阴影)落成可维护的 Flutter 主题
stage_hints: [architecture, breakdown, implementation]
---

# 设计 token 工程化主题

把"散落在各 widget 里的硬编码颜色/字号"收敛成**一处定义、全局复用**的主题系统。
本 skill 管"**token 怎么组织、主题怎么搭、亮暗怎么切**";token 从图里怎么提取见
`flutter-ui-from-image`,对比度/无障碍见 `flutter-accessibility`,组件级样式落地配合 `dart-language-idioms`。

## 0. 心智:token 是单一事实源

- UI 的颜色/字号/间距/圆角都应来自**主题 token**,widget 里写 `Theme.of(context).colorScheme.primary`,**不写** `Color(0xFF...)` 字面量。
- 好处:改一处全局生效、亮暗一致、设计-代码对齐、可测可审查(评审红线见 `flutter-code-review`)。

## 1. 颜色:ColorScheme(Material 3)

两种来源:

- **种子色生成**(快速、和谐):`ColorScheme.fromSeed(seedColor: brandColor, brightness: ...)` —— Material 3 按一个品牌色推导出整套协调色板。
- **精确指定**(还原设计稿):逐个给 `ColorScheme(primary: ..., onPrimary: ..., surface: ...)`,把 `flutter-ui-from-image` 采到的色值精确落位。

```dart
final lightScheme = ColorScheme.fromSeed(seedColor: const Color(0xFF6750A4));
final darkScheme  = ColorScheme.fromSeed(
  seedColor: const Color(0xFF6750A4), brightness: Brightness.dark);
```

- 语义角色:`primary/secondary/tertiary`、`surface/surfaceContainer*`、`onX`、`error`。文字色一律用 `onSurface`/`onPrimary`,保证对比度(见 `flutter-accessibility`)。

## 2. 排版:TextTheme

- 用 Material 3 的语义层级:`displayLarge … titleMedium … bodyLarge … labelSmall`,而不是到处写 `TextStyle(fontSize: 16)`。
- 在 `ThemeData(textTheme: ...)` 统一定义字体族/字重/字号/行高;widget 里 `Theme.of(context).textTheme.bodyLarge`。
- 自定义字体在 `pubspec.yaml` 声明并随包打入(见 `flutter-build-and-release`);可用 `google_fonts`(注意运行时拉取 vs 预打包的取舍)。

## 3. 其余 token:间距 / 圆角 / 阴影 → ThemeExtension

Material 内置主题没有"间距/自定义语义色"槽位时,用 **`ThemeExtension`** 定义自己的 token 组:

```dart
@immutable
class AppTokens extends ThemeExtension<AppTokens> {
  const AppTokens({required this.gap, required this.radius, required this.success});
  final double gap; final double radius; final Color success;
  @override AppTokens copyWith({double? gap, double? radius, Color? success}) => ...
  @override AppTokens lerp(AppTokens? o, double t) => ...   // 支持主题动画过渡
}
```

- 注册到 `ThemeData(extensions: [AppTokens(...)])`;取用 `Theme.of(context).extension<AppTokens>()!`。
- 间距建议用 4/8 栅格(4,8,12,16,24…),圆角/阴影同理成档,避免随手取值。

## 4. 组装 ThemeData + 亮暗双主题

```dart
ThemeData buildTheme(ColorScheme scheme) => ThemeData(
  colorScheme: scheme,
  useMaterial3: true,
  textTheme: appTextTheme,
  extensions: [appTokens(scheme)],
  // 组件级:elevatedButtonTheme / cardTheme / inputDecorationTheme ...
);

MaterialApp(
  theme: buildTheme(lightScheme),
  darkTheme: buildTheme(darkScheme),
  themeMode: ThemeMode.system,   // 或受用户设置驱动
);
```

- 组件统一外观用 `XxxThemeData`(`cardTheme`、`inputDecorationTheme`、`elevatedButtonTheme`…),别在每个组件实例上重复写样式。
- 亮暗共用同一 `buildTheme`,只换 `ColorScheme`,保证两套主题结构一致。

## 5. 与流程衔接

- 新项目:先建 `theme/` 目录(`color_scheme.dart` / `text_theme.dart` / `app_tokens.dart` / `app_theme.dart`),再写业务(见 `flutter-feature-development`)。
- 既有项目治理:把硬编码颜色/字号逐步收敛进主题(小步重构,见 `flutter-refactoring`)。
- Cupertino/跨平台观感差异见 `flutter-cross-platform`。

## 反模式

- ❌ widget 里散落 `Color(0xFF...)` / `fontSize: 16` 硬编码,改一次找一片。
- ❌ 只做亮色主题,暗色靠临时 `if (isDark)` 补丁(应两套 ColorScheme)。
- ❌ 自定义 token 用全局常量而非 `ThemeExtension`,丢失随主题切换/动画过渡的能力。
- ❌ 间距/圆角随手取(7、13、17…),没有栅格,视觉不统一。
- ❌ 文字色不走 `onX`,亮暗下对比度不达标(见 `flutter-accessibility`)。

## 参考 / References

- Material 3 主题化(Flutter):<https://docs.flutter.dev/cookbook/design/themes>
- `ThemeData`:<https://api.flutter.dev/flutter/material/ThemeData-class.html>
- `ColorScheme` / `fromSeed`:<https://api.flutter.dev/flutter/material/ColorScheme-class.html>
- `TextTheme`:<https://api.flutter.dev/flutter/material/TextTheme-class.html>
- `ThemeExtension`(自定义 token):<https://api.flutter.dev/flutter/material/ThemeExtension-class.html>
- Material Design 3 颜色系统:<https://m3.material.io/styles/color/system/overview>
- 自定义字体:<https://docs.flutter.dev/cookbook/design/fonts> · `google_fonts`:<https://pub.dev/packages/google_fonts>
- token 提取见 `flutter-ui-from-image`;对比度见 `flutter-accessibility`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **主题是单一事实源**:颜色/字号/间距只在主题里定义一次,widget 只消费不定义。
- **语义优先于字面**:用 `colorScheme.primary` / `textTheme.bodyLarge` 这类**角色**,而非具体色值/字号,亮暗与改版才不崩。
- **亮暗是结构对称**:两套 ColorScheme 灌进同一份 buildTheme,而不是到处 `if(isDark)`。

**诚实边界:**

- `ColorScheme.fromSeed` 生成的是**协调色**,不等于设计稿精确色;要 1:1 还原需精确指定各角色色(配合 `flutter-ui-from-image`)。
- Material 3 的色彩/组件规范随 Flutter 版本演进,以官方当时文档为准。
- 高度定制的非 Material 视觉,部分需自绘/自定义组件,主题系统覆盖不到全部。
