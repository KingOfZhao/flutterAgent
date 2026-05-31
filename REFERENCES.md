# 参考来源 / References

本文档列出 `flutterAgent` 中每条工程主张、技术选型、断点、阈值的**可点击**依据。
任何 skill / pipeline 输出里出现的「最佳实践」都必须能在下表中找到对应来源。

---

## 1. Flutter 官方文档(docs.flutter.dev)

| 主题 | 链接 | 在本仓库何处引用 |
|---|---|---|
| 架构指南(2024 重写) | <https://docs.flutter.dev/app-architecture> | `architecture-design`, `flutter-mobile` |
| 性能最佳实践 | <https://docs.flutter.dev/perf/best-practices> | `flutter-performance`, `flutter-mobile` |
| 应用大小分析 | <https://docs.flutter.dev/perf/app-size> | `flutter-mobile`(替换旧的「25MB 硬指标」) |
| Impeller 渲染引擎 | <https://docs.flutter.dev/perf/impeller> | `flutter-performance` |
| 启动延迟 | <https://docs.flutter.dev/perf/best-practices#startup-latency> | `flutter-mobile` |
| Adaptive UI 指南 | <https://docs.flutter.dev/ui/adaptive-responsive> | `flutter-cross-platform` |
| Accessibility | <https://docs.flutter.dev/ui/accessibility-and-internationalization/accessibility> | `flutter-accessibility` |
| Internationalization | <https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization> | `flutter-i18n` |
| Testing 总览 | <https://docs.flutter.dev/testing> | `flutter-testing` |
| Build flavors | <https://docs.flutter.dev/deployment/flavors> | `flutter-ci-cd` |
| CD 总览 | <https://docs.flutter.dev/deployment/cd> | `flutter-ci-cd` |
| Android 发布 | <https://docs.flutter.dev/deployment/android> | `flutter-ci-cd` |
| iOS 发布 | <https://docs.flutter.dev/deployment/ios> | `flutter-ci-cd` |
| macOS 发布 | <https://docs.flutter.dev/deployment/macos> | `flutter-ci-cd` |
| Windows / Linux 发布 | <https://docs.flutter.dev/deployment/desktop> | `flutter-ci-cd`, `flutter-desktop` |
| Web 发布 | <https://docs.flutter.dev/deployment/web> | `flutter-ci-cd` |
| 代码混淆 | <https://docs.flutter.dev/deployment/obfuscate> | `flutter-security` |
| State management 选项 | <https://docs.flutter.dev/data-and-backend/state-mgmt/options> | `state-management` |
| Platform integration / Desktop | <https://docs.flutter.dev/platform-integration/desktop> | `flutter-desktop` |
| Animations overview | <https://docs.flutter.dev/ui/animations> | `flutter-animation` |
| Animations tutorial | <https://docs.flutter.dev/ui/animations/tutorial> | `flutter-animation` |
| Implicit animations | <https://docs.flutter.dev/ui/animations/implicit-animations> | `flutter-animation` |
| Hero animations | <https://docs.flutter.dev/ui/animations/hero-animations> | `flutter-animation` |
| Navigation overview | <https://docs.flutter.dev/ui/navigation> | `flutter-navigation` |
| Deep linking | <https://docs.flutter.dev/ui/navigation/deep-linking> | `flutter-navigation` |
| Persistence cookbook | <https://docs.flutter.dev/cookbook/persistence> | `flutter-data-persistence` |
| Widget Preview | <https://docs.flutter.dev/tools/widget-previewer> | `flutter-performance` |
| Memory DevTools | <https://docs.flutter.dev/tools/devtools/memory> | `flutter-resource-lifecycle` |
| ImageCache 大图 | <https://docs.flutter.dev/release/breaking-changes/imagecache-large-images> | `flutter-resource-lifecycle` |
| Cached images cookbook | <https://docs.flutter.dev/cookbook/images/cached-images> | `flutter-resource-lifecycle` |
| State lifecycle | <https://api.flutter.dev/flutter/widgets/State-class.html> | `flutter-resource-lifecycle` |
| Web 部署 | <https://docs.flutter.dev/deployment/web> | `flutter-web` |
| Web 渲染器 | <https://docs.flutter.dev/platform-integration/web/renderers> | `flutter-web` |
| Web FAQ | <https://docs.flutter.dev/platform-integration/web> | `flutter-web` |
| Networking | <https://docs.flutter.dev/data-and-backend/networking> | `flutter-network` |

