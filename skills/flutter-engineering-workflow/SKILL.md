---
id: flutter-engineering-workflow
name: Flutter 工程交付总框架 (理解→修复/新增→自测→文档→交付)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [process, workflow, framework, fix, feature, verify, doc, delivery, sop]
applies_when: 任何对 Flutter(移动端 / PC 桌面端 / Web)代码做修复或新增的工程任务
stage_hints: [breakdown, acceptance]
---

# Flutter 工程交付总框架

这是把"对 Flutter 移动端 / 桌面端项目的工程理解"蒸馏成的**可执行闭环**。
任何针对一个**已有 Flutter 仓库**的"修复 / 新增"任务,都按下面 5 个阶段推进。
每个阶段都有更细的专用 skill:

| 阶段 | 目标 | 专用 skill |
|---|---|---|
| 0 理解 & 定位 | 把需求/缺陷锚定到具体文件、layer、平台 | 本 skill + `architecture-design` |
| 1A 修复 (fix) | 复现 → 定位根因 → 最小改动 → 防回归 | `flutter-debugging` |
| 1B 新增 (feature) | 脚手架 → 状态 → UI → 接线 → 灰度 | `flutter-feature-development` |
| 1C 重构 (refactor) | 有护栏地改结构、不改行为 | `flutter-refactoring` |
| 1D 升级依赖 (deps) | 看现状 → 分级升级 → 验证 → 记录 | `flutter-dependency-maintenance` |
| 2 自测 (verify) | analyze / format / test / build 本地闭环 | `flutter-verification` |
| 3 文档 (docs) | dartdoc / README / CHANGELOG / ADR | `flutter-documentation` |
| 4 交付 (deliver) | 提交规范 / PR / 评审 / CI 门禁 | 本 skill §5 + `flutter-code-review` + `flutter-ci-cd` |

> **代码质量横切能力**(贯穿 1A–1D 实现全程,不属于某一阶段):
> 语言层写地道用 `dart-language-idioms`;失败路径设计用 `flutter-error-handling`;
> 数据类/序列化/provider 的代码生成用 `flutter-codegen`;CPU 密集/并行用 `flutter-concurrency-isolates`;
> 静态分析自动化(质量前移到写代码当下)用 `flutter-static-analysis`。
> 设计可复用库/模块的公共 API 用 `dart-api-package-design`;多包仓库维护用 `flutter-monorepo-melos`。
> 复杂业务用类型建模(让非法状态不可表达/状态机)用 `flutter-domain-modeling`;
> 把代码设计成可测的形状(DI/接缝/纯核心/控时间)用 `flutter-testability-design`;
> 异步编排与事件流(Future 组合/Stream/取消背压)用 `dart-async-streams`。
> 这些是"把代码写好/改好/养好"的底座。

> **平台工程能力**(改动触达原生层 / 打包 / 平台配置时):
> 调原生能力用 `flutter-platform-channels`(MethodChannel/Pigeon/FFI);
> Android 工程层(Gradle/Manifest/权限/R8)用 `flutter-android-platform`;
> iOS/Apple 工程层(Xcode/Info.plist/权限串/ATS/审核)用 `flutter-ios-platform`;
> 桌面三端打包签名公证用 `flutter-desktop-platform`。

> **协议能力**(与后端/设备通信时):
> 选通信协议(HTTP/2·3、REST、gRPC、GraphQL、WebSocket、SSE、MQTT)用 `flutter-network-protocols`;
> 登录与令牌(OAuth2/OIDC/PKCE/JWT/刷新/生物识别)用 `flutter-auth-protocols`。
> (协议选型在先,客户端实现见 `flutter-network`,凭证安全见 `flutter-security`。)

> **UI 识别与还原能力**(输入是设计稿/截图时):
> 从图里提取规格(取色、字号等比换算、渐变方向、关键信息清单)用 `flutter-ui-from-image`;
> 把提取出的 token 落成工程化主题(ColorScheme/TextTheme/ThemeData/亮暗)用 `flutter-design-tokens-theming`;
> 想要"设计稿→代码"端到端照着走用 `flutter-design-to-code-playbook`;照图找组件骨架用 `flutter-ui-component-recipes`。
> (先成规格 → 再成主题 → 再按 1B 实现 UI。)

> **交付与运维能力**(发布与线上阶段):
> 把基础 CI 做深(构建矩阵/缓存/产物归档/发布自动化)用 `flutter-cicd-pipelines`(基础 CI 见 `flutter-ci-cd`);
> 线上可观测(崩溃上报/结构化日志/指标/追踪/行为分析)用 `flutter-observability`。

> 一句话原则:**改动越小越好,验证越足越好,文档跟着改动走。** 不发明不存在的包,不写伪代码,所有"为什么"都要能落到 `REFERENCES.md` 的官方出处。

---

## 阶段 0:理解 & 定位(动手前必做)

> 思维底座:全程用 `flutter-engineer-mindset` 的心智模型与决策启发式做判断(约束链、UI=f(state)、两条线程预算、状态归属、平台在边界)——它管"怎么想",本框架管"怎么走"。

先把任务"翻译"成工程坐标,别急着改代码:

1. **判定任务类型**:修 bug(1A)/ 加功能(1B)/ 重构(1C,`flutter-refactoring`)/ 升级依赖(1D,`flutter-dependency-maintenance`)—— 不同类型走不同路径,别混在一个 PR。
2. **判定目标平台**:mobile(iOS/Android)、desktop(Windows/macOS/Linux)、web。
   平台不同,能力边界不同(权限、窗口、文件系统、`dart:io` vs `dart:html`)。
   - 跨端差异交给 `flutter-cross-platform`;平台细节交给 `flutter-mobile` / `flutter-desktop` / `flutter-web`。
   - 触达原生层 / 平台工程配置(权限、Gradle、Xcode、桌面打包)交给 `flutter-android-platform` / `flutter-ios-platform` / `flutter-desktop-platform`;调原生 API 用 `flutter-platform-channels`。
