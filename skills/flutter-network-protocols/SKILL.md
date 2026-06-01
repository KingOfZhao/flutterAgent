---
id: flutter-network-protocols
name: 通信协议全景 (HTTP/1.1·2·3 / REST / gRPC / GraphQL / WebSocket / SSE / MQTT / TLS)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [protocol, http, http2, http3, rest, grpc, graphql, websocket, sse, mqtt, tls, networking]
applies_when: 选型/理解与后端的通信协议,判断请求-响应 vs 流式 vs 实时推送该用什么
stage_hints: [architecture, breakdown]
see_also: [flutter-network]
---

# 通信协议全景

`flutter-network` 讲"用 Dio 怎么实现客户端"(拦截器/重试/取消/离线队列);本 skill 讲
**协议本身**——每种协议解决什么问题、什么时候用哪个、在 Flutter 里怎么落地。先选对协议,
再谈客户端实现。安全传输细节(pinning)见 `flutter-security`,认证授权协议见 `flutter-auth-protocols`。

## 0. 选型决策树(先问通信形态)

- **请求-响应、资源型** → REST over HTTP(最通用)。
- **强类型、跨语言、低延迟、流式** → gRPC。
- **客户端要精确取数、聚合多资源、避免 over/under-fetching** → GraphQL。
- **服务器→客户端单向持续推送(行情、通知)** → SSE(简单)或 WebSocket。
- **双向实时(聊天、协作、游戏)** → WebSocket。
- **海量设备、弱网、低功耗 IoT、发布/订阅** → MQTT。

> 一句话:**形态决定协议**——别用轮询 REST 硬模拟实时,也别为简单 CRUD 上 gRPC。

## 1. HTTP 版本(1.1 / 2 / 3)

- **HTTP/1.1**:一连接一请求(队头阻塞);最广兼容。
- **HTTP/2**:多路复用(一连接并发多请求)、头压缩、服务端推送;gRPC 建立其上。
- **HTTP/3(QUIC over UDP)**:进一步消除队头阻塞、连接迁移、弱网更快。
- 在 Flutter:`package:http` / Dio 默认 HTTP/1.1;要 HTTP/2 用 `cronet`(Android)/原生栈或特定客户端。多数业务无需手动选版本,但弱网/高并发场景值得评估。

## 2. REST(over HTTP)

- 资源 + HTTP 动词(GET/POST/PUT/PATCH/DELETE)+ 状态码语义;无状态。
- 约定优先:正确用状态码(2xx/4xx/5xx)、幂等性(PUT/DELETE 幂等)、分页、版本化(`/v1/`)。
- Flutter 端用 Dio/`http`(见 `flutter-network`),DTO 用 `json_serializable` 生成(见 `flutter-codegen`)。

## 3. gRPC

- 基于 **Protocol Buffers**(`.proto` 定义 + 代码生成)+ HTTP/2;强类型、二进制、高效。
- 支持四种调用:一元、服务端流、客户端流、双向流。
- Flutter 用 `grpc` + `protoc` 生成 Dart stub;**浏览器需要 gRPC-Web**(浏览器不能直连 HTTP/2 gRPC,见 `flutter-web`)。
- 适合内部服务间 / 移动端要强契约低延迟的场景。

## 4. GraphQL

- 单端点 + 查询语言:客户端声明**要哪些字段**,避免 over/under-fetching;有 query/mutation/subscription。
- Flutter 用 `graphql_flutter` / `ferry`;注意缓存规范化与 N+1 风险(见 `flutter-network` 的 GraphQL 缓存)。
- 代价:服务端复杂度、查询成本控制、缓存比 REST 难。

## 5. 实时:WebSocket vs SSE vs 轮询

- **WebSocket**:全双工长连接,适合双向实时;需自管重连/心跳/鉴权(见 `flutter-network` WebSocket 小节)。Dart 用 `web_socket_channel`。
- **SSE(Server-Sent Events)**:基于 HTTP 的**单向**服务器推送,比 WebSocket 简单,自动重连,适合"只需服务器推"的场景。
- **长轮询**:兜底方案;实时性差、开销大,能用 SSE/WebSocket 就别用。

## 6. MQTT(IoT / 发布订阅)

- 轻量发布/订阅协议,broker 中转;QoS 0/1/2 控制投递保证;适合海量设备、弱网、低功耗。
- Flutter 用 `mqtt_client`;注意保活(keep-alive)、遗嘱(LWT)、断线重连。

## 7. TLS / 安全传输(协议层)

- 生产**一律 HTTPS/WSS**;iOS ATS 默认强制(见 `flutter-ios-platform`)。
- 证书校验默认由系统完成;高安全场景做**证书/公钥固定(pinning)**(实现见 `flutter-security`)。
- 不要在协议层泄漏凭证(token 放头不放 URL;鉴权协议见 `flutter-auth-protocols`)。

## 8. 跨平台注意

- **Web** 限制最多:不能开裸 TCP/原生 gRPC,需 gRPC-Web;WebSocket/SSE/HTTP 可用但受 CORS 约束(见 `flutter-web`)。
- 移动端弱网要考虑超时/重试/退避(见 `flutter-network`)。

## 反模式

- ❌ 用定时轮询 REST 模拟实时推送(费电费流量,延迟高)。
- ❌ 简单 CRUD 强上 gRPC/GraphQL,徒增复杂度。
- ❌ 在浏览器直连原生 gRPC(必须 gRPC-Web)。
- ❌ 明文 HTTP 上线 / token 放进 URL 查询串。
- ❌ WebSocket 不做心跳与重连,弱网下静默掉线。

## 参考 / References

- HTTP 概览(MDN):<https://developer.mozilla.org/en-US/docs/Web/HTTP/Overview>
- Flutter 网络与 HTTP:<https://docs.flutter.dev/data-and-backend/networking>
- gRPC 官方:<https://grpc.io/docs/> · gRPC Dart:<https://grpc.io/docs/languages/dart/>
- gRPC-Web:<https://github.com/grpc/grpc-web>
- Protocol Buffers:<https://protobuf.dev/>
- GraphQL 官方:<https://graphql.org/learn/> · `graphql_flutter`:<https://pub.dev/packages/graphql_flutter>
- WebSocket(MDN):<https://developer.mozilla.org/en-US/docs/Web/API/WebSockets_API> · `web_socket_channel`:<https://pub.dev/packages/web_socket_channel>
- Server-Sent Events(MDN):<https://developer.mozilla.org/en-US/docs/Web/API/Server-sent_events>
- MQTT 官方:<https://mqtt.org/> · `mqtt_client`:<https://pub.dev/packages/mqtt_client>
- TLS(RFC 8446 / HTTP/3 QUIC):<https://datatracker.ietf.org/doc/html/rfc8446> · <https://datatracker.ietf.org/doc/html/rfc9114>
- 客户端实现见 `flutter-network`;鉴权见 `flutter-auth-protocols`;pinning 见 `flutter-security`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **通信形态决定协议**:先分清请求-响应/流式/双向实时/发布订阅,再选协议,而不是反过来。
- **协议 vs 实现是两层**:这里选"用什么协议",`flutter-network` 才是"客户端怎么写"。
- **Web 是约束最强的平台**:任何协议选型先问"在 web 能不能用、要不要降级"。

**诚实边界:**

- 协议选型受后端能力制约,常常不是前端单方面能定;需与后端对齐。
- 各协议的 Dart 库成熟度不一,选型看维护活跃度(见 `flutter-dependency-maintenance`)。
- HTTP/3、gRPC-Web 等在不同平台/客户端支持度不同,以实测与官方支持矩阵为准。