## 2. Material Design 3 / Material 规范

| 主题 | 链接 |
|---|---|
| Window size classes(断点表) | <https://m3.material.io/foundations/layout/applying-layout/window-size-classes> |
| Layout foundations | <https://m3.material.io/foundations/layout> |
| Accessible design | <https://m3.material.io/foundations/accessible-design/overview> |
| Motion(动效规范) | <https://m3.material.io/styles/motion/overview> |

## 3. Apple / Google 平台指引

| 主题 | 链接 |
|---|---|
| Apple HIG — Accessibility | <https://developer.apple.com/design/human-interface-guidelines/accessibility> |
| Apple — Privacy Manifests | <https://developer.apple.com/documentation/bundleresources/privacy_manifest_files> |
| Apple — Notarizing macOS | <https://developer.apple.com/documentation/security/notarizing_macos_software_before_distribution> |
| Android — Accessibility | <https://developer.android.com/guide/topics/ui/accessibility/apps> |
| Android — Security Best Practices | <https://developer.android.com/topic/security/best-practices> |
| Android — App Signing | <https://developer.android.com/studio/publish/app-signing> |
| Google Play Integrity API | <https://developer.android.com/google/play/integrity> |
| Google Play — Data Safety | <https://support.google.com/googleplay/android-developer/answer/10787469> |

## 4. 行业标准与白皮书

| 主题 | 链接 |
|---|---|
| WCAG 2.1(AA 基线) | <https://www.w3.org/TR/WCAG21/> |
| OWASP MASVS(Mobile App Security Verification Standard) | <https://mas.owasp.org/MASVS/> |
| OWASP MASTG(测试手册) | <https://mas.owasp.org/MASTG/> |
| SemVer 2.0 | <https://semver.org/spec/v2.0.0.html> |
| CLDR(国际化数据源) | <https://cldr.unicode.org> |
| ARB 文件格式 | <https://github.com/google/app-resource-bundle/wiki/ApplicationResourceBundleSpecification> |
| GDPR | <https://gdpr.eu> |
| 个人信息保护法 / 数据安全法 | <https://www.gov.cn/xinwen/2021-08/20/content_5632486.htm> |

## 5. 关键 pub.dev 包(全部由 Flutter team 或公认社区维护)

