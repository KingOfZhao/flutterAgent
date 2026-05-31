---
id: flutter-ai-integration
name: Flutter AI 集成与端侧智能规范
version: 1.0.0
platforms: [all]
tags: [ai, llm, genkit, genui, gemma, firebase-ai, mcp, agentic, on-device, flutter_gemma]
applies_when: 需求涉及 AI 功能、大模型集成、端侧推理、生成式 UI 或智能体工作流
stage_hints: [spec, architecture, breakdown]
---

# Flutter AI 集成与端侧智能规范

> 直接依据:
> * Flutter 官方 Skills: **[github.com/flutter/skills](https://github.com/flutter/skills)**
> * Genkit Dart (预览版): **[pub.dev/packages/genkit](https://pub.dev/packages/genkit)**
> * GenUI SDK: **[pub.dev/packages/genui](https://pub.dev/packages/genui)**
> * flutter_gemma: **[pub.dev/packages/flutter_gemma](https://pub.dev/packages/flutter_gemma)**
> * Firebase AI: **[pub.dev/packages/firebase_ai](https://pub.dev/packages/firebase_ai)**
> * Agentic Hot Reload MCP: Flutter 官方 MCP 服务

---

## 1. AI 集成方案选型

| 场景 | 推荐方案 | 特点 |
|------|----------|------|
| 云端 LLM 调用（Gemini/GPT/Claude） | `genkit` | 类型安全结构化输出、工具调用、多轮对话、可观测性 |
| Firebase 生态内 AI | `firebase_ai` | Gemini + Imagen,与 Firebase Auth/Firestore 深度集成 |
| 端侧本地推理 | `flutter_gemma` | 基于 LiteRT-LM,支持 Gemma 4/3n、Qwen3、DeepSeek R1 等 |
| 生成式 UI (Agent → Widget) | `genui` | A2UI 协议,LLM 输出实时映射到 Widget 树 |
| AI Agent 开发工作流 | Agentic Hot Reload | MCP 服务,AI 自动修改代码 → 自动热重载 → 界面刷新 |

---

## 2. Genkit Dart（推荐的全栈 AI 框架）

Genkit 是 Google 开源的 AI 应用构建框架,**Dart 预览版**已发布。

### 2.1 核心能力

- **多模型支持**: Google AI、Anthropic、OpenAI 等
- **类型安全结构化输出**: 编译期保障 LLM 返回的 JSON schema
- **工具调用 (Function Calling)**: 让 LLM 调用 Dart 函数
- **多轮对话**: 内置会话管理
- **可观测性**: 内置 tracing / logging

### 2.2 基本用法

```dart
import 'package:genkit/genkit.dart';
import 'package:genkit_google_genai/genkit_google_genai.dart';

void main() async {
  final ai = Genkit(plugins: [googleAI()]);

  // 简单生成
  final response = await ai.generate(
    model: googleAI.gemini('gemini-flash-latest'),
    prompt: 'Summarize this Flutter app architecture',
  );
  print(response.text);
}
```

### 2.3 结构化输出

```dart
// 定义输出 schema
final recipe = ai.defineSchema<Recipe>(
  'Recipe',
  (json) => Recipe.fromJson(json),
  jsonSchema: recipeJsonSchema,
);

final response = await ai.generate(
  model: googleAI.gemini('gemini-flash-latest'),
  prompt: 'Create a recipe for chocolate cake',
  output: recipe,
);
final Recipe result = response.output!; // 类型安全
```

### 2.4 工具调用

```dart
final weatherTool = ai.defineTool(
  'getWeather',
  'Get current weather for a city',
  inputSchema: {'city': 'string'},
  (input) async {
    final city = input['city'] as String;
    return await weatherApi.fetch(city);
  },
);

final response = await ai.generate(
  model: googleAI.gemini('gemini-flash-latest'),
  prompt: 'What is the weather in Tokyo?',
  tools: [weatherTool],
);
```

---

## 3. 端侧 AI — flutter_gemma

`flutter_gemma` 基于 **LiteRT-LM** 深度定制,通过 Flutter Native Assets 实现零开销本地推理。

### 3.1 支持的模型

| 模型 | 参数量 | 适用场景 |
|------|--------|----------|
| Gemma 4 | 多规格 | Google 最新端侧模型 |
| Gemma 3n | 轻量 | 手机端优先 |
| FastVLM 0.5B | 0.5B | 超轻量视觉语言模型 |
| Qwen3 0.6B | 0.6B | 中文优化 |
| Qwen 2.5 | 多规格 | 通用 |
| Phi-4 Mini | 小型 | 微软端侧模型 |
| DeepSeek R1 | 多规格 | 推理增强 |
| SmolLM 135M | 135M | 极轻量嵌入式 |

### 3.2 基本用法

```dart
import 'package:flutter_gemma/flutter_gemma.dart';

// 初始化（自动利用 GPU/NPU 加速）
final gemma = FlutterGemma.instance;
await gemma.init(modelPath: 'assets/gemma-4-2b.bin');

// 生成
final response = await gemma.generate('Explain BLoC pattern');
print(response);

// 流式生成
await for (final chunk in gemma.generateStream('Write a poem')) {
  stdout.write(chunk);
}
```

### 3.3 架构决策

```
何时用端侧 AI？
├── 离线场景必须可用 → flutter_gemma
├── 隐私敏感数据不能上传 → flutter_gemma
├── 需要极低延迟（<100ms） → flutter_gemma（小模型）
├── 需要强推理/大上下文 → 云端 API (genkit / firebase_ai)
└── 混合模式 → 端侧初筛 + 云端精炼
```

---

## 4. GenUI — 生成式 UI

GenUI 是 Flutter 官方推出的 SDK,实现 **A2UI (Agent-to-UI)** 协议。

### 4.1 核心概念

- LLM 输出的标记和 JSON 数据流 → 实时解析 → 映射到 Flutter Widget 树
- 突破传统"文字墙"聊天界面,Agent 可直接生成下拉框、表单、卡片等交互组件
- 流式渲染,逐 token 更新 UI

### 4.2 基本用法

```dart
import 'package:genui/genui.dart';

GenUI(
  stream: llmResponseStream,  // LLM 的 SSE/流式输出
  builders: {
    'form': (context, data) => DynamicForm(fields: data['fields']),
    'chart': (context, data) => BarChart(data: data['values']),
    'card': (context, data) => InfoCard(title: data['title']),
  },
)
```

### 4.3 适用场景

| 场景 | 示例 |
|------|------|
| 智能客服 | Agent 返回交互式表单收集用户信息 |
| 数据分析 | Agent 返回可视化图表而非文字描述 |
| 电商导购 | Agent 返回商品卡片列表供用户选择 |
| 表单填写 | Agent 动态生成适配当前上下文的输入界面 |

---

## 5. Firebase AI

Firebase AI Logic SDK 提供对 **Gemini** 和 **Imagen** 的访问。

```dart
import 'package:firebase_ai/firebase_ai.dart';

final model = FirebaseAI.googleAI().generativeModel(
  model: 'gemini-flash-latest',
);

final response = await model.generateContent([
  Content.text('Describe this image'),
  Content.inlineData('image/jpeg', imageBytes),
]);
```

**优势**: 与 Firebase Auth、Firestore、Cloud Functions 深度集成,无需单独管理 API key。

---

## 6. Agentic Hot Reload — AI 开发工作流

Flutter 官方提供的 **MCP (Model Context Protocol)** 服务,可与 Codex、Claude Code 等 AI 工具集成。

### 6.1 工作流变化

```
传统流程:
  开发者发指令 → AI 生成代码 → 手动按 r 热重载 → 查看效果

Agentic Hot Reload:
  AI 自动修改代码 → 自动连接运行中的 App → 自动触发 Hot Reload → 界面刷新
```

### 6.2 集成方式

- 通过 MCP 服务暴露 Flutter 运行时能力
- AI Agent 可直接调用 `hotReload`、`hotRestart`、`screenshot` 等工具
- 支持 Codex、Claude Code、Cursor 等主流 AI IDE

---

## 7. 架构最佳实践

### 7.1 混合 AI 架构

```
┌─────────────────────────────────────┐
│             Flutter App              │
├─────────────┬───────────────────────┤
│ 端侧 AI 层  │      云端 AI 层        │
│ flutter_gemma│  genkit / firebase_ai │
│ (离线/隐私)  │  (强推理/大上下文)      │
├─────────────┴───────────────────────┤
│           GenUI 渲染层               │
│   LLM 输出 → Widget 树映射          │
├─────────────────────────────────────┤
│         Repository / 业务层          │
└─────────────────────────────────────┘
```

### 7.2 决策清单

| 维度 | 端侧 (flutter_gemma) | 云端 (genkit/firebase_ai) |
|------|----------------------|---------------------------|
| 延迟 | <100ms（小模型） | 500ms–3s |
| 隐私 | 数据不离开设备 | 需要网络传输 |
| 能力 | 受限于设备算力 | 强推理、大上下文 |
| 成本 | 零 API 费用 | 按 token 计费 |
| 离线 | ✅ 完全离线 | ❌ 需要网络 |
| 模型更新 | 需重新分发 | 服务端即时切换 |

### 7.3 反模式

| ❌ 反模式 | ✅ 正确做法 |
|----------|-------------|
| 所有 AI 调用都走云端 | 评估隐私和延迟需求,端侧能解决的用端侧 |
| 在 UI 层直接调用 LLM API | 通过 Repository 层封装,方便切换模型 |
| GenUI 不做降级处理 | 当 LLM 返回异常时提供兜底 Widget |
| 端侧大模型阻塞 UI 线程 | 使用 Isolate 或流式生成,避免 jank |
| 硬编码 API key 在客户端 | 使用 Firebase AI（自动鉴权）或后端代理 |

---

## 参考

- Genkit Dart: <https://pub.dev/packages/genkit>
- genkit_google_genai: <https://pub.dev/packages/genkit_google_genai>
- GenUI SDK: <https://pub.dev/packages/genui>
- flutter_gemma: <https://pub.dev/packages/flutter_gemma>
- Firebase AI: <https://pub.dev/packages/firebase_ai>
- Flutter Skills (官方): <https://github.com/flutter/skills>
- Dart Skills (官方): <https://github.com/dart-lang/skills>
- LiteRT-LM: <https://ai.google.dev/edge/litert>
- Gemma 模型: <https://ai.google.dev/gemma>
- MCP (Model Context Protocol): <https://modelcontextprotocol.io>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先定推理位置**:端侧(隐私/离线/省成本)vs 云端(能力/算力),再选方案。
- **模型是不确定组件**:输出要校验/兜底,UI 要可降级,别假设永远成功。
- **把 AI 当外部依赖**:Schema 化输入输出,prompt 不散落 UI 层。

**诚实边界:**

- AI 生态/SDK 迭代极快,具体 API 以官方文档为准;本 skill 给选型镜片,非 API 手册。
- 不替你做模型效果评估与隐私/合规审查。
