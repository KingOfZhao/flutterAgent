---
id: dart-mcp-server
name: Dart MCP Server 接入与调用 (dart_mcp 框架 + dart_mcp_server 工具全集 / Claude Code 配置 / 自定义 server 构建)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [mcp, dart-mcp, dart-mcp-server, tooling, analyzer, pub, testing, code-generation, server, claude-code]
applies_when: 需要通过 Dart MCP Server 为 AI 编码助手提供 Dart/Flutter 项目分析、测试、包管理、格式化等工具能力时；或需要基于 dart_mcp 框架构建自定义 MCP server 时
stage_hints: [architecture, breakdown, implementation, acceptance]
see_also: [mcp-toolchain-integration, flutter-verification, flutter-testing, flutter-code-review, flutter-dependency-maintenance, flutter-debugging, flutter-static-analysis]
---

# Dart MCP Server 接入与调用

> 分工:本 skill 负责 **Dart MCP Server 的架构理解、安装配置、工具全集与调用模式**，
> 以及基于 `dart_mcp` 框架**构建自定义 MCP server**。
> 通用 MCP 选型/密钥安全/多 server 节制见 `mcp-toolchain-integration`；
> 接入后的验证门禁见 `flutter-verification`。

> 核心原则:**Dart MCP Server 是把 `dart`/`flutter` CLI 的开发者工具能力以 MCP 协议暴露给 AI 助手**，
> 让模型能直接分析代码、跑测试、搜包、格式化，而不是通过 Bash 盲敲命令再解析输出。

---

## 1. 架构概览：两层设计

`dart-lang/ai` 仓库包含两层，理解这个分层是用好整个体系的前提：

```
┌─────────────────────────────────────────┐
│  dart_mcp_server (具体 server)           │
│  - 随 Dart SDK 发布，dart mcp-server 启动  │
│  - 注册具体工具：analyzer / test / pub... │
│  - stdio transport，与 AI 客户端通信       │
├─────────────────────────────────────────┤
│  dart_mcp (框架 SDK)                     │
│  - pub.dev/packages/dart_mcp (v0.5.x)   │
│  - 基类：MCPServer / ToolsSupport /      │
│    ResourcesSupport / PromptsSupport     │
│  - 用于构建自定义 MCP server              │
└─────────────────────────────────────────┘
```

| 层 | 是什么 | 谁用 | 发布渠道 |
|---|--------|------|---------|
| `dart_mcp` | MCP 协议 Dart SDK 框架 | 构建自定义 server 的开发者 | pub.dev |
| `dart_mcp_server` | 官方 Dart/Flutter 工具 MCP server | 所有 Dart/Flutter 开发者 | 随 Dart SDK 内置 |

---

## 2. 安装与启动

### 2.1 内置方式(Dart SDK ≥ 3.6)

`dart_mcp_server` 随 Dart SDK 一起发布，直接运行：

```bash
dart mcp-server
# 默认 stdio transport，等待客户端连接
```

验证可用：

```bash
dart mcp-server --help
```

### 2.2 源码激活方式(尝鲜 / 自定义)

```bash
dart pub global activate -s git https://github.com/dart-lang/ai.git \
  --git-path pkgs/dart_mcp_server/
```

### 2.3 开发调试：MCP Inspector

```bash
npx @modelcontextprotocol/inspector
# 在 Inspector UI 中配置 command: dart, args: [mcp-server]
```

---

## 3. 客户端配置

### 3.1 Claude Code

```bash
claude mcp add --transport stdio dart -- dart mcp-server
```

或手动编辑 `~/.claude/mcp.json` 或项目级 `.claude/mcp.json`：

```jsonc
{
  "mcpServers": {
    "dart": {
      "command": "dart",
      "args": ["mcp-server"]
    }
  }
}
```

### 3.2 Cursor

编辑 `~/.cursor/mcp.json`(全局) 或 `.cursor/mcp.json`(项目级)：

```jsonc
{
  "mcpServers": {
    "dart": {
      "command": "dart",
      "args": ["mcp-server"]
    }
  }
}
```

### 3.3 VS Code / VS Code Copilot

在 `settings.json` 中启用：

```jsonc
{
  "dart.mcpServer": true
}
```

### 3.4 Gemini CLI

编辑 `~/.gemini/settings.json`：

```jsonc
{
  "mcpServers": {
    "dart": {
      "command": "dart",
      "args": ["mcp-server"]
    }
  }
}
```

### 3.5 通用：手动验证连接

