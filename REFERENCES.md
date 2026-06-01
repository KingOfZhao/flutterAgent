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

## 13. 思维蒸馏方法论(flutter-engineer-mindset / flutter-skill-distillation)

`flutter-engineer-mindset` 用"女娲 · Skill 造人术"的五层认知操作系统(怎么说话 / 怎么想 / 怎么判断 / 什么不做 / 知道局限)与三重验证(跨领域出现 / 有预测力 / 有排他性)提炼资深 Flutter 工程师的心智模型与决策启发式;其中每条工程主张仍落到官方文档出处。

`flutter-skill-distillation` 把该蒸馏法**本地化为可复用的 meta-skill**:定义 Phase 1 采集 → Phase 2 三重验证 → Phase 3 构建(五层 + 本项目 front-matter)→ Phase 4 质量门禁,并提供"蒸馏指定专家(按需)"入口与花名册,使项目具备"持续造 / 更新 mindset skill"的成长性。此外,19 个领域 skill 均补有精简的"心智模型(镜片)+ 诚实边界"层,并由 `tests/test_distillation_and_lenses.py` 守护结构不退化。

### 13.1 已蒸馏专家 mindset(基于公开资料的"思维镜片",非本人)

> 反幻觉:每位专家的心智模型只取**有公开出处**的观点;`诚实边界` 明示"是镜片不是本人 + 时点快照(调研截止 2025-05)"。

| skill | 对象 | 关键出处 |
|---|---|---|
| `remi-rousselet-mindset` | Remi Rousselet(Riverpod/freezed) | <https://riverpod.dev/docs/from_provider/motivation> · <https://github.com/rrousselGit/riverpod> · <https://pub.dev/packages/freezed> |
| `felix-angelov-mindset` | Felix Angelov(Bloc/Mason) | <https://bloclibrary.dev/architecture/> · <https://github.com/felangel/bloc> · <https://verygood.ventures/blog/bloc-from-first-commit> |
| `tim-sneath-mindset` | Tim Sneath(前 Flutter/Dart 产品负责人) | <https://www.youtube.com/watch?v=kpcjBD1XDwU> · <https://blog.flutter.dev/racing-forward-at-i-o-2023-with-flutter-and-dart-df2a8fa841ab> |
| `andrea-bizzotto-mindset` | Andrea Bizzotto(Code With Andrea) | <https://codewithandrea.com/articles/flutter-app-architecture-riverpod-introduction/> · <http://bizz84.github.io/2019/05/21/wabs-practical-architecture-flutter-apps.html> |
| `filip-hracek-mindset` | Filip Hracek(前 Flutter DevRel) | <https://www.youtube.com/watch?v=d_m5csmrf7I> · <https://www.youtube.com/watch?v=RS36gBEp8OI> · <https://filiph.net/> |

| 主题 | 链接 |
|---|---|
| 女娲 · Skill 造人术(蒸馏方法论 / 五层框架) | <https://github.com/alchaincyf/nuwa-skill> |
| 女娲 skill 模板(心智模型 / 决策启发式 / 表达 DNA / 诚实边界结构) | <https://github.com/alchaincyf/nuwa-skill/blob/main/references/skill-template.md> |
| 盒约束布局(模型 1 出处) | <https://docs.flutter.dev/ui/layout/constraints> |
| 声明式 UI(模型 3 出处) | <https://docs.flutter.dev/data-and-backend/state-mgmt/declarative> |
| 状态管理选项(模型 5 出处) | <https://docs.flutter.dev/data-and-backend/state-mgmt/options> |
| 渲染性能 / 两条线程(模型 4 出处) | <https://docs.flutter.dev/perf/rendering-performance> |
| 自适应与跨端(模型 6 出处) | <https://docs.flutter.dev/ui/adaptive-responsive> |

## 14. 代码领域能力(写好 / 改好 / 养好代码)

这组 skill 强化"纯编程与代码维护"——贯穿 `flutter-engineering-workflow` 的实现全程。

### 14.1 Dart 语言地道写法(dart-language-idioms)

