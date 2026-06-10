# Flutter 国际化与无障碍(向量库优质语料·轮5)

> 反思缺口:前九篇全部面向"功能做出来",可用性合规维度(多语言、无障碍)零覆盖,
> 而这两项是上架与企业采购的硬性检查项。来源见 REFERENCES §26。

## 1. 国际化(i18n)

- 官方路径:`flutter_localizations` + `intl`,ARB 文件 + `flutter gen-l10n`
  生成类型安全的 `AppLocalizations`——字符串硬编码进 widget 的项目,补做 i18n
  的成本随页面数线性增长,值得从第一天就走 ARB。
- **复数与性别用 ICU 语法**(ARB 内 `{count, plural, ...}`),不要在 Dart 里
  `count == 1 ? ... : ...` 拼——俄语/阿拉伯语等有 3-6 种复数形态,拼接必错。
- **日期/数字/货币**经 `intl` 的 `DateFormat`/`NumberFormat` 按 locale 格式化,
  不要手写模板;注意格式化依赖 locale 数据初始化。
- RTL(阿拉伯语/希伯来语):用方向化属性 `EdgeInsetsDirectional` / `start/end`
  对齐,而非 `left/right`,布局可免改翻转;图标中有方向语义的(返回箭头)需镜像。
- 文案长度预算:德语/俄语比英文长 30%+,固定宽度按钮与单行 Text 是溢出高发点,
  伪本地化(加长字符串)过一遍 UI 是廉价的回归手段。

## 2. 无障碍(a11y)

- Flutter 自带语义树(SemanticsNode),系统读屏(TalkBack/VoiceOver)消费它——
  大多数 Material 组件自带语义,**自绘/手势容器是语义空洞重灾区**:用 `Semantics`
  widget 补 label/button 语义,纯装饰元素用 `ExcludeSemantics` 移出。
- 官方基线清单:交互目标 ≥48x48dp、文本对比度 ≥4.5:1、支持系统字体缩放
  (用 `MediaQuery.textScalerOf` 响应而非锁死 textScaleFactor=1——锁缩放
  等于把低视力用户挡在外面)。
- 检验方式:真机开读屏走金路径;widget 测试中可用
  `meetsGuideline(textContrastGuideline / androidTapTargetGuideline)` 把
  无障碍基线变成 CI 断言,这是 a11y 不回退的唯一可持续方式。

## 3. 与本仓库其他语料的衔接

- a11y guideline 断言挂进 widget 测试层(flutter-testing-strategy §1);
- 字体缩放下的溢出本质是布局性能/约束问题的近亲(flutter-performance §2);
- locale 切换状态属于 app state(flutter-state-management §1)。