```bash
# 确认 server 能启动并响应
echo '{"jsonrpc":"2.0","id":1,"method":"initialize","params":{"protocolVersion":"2024-11-05","capabilities":{},"clientInfo":{"name":"test","version":"1.0"}}}' | dart mcp-server 2>/dev/null | head -1
```

### 3.6 Roots 配置

当客户端不自动设置 project roots 时，用 `--force-roots-fallback` 降级：

```bash
dart mcp-server --force-roots-fallback
```

Roots 影响 analyzer 的分析范围、测试发现等行为。如果工具调用返回空结果或不完整，先检查 roots 是否覆盖了项目目录。

---

## 4. 工具全集(按能力域分组)

> 工具列表随 Dart SDK 版本持续增长，以下为当前已知工具。
> 接入后先跑 `tools/list` 确认实际可用工具集。

### 4.1 代码分析与诊断

| 工具 | 功能 | 关键参数 | Flutter 工作流对应 |
|------|------|---------|-------------------|
| `analyze` / `analysis_errors` | 获取项目静态分析错误 | `roots`(可选,限定分析范围) | 替代 `flutter analyze` 的手工解析 |
| `resolve_symbol` | 解析符号到定义位置与文档 | `symbol`(符号名), `uri`(文件) | 理解陌生代码库的符号含义 |
| `get_documentation` | 获取符号/库的 API 文档 | `symbol`/`uri` | 查 API 签名，不需要切浏览器 |
| `signature_help` | 获取函数/构造函数的签名信息 | `symbol`, `uri`, `position` | 补全参数列表 |

**调用模式**：

```
改完代码 → analysis_errors 扫描 → 有错则定位修复 → 再扫描确认归零
理解陌生符号 → resolve_symbol 查定义 → get_documentation 查用法
```

**注意**：
- `analysis_errors` 返回的是当前 workspace 的状态，不是整个仓库；修改未保存或 roots 不对会导致"0 error"误判。
- 结合 `flutter-static-analysis` 中的 lint 规则理解错误含义。

### 4.2 测试执行

| 工具 | 功能 | 关键参数 |
|------|------|---------|
| `run_tests` / `run_test` | 运行指定测试文件或目录 | `paths`(测试文件/目录路径), `pattern`(按名称过滤) |
| `test_results` / `get_test_results` | 获取最近一次测试结果 | — |

**调用模式**：

```
写测试 → run_tests(paths: ["test/xxx_test.dart"]) → 红 → 修代码 → run_tests 再跑 → 绿
CI 失败 → test_results 拉取本地复现 → 定位 → 修复
```

**注意**：
- 优先指定具体测试文件路径而非跑全量，减少等待时间。
- 测试失败后的结果里包含 stack trace，结合 `resolve_symbol` 回溯调用链。
- 测试编写规范见 `flutter-testing`。

### 4.3 包管理(pub.dev)

| 工具 | 功能 | 关键参数 | 典型用法 |
|------|------|---------|---------|
| `pub_dev_search` | 搜索 pub.dev 上的包 | `query`(搜索词) | "找一个做视频压缩的包" → `pub_dev_search(query: "video compression")` |
| `add_dependency` | 添加依赖到 pubspec.yaml | `package`(包名), `version`(可选,默认 latest) | 搜索结果确定后直接添加 |
| `remove_dependency` | 从 pubspec.yaml 移除依赖 | `package`(包名) | 清理不再使用的包 |
| `list_dependencies` / `get_dependencies` | 列出当前项目依赖(含传递依赖) | — | 审计依赖树 |

**调用模式**：

```
需求：需要功能X → pub_dev_search(query: "X") → 评估搜索结果(下载量/更新日期/平台支持/空安全)
  → add_dependency(package: "selected_pkg") → flutter pub get → analysis_errors 确认无冲突
```

**注意**：
- `pub_dev_search` 结果是摘要而非全文，关键决策(如选型)仍需人工浏览 pub.dev 页面确认。
- 添加依赖后必跑 `analysis_errors` 确认版本解析无冲突。
- 依赖健康度三问见 `flutter-dependency-maintenance`。

### 4.4 代码格式化

| 工具 | 功能 | 关键参数 |
|------|------|---------|
| `format` / `format_code` | 用 `dart format` 格式化指定文件或整个项目 | `paths`(可选,默认 workspace) |

**调用模式**：

```
写完代码 → format 格式化 → analysis_errors 确认 → 提交
```

### 4.5 运行中应用交互(调试期)