| 主题 | 链接 |
|---|---|
| Effective Dart 总览 | <https://dart.dev/effective-dart> |
| Effective Dart · Usage | <https://dart.dev/effective-dart/usage> |
| Effective Dart · Design | <https://dart.dev/effective-dart/design> |
| 空安全(sound null safety) | <https://dart.dev/null-safety> |
| Records | <https://dart.dev/language/records> |
| Patterns / pattern matching | <https://dart.dev/language/patterns> |
| Branches(switch 表达式) | <https://dart.dev/language/branches> |
| Class modifiers(sealed/final/base) | <https://dart.dev/language/class-modifiers> |
| Extension types | <https://dart.dev/language/extension-types> |
| `dart fix` | <https://dart.dev/tools/dart-fix> |
| Linter rules | <https://dart.dev/tools/linter-rules> |

### 14.2 代码评审(flutter-code-review)

| 主题 | 链接 |
|---|---|
| Google Eng Practices · Code Review | <https://google.github.io/eng-practices/review/> |
| 评审者:看什么 | <https://google.github.io/eng-practices/review/reviewer/looking-for.html> |
| CL 作者指南 | <https://google.github.io/eng-practices/review/developer/> |

### 14.3 安全重构(flutter-refactoring)

| 主题 | 链接 |
|---|---|
| Refactoring(Martin Fowler) | <https://refactoring.com/> |
| Strangler Fig 模式 | <https://martinfowler.com/bliki/StranglerFigApplication.html> |
| 性能最佳实践(Extract Widget/const) | <https://docs.flutter.dev/perf/best-practices> |
| Flutter App 架构 | <https://docs.flutter.dev/app-architecture> |

### 14.4 依赖养护(flutter-dependency-maintenance)

| 主题 | 链接 |
|---|---|
| 依赖管理(pub) | <https://dart.dev/tools/pub/dependencies> |
| 版本约束与解析 | <https://dart.dev/tools/pub/versioning> |
| `flutter pub outdated` | <https://dart.dev/tools/pub/cmd/pub-outdated> |
| `flutter pub upgrade` | <https://dart.dev/tools/pub/cmd/pub-upgrade> |
| Semantic Versioning | <https://semver.org/> |
| Flutter 破坏性变更索引 | <https://docs.flutter.dev/release/breaking-changes> |
| fvm(版本固定) | <https://fvm.app/> |

### 14.5 错误处理(flutter-error-handling)

| 主题 | 链接 |
|---|---|
| Flutter 错误处理 | <https://docs.flutter.dev/testing/errors> |
| `PlatformDispatcher.onError` | <https://api.flutter.dev/flutter/dart-ui/PlatformDispatcher/onError.html> |
| `FlutterError.onError` | <https://api.flutter.dev/flutter/foundation/FlutterError/onError.html> |
| Dart 异常 | <https://dart.dev/language/error-handling> |
| `logging` 包 | <https://pub.dev/packages/logging> |
| `fpdart`(Either/TaskEither) | <https://pub.dev/packages/fpdart> |

### 14.6 代码生成(flutter-codegen)

| 主题 | 链接 |
|---|---|
| `build_runner` | <https://pub.dev/packages/build_runner> |
| `source_gen` | <https://pub.dev/packages/source_gen> |
| freezed | <https://pub.dev/packages/freezed> |
| `json_serializable` | <https://pub.dev/packages/json_serializable> |
| JSON 序列化(官方指南) | <https://docs.flutter.dev/data-and-backend/serialization/json> |
| Riverpod 代码生成 | <https://riverpod.dev/docs/concepts/about_code_generation> |
| `go_router_builder` | <https://pub.dev/packages/go_router_builder> |

### 14.7 并发与隔离区(flutter-concurrency-isolates)

| 主题 | 链接 |
|---|---|
| 并发编程(isolate 模型) | <https://dart.dev/language/concurrency> |
| `Isolate.run` | <https://api.dart.dev/stable/dart-isolate/Isolate/run.html> |
| `Isolate` / Ports | <https://api.dart.dev/stable/dart-isolate/Isolate-class.html> |
| Flutter `compute` | <https://api.flutter.dev/flutter/foundation/compute.html> |
| futures / async-await | <https://dart.dev/libraries/async/async-await> |
| 渲染性能 / 帧预算 | <https://docs.flutter.dev/perf/rendering-performance> |