| 包 | 用途 | 维护方 |
|---|---|---|
| <https://pub.dev/packages/flutter_riverpod> | 状态管理 | Remi Rousselet(Flutter core) |
| <https://pub.dev/packages/flutter_bloc> | 状态管理 | Felix Angelov |
| <https://pub.dev/packages/provider> | DI / 状态 | Flutter team |
| <https://pub.dev/packages/go_router> | 路由 | Flutter team |
| <https://pub.dev/packages/dio> | HTTP 客户端 | 社区,Flutter 生态主流 |
| <https://pub.dev/packages/retrofit> | dio 的注解式客户端 | 社区 |
| <https://pub.dev/packages/drift> | type-safe SQLite | Simon Binder |
| <https://pub.dev/packages/sqflite_sqlcipher> | 加密 SQLite | 社区 |
| <https://pub.dev/packages/shared_preferences> | K-V 存储 | Flutter team |
| <https://pub.dev/packages/flutter_secure_storage> | 安全存储 | 社区 |
| <https://pub.dev/packages/freezed> | sealed class / immutable model | Remi Rousselet |
| <https://pub.dev/packages/fpdart> | `Either` / `Option` | 社区 |
| <https://pub.dev/packages/intl> | i18n + 复数 / 日期 / 数字 | Dart team |
| <https://pub.dev/packages/flutter_localizations> | Material/Cupertino 翻译 | Flutter SDK 内置 |
| <https://pub.dev/packages/mocktail> | Mock(零代码生成) | Very Good Ventures |
| <https://pub.dev/packages/bloc_test> | BLoC 测试 | Felix Angelov |
| <https://pub.dev/packages/golden_toolkit> | 多设备 golden | 社区 |
| <https://pub.dev/packages/patrol> | 强 E2E | LeanCode |
| <https://pub.dev/packages/very_good_analysis> | 严格 lint 集 | Very Good Ventures |
| <https://pub.dev/packages/flutter_lints> | 官方 lint 集 | Flutter team |
| <https://pub.dev/packages/flutter_adaptive_scaffold> | 自适应骨架 | Flutter team |
| <https://pub.dev/packages/cached_network_image> | 图片缓存 | 社区 |
| <https://pub.dev/packages/flutter_image_compress> | 图片压缩 | 社区 |
| <https://pub.dev/packages/infinite_scroll_pagination> | 大列表分页 | 社区 |
| <https://pub.dev/packages/flutter_native_splash> | 启动屏 | 社区 |
| <https://pub.dev/packages/window_manager> | 桌面窗口 | 社区 |
| <https://pub.dev/packages/bitsdojo_window> | 桌面窗口(替代) | bitsdojo |
| <https://pub.dev/packages/tray_manager> | 系统托盘 | 社区 |
| <https://pub.dev/packages/hotkey_manager> | 全局快捷键 | 社区 |
| <https://pub.dev/packages/local_notifier> | 桌面通知 | 社区 |
| <https://pub.dev/packages/screen_retriever> | 屏幕信息 | 社区 |
| <https://pub.dev/packages/auto_updater> | 自动更新 | 社区 |
| <https://pub.dev/packages/flutter_distributor> | 多格式打包 | 社区 |
| <https://pub.dev/packages/msix> | Windows MSIX | 社区 |
| <https://pub.dev/packages/sentry_flutter> | 错误监控 | Sentry |
| <https://pub.dev/packages/firebase_crashlytics> | 崩溃监控 | Firebase |
| <https://pub.dev/packages/permission_handler> | 权限申请 | 社区 |
| <https://pub.dev/packages/flutter_jailbreak_detection> | 越狱检测 | 社区 |
| <https://pub.dev/packages/path_provider> | 跨端路径 | Flutter team |
| <https://pub.dev/packages/dio_certificate_pinning> | 证书锁定 | 社区 |
| <https://pub.dev/packages/lottie> | After Effects 动画播放 | 社区 |
| <https://pub.dev/packages/rive> | 交互式矢量动画 | Rive |
| <https://pub.dev/packages/flutter_animate> | 声明式链式动画 | gskinner |
| <https://pub.dev/packages/animations> | Material motion | Flutter team |
| <https://pub.dev/packages/go_router_builder> | 类型安全路由生成 | Flutter team |
| <https://pub.dev/packages/auto_route> | 代码生成路由 | 社区 |
| <https://pub.dev/packages/drift> | 类型安全 SQLite ORM | Simon Binder |
| <https://pub.dev/packages/sqflite> | 低层 SQLite | Flutter team |
| <https://pub.dev/packages/hive_ce> | NoSQL 文档存储 (community edition) | 社区 |
| <https://pub.dev/packages/flutter_cache_manager> | 大文件缓存 | 社区 |
| <https://pub.dev/packages/genkit> | AI 应用框架 (Dart 预览版) | Google |
| <https://pub.dev/packages/genui> | 生成式 UI (A2UI) | Flutter team |
| <https://pub.dev/packages/flutter_gemma> | 端侧 LLM 推理 (LiteRT-LM) | Google |
| <https://pub.dev/packages/firebase_ai> | Firebase AI (Gemini/Imagen) | Firebase |
| <https://pub.dev/packages/video_player> | 官方视频播放器 | Flutter team |
| <https://pub.dev/packages/visibility_detector> | widget 可见性检测 | Google |
| <https://pub.dev/packages/leak_tracker> | 内存泄漏自动检测 | Flutter team |
| <https://pub.dev/packages/fl_chart> | 声明式图表 (折线/柱状/饼/雷达) | 社区 |
| <https://pub.dev/packages/google_fonts> | Google Fonts 动态加载 | Google |
| <https://pub.dev/packages/url_strategy> | Web URL 策略 (去掉 #) | 社区 |
| <https://pub.dev/packages/dio> | HTTP 客户端 + 拦截器链 | 社区 (dio team) |
| <https://pub.dev/packages/web_socket_channel> | WebSocket 通信 | Dart team |
| <https://pub.dev/packages/graphql_flutter> | GraphQL 客户端 + 缓存 | 社区 |
| <https://pub.dev/packages/grpc> | gRPC Dart 客户端 | Dart team |
| <https://pub.dev/packages/connectivity_plus> | 网络状态监听 | Flutter Community |
| <https://pub.dev/packages/retrofit> | Dio REST 代码生成 | 社区 |