| 工具 | 功能 | 前置条件 |
|------|------|---------|
| `hot_reload` | 触发 Flutter hot reload | 应用正在调试模式运行 |
| `hot_restart` | 触发 Flutter hot restart(全量重建) | 应用正在调试模式运行 |
| `get_selected_widget` | 获取 DevTools 中当前选中的 widget 树信息 | DevTools 已连接 |
| `get_runtime_errors` | 获取运行时的未捕获异常 | 应用正在运行且有错误 |
| `get_widget_tree` | 获取当前 widget 树结构 | 应用正在调试模式运行 |

**调用模式**：

```
改 UI → hot_reload → 目测效果 → 不对 → get_runtime_errors 查错
widget 布局异常 → get_widget_tree 看树结构 → 定位嵌套层级不对的节点
选中异常 widget → get_selected_widget 查属性值 → 发现 padding/color 写错
```

**注意**：
- 这些工具依赖 Flutter 调试会话，非调试期调用会失败。
- `get_widget_tree` 返回的是简化树，深层嵌套可能被截断。

### 4.6 项目 Roots 管理

| 工具 | 功能 |
|------|------|
| `list_roots` | 列出当前 server 已知的项目根目录 |
| `add_root` | 添加项目根目录 |
| `remove_root` | 移除项目根目录 |

**调用时机**：monorepo(Melos)多包场景下，工具调用只命中默认 root 时，手动添加子包目录。

---

## 5. 工作流集成模式

### 5.1 标准开发循环(接 Dart MCP Server)

```
                    ┌──────────────────────────┐
                    │  1. 写/改代码              │
                    └──────────┬───────────────┘
                               ↓
                    ┌──────────────────────────┐
                    │  2. format 格式化          │  ← Dart MCP: format
                    └──────────┬───────────────┘
                               ↓
                    ┌──────────────────────────┐
                    │  3. analysis_errors 静态检 │  ← Dart MCP: analysis_errors
                    │     0 error? → 继续        │
                    │     有错 → 回到 1           │
                    └──────────┬───────────────┘
                               ↓
                    ┌──────────────────────────┐
                    │  4. run_tests 跑相关测试    │  ← Dart MCP: run_tests
                    │     全绿? → 继续            │
                    │     有红 → 回到 1           │
                    └──────────┬───────────────┘
                               ↓
                    ┌──────────────────────────┐
                    │  5. 提交                   │
                    └──────────────────────────┘
```

### 5.2 依赖引入决策链

```
需求 → pub_dev_search(query) → 候选列表
  → 对每个候选：下载量/最近更新/Likes/平台标签/空安全
  → 锁定 1-2 个 → add_dependency → flutter pub get
  → analysis_errors 确认无版本冲突
  → 写最小可用代码验证 API 符合预期
  → 提交 pubspec.yaml + pubspec.lock
```

### 5.3 调试期快速迭代

```
改代码 → hot_reload(秒级) → 效果不对
  → get_runtime_errors 查异常
  → 定位出错 widget → get_selected_widget 查属性
  → 修代码 → hot_reload → 确认修复
```

### 5.4 陌生代码库理解

```
打开陌生项目 → list_roots 确认分析范围
  → 遇到未知符号 → resolve_symbol(符号名) 查定义
  → get_documentation 读 API 文档
  → analysis_errors 了解当前项目的质量状态
  → run_tests 确认测试基线
```

---

## 6. 基于 dart_mcp 构建自定义 MCP Server

> 当 Dart MCP Server 的工具不满足需求时(如内部工具集成、自定义工作流)，
> 用 `dart_mcp` 框架构建自己的 MCP server。

### 6.1 最小可用 server

```dart
import 'dart:async';
import 'package:dart_mcp/server.dart';

final class MyServer extends MCPServer with ToolsSupport {
  MyServer(super.channel) : super.fromStreamChannel();

  @override
  FutureOr<InitializeResult> initialize(InitializeRequest request) {
    // 1. 必须先调用 super.initialize() 建立协议处理器
    final result = super.initialize(request);

    // 2. 注册工具
    registerTool(
      Tool(
        name: 'greet',
        description: '返回问候语',
        inputSchema: Schema.object(
          properties: {
            'name': Schema.string(
              title: '名字',
              description: '要问候的人的名字',
            ),
          },
          required: ['name'],
        ),
      ),
      (request) => CallToolResult(
        content: [TextContent(text: 'Hello, ${request.arguments!['name']}!')],
      ),
    );

    return result;
  }
}

void main() {
  // stdio transport:从 stdin 读取 JSON-RPC，写到 stdout
  serveMCPServer(
    (channel) => MyServer(channel),
    transport: StdioServerTransport(),
  );
}
```

