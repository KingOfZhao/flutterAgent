# Flutter 网络与 API 层(向量库优质语料·轮3)

> 反思缺口:离线同步语料假设"网络层已经做对",但请求层本身的超时/重试/序列化/
> 错误建模无语料支撑。来源见 REFERENCES §26。

## 1. 客户端选型

- **`http`**:官方维护、轻量,适合简单 REST;拦截器/重试需自己组合
  (`http` 的 `Client` 可装饰器叠加)。
- **`dio`**:拦截器链、表单/下载进度、取消令牌、转换器开箱即用——中大型应用
  默认选 dio,但不要同一项目两者混用(连接池与配置分裂)。
- 平台原生引擎:`cupertino_http`/`cronet_http` 把请求交给 NSURLSession/Cronet,
  获得系统级 HTTP/3、缓存与代理支持,接口仍是 `http` 的 `Client`——需要时可平替。

## 2. 健壮性基线(每个项目都该有)

- **超时三件套**:连接、接收、整体超时都要显式设置——默认值要么无限要么过长,
  线上挂起请求会拖死队列。
- **重试只对幂等与可重试错误**:GET/网络抖动/5xx 可指数退避重试,POST 重试必须
  以幂等键为前提(对照本仓库 deepseek_client 的可重试状态码白名单同一原则);
  重试要设上限并对 429 尊重 `Retry-After`。
- **取消传播**:页面销毁时取消在途请求(dio CancelToken / `Client.close`),
  否则回调落在已 dispose 的状态上,产生"setState after dispose"类错误。
- **错误建模**:把传输层错误(超时/断网)、协议层错误(4xx/5xx)、业务错误
  (响应体里的错误码)建成不同类型,UI 据此区分"可重试/需登录/数据问题"——
  把所有异常揉成一个字符串是错误处理腐化的起点。

## 3. 序列化

- 运行时反射不可用(Flutter 关闭 dart:mirrors),JSON 映射用 **代码生成**:
  `json_serializable`(轻量、最通用)或 `freezed`(同时给出不可变模型 + union/
  sealed 类,错误建模友好);手写 `fromJson` 只适合字段极少的模型。
- DTO 与领域模型分离:API 响应模型不直接进 UI——服务端字段变更时只改 data 层
  (对应 flutter-app-architecture §3 的依赖方向)。
- 对不可信响应做防御:数值字段可能以字符串到达、可空性以实际灰度为准,
  解析失败要落到上面的"业务错误"类型而非裸 `FormatException` 穿透。

## 4. 与本仓库其他语料的衔接

- Repository 是重试/缓存策略的安放层(flutter-app-architecture §1);
- outbox 上传幂等键与本篇"POST 幂等重试"同一机制(flutter-offline-sync §2);
- MockClient/fake repository 测试见 flutter-testing-strategy §2。