### 14.8 API 与包设计(dart-api-package-design)

| 主题 | 链接 |
|---|---|
| Effective Dart · Design | <https://dart.dev/effective-dart/design> |
| 创建 package | <https://dart.dev/tools/pub/create-packages> |
| package 布局约定 | <https://dart.dev/tools/pub/package-layout> |
| 发布 package | <https://dart.dev/tools/pub/publishing> |
| pubspec 格式 | <https://dart.dev/tools/pub/pubspec> |
| pub.dev 评分维度 | <https://pub.dev/help/scoring> |
| `@Deprecated` | <https://api.dart.dev/stable/dart-core/Deprecated-class.html> |

### 14.9 静态分析自动化(flutter-static-analysis)

| 主题 | 链接 |
|---|---|
| 自定义静态分析(analysis_options) | <https://dart.dev/tools/analysis> |
| `dart analyze` | <https://dart.dev/tools/dart-analyze> |
| Linter rules 全表 | <https://dart.dev/tools/linter-rules> |
| `flutter_lints` | <https://pub.dev/packages/flutter_lints> |
| `lints`(Dart 官方) | <https://pub.dev/packages/lints> |
| `very_good_analysis` | <https://pub.dev/packages/very_good_analysis> |
| `custom_lint` | <https://pub.dev/packages/custom_lint> |

### 14.10 多包 / monorepo(flutter-monorepo-melos)

| 主题 | 链接 |
|---|---|
| Pub workspaces(monorepo) | <https://dart.dev/tools/pub/workspaces> |
| melos 官网 | <https://melos.invertase.dev/> |
| melos 快速开始 | <https://melos.invertase.dev/getting-started> |
| melos 6→7 迁移(pub workspaces) | <https://melos.invertase.dev/~melos-latest/guides/migrations> |

---

## 15. 平台工程能力(PC / iOS / Android 原生与打包)

### 15.1 原生互操作(flutter-platform-channels)

| 主题 | 链接 |
|---|---|
| 平台通道(platform channels) | <https://docs.flutter.dev/platform-integration/platform-channels> |
| Pigeon(类型安全互操作) | <https://pub.dev/packages/pigeon> |
| dart:ffi(C 互操作) | <https://dart.dev/interop/c-interop> |
| ffigen(C 绑定生成) | <https://pub.dev/packages/ffigen> |
| Objective-C/Swift 互操作 | <https://dart.dev/interop/objective-c-interop> |
| Java/Kotlin 互操作(jnigen) | <https://dart.dev/interop/java-interop> |
| 开发 packages & plugins | <https://docs.flutter.dev/packages-and-plugins/developing-packages> |

### 15.2 Android 平台工程(flutter-android-platform)

| 主题 | 链接 |
|---|---|
| Android add-to-app | <https://docs.flutter.dev/add-to-app> |
| Android 构建与发布 | <https://docs.flutter.dev/deployment/android> |
| Android 权限概览 | <https://developer.android.com/guide/topics/permissions/overview> |
| 运行时权限请求 | <https://developer.android.com/training/permissions/requesting> |
| R8 收缩与混淆 | <https://developer.android.com/build/shrink-code> |
| targetSdk 与 Play 政策 | <https://developer.android.com/google/play/requirements/target-sdk> |
| App Links(深链) | <https://developer.android.com/training/app-links> |
| AGP 版本兼容 | <https://developer.android.com/build/releases/gradle-plugin> |

### 15.3 iOS/Apple 平台工程(flutter-ios-platform)

| 主题 | 链接 |
|---|---|
| iOS 构建与发布 | <https://docs.flutter.dev/deployment/ios> |
| Info.plist 信息属性键 | <https://developer.apple.com/documentation/bundleresources/information_property_list> |
| 保护用户隐私(权限) | <https://developer.apple.com/documentation/uikit/protecting_the_user_s_privacy> |
| App Transport Security | <https://developer.apple.com/documentation/security/preventing_insecure_network_connections> |
| Privacy Manifest 文件 | <https://developer.apple.com/documentation/bundleresources/privacy_manifest_files> |
| App Review Guidelines | <https://developer.apple.com/app-store/review/guidelines/> |
| Universal Links | <https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content> |
| Flutter iOS SwiftPM | <https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-app-developers> |

