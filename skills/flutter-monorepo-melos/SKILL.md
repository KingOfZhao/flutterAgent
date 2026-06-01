---
id: flutter-monorepo-melos
name: Flutter 多包/monorepo 维护 (pub workspaces + melos)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [monorepo, melos, pub-workspaces, multi-package, workspace, versioning, packages, maintenance]
applies_when: 在一个仓库里维护多个互相依赖的 Dart/Flutter package(app + 多个内部库 / 插件)
stage_hints: [architecture, breakdown]
---

# Flutter 多包 / monorepo 维护

当一个仓库里有多个互相依赖的 package(主 app + 若干内部库 / 插件),手动对每个
package `pub get`、对齐依赖版本、跑脚本会很快失控。Dart 的 **pub workspaces**(原生)
+ **melos**(编排)是治理这类 monorepo 的标准组合。本 skill 给"怎么组织、怎么联动、
怎么发版"的套路,与 `dart-api-package-design`(包设计)、`flutter-dependency-maintenance`
(依赖治理)配合。

## 0. 为什么不用一堆散 package

散在多个 package 各自管理的痛点:
- 要对每个 package 分别 `dart pub get`。
- 各 package 可能解析到**不同版本**的同一依赖,context switch 时混乱。
- IDE 打开根目录时分析器为每个 package 建独立 analysis context,体验割裂。

pub workspaces 让整个仓库**共享一次依赖解析**,解决以上问题。

## 1. pub workspaces(原生,Dart 3.6+)

根 `pubspec.yaml` 列出所有成员 package:

```yaml
# 根 pubspec.yaml
name: my_workspace
publish_to: none
environment:
  sdk: ^3.9.0          # pub workspaces 建议 3.9+ 以稳定使用
workspace:
  - packages/shared
  - packages/client_app
  - packages/server
```

每个成员 package 的 `pubspec.yaml` 声明加入 workspace:

```yaml
name: shared
environment:
  sdk: ^3.9.0
resolution: workspace
```

- 根目录一次 `dart pub get` 解析**整个 workspace**,共享一份 `.dart_tool/package_config.json`。
- 内部 package 互相依赖时,workspace 内自动用本地源,不必写 `path:` override。
- `dart analyze` / `dart test` 在整个 workspace 上下文里运行。

## 2. melos(编排层)

pub workspaces 解决依赖解析;**melos** 解决"对多个 package 批量跑命令 / 版本管理 / 发版":

```bash
dart pub global activate melos     # 全局安装
melos bootstrap                    # 初始化 workspace(链接、pub get)
melos list                         # 列出所有 package
melos run <script>                 # 跑在 melos 段里定义的脚本
melos exec -- <cmd>                # 对每个 package 执行命令
```

- **melos 7.x**:依赖 pub workspaces,**不再有 `melos.yaml`**——配置写进根 `pubspec.yaml` 的 `melos:` 段;成员 package 列表用 `workspace:` 字段。
- melos 6.x 及更早用独立 `melos.yaml` + `pubspec_overrides.yaml`;**升级到 7.x 需迁移**(见官方 migration 指南)。
- `melos analyze` 在 7.x 已移除(因为 `dart/flutter analyze` 现在能在整个 workspace 跑)。

## 3. 批量脚本(melos scripts)

在根 `pubspec.yaml` 的 `melos:` 段定义可复用脚本,统一对所有(或筛选过的)package 执行:

```yaml
melos:
  scripts:
    analyze:
      run: dart analyze .
      exec:
        concurrency: 5
    test:
      run: dart test
      packageFilters:
        dirExists: test     # 只对有 test/ 的包跑
```

- `packageFilters` 可按"是否 Flutter 包 / 是否有某目录 / 是否私有"筛选目标。
- 把 `analyze`/`test`/`format` 做成 melos 脚本,CI 一行 `melos run test` 跑全仓(见 `flutter-ci-cd`)。

## 4. 版本与发布

- melos 提供 `melos version`(按 Conventional Commits 自动 bump + 生成各包 CHANGELOG)与 `melos publish`(对可发布包发 pub)。
- 内部库遵循 SemVer 与 API 稳定性约定(见 `dart-api-package-design`);破坏性变更联动下游包一起升。
- `publish_to: none` 标记不发布的包(如主 app),避免误发。

## 5. 何时才值得上 monorepo

- 多个 package **频繁联动改动**(改库立刻在 app 验证)时收益大。
- 单一 app、没有可复用库时,monorepo 是过度工程——别为了"看起来专业"而上。

## 反模式

- ❌ 多包仓库不用 workspace,手动 `path:` 互相依赖 + 各自 `pub get`,版本飘移。
- ❌ melos 6 → 7 升级不做迁移,`melos.yaml` 与 pub workspaces 配置打架。
- ❌ 成员包不写 `resolution: workspace`,游离在 workspace 之外。
- ❌ 把不该发布的 app 包漏标 `publish_to: none`,误发到 pub。
- ❌ 单包项目硬套 monorepo,徒增结构复杂度。

## 参考 / References

- Pub workspaces(monorepo,官方):<https://dart.dev/tools/pub/workspaces>
- melos 官网:<https://melos.invertase.dev/>
- melos 快速开始:<https://melos.invertase.dev/getting-started>
- melos 6→7 迁移(pub workspaces):<https://melos.invertase.dev/~melos-latest/guides/migrations>
- pubspec 格式:<https://dart.dev/tools/pub/pubspec>
- Conventional Commits(版本联动):<https://www.conventionalcommits.org/>
- 包设计/发布见 `dart-api-package-design`;依赖治理见 `flutter-dependency-maintenance`;CI 见 `flutter-ci-cd`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **一次解析,全仓一致**:pub workspaces 的核心价值是消除跨包版本飘移。
- **workspaces 管解析,melos 管编排**:分清两者职责,别指望一个工具做全部。
- **monorepo 是手段不是目的**:只有"多包频繁联动"才值得,否则是过度工程。

**诚实边界:**

- pub workspaces 需较新 SDK(3.6+,稳定建议 3.9+);老项目升级有门槛。
- melos 6→7 是破坏性迁移,版本细节以官方 migration 文档为准。
- 这里给组织与命令骨架,具体脚本/过滤器配置随项目而定。