## 6. Flutter & Dart 官方 Skills

| 项目 | 链接 | 说明 |
|---|---|---|
| Flutter Skills | <https://github.com/flutter/skills> | 官方 Flutter 工程最佳实践 Skills |
| Dart Skills | <https://github.com/dart-lang/skills> | 官方 Dart 语言 Skills |

## 7. 开源 Flutter 应用对照(可作为架构参考)

| 项目 | 链接 | 价值 |
|---|---|---|
| flutter/samples | <https://github.com/flutter/samples> | Flutter 团队官方示例集合,含 compass_app / adaptive_app / web_dashboard |
| Wonderous | <https://github.com/gskinnerTeam/flutter-wonderous-app> | 跨端(mobile+desktop)动效参考,gskinner 出品 |
| Very Good CLI | <https://github.com/VeryGoodOpenSource/very_good_cli> | Very Good Ventures 工程模板 |
| Very Good Core | <https://github.com/VeryGoodOpenSource/very_good_core> | Flutter 完整模板 |
| Very Good Workflows | <https://github.com/VeryGoodOpenSource/very_good_workflows> | CI 流水线模板 |
| Cake Wallet | <https://github.com/cake-tech/cake_wallet> | 含钱包 / 加密 / 安全实践 |
| Bluesky | <https://github.com/bluesky-social/social-app> | 大型实际产品(用 React Native;参考其架构选择) |
| ResoCoder Clean Arch 课程 | <https://github.com/ResoCoder/flutter-tdd-clean-architecture-course> | Clean Architecture 落地的经典教程 |

## 7. CI / CD 工具

| 工具 | 链接 |
|---|---|
| fastlane | <https://docs.fastlane.tools> |
| fastlane match | <https://docs.fastlane.tools/actions/match/> |
| fastlane supply (Play) | <https://docs.fastlane.tools/actions/supply/> |
| Codemagic Flutter | <https://docs.codemagic.io/yaml-quick-start/building-a-flutter-app> |
| GitHub Actions Flutter Action | <https://github.com/subosito/flutter-action> |
| Codecov | <https://codecov.io> |
| lcov / genhtml | <https://github.com/linux-test-project/lcov> |

## 8. 价目表(成本估算依据)

| 模型 | 链接 |
|---|---|
| DeepSeek API 价目 | <https://api-docs.deepseek.com/quick_start/pricing> |
| OpenAI API 价目 | <https://openai.com/api/pricing/> |

`src/flutter_agent/pricing.py` 的默认表完全照搬上面两张表,可被 `PRICING_CONFIG` 环境变量覆盖。

## 9. 工作流方法学