### 15.4 桌面平台工程(flutter-desktop-platform)

| 主题 | 链接 |
|---|---|
| 桌面支持总览 | <https://docs.flutter.dev/platform-integration/desktop> |
| 构建与发布 Windows | <https://docs.flutter.dev/deployment/windows> |
| 构建与发布 macOS | <https://docs.flutter.dev/deployment/macos> |
| 构建与发布 Linux | <https://docs.flutter.dev/deployment/linux> |
| msix 打包 | <https://pub.dev/packages/msix> |
| macOS 公证(notarytool) | <https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution> |
| AppImage / Flatpak / Snap | <https://appimage.org/> · <https://flatpak.org/> · <https://snapcraft.io/> |
| window_manager | <https://pub.dev/packages/window_manager> |

## 16. 协议能力(通信与认证授权)

### 16.1 通信协议(flutter-network-protocols)

| 主题 | 链接 |
|---|---|
| HTTP 概览(MDN) | <https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview> |
| Flutter 网络与 HTTP | <https://docs.flutter.dev/data-and-backend/networking> |
| gRPC 官方 / Dart | <https://grpc.io/docs/> · <https://grpc.io/docs/languages/dart/> |
| gRPC-Web | <https://github.com/grpc/grpc-web> |
| Protocol Buffers | <https://protobuf.dev/> |
| GraphQL / graphql_flutter | <https://graphql.org/learn/> · <https://pub.dev/packages/graphql_flutter> |
| WebSocket / web_socket_channel | <https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API> · <https://pub.dev/packages/web_socket_channel> |
| Server-Sent Events | <https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events> |
| MQTT / mqtt_client | <https://mqtt.org/> · <https://pub.dev/packages/mqtt_client> |
| TLS 1.3 / HTTP/3(RFC) | <https://datatracker.ietf.org/doc/html/rfc8446> · <https://datatracker.ietf.org/doc/html/rfc9114> |

### 16.2 认证授权协议(flutter-auth-protocols)

| 主题 | 链接 |
|---|---|
| OAuth 2.0 / RFC 6749 | <https://oauth.net/2/> · <https://datatracker.ietf.org/doc/html/rfc6749> |
| PKCE(RFC 7636) | <https://datatracker.ietf.org/doc/html/rfc7636> |
| OAuth for Native Apps(RFC 8252) | <https://datatracker.ietf.org/doc/html/rfc8252> |
| OpenID Connect | <https://openid.net/developers/how-connect-works/> |
| JWT(RFC 7519) | <https://datatracker.ietf.org/doc/html/rfc7519> · <https://jwt.io/introduction> |
| flutter_appauth | <https://pub.dev/packages/flutter_appauth> |
| flutter_secure_storage | <https://pub.dev/packages/flutter_secure_storage> |
| local_auth(生物识别) | <https://pub.dev/packages/local_auth> |
| OWASP MASVS | <https://mas.owasp.org/MASVS/> |

---

## 17. UI 识别与还原能力(设计稿/截图 → Flutter)

### 17.1 从图片还原 UI(flutter-ui-from-image)

| 主题 | 链接 |
|---|---|
| MediaQuery / 逻辑像素 | <https://api.flutter.dev/flutter/widgets/MediaQuery-class.html> |
| 自适应与响应式设计 | <https://docs.flutter.dev/ui/adaptive-responsive> |
| LayoutBuilder | <https://api.flutter.dev/flutter/widgets/LayoutBuilder-class.html> |
| Color(含 withValues) | <https://api.flutter.dev/flutter/dart-ui/Color-class.html> |
| Gradient(Linear/Radial/Sweep) | <https://api.flutter.dev/flutter/painting/Gradient-class.html> |
| BoxDecoration(渐变/阴影/圆角) | <https://api.flutter.dev/flutter/painting/BoxDecoration-class.html> |
| ShaderMask(渐变蒙版) | <https://api.flutter.dev/flutter/widgets/ShaderMask-class.html> |
| TextScaler(文字缩放) | <https://api.flutter.dev/flutter/painting/TextScaler-class.html> |
| 颜色对比度(WCAG) | <https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html> |
| flutter_screenutil(可选) | <https://pub.dev/packages/flutter_screenutil> |

