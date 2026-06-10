# 主题与设计系统工程化(向量库优质语料·轮20)

> 反思缺口:UI 语料覆盖了动效与布局,但"颜色/字体/间距如何不散落在
> 两百个文件里"——设计系统的工程化方法零覆盖。来源见 REFERENCES §29。

## 1. ThemeData 的机制与正确用法

- `Theme.of(context)` 是 InheritedWidget 查找:主题变更只重建依赖了
  主题的 widget(flutter-rendering-pipeline §1 的传播机制),暗色切换
  代价可控的原因即此;
- **硬编码 `Color(0xFF...)` 散落在 build 里是设计系统的破窗**:所有
  颜色取自 `colorScheme`、字体取自 `textTheme`、组件形态用各组件的
  `XxxThemeData`(ButtonTheme/CardTheme…)集中声明——改一处全局生效,
  也是暗色模式"自动就对"的前提;
- Material 3:`ColorScheme.fromSeed` 从种子色生成全套和谐色板,
  `useMaterial3` 默认开启(3.16+);自定义品牌色优先覆盖 scheme 的
  语义槽位(primary/secondary/surface)而非绕过 scheme 自建颜色常量。

## 2. design token 的落地形态:ThemeExtension

- scheme 槽位不够时(品牌渐变/特殊语义色"上涨红/下跌绿"),标准做法
  是 `ThemeExtension<T>`:自定义 token 集挂进 ThemeData,取用走
  `Theme.of(context).extension<T>()`,且自带 `lerp` 支持主题切换动画;
- 这是"设计 token(Figma 变量)→ 代码"的对接点:token 命名按**语义**
  (surfaceWarning)而非按值(lightYellow),设计改值不改代码引用;
- 反模式:为绕过主题而写 `AppColors.xxx` 静态常量类——失去暗色模式
  与动态主题能力,等于把 token 焊死。

## 3. 暗色模式与动态颜色

- `MaterialApp(theme:, darkTheme:, themeMode:)` 三件套,themeMode 由
  用户设置驱动(默认 system);**两套主题都从同一逻辑生成**(同一
  seed 不同 brightness),手维护两套常量必然漂移;
- 验收点:暗色下的图片/插画(白底图刺眼)、elevation 表达(暗色用
  surface tint 而非阴影)、对比度复检(flutter-i18n-accessibility §4
  的断言在两套主题下各跑一遍);
- Android 12+ 动态取色(Material You)用 dynamic_color 包,取不到时
  回退品牌 seed。

## 4. 字体与密度

- 自定义字体进 pubspec 声明,中文字体体积大,按需子集化或用系统字体
  栈(包体积,flutter-release-engineering §1);
- `textScaler`(用户系统字号)必须尊重:固定容器高度 + 大字号 = 溢出
  条纹,容器给 min 约束而非固定值(flutter-i18n-accessibility §3);
- 桌面/移动密度差异用 `VisualDensity.adaptivePlatformDensity`
  (flutter-web-desktop-adaptive §2 的配套)。

## 5. 与本仓库其他语料的衔接

- InheritedWidget 重建传播 ← 轮11 §1;对比度/字号断言 ← flutter-i18n-accessibility;
- 字体体积 ← flutter-release-engineering §1;平台密度 ← flutter-web-desktop-adaptive。
