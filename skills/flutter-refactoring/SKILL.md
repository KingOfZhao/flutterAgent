---
id: flutter-refactoring
name: Flutter 安全重构 SOP (小步 + 测试护栏 + 常见手法)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [refactoring, refactor, maintenance, tech-debt, tests, safe-change, legacy]
applies_when: 不改变外部行为地改进代码结构(拆 widget / 上移状态 / 拆 god class / 偿还技术债)
stage_hints: [architecture, breakdown]
---

# Flutter 安全重构 SOP

重构的定义是:**在不改变外部可观察行为的前提下,改进内部结构。**
关键词是"不改变行为"——所以重构和改功能/修 bug 必须分开 PR。本 skill 给一套
"有护栏、可回退、小步前进"的做法,是 `flutter-engineering-workflow` 里独立于
1A 修复 / 1B 新增的第三类改动。语言层手法见 `dart-language-idioms`,验证见 `flutter-verification`。

## 0. 黄金前提:先有护栏,再动手

**没有测试覆盖的代码不要直接重构。** 顺序是:

1. 先为要改的行为补**特征测试(characterization test)**——把"现在的行为"钉死成测试(哪怕行为本身不完美)。
2. 跑绿,确认护栏到位。
3. 再开始重构;每一小步后重跑测试,绿了才继续。

> 没有测试的重构 = 在裸奔时做手术。补不了测试就先别重构,或缩小重构范围到可测的边界。

## 1. 小步原则

- 一次只做**一种**变换(改名 / 提取 / 内联 / 上移),不要一把梭。
- 每步都让代码**保持可编译、测试可跑绿**;commit 粒度小,便于二分定位与回退。
- 用 IDE 的自动重构(rename / extract method / extract widget)优先于手改——更安全、少手误。

## 2. 重构与其它改动分开

- 重构 PR 不夹带行为变更;行为变更 PR 不夹带大重构(见 `flutter-code-review` 红线)。
- commit 用 `refactor:` 前缀(Conventional Commits),让 reviewer 知道"这块不该有行为 diff"。
- 真要"边修边重构":先开重构 PR 合入,再在干净基线上开修复 PR。

## 3. Flutter 常见重构手法

- **Extract Widget**:臃肿 `build()` 里的子树提成独立 `StatelessWidget`(优先于 `_buildXxx()` 私有方法——独立 widget 有自己的 rebuild 边界,利于性能,见 `flutter-performance`)。
- **Lift State Up / Down**:状态放到"真正拥有它"的最小公共祖先;只读处下放,别让状态飘在过高层级(见 `flutter-engineer-mindset` 状态归属)。
- **拆 God Class / 巨型 Widget**:按职责拆分;UI 与业务逻辑分离到 presentation/domain(见 `architecture-design`)。
- **抽取 domain 层**:把混在 widget 里的业务规则提成纯 Dart 的 usecase/entity——纯函数可单测,是重构最大收益点。
- **替换魔法值**:散落的常量/字符串提成具名常量或枚举(配合 sealed,见 `dart-language-idioms`)。
- **统一状态管理**:把零散的 `setState` 收敛到仓库既有方案(见 `state-management`),但一次只迁一块。
- **消除重复(DRY 适度)**:重复 3 次以上再抽象;过早抽象比重复更难维护。

## 4. 收尾验证(等价于没改行为)

```bash
dart format .
dart analyze                 # 不应新增 error/warning
flutter test --coverage      # 行为测试应全绿且数量不减
```

- 重构后测试**全绿且断言未被削弱**,才算"行为没变"。
- 性能敏感处对比重构前后(profile / 包体积,见 `flutter-performance`)。
- 公共 API 形状若变了(哪怕只是改名),那已不是纯重构——按破坏性变更走文档/CHANGELOG(见 `flutter-documentation`)。

## 5. 大型/遗留代码的策略

- **童子军法则**:每次路过就让碰到的那一小块变好一点,而非攒一个"大重构季"。
- **绞杀者模式(Strangler Fig)**:新结构与旧结构并存,逐步把流量/调用迁过去,最后删旧的,而不是一次性推倒。
- **接缝(seam)**:在难测的旧代码里先引入依赖注入/接口接缝,让它变得可测,再重构。

## 反模式

- ❌ 无测试就大重构,改完"看着对"就提交。
- ❌ 把重构和功能/修复揉进一个 PR,reviewer 无法分辨行为是否变了。
- ❌ 一个巨型重构 PR 改几十个文件,无法二分、无法回退。
- ❌ 借重构之名顺手改行为/改 API 却不更新文档。
- ❌ 过早抽象:为"将来可能用到"造一堆接口,增加而非降低复杂度。

## 参考 / References

- Refactoring(Martin Fowler,定义与手法目录):<https://refactoring.com/>
- Strangler Fig 模式:<https://martinfowler.com/bliki/StranglerFigApplication.html>
- Flutter 性能最佳实践(Extract Widget / const 收益):<https://docs.flutter.dev/perf/best-practices>
- Flutter App 架构(分层指引):<https://docs.flutter.dev/app-architecture>
- Effective Dart(可读性/设计):<https://dart.dev/effective-dart/design>
- Conventional Commits(`refactor:`):<https://www.conventionalcommits.org/>
- 测试护栏写法见 `flutter-testing`;验证门禁见 `flutter-verification`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **行为不变是定义**:重构的成功判据是"测试全绿且断言没被削弱",不是"我觉得更干净"。
- **小步可回退**:每步保持绿、commit 够小,出问题能秒级二分定位。
- **先护栏后动刀**:没有测试覆盖的重构是赌博;补不了测试就缩小范围。

**诚实边界:**

- 改了公共 API/行为就不再是纯重构,需走破坏性变更流程。
- 重构降低的是"未来修改成本",短期不产出用户可见价值,要对预期诚实。
- 遗留系统的接缝引入本身有风险,需配套测试,不能盲目套模式。
