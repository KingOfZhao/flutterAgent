---
id: flutter-dependency-maintenance
name: Flutter 依赖养护 (pub upgrade / 破坏性升级 / SDK 迁移 / dart fix)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [dependencies, pub, upgrade, migration, maintenance, semver, dart-fix, outdated, lockfile]
applies_when: 升级/收敛依赖、处理破坏性升级、迁移 SDK 版本、解决版本冲突
stage_hints: [breakdown, acceptance]
---

# Flutter 依赖养护

依赖不养护就会"腐烂":过时的包带着已知漏洞、与新 SDK 不兼容、阻塞其他升级。
养护的目标是**持续小步升级**而非攒到"大爆炸式迁移"。本 skill 给一套
看清现状→分级升级→验证→记录的流程,是 `flutter-engineering-workflow` 里
"升级依赖"这类任务的专用 SOP。升级后的验证门禁见 `flutter-verification`。

## 0. 先看清现状

```bash
flutter pub outdated     # 列出每个包: 当前 / 可升(兼容) / 最新(可能破坏)
dart pub deps            # 看依赖树,定位是谁拉进了某个传递依赖
```

`pub outdated` 三列要会读:
- **Current**:你现在锁定的版本(`pubspec.lock`)。
- **Upgradable**:在 `pubspec.yaml` 约束内能升到的最高版本(安全)。
- **Resolvable / Latest**:放宽约束后能到的最新版(可能含破坏性变更)。

## 1. 分级升级(从安全到有风险)

1. **补丁/次版本(SemVer 兼容)**:`flutter pub upgrade` 在现有约束内升,跑测试,基本无风险。
2. **主版本(可能破坏)**:`flutter pub upgrade --major-versions` 会改写 `pubspec.yaml` 约束。**一次只升一个或一组相关包**,逐个验证,别一把全升导致无法定位是谁炸的。
3. 升级前**必读该包的 CHANGELOG / migration guide**,尤其主版本号变化(SemVer 里 major bump = 有破坏性变更)。

## 2. 版本约束与锁文件

- `pubspec.yaml` 用 **caret 约束** `^1.2.3`(允许 `>=1.2.3 <2.0.0`),既拿补丁又挡破坏性主版本。
- `pubspec.lock` **应提交**(应用类项目),保证团队/CI 构建可复现;**库(package)类项目**通常不提交 lock。
- 解决冲突时用 `dependency_overrides` 是**临时**手段,要留 TODO 并尽快回归正常约束——长期 override 会掩盖真实不兼容。

## 3. SDK / Flutter 版本迁移

- 用 **fvm** 固定项目 Flutter 版本(见 `flutter-environment-setup`),团队一致、可复现。
- 升 Dart/Flutter 大版本前看官方 **release notes / breaking changes** 与 **migration guide**。
- `dart fix --apply` 自动套用很多 SDK 迁移与废弃 API 替换:
  ```bash
  dart fix --dry-run     # 先看会改什么
  dart fix --apply       # 套用
  ```
- 升级后 `flutter analyze` 找剩余的废弃 API(`deprecated`),按提示替换。

## 4. 引入新依赖的判据(反幻觉)

加一个包前确认(与 `architecture-design` 一致):
- pub.dev **可查**、**活跃维护**(近期有更新、issue 有响应)、**非 `discontinued`**。
- 协议(license)合规;包评分 / popularity 可作参考但非唯一标准。
- 真的需要吗?几十行能自己写的别为此引入一个传递依赖一大坨的包。
- 平台支持覆盖你的目标平台(mobile/desktop/web)。

## 5. 安全与健康

- 关注依赖的已知漏洞(包的 changelog / GitHub advisory);敏感项目定期审计。
- `flutter pub outdated` 设为定期任务(或 CI 周期跑),别让债越积越多。
- 移除不再使用的依赖——每个依赖都是维护成本与攻击面。

## 6. 升级后的验证(必须)

```bash
flutter pub get
dart format --output=none --set-exit-if-changed .
flutter analyze                 # 0 error;关注新出现的 deprecated
flutter test --coverage         # 行为不应回归
flutter build apk --debug       # 或对应平台,确认仍可编译
```

- 任一红了就停下排查;主版本升级尤其要手动冒烟核心路径。
- 记录:用户可见行为/依赖变化写进 `CHANGELOG`(见 `flutter-documentation`),破坏性升级在 PR 标 `BREAKING`。

## 反模式

- ❌ 一次 `--major-versions` 全升,炸了无法定位是哪个包。
- ❌ 不读 CHANGELOG 就升主版本,被破坏性变更打个措手不及。
- ❌ 用 `dependency_overrides` 长期压冲突,掩盖真实不兼容。
- ❌ 应用类项目不提交 `pubspec.lock`,导致"我这能跑、CI 不行"。
- ❌ 为一点点功能引入庞大或废弃的包。

## 参考 / References

- 依赖版本管理(pub):<https://dart.dev/tools/pub/dependencies>
- 版本约束与解析:<https://dart.dev/tools/pub/versioning>
- `flutter pub outdated`:<https://dart.dev/tools/pub/cmd/pub-outdated>
- `flutter pub upgrade`:<https://dart.dev/tools/pub/cmd/pub-upgrade>
- `dart fix`:<https://dart.dev/tools/dart-fix>
- Semantic Versioning:<https://semver.org/>
- 升级 Flutter 与破坏性变更索引:<https://docs.flutter.dev/release/breaking-changes>
- fvm(版本固定):<https://fvm.app/>
- 验证门禁见 `flutter-verification`;新依赖判据见 `architecture-design`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **持续小步胜过大爆炸**:常态化升级让每次 diff 小、可定位;攒大了就成迁移地狱。
- **主版本号 = 破坏性信号**:SemVer 下 major bump 必读迁移说明,别假设兼容。
- **每个依赖都是负债**:能不加就不加,不用了就删——它是维护成本和攻击面。

**诚实边界:**

- `dart fix` 只能自动改"工具知道怎么改"的部分,复杂迁移仍需人工。
- 升级能否成功受传递依赖牵制,有时被卡在某个未更新的包上,需权衡等待 vs 替换。
- 安全审计这里只给入口,合规/漏洞细节以官方 advisory 为准。