### 6.2 核心 API 速查

#### MCPServer 基类

```dart
base class MCPServer {
  // 生命周期
  FutureOr<void> get initialized;   // 握手完成
  bool get ready;                    // 未关闭 + 已初始化

  // 必须重写
  FutureOr<InitializeResult> initialize(InitializeRequest request);

  // 可重写
  void handleInitialized(InitializedNotification notification);
  Future<void> done;                 // 连接关闭时 complete
}
```

#### ToolsSupport mixin

```dart
base mixin ToolsSupport on MCPServer {
  // 注册工具 + 处理器
  void registerTool(
    Tool tool,
    FutureOr<CallToolResult> Function(CallToolRequest) impl, {
    bool validateArguments = true,   // 默认：自动校验参数 schema
  });

  // 移除工具(运行时可动态增删)
  void unregisterTool(String name);
}
```

- `tools/list` 和 `tools/call` 由 mixin 自动处理，不需要手动实现。
- `validateArguments: true`(默认)时，参数不符合 `inputSchema` 会在到达 handler 前被拒绝。
- 初始化后注册/移除工具会自动发 `ToolListChangedNotification` 通知客户端。

#### Tool 定义

```dart
Tool({
  required String name,                    // 唯一名称
  String? description,                     // 给 AI 看的描述(影响调用准确率)
  InputSchema? inputSchema,                // JSON Schema 参数定义
  ToolAnnotations? annotations,            // title / readOnlyHint / destructiveHint
})
```

#### ResourcesSupport mixin(提供只读数据)

```dart
base mixin ResourcesSupport on MCPServer {
  void registerResource(Resource resource, ReadResourceHandler handler);
  void unregisterResource(Uri uri);
}
```

```dart
Resource({
  required Uri uri,
  required String name,
  String? description,
  String? mimeType,
})
```

#### PromptsSupport mixin(提供 prompt 模板)

```dart
base mixin PromptsSupport on MCPServer {
  void registerPrompt(Prompt prompt, GetPromptHandler handler);
  void unregisterPrompt(String name);
}
```

### 6.3 自定义 server 的输入输出

#### 返回结构化内容

```dart
CallToolResult(
  content: [
    TextContent(text: '文本结果'),
    ImageContent(data: base64Bytes, mimeType: 'image/png'),
    EmbeddedResource(...),  // 引用已注册的 resource
  ],
  isError: false,
)
```

#### Schema 构建(类型安全的参数定义)

```dart
// 简单类型
Schema.string(title: 'Label', description: '...', enumValues: ['a', 'b']);
Schema.number(title: 'Count', minimum: 0, maximum: 100);
Schema.boolean(title: 'Flag');
Schema.object(properties: {...}, required: [...]);

// 数组
Schema.array(items: Schema.string());

// 联合类型
Schema.anyOf([Schema.string(), Schema.number()]);
```

### 6.4 实战模式：包装 CLI 为 MCP 工具

最常见的自定义 server 需求：把团队内部的 CLI 工具包装成 MCP 工具。

```dart
registerTool(
  Tool(
    name: 'run_codegen',
    description: '运行项目的代码生成(build_runner)',
    inputSchema: Schema.object(
      properties: {
        'watch': Schema.boolean(
          title: '持续监听',
          description: '是否以 watch 模式运行',
        ),
      },
    ),
  ),
  (request) async {
    final watch = request.arguments?['watch'] == true;
    final args = ['run', 'build_runner', 'build', '--delete-conflicting-outputs'];
    if (watch) args.add('--watch');

    final result = await Process.run('dart', args);
    return CallToolResult(
      content: [TextContent(text: result.stdout.toString())],
      isError: result.exitCode != 0,
    );
  },
);
```

### 6.5 调试与发布

```bash
# 本地调试(MCP Inspector)
npx @modelcontextprotocol/inspector

# 全局激活
dart pub global activate --source path .
# 或发布到 pub.dev 后
dart pub global activate my_mcp_server

# 在客户端配置
# {"command": "dart", "args": ["run", "my_mcp_server"]}
# 或全局激活后
# {"command": "my_mcp_server"}
```

---

## 7. 与其他 skill 的协作

