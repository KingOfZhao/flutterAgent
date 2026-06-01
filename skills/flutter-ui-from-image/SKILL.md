---
id: flutter-ui-from-image
name: 从图片/设计稿还原 UI (取色 / 字号等比换算 / 渐变方向 / 关键信息提取)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [ui, design, screenshot, color, gradient, typography, responsive, scaling, design-to-code, figma]
applies_when: 输入是一张 UI 图片/截图/设计稿,需要识别其视觉规格并还原成 Flutter 实现
stage_hints: [spec, breakdown]
---

# 从图片/设计稿还原 UI

输入一张界面图(截图、设计稿、参考图),输出**结构化的 UI 规格**——颜色、字号、间距、
渐变、布局、组件、状态——让实现阶段能"照着规格写 Flutter",而不是凭感觉描红。
本 skill 管"**怎么读图、怎么换算**";把规格落成工程化主题见 `flutter-design-tokens-theming`,
动画/转场见 `flutter-animation`,自适应布局见 `flutter-cross-platform`。

## 0. 先定基准(一切换算的前提)

读图前先确定三个基准,否则数值无意义:

- **设计稿基准宽度 `designWidth`**:常见 375 / 390(iPhone)、360(Android)、1440(Web)。图里所有像素值都是相对这个宽度的。
- **目标设备逻辑宽度**:运行时取 `MediaQuery.sizeOf(context).width`(逻辑像素 dp,**不是物理像素**)。
- **缩放系数 `scale = targetWidth / designWidth`**:所有尺寸/间距/字号按它等比换算的基础。

> 关键认知:Flutter 用**逻辑像素(dp)**布局,设计稿的 px 在 @1x 下约等于 dp;高分屏的物理像素由 `devicePixelRatio` 处理,**不要**手动乘 dpr 去布局。

## 1. 颜色采集

1. **取色**:对目标区域取色 → 得到 `#RRGGBB` + alpha。Flutter 写法 `Color(0xFFRRGGBB)`(前两位是 alpha,`FF`=不透明);带透明度用 `Color(0x80RRGGBB)` 或 `color.withValues(alpha: 0.5)`(新 API,替代废弃的 `withOpacity`)。
2. **分类落位**(对应 Material 3 `ColorScheme`,见 `flutter-design-tokens-theming`):
   - 主色 / 品牌色 → `primary`;强调/次要 → `secondary` / `tertiary`。
   - 背景/卡片 → `surface` / `surfaceContainer*`;文字 → `onSurface` / `onPrimary`(注意对比度,见 `flutter-accessibility`)。
   - 语义色:成功/警告/错误 → 自定义扩展(`ThemeExtension`)或 `error`。
3. **区分实色 vs 渐变**:同一区域若有明显明暗过渡 → 是渐变(见 §3),别只取一个色。
4. **对比度校验**:正文文字与背景对比度应达 WCAG AA(正常文字 ≥ 4.5:1),取色后验一遍(见 `flutter-accessibility`)。

## 2. 字号 / 间距「等比换算」

设计稿上量到的是 `designValue`(px),换算到当前设备:

```
scale       = targetWidth / designWidth          // 例 390/375 ≈ 1.04
scaledValue = designValue * scale
```

落地三种方式(按需选):

- **简单等比**:写个 helper `double sw(double v) => v * MediaQuery.sizeOf(context).width / 375;`,字号 `fontSize: sw(16)`、间距 `EdgeInsets.all(sw(12))`。
- **`LayoutBuilder`**:在受约束容器内按 `constraints.maxWidth` 等比(局部组件更准)。
- **成熟方案**:`flutter_screenutil` 等(`.sp` / `.w` / `.h`),团队统一一种,别混用(选包见 `flutter-dependency-maintenance`)。

注意事项:

- **字号不要无脑全等比**:正文字号要尊重系统**文字缩放**(`MediaQuery.textScalerOf`,无障碍放大),给上下限 `clamp`,别让等比把大屏字撑爆/小屏挤没(见 `flutter-accessibility`)。
- **高度尽量别等比**:宽度等比 + 高度交给内容/`Flexible`/`AspectRatio`,纯按高度比例缩放在不同长宽比设备上易变形。
- **断点优先于无限等比**:平板/桌面/Web 用响应式断点换布局(见 `flutter-cross-platform`),而不是把手机布局拉伸 3 倍。

## 3. 渐变方向识别

判断渐变**类型 + 方向**,映射到 Flutter:

- **线性 `LinearGradient`**:看明暗过渡的轴向 → 设 `begin`/`end`(`Alignment`)。常见对照:

  | 视觉方向 | begin → end |
  |---|---|
  | 从上到下 | `topCenter` → `bottomCenter` |
  | 从左到右 | `centerLeft` → `centerRight` |
  | 左上→右下(≈45°) | `topLeft` → `bottomRight` |
  | 右上→左下 | `topRight` → `bottomLeft` |

  任意角度:用 `Alignment(x, y)`(x,y ∈ [-1,1])或 `GradientRotation(radians)` 转 `transform`。