3. **锚定代码位置**:按 Clean Architecture 三层(presentation / domain / data,见 `architecture-design`)定位"改动应落在哪一层"。
   - UI 不对 → presentation(widget / state)。
   - 业务规则不对 → domain(usecase / entity)。
   - 数据来源不对 → data(repository / datasource / dto)。
4. **明确验收口径**:把"做完的标准"写成可被测试断言的句子(Given/When/Then),后面阶段 2 会逐条验证。
5. **盘点影响面**:`grep` / IDE 找引用,列出 `files_touched`,评估是否触达公共 API(决定是否要 CHANGELOG / 破坏性变更说明)。

产出:一个"改动计划"——任务类型、平台、受影响 layer、`files_touched`、验收清单。

---

## 阶段 1A:修复(fix) — 详见 `flutter-debugging`

核心顺序不可跳:**先复现,再定位,后修改,必加回归测试。**

1. **稳定复现**:写出最小复现步骤;能复现才能确认修好了。
2. **定位根因**:用 `flutter analyze`、stack trace、`debugPrint` / `log`、DevTools 缩小范围;区分"症状"与"根因",不要只压症状。
3. **最小改动**:只改根因相关代码,不顺手重构无关部分(重构单独开 PR)。
4. **先写失败测试**:先补一个能复现该 bug 的测试(red),改完后它转绿(green)——这就是防回归。
5. **回归扫描**:同类代码路径是否有同样 bug?一并列出。

---

## 阶段 1B:新增(feature) — 详见 `flutter-feature-development`

按"垂直切片"交付,一个 feature 自带 data→domain→presentation→test:

1. **脚手架**:在 `lib/features/<feature>/` 下建 `data/ domain/ presentation/` 三层目录。
2. **领域先行**:先定 entity / usecase 的契约(纯 Dart,可单测),再填实现。
3. **状态管理**:遵循仓库既有方案(Riverpod / BLoC,见 `state-management`),不要在同一仓库混用两套。
4. **UI 接线**:widget 只消费 state,不放业务逻辑;空/加载/错误三态都要有。
   - 若需求带**设计稿/截图**:先用 `flutter-ui-from-image` 读图成规格(取色/字号等比换算/渐变方向/关键信息),再用 `flutter-design-tokens-theming` 落成主题,widget 只消费主题 token,不硬编码色值字号。
5. **依赖选型**:新引入的包必须 pub.dev 可查、活跃维护,并在 PR 写明理由(反幻觉,见 `architecture-design`)。
6. **灰度/开关**:对有风险的功能加 feature flag,便于回滚。

---

## 阶段 2:自测(verify) — 详见 `flutter-verification`

**任何改动在交付前必须本地跑通这条门禁链**(等价于 CI 第一道关):

```bash
dart format --output=none --set-exit-if-changed .   # 1. 格式
flutter analyze                                      # 2. 静态分析(0 error)
flutter test --coverage                              # 3. 单元 + widget 测试
flutter test integration_test                        # 4. 集成测试(若有)
flutter build apk --debug   # 或对应平台 build,确认能编出来
```

- 任何一步红了就停下修,不要带着失败往下走。
- 新增/修复都要有对应测试覆盖(见阶段 1A 第 4 步、`flutter-testing`)。
- 性能敏感改动额外跑 profile(见 `flutter-performance`)。

---

## 阶段 3:文档(docs) — 详见 `flutter-documentation`

文档**跟着改动走**,不是事后补:

- 改了**公共 API** → 更新 `///` dartdoc 注释。
- 改了**用户可见行为 / 依赖** → 更新 `README` 与 `CHANGELOG`(遵循 Keep a Changelog + SemVer)。
- 做了**重要架构决策** → 写一条 ADR(Architecture Decision Record)。
- 破坏性变更 → 在 PR 与 CHANGELOG 顶部显著标注 `BREAKING`,给迁移指引。

---

## 阶段 4:交付(deliver)

1. **提交信息**:用 Conventional Commits(`fix:` / `feat:` / `refactor:` / `docs:` / `test:` …),与阶段 1 的任务类型对应。
2. **PR 自查**:diff 是否最小?是否含无关改动?测试是否覆盖?文档是否同步?
3. **CI 门禁**:format / analyze / test / build 必须全绿(见 `flutter-ci-cd`)。
4. **可回滚**:风险功能带 flag;数据库迁移要可回退(见 `flutter-data-persistence`)。

---

## 反模式(明确禁止)

- ❌ 没复现就改 bug;❌ 改完不加回归测试。
- ❌ 一个 PR 里混"修复 + 大重构 + 新功能"。
- ❌ 引入 pub.dev 查不到 / 已废弃 / 版本超前的包。
- ❌ 改了行为却不动文档 / CHANGELOG。
- ❌ 本地没跑 `analyze` / `test` 就提 PR,把验证甩给 CI。

## 参考 / References

- Flutter 官方测试总览:<https://docs.flutter.dev/testing/overview>
- Dart 静态分析 `dart analyze`:<https://dart.dev/tools/dart-analyze>
- Effective Dart(文档与风格):<https://dart.dev/effective-dart>
- Conventional Commits 规范:<https://www.conventionalcommits.org/>
- Keep a Changelog:<https://keepachangelog.com/>
- Semantic Versioning:<https://semver.org/>
- 架构分层与各专用 skill 出处见 `REFERENCES.md`。