| 场景 | 主要 skill | Dart MCP Server 的角色 |
|------|-----------|----------------------|
| 改完代码自测 | `flutter-verification` | 提供 `format` → `analysis_errors` → `run_tests` 的自动化执行 |
| 写测试 | `flutter-testing` | `run_tests` 快速反馈红/绿，`analysis_errors` 检查测试代码质量 |
| 引入新依赖 | `flutter-dependency-maintenance` | `pub_dev_search` + `add_dependency` 自动化搜索与添加 |
| Code Review | `flutter-code-review` | `analysis_errors` 提供静态诊断数据作为 review 输入 |
| 调试 | `flutter-debugging` | `get_runtime_errors` + `get_widget_tree` + `hot_reload` 加速定位 |
| 静态分析规则 | `flutter-static-analysis` | `analysis_errors` 执行 lint 规则检查 |
| MCP 多 server 管理 | `mcp-toolchain-integration` | 作为工具链中的核心 server，负责 Dart/Flutter 侧所有工具能力 |

---

## 反模式

- ❌ 把 Dart MCP Server 当万能工具：它覆盖代码→测试→依赖→格式闭环，但设计稿取数(Figma)、浏览器验证(Playwright)、PR 协作(GitHub)仍需其他 MCP server。
- ❌ `analysis_errors` 返回 0 error 就认为代码没问题——静态分析通过 ≠ 逻辑正确，还要跑测试。
- ❌ `pub_dev_search` 结果不人工确认直接 `add_dependency`——搜索摘要可能过时，包的质量、兼容性仍需人工判断。
- ❌ 每改一行就 `run_tests` 跑全量测试——浪费时间和 token，先跑相关测试文件，最后跑全量。
- ❌ 不检查 roots 配置就开始调工具——roots 不对会导致 analyzer 分析范围错误，搜索结果为空。
- ❌ 自定义 server 时在 handler 里放长时间阻塞操作(如 `Process.run` 等 CI)——MCP 协议期望快速响应，长任务用通知机制。
- ❌ 自定义 server 的 `Tool.description` 写得太模糊——AI 靠描述选择工具，描述不准直接导致调用错误工具。
- ❌ `get_widget_tree` / `get_runtime_errors` 在非调试期反复调用——这些工具依赖运行中的调试会话。
- ❌ 把 `dart_mcp_server` 和 `dart_mcp` 框架搞混——前者是现成的工具集，后者是构建框架，需求不同选型不同。

---

## 参考 / References

- dart-lang/ai 仓库(含 dart_mcp + dart_mcp_server):<https://github.com/dart-lang/ai/tree/main/pkgs>
- dart_mcp SDK 文档(pub.dev):<https://pub.dev/packages/dart_mcp>
- Dart MCP Server 官方文档:<https://dart.dev/tools/mcp-server>
- Flutter AI MCP 文档:<https://docs.flutter.dev/ai/mcp-server>
- MCP 协议规范:<https://modelcontextprotocol.io/>
- MCP Inspector 调试:<https://github.com/modelcontextprotocol/inspector>
- 通用 MCP 选型/安全/配置见 `mcp-toolchain-integration`
- 接入后验证门禁见 `flutter-verification`
- 测试编写规范见 `flutter-testing`
- 依赖管理决策见 `flutter-dependency-maintenance`
- 静态分析规则见 `flutter-static-analysis`

---

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **Dart MCP Server 是 CLI 的语义化代理**：它把 `dart analyze` / `flutter test` 等命令的机器可读输出，以结构化 MCP 协议暴露给 AI，减少模型对 CLI 文本输出的解析负担。
- **框架与工具的分层思考**：`dart_mcp`(框架)解决"怎么建 MCP server"，`dart_mcp_server`(产品)解决"Dart/Flutter 开发需要哪些工具能力"。用现成工具不满足时才考虑自定义 server。
- **一个工具一次调用，一个阶段一个闭环**：format → analyze → test 是顺序依赖的，不要并行瞎调。
- **tool description 是 AI 的"API 文档"**：自定义 server 时，description 的质量直接决定模型能否在正确时机选择正确工具。

**诚实边界:**

- 工具列表随 Dart SDK 版本变化，以 `tools/list` 实际返回为准；本 skill 提供的是当前已知工具集框架。
- `dart_mcp` 框架仍为 experimental(截至 2026 年)，API 可能 breaking change；生产级自定义 server 需锁定版本。
- 运行中应用交互工具(`hot_reload`/`get_widget_tree` 等)依赖 Flutter 调试会话，非调试场景不可用。
- `pub_dev_search` 的结果质量取决于 pub.dev 搜索 API，不保证语义搜索精度。
- 本 skill 不替代各客户端(Cursor/Claude Code/VS Code)各自的 MCP 配置文档，只提供通用配置模板。