- **径向 `RadialGradient`**:从一点向外发散(光晕/球形)→ 设 `center` / `radius`。
- **扫描 `SweepGradient`**:绕中心角度扫(环形进度/色盘)→ 设 `startAngle` / `endAngle`。
- **色标 `stops`**:多于两色或过渡不均匀时,按比例给 `colors` + `stops`(0.0–1.0)。
- 落地:`Container(decoration: BoxDecoration(gradient: ...))`;文字渐变用 `ShaderMask`。

## 4. 当前页面「关键信息」提取清单

读图产出一份结构化清单(交给阶段 1B 实现):

1. **布局结构**:从外到内的树——Scaffold? AppBar? 列表/网格? 卡片? 是否可滚动? 用 `Column/Row/Stack/Wrap/ListView/GridView` 哪个。
2. **组件清单**:按钮(填充/描边/文本)、输入框、卡片、头像、徽标、标签页、底部导航等 → 尽量映射到 Material/Cupertino 既有组件。
3. **间距与圆角**:外边距/内边距/元素间距(量取并等比)、`borderRadius`、阴影(`elevation` / `BoxShadow` 的 blur/offset/色)。
4. **排版**:字体族、字重(w400/500/700)、字号、行高(`height`)、字间距(`letterSpacing`)、对齐。
5. **图标与图片**:图标尽量用 `Icons` / 矢量;占位图与圆角裁剪(`ClipRRect`)。
6. **状态**:这张图是哪种状态?要补齐**空 / 加载 / 错误 / 正常**四态(见 `flutter-error-handling`)。
7. **响应式假设**:这是手机/平板/桌面哪一档?需要哪些断点(见 `flutter-cross-platform`)。
8. **不确定项**:列出图里看不准的(精确色值、隐藏交互、滚动行为)——标注"待与设计/源文件确认",不要瞎猜填死。

## 反模式

- ❌ 不定基准宽度就直接写死 px,换设备全错位。
- ❌ 把宽高字号**全部**无脑等比,导致大屏字巨大、不同长宽比变形。
- ❌ 等比字号无视系统文字缩放,踩无障碍红线。
- ❌ 渐变只取一个中间色当实色,丢掉方向与层次。
- ❌ 用物理像素 × devicePixelRatio 去布局(Flutter 用逻辑像素)。
- ❌ 把从有损截图取的色值当成"精确设计值"写进规范,不标注近似。
- ❌ 只还原"正常态"一张图,漏掉空/加载/错误态。

## 参考 / References

- `MediaQuery` / 逻辑像素:<https://api.flutter.dev/flutter/widgets/MediaQuery-class.html>
- 自适应与响应式设计:<https://docs.flutter.dev/ui/adaptive-responsive>
- `LayoutBuilder`:<https://api.flutter.dev/flutter/widgets/LayoutBuilder-class.html>
- `Color` 类(含 `withValues`):<https://api.flutter.dev/flutter/dart-ui/Color-class.html>
- `LinearGradient` / `RadialGradient` / `SweepGradient`:<https://api.flutter.dev/flutter/painting/Gradient-class.html>
- `BoxDecoration`(渐变/阴影/圆角):<https://api.flutter.dev/flutter/painting/BoxDecoration-class.html>
- `ShaderMask`(文字/图形渐变):<https://api.flutter.dev/flutter/widgets/ShaderMask-class.html>
- 文字缩放 `TextScaler`:<https://api.flutter.dev/flutter/painting/TextScaler-class.html>
- 颜色对比度(WCAG):<https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html>
- `flutter_screenutil`(可选等比方案):<https://pub.dev/packages/flutter_screenutil>
- 主题落地见 `flutter-design-tokens-theming`;响应式见 `flutter-cross-platform`;对比度见 `flutter-accessibility`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先定基准再谈数值**:没有 designWidth / 逻辑像素这把尺,任何 px 都是无意义的。
- **等比是手段不是教条**:宽度等比 + 内容驱动高度 + 断点换布局,比"全等比拉伸"更对。
- **图是某一状态的快照**:还原 UI 要补齐空/载入/错误态,而不是只描红正常态。
- **逻辑像素思维**:用 dp 布局,把 devicePixelRatio 交给框架。

**诚实边界:**

- 从**有损截图/缩放图**取色、量尺寸都是**近似值**;精确值应以设计源文件(Figma/Sketch 的标注/导出 token)为准。
- 像素级取色需要具备视觉能力的模型或取色器配合;本 skill 提供的是**识别方法与换算规则**,不替代实际取色工具。
- 交互、动效、滚动行为、隐藏状态无法从单张静态图完全推断,需向设计/产品确认。
- 字体若非系统字体,需确认授权与资源接入(见 `flutter-build-and-release` 资源打包)。
