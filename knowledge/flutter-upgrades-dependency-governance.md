# 升级与依赖治理(向量库优质语料·轮22)

> 反思缺口:CI/CD 语料钉死了版本("SDK 钉死/lockfile 入库"),但"钉死
> 之后如何安全地动"——升级节奏/破坏性变更应对/依赖健康度,零覆盖。
> 来源见 REFERENCES §29。

## 1. 版本约束机制(语义先于操作)

- pub 走语义化版本,`^1.2.3` 接受 <2.0.0;**应用项目依赖 lockfile 锁
  精确版本**(可复现构建,flutter-cicd-engineering §2),**包项目不入
  lockfile** 且约束放宽(下游才有解空间)——同一文件两种纪律;
- `pub upgrade` 在约束内更新 lockfile;`pub upgrade --major-versions`
  连 pubspec 约束一起跨大版本;`pub outdated` 是升级前的体检表
  (resolvable 列 = 当前约束下能到哪);
- 传递依赖冲突的临时出口 `dependency_overrides` 只该活在"等上游发版"
  的窗口期,长期 override 是债——每条都应附跟踪 issue。

## 2. Flutter SDK 升级的节奏策略

- 稳定版按季度发布;**升级最优节奏是"常小步,不跳级"**:跳多个大版本
  会把多批破坏性变更叠加成不可二分的大爆炸,排错成本超线性增长;
- 升级标准流程:读 release notes 的 breaking changes 章节 → `flutter
  upgrade` → 跑 `dart fix --apply`(官方把大量 API 迁移做成了自动
  修复)→ 全量测试 + golden 基线重生成(渲染细节变化会让 golden
  全红,这是预期内噪声,flutter-testing-strategy §3)→ 真机冒烟;
- Flutter 的弃用政策:API 弃用后保留约一年/四个稳定版再删除——
  deprecation warning 是"一年倒计时",CI 把弃用告警纳入观测而非无视
  (lint 基线只许减不许增)。

## 3. 第三方依赖的健康度治理

- 引入前评估:pub.dev 分数只是入门线,更关键是**维护活性**(最近
  提交/issue 响应)与**作者结构**(单人包 vs 团队/官方包)——单人
  弃坑是 Flutter 生态最常见的供应链死法;
- 每个直接依赖问三句:能否用官方包/语言能力替代(轮21 §4 宏教训:
  押注未落地路线的依赖会失效)?fork 维护的成本能否承受?它再拉进
  多少传递依赖?
- 升级批次纪律:**框架升级与依赖升级分批提交**,混在一起出问题无法
  二分;Renovate/dependabot 自动 PR + CI 绿了再合,把"定期大升级"
  摊薄成"持续小升级";
- 安全侧:lockfile 入库使依赖树可审计(flutter-mobile-security §5),
  `dart pub audit`(SDK 3.10+)做已知漏洞扫描。

## 4. 与本仓库其他语料的衔接

- lockfile 可复现 ← flutter-cicd-engineering §2;golden 基线 ← flutter-testing-strategy §3;
- 供应链锁定 ← flutter-mobile-security §5;宏路线教训 ← dart-language-advanced §4。
