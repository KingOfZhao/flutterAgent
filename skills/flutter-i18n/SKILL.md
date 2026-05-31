---
id: flutter-i18n
name: Flutter 国际化 / 本地化规范
version: 1.0.0
platforms: [all]
tags: [i18n, l10n, intl, arb, localization]
applies_when: 目标用户覆盖 ≥ 2 个语言区域,或上架国际市场
stage_hints: [spec, architecture, breakdown]
---

# Flutter 国际化 / 本地化 (i18n / l10n) 规范

> 直接依据:
> * Flutter 官方:**[docs.flutter.dev/ui/accessibility-and-internationalization/internationalization](https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization)**
> * ARB 文件格式:<https://github.com/google/app-resource-bundle/wiki/ApplicationResourceBundleSpecification>
> * `intl` 包(由 Dart 团队维护):<https://pub.dev/packages/intl>
> * `flutter_localizations`:Flutter SDK 内置
> * `gen-l10n`:`flutter create` 默认生成路径
> * CLDR(数字 / 日期 / 复数规则数据源):<https://cldr.unicode.org>

## 1. 选型(官方推荐路线)

```
flutter_localizations + gen-l10n + ARB 文件
```

- **flutter_localizations**:提供 Material/Cupertino/Widgets 三套官方翻译(76 种语言)
- **gen-l10n**:Flutter 内置代码生成器,把 ARB 文件编译成强类型 `AppLocalizations`
- **ARB**:Google 官方的资源束格式,VS Code / Android Studio 都有原生支持
- **intl**:由 Dart 团队维护,提供 `Intl.message`、复数 / 性别 / 日期 / 数字格式化

> **不要**手写 Map 翻译表,**不要**用社区包 `easy_localization` 等(失去 Flutter 团队的官方 Cupertino/Material 资源)。

## 2. 工程目录

```
lib/
  l10n/
    app_en.arb           # 主语言(template-arb-file)
    app_zh.arb
    app_ja.arb
  generated/             # gen-l10n 输出(gitignored)
    app_localizations.dart
    app_localizations_en.dart
    app_localizations_zh.dart
l10n.yaml                # gen-l10n 配置
```

`l10n.yaml`(项目根目录):

```yaml
arb-dir: lib/l10n
template-arb-file: app_en.arb
output-localization-file: app_localizations.dart
output-class: AppLocalizations
nullable-getter: false
synthetic-package: false
output-dir: lib/generated
```

`pubspec.yaml`:

```yaml
dependencies:
  flutter_localizations:
    sdk: flutter
  intl: ^0.19.0
flutter:
  generate: true   # 关键!触发 gen-l10n
```

## 3. ARB 写法(必学)

```jsonc
// app_en.arb
{
  "@@locale": "en",
  "appTitle": "Todo",
  "@appTitle": { "description": "App title shown on launcher" },

  "greeting": "Hello, {name}!",
  "@greeting": {
    "placeholders": {
      "name": { "type": "String", "example": "Alice" }
    }
  },

  "itemCount": "{count, plural, =0{No items} =1{1 item} other{{count} items}}",
  "@itemCount": {
    "placeholders": { "count": { "type": "int", "format": "compact" } }
  },

  "lastSeen": "Last seen {date}",
  "@lastSeen": {
    "placeholders": { "date": { "type": "DateTime", "format": "yMMMd" } }
  }
}
```

复数语法是 ICU MessageFormat,**禁止**用「`if count == 0 ...`」自己写。
数据来自 CLDR — 不同语言的复数桶不一样(俄语有 4 个),交给 intl/CLDR。

## 4. App 入口接线

```dart
import 'package:flutter_localizations/flutter_localizations.dart';
import 'generated/app_localizations.dart';

MaterialApp(
  localizationsDelegates: AppLocalizations.localizationsDelegates,
  supportedLocales: AppLocalizations.supportedLocales,
  locale: const Locale('zh'),                  // 强制语言;留 null 走系统
  localeResolutionCallback: (locale, supported) {
    if (locale == null) return supported.first;
    for (final s in supported) {
      if (s.languageCode == locale.languageCode) return s;
    }
    return supported.first;
  },
)

// 在 widget 里:
Text(AppLocalizations.of(context)!.appTitle)
```

## 5. 工程红线

- **禁止**硬编码用户可见字符串(`Text('登录')`),用 `Text(loc.login)`
- **禁止**用 `+` 拼接翻译片段(`Text(loc.welcome + name)`),用占位符
- **禁止**对日期 / 数字使用 `toString()`,用 `DateFormat.yMMMd(locale).format(d)`、`NumberFormat.currency(locale, name: 'CNY').format(v)`
- **禁止**在 widget 里写 `Locale('zh')` 比较,用 `Localizations.localeOf(context)`
- **必须**为每个翻译 key 加 `@key.description` 注释,翻译员才知道上下文
- **必须**有占位符 `example` 字段,工具(Lokalise / Crowdin)能预览
- **必须**在 CI 跑 `flutter gen-l10n --untranslated-messages-file=untranslated.json`,缺翻译就 fail

## 6. RTL(从右到左)

如果目标语言含 ar / he / fa:
- `MaterialApp` 自动根据 locale 切 `TextDirection`
- 自写组件用 `EdgeInsetsDirectional.only(start:, end:)` 而非 `left/right`
- icons 不要假定方向(返回箭头要用 `Icons.arrow_back_ios_new` + `Directionality`)

测试:`tester.binding.window.localeTestValue = const Locale('ar')` 强制 RTL。

## 7. 字体

- CJK / Arabic 需要 fallback,默认 Roboto 不含中日韩字符
- 推荐 `google_fonts`(<https://pub.dev/packages/google_fonts>)或 bundling Noto Sans
- 桌面端 + Windows 老系统注意:Roboto + Noto Sans CJK SC + Noto Color Emoji 至少 3 条 fontFamilyFallback

## 8. 必须产出

每个 PRD 必须给出:
1. 目标语言矩阵(语言 × 区域,如 zh_CN / zh_TW / en_US / ja_JP)
2. 每种语言对应的 ARB 文件路径与翻译承包方
3. 文本占位符 + 复数规则的清单(每个动态文案)
4. 日期 / 数字 / 货币的格式策略(用 intl 的哪个 format)
5. RTL 兼容性结论(支持 / 不支持 / 暂不支持但布局已预留)
6. CI 检查项:`flutter gen-l10n` 必须无 warning;缺翻译数 = 0

## 9. 翻译协作工具

| 工具 | ARB 支持 | 链接 |
|---|---|---|
| **Lokalise** | 原生 | <https://lokalise.com> |
| **Crowdin** | 原生 | <https://crowdin.com> |
| **POEditor** | 原生 | <https://poeditor.com> |
| VS Code 扩展 | `Flutter Intl` (by Localizely) | marketplace 内搜 `localizely.flutter-intl` |
