---
id: flutter-design-to-code-playbook
name: 设计稿 → Flutter 代码 端到端 playbook
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [playbook, design-to-code, workflow, ui, theming, end-to-end, figma, screenshot]
applies_when: 拿到一张/一组设计稿或截图,要端到端落成可运行、可验收的 Flutter UI
stage_hints: [spec, breakdown, implementation, acceptance]
see_also: [flutter-ui-from-image, flutter-figma-mcp, flutter-design-tokens-theming, flutter-ui-component-recipes]
---

# 设计稿 → Flutter 代码 端到端 playbook

把零散的"读图 / 取色 / 搭主题 / 写 widget / 自测"串成**一条可照着走的流水线**。
每一步都有**输入 → 动作 → 产物 → 验收**,产物喂给下一步,最后交付可运行、可回归的 UI。
本 playbook 是编排者;具体方法分别在 `flutter-ui-from-image`、`flutter-design-tokens-theming`、
`flutter-feature-development`、`flutter-verification` 里,这里负责把它们按顺序接好。

## 阶段总览

```
S0 对齐    → S1 读图成规格 → S2 建主题 token → S3 搭骨架 → S4 实现组件
          → S5 等比/响应式 → S6 状态四态 → S7 自测验收 → S8 与设计比对交付
```

## S0. 对齐与基准(别跳过)

- 输入:设计稿/截图 + 目标平台(手机/平板/桌面/Web)+ 是否有设计源文件(Figma/Sketch)。
- 动作:确认设计稿**基准宽度**(375/390/360/1440)、是否要亮暗双主题、字体来源与授权。**有 Figma 源文件 → S1 改走 `flutter-figma-mcp` 精确取数,不目测**。
- 产物:一页"基准与约束"备忘。
- 验收:基准宽度、目标平台、主题模式三者明确。
- 出处:`flutter-ui-from-image` §0。

## S1. 读图成结构化规格

- 输入:图 + S0 基准。
- 动作:按 `flutter-ui-from-image` 提取——取色、字号/间距等比换算、渐变方向、关键信息清单(布局树/组件/圆角阴影/排版/状态/响应式档位/不确定项)。
- 产物:`ui-spec.md`(结构化规格 + 不确定项待确认列表)。
- 验收:每个可见元素都有色/字/间距记录;不确定项已标注,不瞎填。

## S2. 建主题 token

- 输入:S1 的色板与排版。
- 动作:按 `flutter-design-tokens-theming` 建 `theme/`——`ColorScheme`(fromSeed 或精确指定)、`TextTheme`、`ThemeExtension`(间距/圆角/阴影/语义色)、亮暗双主题。
- 产物:`theme/` 目录 + `buildTheme()`,接到 `MaterialApp.theme/darkTheme`。
- 验收:无硬编码色值/字号;亮暗都能跑;正文对比度达 WCAG AA(见 `flutter-accessibility`)。

## S3. 搭骨架(布局树先行)

- 输入:S1 布局树。
- 动作:先用占位(`Container`/`Placeholder` + 主题色)把布局结构搭出来(Scaffold/AppBar/列表/卡片/Stack),只验证**结构与间距**,不填细节。
- 产物:可运行的"灰模"页面。
- 验收:整体布局、留白、对齐与设计稿一致;尚未涉及像素细节。

## S4. 实现组件(照表找 widget)

- 输入:S1 组件清单。
- 动作:逐个把占位换成真实组件,优先用 Material/Cupertino 既有组件;常见 UI → widget 的映射与代码骨架查 `flutter-ui-component-recipes`;widget 只消费主题 token。
- 产物:成型的 UI(正常态)。
- 验收:组件外观/交互与设计稿一致;无内联硬编码样式。

## S5. 等比与响应式

- 输入:S1 等比换算结果 + 目标档位。
- 动作:套用等比 helper / `LayoutBuilder`(`flutter-ui-from-image` §2);平板/桌面/Web 用断点换布局(`flutter-cross-platform`),而非无限拉伸;字号 `clamp` 并尊重系统文字缩放。
- 产物:多尺寸下都不溢出/不变形的 UI。
- 验收:小屏不挤、大屏不糊;系统放大字体仍可用。

## S6. 补齐状态四态

- 输入:页面数据依赖。
- 动作:补 **空 / 加载 / 错误 / 正常** 四态(`flutter-error-handling`);骨架屏/重试入口。
- 产物:四态都有 UI。
- 验收:断网/空数据/异常下不白屏不崩。

## S7. 自测与验收门禁

- 动作:跑 `flutter-verification` 门禁——`format → analyze → test → build`;关键组件加 widget test / golden test(像素回归)。
- 产物:全绿的本地门禁 + golden 基线。
- 验收:CI 关卡通过(见 `flutter-ci-cd`);golden 测试锁住视觉。

## S8. 与设计比对 + 交付

- 动作:把成品与设计稿叠图比对(间距/色/字);记录"有意偏离"的原因;按 `flutter-documentation` 更新 README/CHANGELOG。
- 产物:PR + 比对说明 + 文档。
- 验收:差异都被解释或修正;评审通过(`flutter-code-review`)。

## 反模式

- ❌ 跳过 S0/S1 直接对着图描红,边写边猜色值字号。
- ❌ 不建主题就开写,颜色字号散落各处(S2 缺失)。
- ❌ 先死磕单个组件像素,再发现整体布局错(应先 S3 灰模)。
- ❌ 只交付正常态,漏空/加载/错误(S6 缺失)。
- ❌ 没有 golden/widget test,改样式无回归保护(S7 缺失)。
- ❌ 把"看不准的细节"直接拍脑袋写死,不回到设计源确认。

## 参考 / References

- 读图方法:见 `flutter-ui-from-image`(§ REFERENCES)。
- 主题落地:见 `flutter-design-tokens-theming`(§ REFERENCES)。
- 实现 SOP:见 `flutter-feature-development`;自测门禁:见 `flutter-verification`。
- Golden 测试:<https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html>
- Widget 测试:<https://docs.flutter.dev/cookbook/testing/widget/introduction>
- 自适应/响应式:<https://docs.flutter.dev/ui/adaptive-responsive>
- 总编排见 `flutter-engineering-workflow`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **由粗到细**:基准 → 规格 → 主题 → 灰模 → 组件 → 细节,任何一步都建立在上一步产物上,别跳级。
- **结构先于像素**:先把布局/留白搭对(灰模),再抠颜色字号,返工成本最低。
- **token 是地基**:颜色字号先进主题再被消费,UI 才好改、亮暗才一致。
- **状态四态是默认**:一张图只是正常态的快照,交付要补齐空/载入/错误。

**诚实边界:**

- 单张静态图无法推断交互、动效、滚动、隐藏状态——这些需设计/产品确认或参考源文件。
- 像素级 100% 还原通常不必要也不经济;以"语义一致 + 关键间距/色对齐"为目标,有意偏离要记录。
- 本 playbook 是流程编排,不含具体框架实现细节;各步深度以被引用 skill + 当时官方文档为准。