### 17.2 设计 token 工程化主题(flutter-design-tokens-theming)

| 主题 | 链接 |
|---|---|
| Material 3 主题化(Flutter) | <https://docs.flutter.dev/cookbook/design/themes> |
| ThemeData | <https://api.flutter.dev/flutter/material/ThemeData-class.html> |
| ColorScheme / fromSeed | <https://api.flutter.dev/flutter/material/ColorScheme-class.html> |
| TextTheme | <https://api.flutter.dev/flutter/material/TextTheme-class.html> |
| ThemeExtension(自定义 token) | <https://api.flutter.dev/flutter/material/ThemeExtension-class.html> |
| Material Design 3 颜色系统 | <https://m3.material.io/styles/color/system/overview> |
| 自定义字体 / google_fonts | <https://docs.flutter.dev/cookbook/design/fonts> · <https://pub.dev/packages/google_fonts> |

### 17.3 设计稿→代码 playbook(flutter-design-to-code-playbook)

| 主题 | 链接 |
|---|---|
| Widget 测试入门 | <https://docs.flutter.dev/cookbook/testing/widget/introduction> |
| Golden 测试(matchesGoldenFile) | <https://api.flutter.dev/flutter/flutter_test/matchesGoldenFile.html> |
| 自适应/响应式设计 | <https://docs.flutter.dev/ui/adaptive-responsive> |

### 17.4 组件还原范例库(flutter-ui-component-recipes)

| 主题 | 链接 |
|---|---|
| Material 组件目录 | <https://docs.flutter.dev/ui/widgets/material> |
| Widget 目录总览 | <https://docs.flutter.dev/ui/widgets> |
| Material 3 组件 | <https://m3.material.io/components> |
| Cupertino 组件 | <https://docs.flutter.dev/ui/widgets/cupertino> |
| CustomPaint | <https://api.flutter.dev/flutter/widgets/CustomPaint-class.html> |

## 18. 交付:CI/CD 深化(flutter-cicd-pipelines)

| 主题 | 链接 |
|---|---|
| GitHub Actions 矩阵 | <https://docs.github.com/actions/using-jobs/using-a-matrix-for-your-jobs> |
| Actions 缓存依赖 | <https://docs.github.com/actions/using-workflows/caching-dependencies-to-speed-up-workflows> |
| Actions 环境(审批/保护) | <https://docs.github.com/actions/deployment/targeting-different-environments/using-environments-for-deployment> |
| Actions Secrets | <https://docs.github.com/actions/security-guides/encrypted-secrets> |
| 可复用 workflow | <https://docs.github.com/actions/using-workflows/reusing-workflows> |
| Flutter CI/CD 部署 | <https://docs.flutter.dev/deployment/cd> |
| Flutter flavors / dart-define | <https://docs.flutter.dev/deployment/flavors> |
| fastlane | <https://docs.fastlane.tools/> |
| subosito/flutter-action | <https://github.com/subosito/flutter-action> |

## 19. 运维:可观测性(flutter-observability)

| 主题 | 链接 |
|---|---|
| Flutter 错误处理(onError) | <https://docs.flutter.dev/testing/errors> |
| PlatformDispatcher.onError | <https://api.flutter.dev/flutter/dart-ui/PlatformDispatcher/onError.html> |
| Firebase Crashlytics(Flutter) | <https://firebase.google.com/docs/crashlytics/get-started?platform=flutter> |
| Sentry for Flutter | <https://docs.sentry.io/platforms/flutter/> |
| Firebase Performance Monitoring | <https://firebase.google.com/docs/perf-mon/get-started-flutter> |
| Firebase Analytics(Flutter) | <https://firebase.google.com/docs/analytics/get-started?platform=flutter> |
| logging 包 | <https://pub.dev/packages/logging> |
| OpenTelemetry / Dart | <https://opentelemetry.io/docs/> · <https://pub.dev/packages/opentelemetry> |
| Dart 混淆与符号 | <https://docs.flutter.dev/deployment/obfuscate> |

---

> 任何对本仓库 skill / pipeline 的修改若引入新的「最佳实践」结论,**必须**在本文档新增一行可点击的来源。否则视为未经证据支持的主张,应回退。
