---
id: flutter-network
name: Flutter 网络层工程规范
version: 1.0.0
platforms: [all]
tags: [network, dio, http, websocket, graphql, grpc, interceptor, retry, offline, cancel]
applies_when: 需求涉及 API 调用 / 网络请求 / 实时通信 / 离线同步
stage_hints: [architecture, breakdown]
---

# Flutter 网络层工程规范

> 直接依据:
> * Flutter 官方 Networking: **[docs.flutter.dev/data-and-backend/networking](https://docs.flutter.dev/data-and-backend/networking)**
> * Dio package: **[pub.dev/packages/dio](https://pub.dev/packages/dio)**
> * web_socket_channel: **[pub.dev/packages/web_socket_channel](https://pub.dev/packages/web_socket_channel)**
> * graphql_flutter: **[pub.dev/packages/graphql_flutter](https://pub.dev/packages/graphql_flutter)**
> * connectivity_plus: **[pub.dev/packages/connectivity_plus](https://pub.dev/packages/connectivity_plus)**

---

## 1. HTTP 客户端选型

| 方案 | 适用场景 | 说明 |
|------|---------|------|
| `dio` | 绝大多数项目（默认推荐） | 拦截器链、取消、上传下载、FormData、日志 |
| `http` | 极简项目 / package 开发 | Flutter 官方维护,零依赖 |
| `chopper` / `retrofit` | REST API 代码生成 | 类型安全,接口定义与实现分离 |
| `graphql_flutter` | GraphQL 后端 | 缓存、subscription、optimistic UI |
| `grpc` | 微服务 / 高性能 RPC | protobuf、双向流、低延迟 |

---

## 2. Dio 拦截器链设计

拦截器是网络层的核心骨架,顺序至关重要:

```
请求发出 →
  ① AuthInterceptor       (注入 Token)
  ② ConnectivityInterceptor (检查网络状态)
  ③ RetryInterceptor       (429 / 5xx 重试)
  ④ CacheInterceptor       (SWR 缓存策略)
  ⑤ LogInterceptor         (日志,仅 debug)
→ 服务端
→ 响应返回
```

### 2.1 基础 Dio 配置

```dart
class ApiClient {
  late final Dio _dio;

  ApiClient({required String baseUrl, required TokenStore tokenStore}) {
    _dio = Dio(BaseOptions(
      baseUrl: baseUrl,
      connectTimeout: const Duration(seconds: 10),
      receiveTimeout: const Duration(seconds: 30),
      sendTimeout: const Duration(seconds: 15),
      headers: {
        'Accept': 'application/json',
        'Content-Type': 'application/json',
      },
    ));

    // 拦截器顺序很重要
    _dio.interceptors.addAll([
      AuthInterceptor(tokenStore: tokenStore),
      RetryInterceptor(dio: _dio),
      if (kDebugMode) LogInterceptor(requestBody: true, responseBody: true),
    ]);
  }

  Dio get dio => _dio;
}
```

### 2.2 Token 刷新拦截器（解决竞态问题）

多个并发请求同时收到 401 时,只应触发**一次** refresh:

```dart
class AuthInterceptor extends QueuedInterceptor {
  // ↑ QueuedInterceptor 保证同一时刻只有一个请求进入 onError
  final TokenStore _tokenStore;
  final Dio _tokenDio; // 独立 Dio 实例,避免死锁

  AuthInterceptor({required TokenStore tokenStore})
      : _tokenStore = tokenStore,
        _tokenDio = Dio(BaseOptions(baseUrl: tokenStore.baseUrl));

  @override
  void onRequest(RequestOptions options, RequestInterceptorHandler handler) {
    final token = _tokenStore.accessToken;
    if (token != null) {
      options.headers['Authorization'] = 'Bearer $token';
    }
    handler.next(options);
  }

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    if (err.response?.statusCode != 401) {
      return handler.next(err);
    }

    // 尝试刷新 token
    try {
      final refreshToken = _tokenStore.refreshToken;
      if (refreshToken == null) {
        return handler.reject(err);
      }

      final response = await _tokenDio.post('/auth/refresh', data: {
        'refresh_token': refreshToken,
      });

      final newAccess = response.data['access_token'] as String;
      final newRefresh = response.data['refresh_token'] as String;
      await _tokenStore.save(access: newAccess, refresh: newRefresh);

      // 用新 token 重发原始请求
      final opts = err.requestOptions;
      opts.headers['Authorization'] = 'Bearer $newAccess';
      final retryResponse = await _tokenDio.fetch(opts);
      return handler.resolve(retryResponse);
    } on DioException {
      // refresh 也失败 → 强制登出
      await _tokenStore.clear();
      return handler.reject(err);
    }
  }
}
```

**关键要点**:
- 使用 `QueuedInterceptor` 而非 `Interceptor` — 队列化处理,同一时刻只处理一个 401,其余排队等待
- 刷新使用独立 `Dio` 实例 — 避免 refresh 请求又被自己的拦截器拦截导致死锁
- refresh 失败 → 清除 token + 强制导航到登录页

---

## 3. 请求取消 (CancelToken)

页面退出、搜索框输入防抖时必须取消未完成请求:

```dart
class _SearchPageState extends State<SearchPage> {
  CancelToken? _cancelToken;

  Future<void> _search(String query) async {
    // 取消上一次请求
    _cancelToken?.cancel('new search');
    _cancelToken = CancelToken();

    try {
      final response = await dio.get(
        '/search',
        queryParameters: {'q': query},
        cancelToken: _cancelToken,
      );
      if (mounted) setState(() => _results = response.data);
    } on DioException catch (e) {
      if (e.type == DioExceptionType.cancel) return; // 正常取消,忽略
      rethrow;
    }
  }

  @override
  void dispose() {
    _cancelToken?.cancel('page disposed');
    super.dispose();
  }
}
```

---

## 4. 重试策略

```dart
class RetryInterceptor extends Interceptor {
  final Dio _dio;
  final int maxRetries;
  final Duration baseDelay;

  RetryInterceptor({
    required Dio dio,
    this.maxRetries = 3,
    this.baseDelay = const Duration(milliseconds: 500),
  }) : _dio = dio;

  @override
  void onError(DioException err, ErrorInterceptorHandler handler) async {
    final statusCode = err.response?.statusCode ?? 0;
    final isRetryable = statusCode == 408 || statusCode == 429 ||
        statusCode >= 500 || err.type == DioExceptionType.connectionTimeout;

    if (!isRetryable) return handler.next(err);

    final opts = err.requestOptions;
    final retryCount = (opts.extra['_retryCount'] as int?) ?? 0;
    if (retryCount >= maxRetries) return handler.next(err);

    opts.extra['_retryCount'] = retryCount + 1;

    // 429 时尊重 Retry-After
    final retryAfter = err.response?.headers.value('retry-after');
    final delay = retryAfter != null
        ? Duration(seconds: int.tryParse(retryAfter) ?? 1)
        : baseDelay * (1 << retryCount); // 指数退避

    await Future.delayed(delay);
    try {
      final response = await _dio.fetch(opts);
      handler.resolve(response);
    } on DioException catch (e) {
      handler.next(e);
    }
  }
}
```

---

## 5. WebSocket / 实时通信

### 5.1 基础连接 + 自动重连

```dart
class ReconnectingWebSocket {
  final String url;
  final Duration reconnectDelay;
  final int maxRetries;

  WebSocketChannel? _channel;
  StreamSubscription? _sub;
  int _retryCount = 0;
  bool _disposed = false;

  final _controller = StreamController<dynamic>.broadcast();
  Stream<dynamic> get stream => _controller.stream;

  ReconnectingWebSocket({
    required this.url,
    this.reconnectDelay = const Duration(seconds: 2),
    this.maxRetries = 10,
  });

  void connect() {
    if (_disposed) return;
    _channel = WebSocketChannel.connect(Uri.parse(url));
    _retryCount = 0;

    _sub = _channel!.stream.listen(
      (data) {
        _retryCount = 0; // 收到数据重置计数
        _controller.add(data);
      },
      onError: (error) => _reconnect(),
      onDone: () => _reconnect(),
    );
  }

  void _reconnect() {
    if (_disposed || _retryCount >= maxRetries) return;
    _retryCount++;
    final delay = reconnectDelay * (1 << (_retryCount - 1).clamp(0, 5));
    Future.delayed(delay, connect);
  }

  void send(dynamic data) {
    _channel?.sink.add(data);
  }

  void dispose() {
    _disposed = true;
    _sub?.cancel();
    _channel?.sink.close();
    _controller.close();
  }
}
```

### 5.2 心跳保活

```dart
// 每 30s 发送 ping,超过 45s 无 pong 则视为断连
Timer.periodic(const Duration(seconds: 30), (_) {
  _channel?.sink.add(jsonEncode({'type': 'ping'}));
});
```

---

## 6. 离线优先 / 请求队列

### 6.1 架构模式

```
用户操作 → Repository
             ├── 有网 → API → 缓存到本地 → 返回
             └── 无网 → 读本地缓存
                        └── 写操作入队 → 恢复网络后重放
```

### 6.2 离线队列实现

```dart
class OfflineQueue {
  final Dio _dio;
  final Box<Map> _queueBox; // Hive box

  OfflineQueue(this._dio, this._queueBox);

  /// 入队（无网时调用）
  Future<void> enqueue(RequestOptions opts) async {
    await _queueBox.add({
      'method': opts.method,
      'path': opts.path,
      'data': opts.data,
      'queryParameters': opts.queryParameters,
      'headers': opts.headers,
      'timestamp': DateTime.now().toIso8601String(),
    });
  }

  /// 恢复网络后重放所有排队请求
  Future<void> flush() async {
    final keys = _queueBox.keys.toList();
    for (final key in keys) {
      final item = _queueBox.get(key);
      if (item == null) continue;
      try {
        await _dio.request(
          item['path'],
          data: item['data'],
          queryParameters: Map<String, dynamic>.from(item['queryParameters'] ?? {}),
          options: Options(method: item['method']),
        );
        await _queueBox.delete(key); // 成功则移除
      } on DioException {
        break; // 仍然失败,停止重放
      }
    }
  }
}
```

### 6.3 网络状态监听

```dart
// connectivity_plus 监听网络变化
final connectivity = Connectivity();
connectivity.onConnectivityChanged.listen((result) {
  if (result != ConnectivityResult.none) {
    offlineQueue.flush(); // 恢复网络,重放队列
  }
});
```

---

## 7. GraphQL 集成

```dart
// graphql_flutter 基础配置
final httpLink = HttpLink('https://api.example.com/graphql');
final authLink = AuthLink(getToken: () async => 'Bearer ${tokenStore.accessToken}');
final link = authLink.concat(httpLink);

final client = GraphQLClient(
  link: link,
  cache: GraphQLCache(store: HiveStore()), // 持久化缓存
);
```

### 7.1 缓存策略

| 策略 | 用途 |
|------|------|
| `CachePolicy.cacheFirst` | 列表页,优先显示缓存再后台刷新 |
| `CachePolicy.networkOnly` | 写操作后的重新获取 |
| `CachePolicy.cacheAndNetwork` | 先显示缓存 + 后台更新后刷新 UI |

---

## 8. gRPC 集成

```dart
// protobuf 生成的 client
final channel = ClientChannel(
  'api.example.com',
  port: 443,
  options: const ChannelOptions(credentials: ChannelCredentials.secure()),
);
final stub = MyServiceClient(channel);

// 双向流示例
final stream = stub.streamUpdates(StreamRequest(topic: 'prices'));
await for (final update in stream) {
  // 处理实时更新
}

// 页面退出时关闭
await channel.shutdown();
```

---

## 9. 错误处理分层

```dart
/// 统一错误类型,上层不关心 HTTP/WebSocket/gRPC 差异
sealed class AppNetworkError {
  const AppNetworkError();
}

class Unauthorized extends AppNetworkError {
  const Unauthorized();
}

class ServerError extends AppNetworkError {
  final int statusCode;
  final String? message;
  const ServerError(this.statusCode, this.message);
}

class NoConnection extends AppNetworkError {
  const NoConnection();
}

class Timeout extends AppNetworkError {
  const Timeout();
}

class Cancelled extends AppNetworkError {
  const Cancelled();
}

/// Dio 异常 → AppNetworkError
AppNetworkError mapDioError(DioException e) {
  return switch (e.type) {
    DioExceptionType.connectionTimeout ||
    DioExceptionType.receiveTimeout ||
    DioExceptionType.sendTimeout => const Timeout(),
    DioExceptionType.cancel => const Cancelled(),
    DioExceptionType.badResponse => switch (e.response?.statusCode) {
      401 => const Unauthorized(),
      _ => ServerError(e.response!.statusCode!, e.response?.statusMessage),
    },
    _ => const NoConnection(),
  };
}
```

---

## 10. SSL Pinning 与调试共存

```dart
// 生产: 启用 certificate pinning
// 开发: 允许 Charles/Proxyman 抓包

Dio createDio({required bool isProduction}) {
  final dio = Dio();

  if (isProduction) {
    // SHA-256 fingerprint pinning
    (dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
      final client = HttpClient();
      client.badCertificateCallback = (cert, host, port) {
        final fingerprint = sha256.convert(cert.der).toString();
        return _trustedFingerprints.contains(fingerprint);
      };
      return client;
    };
  } else {
    // 开发环境: 信任所有证书 (允许代理抓包)
    (dio.httpClientAdapter as IOHttpClientAdapter).createHttpClient = () {
      final client = HttpClient();
      client.badCertificateCallback = (_, __, ___) => true;
      return client;
    };
  }

  return dio;
}
```

---

## 11. 必须产出

1. **Dio 配置**: baseUrl、timeout、拦截器顺序
2. **Token 刷新方案**: QueuedInterceptor 还是自行加锁,refresh 失败时的登出流程
3. **取消策略**: 哪些页面/场景需要 CancelToken
4. **重试策略**: 哪些 status code 重试,最大次数,退避间隔
5. **离线方案**: 是否需要离线队列,缓存策略(cache-first / network-first)
6. **错误分层**: API 层错误如何映射到 UI 提示

## 12. 红线

- 不要在 Repository 层直接 `catch` 并吞掉网络错误 — 必须向上传递
- 不要用普通 `Interceptor` 做 token refresh — 并发 401 会触发多次 refresh,用 `QueuedInterceptor`
- 不要把 refresh token 存在 `SharedPreferences`(明文) — 必须用 `flutter_secure_storage`
- 不要忘记页面退出取消请求 — 未取消的请求会回调已 disposed 的 State
- 不要在 Web 平台使用 `dart:io` 的 `HttpClient` — 必须条件导入或直接用 Dio
- 不要硬编码 base URL — 通过 env / flavor 注入
- 不要忽略 WebSocket 断线重连 — 移动网络切换(WiFi↔4G)必断,用户无感知

---

## 参考

- Flutter 官方 Networking: <https://docs.flutter.dev/data-and-backend/networking>
- Dio: <https://pub.dev/packages/dio>
- web_socket_channel: <https://pub.dev/packages/web_socket_channel>
- graphql_flutter: <https://pub.dev/packages/graphql_flutter>
- grpc: <https://pub.dev/packages/grpc>
- connectivity_plus: <https://pub.dev/packages/connectivity_plus>
- flutter_secure_storage: <https://pub.dev/packages/flutter_secure_storage>
- retrofit (Dio 代码生成): <https://pub.dev/packages/retrofit>
- chopper (HTTP 代码生成): <https://pub.dev/packages/chopper>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **横切关注走拦截器链**:鉴权/刷新/日志/重试集中,不散落调用点。
- **网络必然失败**:取消/超时/重试/离线队列是默认设计,不是补丁。
- **契约先行**:DTO+序列化与 UI 模型解耦,服务端变更不击穿 UI。

**诚实边界:**

- 后端契约/鉴权细节依具体 API,本 skill 给结构,非具体协议。
- 弱网/丢包行为需真实网络环境实测。
