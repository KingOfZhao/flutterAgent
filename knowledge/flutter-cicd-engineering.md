# Flutter CI/CD 工程化(向量库优质语料·轮9)

> 反思缺口:发布工程语料覆盖"怎么发",但"每次提交到可发布之间的自动化流水线"
> 无语料——这是团队规模化后的第一瓶颈。来源见 REFERENCES §27。

## 1. 流水线分层(快反馈在前)

- **PR 级(分钟级)**:`dart format --set-exit-if-changed` → `flutter analyze`
  → 单元+widget 测试 + golden——全部可在 Linux runner 跑,便宜且快;
  format/analyze 挂在最前,失败最快的检查先执行。
- **合并级(十分钟级)**:debug/profile 构建可编译性验证 + 集成测试
  (设备实验室或模拟器矩阵);
- **发布级(小时级)**:签名 release 构建 + 商店上传 + 灰度
  (flutter-release-engineering §3)。三层不要塞进同一个 workflow——
  PR 反馈超过 10 分钟,开发者就开始批量攒提交,质量反而劣化。

## 2. 可复现构建的纪律

- **版本钉死三件套**:Flutter SDK 版本(FVM 或 CI 内显式 channel+version)、
  `pubspec.lock` 入库(应用项目必须,纯库可不入)、原生侧
  Gradle/CocoaPods lockfile 一并入库——"本地能过 CI 挂"多数源于三者之一漂移。
- 缓存正确性优先于缓存命中率:pub 缓存/Gradle 缓存按 lockfile 哈希作 key,
  盲缓存导致的"清缓存就好了"比慢更伤信任。
- iOS 构建需 macOS runner(贵且慢):PR 级只做 Android/Linux 可编译验证,
  iOS 构建放合并级/夜间,是常见的成本平衡点。

## 3. 签名与机密管理

- CI 内签名:keystore/证书以 base64 secret 注入临时文件,任务结束即清理;
  **永不入库**(flutter-mobile-security §2 同源纪律)。iOS 推荐 fastlane
  match(证书集中加密仓库)或 App Store Connect API key,避免个人证书
  绑定单台机器。
- 构建注入环境配置用 `--dart-define-from-file` + 按环境分文件,
  机密仍走服务端(flutter-release-engineering §2)。

## 4. 工具选型

- 通用 CI(GitHub Actions 等)+ fastlane 脚本:控制力最强,原生侧脚本
  自己维护;
- 托管移动 CI(Codemagic 等)与 Firebase App Distribution / TestFlight
  分发:把签名/商店上传的胶水外包,小团队提速明显;
- 选型判据:团队是否有人愿意长期维护 fastlane/原生构建脚本——没有就买托管。

## 5. 与本仓库其他语料的衔接

- 测试金字塔决定各层跑什么 ← flutter-testing-strategy §1;
- a11y guideline 断言可挂 PR 级 ← flutter-i18n-accessibility §2;
- 发布级灰度与崩溃监控 ← flutter-release-engineering §3。
