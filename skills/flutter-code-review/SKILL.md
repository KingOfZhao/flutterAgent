---
id: flutter-code-review
name: Flutter 代码评审 SOP (看什么 / 红线 / 怎么给反馈)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [code-review, review, pr, quality, checklist, feedback, maintenance]
applies_when: 评审一个 Flutter/Dart PR,或自查自己的改动是否可合入
stage_hints: [acceptance]
---

# Flutter 代码评审 SOP

评审不是"找茬",而是用一套**固定视角**把改动过一遍,既挡住缺陷,也把
知识扩散到团队。本 skill 给"看什么 / 哪些是红线 / 怎么表达反馈",是
`flutter-engineering-workflow` 阶段 4 交付前的关卡。自测门禁(format/analyze/test)
见 `flutter-verification`——评审是在门禁绿之后才上手看人能看的东西。

## 0. 评审前提(没满足就先打回,别逐行读)

- CI/自测门禁是绿的(`format` / `analyze` / `test` 见 `flutter-verification`)。
- PR 描述说清了 **为什么改**(不只是"改了什么")、影响面、验证方式。
- diff 是**单一主题**:一个 PR 不混"修 bug + 大重构 + 新功能"。混了就请拆。

## 1. 评审顺序(从大到小,别一上来抠括号)

1. **意图**:这个改动解决的问题对吗?是不是在对的层(presentation/domain/data,见 `architecture-design`)解决?
2. **设计**:有没有更简单的实现?是否过度设计 / 引入不必要抽象?公共 API 形状合理吗?
3. **正确性**:边界条件、空/加载/错误三态、并发与异步竞态、平台差异。
4. **测试**:改了行为有没有对应测试?修 bug 有没有回归测试(先红后绿)?见 `flutter-testing`。
5. **可维护性**:命名、可读性、是否地道(见 `dart-language-idioms`)、注释是否解释"为什么"。
6. **细节**:格式/风格——基本交给 `dart format`/`analyze`,人不该花时间在这。

## 2. Flutter/Dart 专属检查清单

- **状态与 rebuild**:`build()` 里有没有干重活/建 controller?`const` 用足了吗?(见 `flutter-performance`)
- **资源生命周期**:凡 `create` 必 `dispose`——controller / stream 订阅 / animation(见 `flutter-resource-lifecycle`)。
- **状态管理一致性**:是否遵循仓库既有方案(Riverpod/BLoC),没有混用两套(见 `state-management`)。
- **空安全**:有没有滥用 `!` / `late` 绕空检查(见 `dart-language-idioms`)。
- **错误处理**:失败路径有没有被吞掉?用户可见错误有没有兜底 UI(见 `flutter-error-handling`)。
- **依赖**:新引入的包 pub.dev 可查、活跃维护、协议合规吗?(见 `architecture-design` 反幻觉约定)
- **平台/适配**:用了 `dart:io` 的代码在 web 会炸吗?响应式断点处理了吗?(见 `flutter-cross-platform`)
- **i18n / a11y**:用户可见文案有没有硬编码?交互控件有没有语义标签?(见 `flutter-i18n` / `flutter-accessibility`)
- **安全**:有没有把 token / 密钥写进代码或日志?(见 `flutter-security`)

## 3. 红线(出现就必须改,不是"建议")

- ❌ 代码里出现明文密钥 / token / 凭证,或把它们打进日志。
- ❌ 静默吞异常(`catch (_) {}` 什么都不做),让失败无声无息。
- ❌ 无回归测试地"修好了"一个 bug。
- ❌ 引入 pub.dev 查不到 / 已 `discontinued` / 版本超前的包。
- ❌ 破坏性变更(改公共 API / 行为)却不更新 CHANGELOG / 迁移说明(见 `flutter-documentation`)。
- ❌ 把验证甩给 CI:本地没跑 analyze/test 就提审。

## 4. 反馈的表达方式(对事不对人)

- 用**问题**而非命令:"这里如果列表为空会怎样?"优于"你这写错了"。
- 区分**阻断性**与**可选项**:给可选建议加前缀 `nit:`(吹毛求疵)/ `suggestion:`,让作者分清必须改还是参考。
- 解释**为什么**,最好附出处或例子,让评审成为知识传递而非权力展示。
- 表扬好改动——正反馈和挑错一样重要。
- 给出明确的下一步:approve / request changes / comment,别让作者猜。

## 5. 作者侧自查(提审前先自己当一次评审)

- 自己先把整个 diff 读一遍,把"待会儿会被问"的地方在 PR 描述里先说清。
- 删掉调试代码 / `print` / 注释掉的旧代码 / TODO 无主。
- 确认 diff 最小、主题单一、文档跟着改动走。

## 反模式

- ❌ 只看风格不看设计(给一堆格式 nit,放过架构问题)。
- ❌ "整体看着没问题"就 approve 大改动,不真正读关键路径。
- ❌ 用评审夹带个人偏好当硬性要求(团队约定 > 个人喜好)。
- ❌ 一次几千行的巨型 PR——评审质量必然下降,应推动拆分。

## 参考 / References

- Google Engineering Practices · Code Review:<https://google.github.io/eng-practices/review/>
- 评审者指南 What to look for:<https://google.github.io/eng-practices/review/reviewer/looking-for.html>
- CL 作者指南:<https://google.github.io/eng-practices/review/developer/>
- Effective Dart(可读性/设计依据):<https://dart.dev/effective-dart>
- Conventional Commits(提交主题单一):<https://www.conventionalcommits.org/>
- 各专项检查的出处见对应 skill 与 `REFERENCES.md`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **从意图到细节**:先确认"该不该这么改",再看"改得对不对",最后才是风格。
- **评审是知识扩散**:每条评论都该让作者(和未来读者)学到点什么。
- **红线零容忍,其余可商量**:把"必须改"和"建议"分清,降低摩擦。

**诚实边界:**

- 评审挡不住所有 bug;它是质量网的一层,不替代测试与真机验证。
- 工具能查的(格式/部分 lint)就别用人评审,省给真正需要判断的地方。
- 评审标准随团队语境变化,这里给的是通用骨架,不是教条。