| 主题 | 链接 |
|---|---|
| Atlassian — User Stories | <https://www.atlassian.com/agile/project-management/user-stories> |
| BDD / Cucumber | <https://cucumber.io/docs/bdd/> |
| Scaled Agile Framework — Epic | <https://scaledagileframework.com/epic/> |
| Planning Poker | <https://www.mountaingoatsoftware.com/agile/planning-poker> |
| INVEST 原则 | <https://en.wikipedia.org/wiki/INVEST_(mnemonic)> |
| Agile Alliance — Acceptance | <https://www.agilealliance.org/glossary/acceptance/> |
| Effective Dart | <https://dart.dev/effective-dart> |
| Robert C. Martin — Clean Architecture | <https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html> |

## 10. LLM 工程参考(成本 / 缓存 / 幻觉)

- **包名幻觉(package hallucination)**:Lasso Security 2024 报告把生成式工具在 npm/PyPI 上推荐的 ~5% 包归为不存在;Flutter 等价生态是 pub.dev — `src/flutter_agent/pub_validator.py` 对此设防。
- **JSON repair pattern**:OpenAI / Anthropic 官方建议在 JSON-mode 不可用时附加 `temperature=0` 修复二次调用;`src/flutter_agent/pipeline.py` 的 `_invoke_stage` 即遵循该模式。
- **SSE 流式协议**:遵循 OpenAI Chat Completions API 流式协议;`src/flutter_agent/routes/openai_compat.py` 输出 `data: {...}` / `data: [DONE]`。

## 11. 工程交付闭环框架(fix / feature / verify / docs / deliver)

支撑 `flutter-engineering-workflow`、`flutter-feature-development`、`flutter-debugging`、`flutter-verification`、`flutter-documentation` 五个 skill 的官方/标准出处。

### 11.1 修复 / 调试(flutter-debugging)

| 主题 | 链接 |
|---|---|
| Flutter 调试总览 | <https://docs.flutter.dev/testing/debugging> |
| DevTools 总览 | <https://docs.flutter.dev/tools/devtools/overview> |
| DevTools — Performance | <https://docs.flutter.dev/tools/devtools/performance> |
| DevTools — Memory | <https://docs.flutter.dev/tools/devtools/memory> |
| `dart:developer` `log()` | <https://api.flutter.dev/flutter/dart-developer/log.html> |
| `git bisect` | <https://git-scm.com/docs/git-bisect> |

### 11.2 新增功能(flutter-feature-development)

| 主题 | 链接 |
|---|---|
| Flutter 应用架构指南 | <https://docs.flutter.dev/app-architecture> |
| 状态管理选项 | <https://docs.flutter.dev/data-and-backend/state-mgmt/options> |
| `go_router` | <https://pub.dev/packages/go_router> |
| 国际化 | <https://docs.flutter.dev/ui/accessibility-and-internationalization/internationalization> |

### 11.3 自测门禁(flutter-verification)

| 主题 | 链接 |
|---|---|
| Flutter 测试总览 | <https://docs.flutter.dev/testing/overview> |
| 集成测试 | <https://docs.flutter.dev/testing/integration-tests> |
| golden 测试 `matchesGoldenFile` | <https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html> |
| `dart format` | <https://dart.dev/tools/dart-format> |
| `dart analyze` | <https://dart.dev/tools/dart-analyze> |
| `flutter pub outdated` | <https://dart.dev/tools/pub/cmd/pub-outdated> |
| 包体积分析 | <https://docs.flutter.dev/perf/app-size> |

### 11.4 文档(flutter-documentation)

| 主题 | 链接 |
|---|---|
| Effective Dart — Documentation | <https://dart.dev/effective-dart/documentation> |
| `dart doc` 工具 | <https://dart.dev/tools/dart-doc> |
| dartdoc 写法指南 | <https://dart.dev/tools/doc-comments> |
| Keep a Changelog | <https://keepachangelog.com/> |
| Semantic Versioning | <https://semver.org/> |
| ADR(Architecture Decision Records) | <https://github.com/joelparkerhenderson/architecture-decision-record> |

### 11.5 交付规范(flutter-engineering-workflow)

| 主题 | 链接 |
|---|---|
| Conventional Commits | <https://www.conventionalcommits.org/> |

## 12. 环境 / 打包 / 性能(官方 skill 格式)

