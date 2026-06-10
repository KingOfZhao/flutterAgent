# Flutter 测试策略(向量库优质语料)

> 用途:为"怎么测/测试金字塔/CI"类需求提供检索接地语料。来源见 REFERENCES §25。

## 1. 三层金字塔(官方分层)

| 层 | 工具 | 速度 | 该测什么 |
|---|---|---|---|
| unit | `test` 包 | 毫秒级 | 纯 Dart 逻辑:repository、解析、状态机转换 |
| widget | `flutter_test` + `WidgetTester` | 十毫秒级 | 单组件渲染与交互:pump → 交互 → expect finder |
| integration | `integration_test` 包 | 秒级,真机/模拟器 | 关键用户旅程(登录、下单等金路径),数量克制 |

比例失衡的典型症状:integration 测试几十个、unit 几乎没有 → CI 慢且 flaky;
应把可下沉的断言下沉到 widget/unit 层。

## 2. 可测性设计

- 依赖注入是前提:repository/服务通过构造器或 provider 注入,测试时替换为 fake;
  `mockito`/`mocktail` 生成 mock,但**优先手写 fake**(行为可读,不绑定调用次数)。
- 时间与随机:用 `fakeAsync`/注入 clock,不要在测试里真 sleep。
- 网络:测试一律不打真网——repository 层断开,或用 `http` 的 MockClient。

## 3. widget 测试要点

- `pumpWidget` 后需要 `pump()`(单帧)或 `pumpAndSettle()`(等动画结束)才能看到
  异步后的 UI;`pumpAndSettle` 对无限动画(如 loading spinner)会超时——改用
  定长 `pump(duration)`。
- finder 优先级:语义化(`find.bySemanticsLabel`)> Key > 文本——文本最脆弱,
  改文案即碎。
- golden 测试(截图对比)适合设计系统组件;平台字体渲染差异会导致 CI 与本地
  不一致,需固定字体与设备像素比。

## 4. CI 基线

`flutter analyze` + `flutter test`(unit/widget)每次提交必跑;integration 测试
放每日或合并前,真机农场(Firebase Test Lab 等)按发布节奏跑。
