---
id: flutter-accessibility
name: Flutter 可访问性 (a11y) 规范
version: 1.0.0
platforms: [all]
tags: [a11y, accessibility, semantics, wcag]
applies_when: 任何面向终端用户的 UI 都必须满足 a11y 验收
stage_hints: [spec, acceptance]
---

# Flutter 可访问性 (a11y) 规范

> 直接依据:
> * Flutter 官方:**[docs.flutter.dev/ui/accessibility-and-internationalization/accessibility](https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility)**
> * W3C **WCAG 2.1** (Level AA):<https://www.w3.org/TR/WCAG21/>
> * Apple HIG Accessibility:<https://developer.apple.com/design/human-interface-guidelines/accessibility>
> * Android Accessibility:<https://developer.android.com/guide/topics/ui/accessibility/apps>
> * Material 3 Accessibility:<https://m3.material.io/foundations/accessible-design/overview>

## 1. 强制基线(WCAG 2.1 AA 子集)

| 项 | 标准 | Flutter 落地 |
|---|---|---|
| **对比度** | 普通文本 ≥ 4.5:1,大字号 ≥ 3:1 | 用 `ColorScheme` 暗/亮主题统一,设计验收用 [accessible-colors.com](https://accessible-colors.com) 检查 |
| **触摸目标** | ≥ 48×48 dp(Material) / 44×44 pt(iOS HIG) | 自定义 IconButton 必须包 `SizedBox` 撑到 48 |
| **焦点顺序** | 可纯键盘遍历,顺序合理 | `FocusTraversalGroup` + `OrderedTraversalPolicy` |
| **可缩放字体** | 支持系统字体 1.3× 不破布局 | `MediaQuery.textScalerOf(context)` (Flutter 3.16+,旧版用 textScaleFactor) |
| **替代文本** | 所有非装饰图像有 `semanticLabel` | Image / Icon 必填 `semanticLabel`,装饰图标显式 `excludeFromSemantics: true` |
| **状态可读** | TalkBack / VoiceOver 能播报状态变化 | 自定义控件用 `Semantics(value:..., onTap:..., ...)` |
| **避免仅靠颜色传达信息** | 红/绿状态必须叠加图标或文字 | 不要只用 `Colors.red` 表示错误 |

## 2. Flutter Semantics 体系

Flutter 通过 **Semantics tree**(独立于 widget tree)与平台 a11y API 对接:
- Android:TalkBack(基于 AccessibilityNodeInfo)
- iOS / macOS:VoiceOver(基于 UIAccessibility)
- Linux/Windows:屏幕阅读器(GTK ATK / UIA)

文档:<https://api.flutter.dev/flutter/semantics/SemanticsNode-class.html>

实务用法:

```dart
// 自定义可点击区域必须暴露语义
Semantics(
  label: '删除待办「买牛奶」',
  button: true,
  enabled: !disabled,
  onTap: () => controller.delete(item.id),
  child: InkWell(onTap: ..., child: const Icon(Icons.delete)),
)

// 装饰性图片排除在语义树外
Image.asset('decor.png', excludeFromSemantics: true);

// 列表项 hint
Semantics(
  label: item.title,
  hint: '双击打开详情',
  child: ListTile(...),
)
```

## 3. 测试方法(必须在 acceptance 里写)

| 工具 | 用途 | 文档 |
|---|---|---|
| `meets_tap_target_size`, `meets_text_contrast` | widget 测试断言 | [flutter.dev a11y/AccessibilityGuideline](https://api.flutter.dev/flutter/flutter_test/AccessibilityGuideline-class.html) |
| `SemanticsTester` | 验证 semantics tree | [flutter_test/SemanticsTester](https://api.flutter.dev/flutter/flutter_test/SemanticsTester-class.html) |
| **Accessibility Scanner**(Android) | 真机扫描 | <https://play.google.com/store/apps/details?id=com.google.android.apps.accessibility.auditor> |
| **VoiceOver**(iOS / macOS) | 真机听感 | 设置 → 辅助功能 |
| `flutter test --plain-name accessibility` | CI 自动跑 | — |

最小用例:

```dart
testWidgets('LoginPage meets a11y guidelines', (tester) async {
  final handle = tester.ensureSemantics();
  await tester.pumpWidget(const MaterialApp(home: LoginPage()));
  await expectLater(tester, meetsGuideline(textContrastGuideline));
  await expectLater(tester, meetsGuideline(androidTapTargetGuideline));
  await expectLater(tester, meetsGuideline(iOSTapTargetGuideline));
  await expectLater(tester, meetsGuideline(labeledTapTargetGuideline));
  handle.dispose();
});
```

> 这 4 条 guideline 是 `flutter_test` 内置的官方断言;失败必须修复或显式声明豁免理由。

## 4. 必须产出

每个 feature 的 acceptance 段落必须包含:
1. **触摸目标尺寸清单**:所有交互元素的最小尺寸是否 ≥ 48 dp。
2. **键盘可达性**:Tab/Shift+Tab 能不能闭环,Enter/Escape 行为是否符合预期。
3. **屏幕阅读器脚本**:每个核心页面用 TalkBack 朗读应念出什么内容(写成台词)。
4. **字体放大用例**:1.3× 系统字号下页面是否出现截断 / 重叠。
5. **对比度报告**:文字/背景颜色对的对比度数值(可用工具计算)。

## 5. Flutter 3.44 无障碍新能力

### 5.1 prefers-reduced-motion 自动适配

Flutter 3.44 引擎自动响应系统"减弱动态效果"设置:
- **iOS / macOS / Windows**: 用户开启"减弱动态效果"后,Flutter Web 和桌面端自动禁用/简化非必要动效
- **Web 端**: 自动适配 CSS `prefers-reduced-motion` 媒体查询
- 无需在 Dart 代码中写任何判断逻辑,框架自动降级

通过 `AccessibilityFeatures` 可编程检测:

```dart
final features = MediaQuery.accessibilityFeaturesOf(context);
if (features.reduceMotion) {
  // 使用简化动画或直接跳过
}
```

### 5.2 Semantics Value 百分比支持

进度条等组件现在支持百分比字符串作为语义值:
- 之前屏幕阅读器播报:"零点五"、"零点七五"
- 现在支持:"50%"、"75%",听觉体验更自然

```dart
Semantics(
  value: '${(progress * 100).round()}%',  // "75%"
  child: LinearProgressIndicator(value: progress),
)
```

### 5.3 Slider 语义节点精度

Slider 的 Semantics Node 重构,精准映射屏幕上的实际物理大小和位置,对依赖触摸探索或外接辅助设备的用户提供更精确的盲操体验。

## 6. 红线

- 不要为了好看用 `Opacity` 0.5 灰显文字(对比度会跌破 4.5:1)
- 不要把可点击区域做成 < 48 dp
- 不要用纯色 emoji / icon 传达状态而不附文字
- 不要 `Semantics(excludeSemantics: true)` 盖住整个交互元素
- 不要忘记表单错误的 `Semantics(liveRegion: true)`,否则屏幕阅读器不会播报
- 不要忽略 `reduceMotion` 标志——对前庭功能障碍、癫痫等用户群体有直接影响

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **无障碍是语义不是外观**:读屏器消费的是 Semantics 树,不是像素。
- **基线是红线**:对比度 / 触达尺寸 / 可聚焦是底线,不是锦上添花。
- **用户偏好是输入信号**:尊重 reduceMotion / 大字体 / 高对比等系统设置。

**诚实边界:**

- 自动检查只覆盖一部分,真实可用性需真人 + 读屏器(TalkBack/VoiceOver)实测。
- 各平台读屏器行为有差异,以真机为准。
