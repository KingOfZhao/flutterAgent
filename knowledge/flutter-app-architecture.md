# Flutter 应用架构分层(向量库优质语料·轮1)

> 用途:为"项目结构/分层/repository/MVVM/clean architecture"类需求提供检索接地语料。来源见 REFERENCES §26。

## 1. 官方推荐:两层起步,按需加层

Flutter 官方架构指南(2024)推荐 **UI 层 + Data 层** 的 MVVM 变体:

- **UI 层** = View(widget,只描述界面)+ ViewModel(持有 UI 状态、暴露命令,
  不直接碰网络/数据库);
- **Data 层** = Repository(单一事实源,负责缓存/合并/重试等业务数据策略)
  + Service(对 API/插件的最薄封装,无状态);
- **Domain 层是可选的**:只有当多个 ViewModel 重复同一段业务逻辑时才抽 use-case,
  一开始就上完整 clean architecture 是小项目最常见的过度工程。

## 2. 目录组织:feature-first 优于 layer-first

- layer-first(`lib/views/`、`lib/models/` 全局分桶)在功能变多后,改一个功能
  要横跨所有目录——官方与社区主流实践都推荐 **feature-first**:
  `lib/features/<feature>/{ui,data,domain}`,公共物放 `lib/core/` 或 `lib/shared/`。
- 判断目录健康度的启发式:删除一个 feature 应该≈删除一个目录。

## 3. 依赖规则(分层的实质)

- 依赖只能向下:UI → (Domain) → Data;Repository 不 import widget,
  Service 不 import Repository。违反方向的 import 是腐化的最早信号,
  可用 `dart analyze` 自定义 lint 或 import 检查工具守护。
- ViewModel 不持有 BuildContext;导航/弹窗通过回调或事件流出,否则无法纯 Dart 测试。
- 单一事实源:同一业务数据只允许一个 Repository 拥有,UI 不得绕过 Repository
  直连 Service——绕过的那一刻,缓存一致性与离线策略就失效了。

## 4. 与本仓库其他语料的衔接

- 状态管理方案放在 ViewModel 槽位(见 flutter-state-management);
- Repository 是离线同步策略的安放点(见 flutter-offline-sync §2);
- 分层的直接回报是可测性:ViewModel/Repository 纯 Dart 单测(见 flutter-testing-strategy §2)。