以下三个 skill 采用 [flutter/skills](https://github.com/flutter/skills) 的官方结构(Contents / Core Concepts / Workflow + Task Progress / Conditional Logic / Examples / Troubleshooting),并保留本项目加载器所需的 front-matter 字段。

### 12.1 环境(flutter-environment-setup)

| 主题 | 链接 |
|---|---|
| 安装指南 | <https://docs.flutter.dev/get-started/install> |
| Linux 桌面构建依赖 | <https://docs.flutter.dev/platform-integration/linux/building> |
| Windows 桌面构建依赖 | <https://docs.flutter.dev/platform-integration/windows/building> |
| macOS 工具链 | <https://docs.flutter.dev/platform-integration/macos/building> |
| fvm(版本管理) | <https://fvm.app> |
| CI setup-action | <https://github.com/subosito/flutter-action> |

### 12.2 打包 / 发布(flutter-build-and-release)

| 主题 | 链接 |
|---|---|
| Android 发布 | <https://docs.flutter.dev/deployment/android> |
| iOS 发布 | <https://docs.flutter.dev/deployment/ios> |
| macOS / Windows / Linux 发布 | <https://docs.flutter.dev/deployment/macos> |
| Web 发布 | <https://docs.flutter.dev/deployment/web> |
| flavors(多环境) | <https://docs.flutter.dev/deployment/flavors> |
| 代码混淆与符号 | <https://docs.flutter.dev/deployment/obfuscate> |

### 12.3 性能剖析(flutter-performance-profiling)

| 主题 | 链接 |
|---|---|
| 性能总览 | <https://docs.flutter.dev/perf> |
| 性能最佳实践 | <https://docs.flutter.dev/perf/best-practices> |
| DevTools Performance | <https://docs.flutter.dev/tools/devtools/performance> |
| 渲染性能 | <https://docs.flutter.dev/perf/rendering-performance> |
| Impeller | <https://docs.flutter.dev/perf/impeller> |
| 应用体积 | <https://docs.flutter.dev/perf/app-size> |

### 12.4 官方 skill 格式来源

| 主题 | 链接 |
|---|---|
| Flutter 官方 Agent Skills | <https://github.com/flutter/skills> |
| 官方 skill 示例(reducing-app-size) | <https://github.com/flutter/skills/blob/main/skills/flutter-reducing-app-size/SKILL.md> |

## 13. 思维蒸馏方法论(flutter-engineer-mindset)

`flutter-engineer-mindset` 用"女娲 · Skill 造人术"的五层认知操作系统(怎么说话 / 怎么想 / 怎么判断 / 什么不做 / 知道局限)与三重验证(跨领域出现 / 有预测力 / 有排他性)提炼资深 Flutter 工程师的心智模型与决策启发式;其中每条工程主张仍落到官方文档出处。

| 主题 | 链接 |
|---|---|
| 女娲 · Skill 造人术(蒸馏方法论 / 五层框架) | <https://github.com/alchaincyf/nuwa-skill> |
| 女娲 skill 模板(心智模型 / 决策启发式 / 表达 DNA / 诚实边界结构) | <https://github.com/alchaincyf/nuwa-skill/blob/main/references/skill-template.md> |
| 盒约束布局(模型 1 出处) | <https://docs.flutter.dev/ui/layout/constraints> |
| 声明式 UI(模型 3 出处) | <https://docs.flutter.dev/data-and-backend/state-mgmt/declarative> |
| 状态管理选项(模型 5 出处) | <https://docs.flutter.dev/data-and-backend/state-mgmt/options> |
| 渲染性能 / 两条线程(模型 4 出处) | <https://docs.flutter.dev/perf/rendering-performance> |
| 自适应与跨端(模型 6 出处) | <https://docs.flutter.dev/ui/adaptive-responsive> |

---

> 任何对本仓库 skill / pipeline 的修改若引入新的「最佳实践」结论,**必须**在本文档新增一行可点击的来源。否则视为未经证据支持的主张,应回退。
