---
id: mcp-toolchain-integration
name: MCP 工具链接入 (免费 server 选型 / 配置模式 / 密钥安全 / 验证与节制)
version: 1.0.0
platforms: [all]
tags: [mcp, tooling, integration, dart-mcp, figma, context7, github, playwright, server, token, 工具链]
applies_when: 需要为编码工作流接入/配置 MCP server(文档查询、设计稿取数、Dart 工具、浏览器自动化、仓库操作)时
stage_hints: [architecture, breakdown, implementation]
see_also: [flutter-figma-mcp, dart-mcp-server, flutter-verification, dev-problem-log]
---

# MCP 工具链接入

> 分工:本 skill 负责 **MCP server 的选型、配置、密钥安全与验证**。
> Figma 取数的领域方法见 `flutter-figma-mcp`;接入后的产出验证纪律见 `flutter-verification`。

> 核心原则:**每接一个 server 都要回答"它替代了哪个手工步骤"**。
> MCP 不是越多越好——每个 server 的工具描述都占上下文,接而不用是纯负担。

---

## 1. 免费 server 选型(按 Flutter 工作流价值排序)

| Server | 解决什么 | 接入成本 | 凭证 |
|--------|---------|---------|------|
| **Dart MCP Server**(官方) | analyzer 诊断、跑测试、pub 管理、hot reload | `dart mcp-server` 即起 | 无 |
| **Framelink Figma MCP** | Figma 节点/样式精确取数(见 `flutter-figma-mcp`) | npx 一行 | Figma PAT(只读) |
| **Context7** | 实时库文档,治"模型记忆里的过期 API" | npx / 远端 | 免费 API key |
| **GitHub MCP**(官方) | PR / issue / CI 状态操作 | 远端或 docker | GitHub token |
| **Playwright MCP**(微软) | 浏览器自动化,验证 Flutter Web 产物 | npx | 无 |
| **官方参考 servers** | filesystem / git / fetch 基础能力 | npx | 无 |

选型判据:

- 优先**官方/一方维护**的 server(Dart/GitHub/Playwright),社区 server 看维护活跃度与下载量再上。
- 客户端已内置的能力(文件读写、终端、搜索)**不要**再接同类 server 重复占上下文。
- 一个工作流阶段一个 server:文档→Context7,设计→Figma,执行→Dart,验证→Playwright,协作→GitHub。

## 2. 配置模式

### 2.1 stdio 型(本地进程,最常见)

```jsonc
// mcp 配置文件(各客户端路径不同:Windsurf/Cursor/Claude 各有约定)
{
  "mcpServers": {
    "dart": { "command": "dart", "args": ["mcp-server"] },
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": { "FIGMA_API_KEY": "${env:FIGMA_API_KEY}" }   // 引环境变量,不写裸值
    },
    "playwright": { "command": "npx", "args": ["-y", "@playwright/mcp@latest"] }
  }
}
```

### 2.2 SSE / 远端型

- 本地 SSE:如 Figma Dev Mode MCP(`http://127.0.0.1:3845/sse`,需桌面端开启)。
- 远端托管:如 GitHub 官方远端 server——免本地进程,但凭证经过第三方,敏感仓库自行评估。

### 2.3 通用注意

- `npx -y` 方式每次解析最新版,**CI/团队环境锁版本**(`figma-developer-mcp@x.y.z`),避免上游 breaking change 静默炸配置。
- server 进程的 stdout 即协议通道,自写 server 时日志必须走 stderr。

## 3. 密钥安全(红线)

- 凭证只放**环境变量**或客户端的 secret 管理,配置文件里用 `${env:...}` 引用;含裸 token 的 mcp.json **绝不提交仓库**(`.gitignore` 兜底)。
- 按最小权限申请:Figma PAT 只读 scope;GitHub token 只勾需要的仓库与权限。
- token 等同于其账号的可见范围,泄漏即全量泄漏;定期轮换,离项目即吊销。

## 4. 接入后验证

每接一个 server,做一次冒烟:

1. 客户端能列出该 server 的工具(连接成功)。
2. 跑一个最小真实调用(如 Dart MCP 跑一个测试、Figma 取一个已知 node)。
3. 故意给错凭证确认失败信息可读——避免线上排错时盲猜。

失败排查顺序:命令本身可在终端手动跑通 → env 是否传入 → 客户端日志看握手错误。
工具调用产出仍要走 `flutter-verification` 的门禁,MCP 不豁免验证。

## 5. 节制与维护

- **工具总数控制**:server 多了之后模型选错工具的概率上升;不活跃的 server 及时下线。
- 每个 server 在团队文档里记一行:用途 / 凭证来源 / 锁定版本 / 负责人。
- 接入中踩的坑按 `dev-problem-log` 记录,积累后回灌本 skill。

## 反模式

- ❌ 接一堆 server "备着",一个月没调用过一次——纯上下文负担。
- ❌ mcp.json 里写裸 token 并提交仓库。
- ❌ 用 MCP 重复客户端已内置的能力(文件读写/终端)。
- ❌ `npx -y` 不锁版本直接进 CI。
- ❌ 接入后从不冒烟,出问题时分不清是 server 挂了还是凭证错了。
- ❌ 把 MCP 工具的输出当真相直接交付,跳过验证门禁。

## 参考 / References

- MCP 规范:<https://modelcontextprotocol.io/>
- Dart MCP Server(官方):<https://dart.dev/tools/mcp-server>
- Framelink Figma MCP:<https://github.com/GLips/Figma-Context-MCP>
- Context7:<https://github.com/upstash/context7>
- GitHub MCP Server(官方):<https://github.com/github/github-mcp-server>
- Playwright MCP(微软):<https://github.com/microsoft/playwright-mcp>
- 官方参考 servers:<https://github.com/modelcontextprotocol/servers>
- Figma 取数方法见 `flutter-figma-mcp`;验证门禁见 `flutter-verification`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **server 是能力插槽不是收藏品**:接入的判据是"替代了哪个手工步骤",不是"可能有用"。
- **凭证即爆炸半径**:每个 token 的 scope 就是泄漏时的损失上限,最小权限不是繁文缛节。
- **接入即冒烟**:没验证过的集成等于没有集成,出事时排错成本翻倍。

**诚实边界:**

- MCP 生态演进快:server 列表、配置字段、客户端支持度以各官方仓库当时文档为准。
- "免费"指 server 本身开源/免费,背后服务(Figma/GitHub/Context7)的配额与付费墙以各家政策为准。
- 各 IDE/客户端的 mcp 配置文件路径与 secret 管理方式不同,本 skill 给通用模式,不替代客户端文档。
