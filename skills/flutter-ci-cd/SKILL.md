---
id: flutter-ci-cd
name: Flutter CI/CD 与发布规范
version: 1.0.0
platforms: [all]
tags: [ci, cd, fastlane, github-actions, codemagic, flavors]
applies_when: 任何上架 / 内测分发的项目
stage_hints: [architecture, breakdown, acceptance]
---

# Flutter CI / CD 规范

> 直接依据:
> * Flutter 官方 CD 文档:**[docs.flutter.dev/deployment/cd](https://docs.flutter.dev/deployment/cd)**
> * Build flavors:<https://docs.flutter.dev/deployment/flavors>
> * Android 发布:<https://docs.flutter.dev/deployment/android>
> * iOS 发布:<https://docs.flutter.dev/deployment/ios>
> * macOS 发布:<https://docs.flutter.dev/deployment/macos>
> * Windows / Linux 发布:<https://docs.flutter.dev/deployment/desktop>
> * Web 发布:<https://docs.flutter.dev/deployment/web>
> * fastlane:<https://docs.fastlane.tools>
> * Codemagic Flutter 模板:<https://docs.codemagic.io/yaml-quick-start/building-a-flutter-app>
> * GitHub Actions 官方 Flutter 模板:<https://github.com/subosito/flutter-action>

## 1. 强制 CI 关卡(任何 PR 必须通过)

```yaml
# .github/workflows/ci.yaml(完整片段)
name: ci
on: [pull_request]
jobs:
  analyze-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: subosito/flutter-action@v2
        with: { flutter-version: '3.22.x', channel: 'stable', cache: true }
      - run: flutter --version
      - run: flutter pub get
      - run: dart format --output=none --set-exit-if-changed .
      - run: flutter analyze
      - run: flutter test --coverage --reporter expanded
      - uses: codecov/codecov-action@v4
        with: { files: coverage/lcov.info }
```

必须门控:
1. `dart format` 通过(用 `very_good_analysis` 或 `flutter_lints` 作为 analysis_options)
2. `flutter analyze` 0 error / 0 warning
3. `flutter test` 通过且覆盖率不下降(domain ≥ 90%、data ≥ 75% — 见 flutter-testing skill)
4. **依赖锁定**:`pubspec.lock` 入库,CI `pub get --enforce-lockfile`(Flutter 3.16+)
5. **license 扫描**:不允许 GPL/AGPL/SSPL 依赖

## 2. Flavors(必做)

Flutter 官方支持的多环境方案:**[docs.flutter.dev/deployment/flavors](https://docs.flutter.dev/deployment/flavors)**

至少三个 flavor:`dev` / `staging` / `prod`,每个差异:
- 应用 ID(`com.app.todo.dev` / `.staging` / `.todo`)
- App 名 + icon(避免误启)
- API base URL + feature flags
- 上报 dsn(Sentry / Crashlytics 区分项目)

```bash
flutter run --flavor dev   --dart-define=ENV=dev   -t lib/main_dev.dart
flutter build apk --flavor prod --dart-define=ENV=prod --release
```

入口:`main_dev.dart` / `main_staging.dart` / `main_prod.dart`,各自加载对应 `Config`,然后 `runApp(...)`。

## 3. 移动端发布管线

### Android

| 步骤 | 工具 | 来源 |
|---|---|---|
| 签名 | upload keystore (`*.jks`)+ Play App Signing | <https://developer.android.com/studio/publish/app-signing> |
| 构建 | `flutter build appbundle --flavor prod --release --obfuscate --split-debug-info=./symbols/android` | flutter.dev |
| 上传 | fastlane `supply` | <https://docs.fastlane.tools/actions/supply/> |
| 渠道 | Internal → Closed → Open → Production | Play Console |

**禁止**:把 keystore 提交进 git;使用 GitHub Secrets / Codemagic 加密变量。

### iOS

| 步骤 | 工具 | 来源 |
|---|---|---|
| 证书 | `match` | <https://docs.fastlane.tools/actions/match/> |
| 构建 | `flutter build ipa --flavor prod --release --export-options-plist=ExportOptions.plist` | flutter.dev |
| 上传 | `pilot` (TestFlight) → `deliver` (App Store) | fastlane |
| 隐私清单 | `PrivacyInfo.xcprivacy`(2024 起强制) | <https://developer.apple.com/documentation/bundleresources/privacy_manifest_files> |

iOS 17+ **必须**有隐私清单,否则 App Store 不接受;Flutter 3.19+ 默认生成。

### Flutter 3.44 构建工具链更新

**Swift Package Manager 默认**:Flutter 3.44 起 SwiftPM 彻底取代 CocoaPods:
- `flutter build ios` 自动将 Xcode 工程迁移为 SwiftPM 架构
- Mac 上不再需要安装 Ruby / CocoaPods,只需 Xcode
- CI 流程可移除 `gem install cocoapods` / `pod install` 步骤

**AGP 9.0 + 内置 Kotlin**:Android Gradle 插件 9.0 内置 Kotlin 支持,解决了长期困扰的 AGP 与 KGP 版本兼容性问题。CI 配置中应确保 AGP ≥ 9.0。

**Apple Silicon 原生支持**:Flutter SDK 和所有辅助二进制工具已全部重编为 ARM64,CI 使用 Apple Silicon runner 无需 Rosetta。注意:Flutter 未来版本将**停止支持 Intel Mac 主机**,需提前规划 CI runner 迁移。

## 4. 桌面端发布

### macOS

- 沙箱与 entitlements:<https://docs.flutter.dev/deployment/macos#configure-app-sandbox>
- 公证:`notarytool submit --apple-id ... --team-id ... --password ...`
- 分发:dmg(用 `create-dmg`)或 Mac App Store
- 自动更新:Sparkle 2(<https://sparkle-project.org>),配合 `auto_updater` (<https://pub.dev/packages/auto_updater>)

### Windows

- 包格式优先级:**MSIX**(Windows 10/11 推荐)> Squirrel(EXE 安装包)
- MSIX 工具:`msix` 包(<https://pub.dev/packages/msix>),`flutter pub run msix:create`
- 代码签名:EV 证书(SmartScreen 不警告)或标准 OV 证书
- Microsoft Store 分发(可选)

### Linux

- AppImage(便携)/ snap / flatpak / deb / rpm
- 工具:`flutter_distributor`(<https://pub.dev/packages/flutter_distributor>)统一打包多格式

## 5. Web 发布

- `flutter build web --release --web-renderer canvaskit --base-href /app/`
- 部署到 Cloudflare Pages / Netlify / Firebase Hosting / 自建 nginx
- `flutter build web --pwa-strategy offline-first` 启用 PWA

## 6. 版本号策略

- 语义化版本:`MAJOR.MINOR.PATCH+BUILD`(`pubspec.yaml` 的 `version: 1.4.2+1042`)
- BUILD 号 = CI build number(单调递增),Android `versionCode` / iOS `CFBundleVersion`
- tag → 发布 commit → 自动 build pipeline

## 7. 监控与回滚

- 错误上报:**Sentry**(<https://pub.dev/packages/sentry_flutter>)或 **Firebase Crashlytics**(<https://pub.dev/packages/firebase_crashlytics>)
- 性能上报:`firebase_performance`
- A/B 与开关:`firebase_remote_config` 或 `posthog`
- 回滚:Play Console / App Store Connect 都支持 "halt rollout";桌面端通过自动更新通道版本号下调

## 8. 必须产出

每个产出需包含:
1. CI 文件路径与 job 列表
2. 至少 3 个 flavor(dev/staging/prod)的差异表
3. 每个目标平台的签名 / 公证 / 上架步骤清单
4. 版本号策略与升级路径(强制更新 vs 灰度)
5. 监控与回滚预案(包含 SLO:崩溃率 < 0.5%、ANR < 0.1%)
6. 隐私清单 / GDPR / 个保法合规结论

## 9. 红线

- 不要在 CI 日志里打印 secret(用 `***` mask)
- 不要把 keystore / p8 私钥提交进仓库
- 不要 `flutter build` 时省略 `--obfuscate --split-debug-info`(否则栈被解混淆是噩梦)
- 不要发布带 `print` 日志的 release 版
- 不要绕过商店审核分发(企业证书除外,且必须明确合规)
