---
id: flutter-cicd-pipelines
name: CI/CD 深化 (构建矩阵 / 缓存 / 产物归档 / 发布自动化)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [ci, cd, pipeline, matrix, cache, artifacts, release-automation, fastlane, github-actions, secrets]
applies_when: 已有基础 CI,需要把流水线做深做稳——加速、分环境、产物可追溯、发布自动化
stage_hints: [architecture, breakdown, acceptance]
extends: [flutter-ci-cd]
see_also: [flutter-ci-cd, flutter-build-and-release]
---

# CI/CD 深化

`flutter-ci-cd` 解决"**有没有 CI 关卡 + 各端怎么打包发布**";本 skill 解决"**流水线怎么做深、做快、可追溯、能自动发版**"。
两者配套:先有 `flutter-ci-cd` 的 format/analyze/test/build 关卡,再用这里的工程化手段强化。

## 1. 构建矩阵(matrix)

- 用矩阵在一份 workflow 里并行覆盖多维度:**平台**(android/ios/web/desktop)× **渠道**(dev/staging/prod flavor)× **Flutter 通道**(stable/beta,按需)。
- 收益:一处定义、并行执行、覆盖全;失败定位到具体组合。
- 控制规模:`include`/`exclude` 精修组合,别让矩阵指数膨胀;非必要组合放到 nightly 而非每次 PR。
- PR 阶段跑"快矩阵"(analyze+test),发布阶段才跑"全矩阵"(各端 build)。

## 2. 缓存(让流水线快起来)

按 ROI 缓存,key 要带 lockfile 哈希以正确失效:

- **Pub 依赖**:缓存 `~/.pub-cache`,key = `pubspec.lock` 哈希。
- **Gradle**(Android):缓存 `~/.gradle/caches` + wrapper,key = gradle 文件哈希。
- **CocoaPods/SwiftPM**(iOS):缓存 `Pods/` 与 SPM 解析。
- **构建产物**:`build/` 一般不缓存(易脏);跨 job 传递用 artifact 而非 cache。
- 官方 setup action 多自带缓存开关(如 `subosito/flutter-action` 的 `cache: true`)。

## 3. 环境与密钥分层

- 用 CI 的 **Environments / Secrets** 把 dev/staging/prod 的密钥、签名证书、API base 分层,**绝不进仓库**(见 `flutter-security`)。
- 注入方式:`--dart-define` / `--dart-define-from-file`(`flutter build --dart-define-from-file=env/prod.json`)把编译期配置喂进去;敏感值从 secret 取。
- 签名材料(keystore/p12/provisioning/notary key)以 base64 存 secret,运行时解码到临时文件,用后即焚。
- 受保护环境加**人工审批**门(prod 发布前需 reviewer 批准)。

## 4. 产物与符号归档(可追溯)

- 每次发布构建都归档:**安装包**(APK/AAB/IPA/MSIX/DMG)、**符号文件**(Android `mapping.txt`、iOS dSYM)、**构建元数据**(commit/版本/flavor)。
- 符号文件必须上传到崩溃平台(Crashlytics/Sentry,见 `flutter-observability`),否则线上崩溃栈无法还原(R8/混淆后,见 `flutter-android-platform`)。
- 产物按版本号 + commit 命名,可回溯到精确源码。

## 5. 版本与发布自动化

- **触发**:打 tag(`v1.2.3`)或合并到 release 分支触发发布流水线;PR 只做校验不发布。
- **版本号**:从 tag 推导 `version: x.y.z+build`(build 号常用 CI run number),避免手填漂移(见 `flutter-dependency-maintenance` SemVer)。
- **店铺提交**:用 **fastlane**(`supply` 上 Play、`deliver`/`pilot` 上 App Store/TestFlight)做可重复的提交;桌面/Web 走各自渠道(见 `flutter-desktop-platform`、`flutter-build-and-release`)。
- **渐进发布**:Play 分阶段放量、TestFlight 灰度;出问题暂停 rollout。
- **变更记录**:发布自动生成/校验 CHANGELOG(见 `flutter-documentation`)。

## 6. 流水线可维护性

- 抽**可复用 workflow**(reusable workflow / composite action)消除多仓重复;monorepo 用路径过滤只跑受影响的包(见 `flutter-monorepo-melos`)。
- 流水线即代码:评审 workflow 变更(见 `flutter-code-review`);失败要有清晰日志与重试策略(区分 flaky 与真失败)。
- 把质量门禁尽量左移:本地 `flutter-static-analysis` + pre-commit,CI 兜底。

## 反模式

- ❌ 每次 PR 都跑全平台全 flavor 全 build,几十分钟起步还烧额度(应分快/全两档)。
- ❌ 不缓存依赖,每次从零拉取。
- ❌ 缓存 key 不带 lockfile 哈希,依赖变了还命中旧缓存。
- ❌ 签名证书/密钥提交进仓库或硬编码进 workflow。
- ❌ 发布不归档 dSYM/mapping,线上崩溃栈无法符号化。
- ❌ 版本号手填,tag 与 pubspec 漂移。
- ❌ prod 发布无审批门、无分阶段放量,一把梭全量。

## 参考 / References

- GitHub Actions 矩阵:<https://docs.github.com/actions/using-jobs/using-a-matrix-for-your-jobs>
- Actions 缓存依赖:<https://docs.github.com/actions/using-workflows/caching-dependencies-to-speed-up-workflows>
- Actions 环境(审批/保护):<https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment>
- Actions Secrets:<https://docs.github.com/actions/security-guides/encrypted-secrets>
- 可复用 workflow:<https://docs.github.com/actions/using-workflows/reusing-workflows>
- Flutter CI 部署文档:<https://docs.flutter.dev/deployment/cd>
- `--dart-define-from-file`:<https://docs.flutter.dev/deployment/flavors>
- fastlane:<https://docs.fastlane.tools/>
- `subosito/flutter-action`:<https://github.com/subosito/flutter-action>
- 基础 CI/各端发布见 `flutter-ci-cd`;打包细节见 `flutter-build-and-release`;符号上报见 `flutter-observability`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **快/全两档**:PR 求快(analyze+test),发布求全(矩阵 build),别用一套跑所有场景。
- **可追溯优先**:每个线上包都能回到 commit + 符号文件,否则线上崩溃就是黑盒。
- **密钥永远在仓库外**:CI secret + 即用即焚,签名材料绝不入库。
- **发版是可重复的脚本**,不是手工操作(fastlane / tag 驱动)。

**诚实边界:**

- CI 平台(GitHub Actions/GitLab CI/Codemagic/Bitrise)语法各异,本 skill 给的是**通用策略**,具体 YAML 以对应平台文档为准。
- iOS 发布仍受 Apple 证书/Provisioning/公证约束(见 `flutter-ios-platform`),CI 只是自动化它,绕不过苹果流程。
- 缓存与矩阵的最优配置随项目规模、额度、构建时长而变,需实测调参,非一套通用最优。
