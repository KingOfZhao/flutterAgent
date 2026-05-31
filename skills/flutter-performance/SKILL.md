---
id: flutter-performance
name: Flutter 性能预算与优化规范
version: 1.0.0
platforms: [all]
tags: [performance, profiling, frame-budget, isolate, image, chart, realtime, ticker]
applies_when: 列表 / 动画 / 大图 / 实时数据 / 长任务场景 / 高频图表 / K线 / 波形
stage_hints: [architecture, breakdown]
---

# Flutter 性能规范

## 1. 性能预算(必须写进 acceptance)

| 指标 | 目标 | 测量方法 |
|---|---|---|
| 冷启动到首帧 (mobile mid-tier) | ≤ 2.0s | `flutter run --trace-startup --profile` |
| 帧时间 (raster + UI) | < 16ms (60fps) / < 8ms (120fps) | DevTools Performance |
| 跳帧 (jank) 比例 | < 1% | DevTools 录制 30s |
| Release apk size | ≤ 25MB | `flutter build apk --analyze-size` |
| 首屏内存 | ≤ 180MB (mobile) | Observatory |
| Desktop 大列表滚动 | 1000 行 60fps 平稳 | profile mode + GPU monitor |

## 2. 列表

- 长列表必须 `ListView.builder` / `SliverList`,**禁止** `ListView(children: [...])`
- item 之间互不重排时套 `RepaintBoundary`
- 复杂 item 用 `AutomaticKeepAliveClientMixin`(慎用,内存换性能)
- 分页:`infinite_scroll_pagination` 或自实现 `PagingController`
- 列表 + 详情页转场,使用 `Hero` 共享元素 + `precacheImage`

## 3. 图片

| 场景 | 方案 |
|---|---|
| 网络图 | `cached_network_image`(自带磁盘缓存) |
| 大图(摄影) | `flutter_image_compress` 二级缩略 + 原图懒加载 |
| svg | `flutter_svg`,**避免** 在列表里大量同时绘制(预栅格化) |
| 占位 | shimmer 包,统一 skeleton |

必须设置 `cacheWidth` / `cacheHeight`,匹配显示尺寸的 dp,**禁止**直接显示 4096×4096 的原图。

## 4. 动画与重建

- 减少 `setState` 触发面:把可变状态下沉到最小子树
- 用 `AnimatedBuilder` 包到只动的子树
- `Selector` (provider) / `select` (riverpod) 精确订阅
- 用 `const` 构造体能 const 就 const(常量子树不重建)
- 慎用 `Opacity`,优先 `FadeTransition` 或 `AnimatedOpacity`

## 5. 长任务 / 阻塞

- > 16ms 计算 ⇒ 必须 `compute()` 或 `Isolate.run()`
- 列表 sort / json parse 大对象 ⇒ isolate
- 网络请求 + JSON 解码: `dio` + isolate JSON parsing(`computeIsolate`)
- 文件 IO: 桌面端 ≥ 1MB / 移动端 ≥ 200KB 必须 isolate

## 6. 启动优化

- `main()` 内只做 `WidgetsFlutterBinding.ensureInitialized`,其余初始化推迟到 `runApp` 后
- splash + 骨架屏并行:Riverpod `FutureProvider` 预热
- `flutter_native_splash` 提供原生闪屏,避免白屏
- 禁止在 `main()` 同步读取大文件

## 7. 包体积

- `--split-per-abi`(Android)
- 移除未使用资源:`flutter build apk --analyze-size` 后审查
- 字体子集化:`flutter pub run flutter_subsets`(中文场景刚需)
- 图片压缩:WebP 优先

## 8. 桌面端额外项

- 大窗口拖拽 resize 不能掉帧:`window_manager` + `setMinimumSize` 限制极端比例
- 多显示器移动:监听 `screen_retriever` 事件,刷新 DPI 缓存
- CPU usage 限制:大列表非可见时降低刷新率(60→30)

## 9. 高频率刷新图表（实时行情 / 传感器 / 音频波形）

实时图表需要在 16ms 帧预算内完成「数据接收 → 计算 → 绘制」闭环。核心原则:**只重绘图表画布,不 rebuild widget 树**。

### 9.1 架构选型

| 方案 | 适用场景 | 帧率上限 | 说明 |
|------|---------|---------|------|
| `fl_chart` | 中低频更新 (≤ 5fps),业务图表 | ~30fps | 声明式 API,易用但每次更新触发 build |
| `CustomPainter` + `Ticker` | 高频 (30-60fps),波形/K线 | 60fps | 直接 Canvas 绘制,零 widget rebuild |
| `CustomPainter` + `repaint` Listenable | 高频,数据驱动 | 60fps | 数据 ValueNotifier 触发 repaint,不经 setState |
| `RenderObject` (自定义) | 极致性能,游戏级实时渲染 | 120fps | 最底层,复杂度高 |

### 9.2 核心模式：ValueNotifier + CustomPainter

**关键**: `CustomPainter(repaint: notifier)` — 当 notifier 变化时只重绘 Canvas,**不触发 setState / build**。

```dart
/// 环形缓冲区: O(1) 添加,固定内存
class RingBuffer<T> {
  final List<T?> _buffer;
  int _head = 0;
  int _count = 0;

  RingBuffer(int capacity) : _buffer = List<T?>.filled(capacity, null);

  int get length => _count;
  int get capacity => _buffer.length;

  void add(T value) {
    _buffer[_head] = value;
    _head = (_head + 1) % capacity;
    if (_count < capacity) _count++;
  }

  T operator [](int index) {
    assert(index < _count);
    final actualIndex = (_head - _count + index) % capacity;
    return _buffer[actualIndex] as T;
  }
}

/// 数据模型: 使用 ValueNotifier 驱动重绘
class ChartDataNotifier extends ValueNotifier<int> {
  final RingBuffer<double> points;

  ChartDataNotifier({int capacity = 1024})
      : points = RingBuffer(capacity),
        super(0);

  void addPoint(double value) {
    points.add(value);
    // 只改变 value 触发 repaint,不走 setState
    this.value++;
  }

  void addBatch(List<double> values) {
    for (final v in values) {
      points.add(v);
    }
    this.value++;
  }
}
```

```dart
/// 高性能图表画笔
class RealtimeChartPainter extends CustomPainter {
  final ChartDataNotifier data;
  final Color lineColor;
  final double strokeWidth;

  RealtimeChartPainter({
    required this.data,
    this.lineColor = Colors.blue,
    this.strokeWidth = 1.5,
  }) : super(repaint: data);  // ← 关键: repaint 绑定

  @override
  void paint(Canvas canvas, Size size) {
    if (data.points.length < 2) return;

    final paint = Paint()
      ..color = lineColor
      ..strokeWidth = strokeWidth
      ..style = PaintingStyle.stroke
      ..isAntiAlias = false;  // 高频场景可关闭抗锯齿省 GPU

    final path = Path();
    final count = data.points.length;
    final dx = size.width / (count - 1);

    // 计算 Y 范围 (可缓存避免每帧计算)
    double minY = double.infinity, maxY = double.negativeInfinity;
    for (int i = 0; i < count; i++) {
      final v = data.points[i];
      if (v < minY) minY = v;
      if (v > maxY) maxY = v;
    }
    final rangeY = (maxY - minY).clamp(0.001, double.infinity);

    for (int i = 0; i < count; i++) {
      final x = i * dx;
      final y = size.height - ((data.points[i] - minY) / rangeY) * size.height;
      if (i == 0) {
        path.moveTo(x, y);
      } else {
        path.lineTo(x, y);
      }
    }

    canvas.drawPath(path, paint);
  }

  @override
  bool shouldRepaint(covariant RealtimeChartPainter oldDelegate) => false;
  // ↑ 返回 false! 重绘由 repaint: data 驱动,不依赖 shouldRepaint
}
```

```dart
/// Widget 层: 一次 build,后续只 repaint Canvas
class RealtimeChart extends StatelessWidget {
  final ChartDataNotifier data;

  const RealtimeChart({required this.data});

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(  // ← 隔离重绘区域
      child: CustomPaint(
        painter: RealtimeChartPainter(data: data),
        size: Size.infinite,
      ),
    );
  }
}
```

### 9.3 数据采集层: Stream 节流 + Isolate

```dart
/// WebSocket / 传感器高频数据 → Isolate 预处理 → UI 线程绘制
class ChartDataSource {
  final ChartDataNotifier notifier;
  StreamSubscription? _sub;

  ChartDataSource(this.notifier);

  /// 接入实时数据流,自动节流到目标帧率
  void connect(Stream<double> rawStream, {int targetFps = 30}) {
    final interval = Duration(milliseconds: 1000 ~/ targetFps);
    final buffer = <double>[];
    Timer? batchTimer;

    _sub = rawStream.listen((value) {
      buffer.add(value);
      // 批量推送: 每帧间隔攒一批,一次 addBatch
      batchTimer ??= Timer(interval, () {
        if (buffer.isNotEmpty) {
          notifier.addBatch(List.of(buffer));
          buffer.clear();
        }
        batchTimer = null;
      });
    });
  }

  /// 重数据处理(移动均线 / FFT)放到 Isolate
  static Future<List<double>> processInIsolate(
    List<double> raw,
    int windowSize,
  ) async {
    return Isolate.run(() {
      // 示例: 简单移动平均
      final result = <double>[];
      for (int i = 0; i < raw.length; i++) {
        final start = (i - windowSize + 1).clamp(0, raw.length);
        double sum = 0;
        for (int j = start; j <= i; j++) sum += raw[j];
        result.add(sum / (i - start + 1));
      }
      return result;
    });
  }

  void dispose() {
    _sub?.cancel();
  }
}
```

### 9.4 多图表 / 多曲线优化

```dart
/// 多曲线共享同一个 Canvas,避免多个 CustomPaint 叠加
class MultiLineChartPainter extends CustomPainter {
  final List<ChartDataNotifier> series;
  final List<Color> colors;

  MultiLineChartPainter({required this.series, required this.colors})
      : super(repaint: Listenable.merge(series));
  //                    ↑ 合并多个 Notifier,任一变化触发 repaint

  @override
  void paint(Canvas canvas, Size size) {
    for (int s = 0; s < series.length; s++) {
      _drawSeries(canvas, size, series[s], colors[s % colors.length]);
    }
  }

  void _drawSeries(Canvas canvas, Size size, ChartDataNotifier data, Color color) {
    // ... 同 RealtimeChartPainter.paint 逻辑
  }

  @override
  bool shouldRepaint(covariant MultiLineChartPainter old) => false;
}
```

### 9.5 性能检查清单

| 检查项 | 预期 | 工具 |
|--------|------|------|
| 图表区域 widget rebuild 次数 | 首次 build 后 = 0 | DevTools Widget rebuild tracker |
| 帧时间 (raster) | < 8ms (120Hz) / < 16ms (60Hz) | DevTools Performance overlay |
| 内存占用随时间 | 平稳(环形缓冲区固定) | DevTools Memory |
| CPU 隔离 | 数据处理不在 UI isolate | `Timeline.startSync` + Observatory |
| GC 暂停 | < 2ms / 次 | DevTools Memory → GC events |

### 9.6 常见反模式

| ❌ 反模式 | ✅ 正确做法 |
|----------|-----------|
| `setState` + `fl_chart` 每 33ms 全量 rebuild | `ValueNotifier` + `CustomPainter(repaint:)` |
| `StreamBuilder` 包裹整个图表 widget | Stream → buffer → `notifier.addBatch()` |
| 每帧 `new Path()` + `new Paint()` | 复用 Paint 对象,Path 用 `reset()` |
| 数据点无限增长 `List.add()` | `RingBuffer` 固定容量 |
| 在 `paint()` 中做排序 / 聚合计算 | Isolate 预处理,paint 只读 |
| 多曲线用多个 `Stack` + `CustomPaint` | 单个 `CustomPaint` 多曲线合绘 |
| 图表不包 `RepaintBoundary` | 必须包,隔离 raster 重绘区域 |
| 120Hz 设备上以 60fps 推数据 | 用 `Ticker` 与屏幕刷新率同步 |

### 9.7 使用 Ticker 与屏幕刷新率同步

```dart
class _ChartScreenState extends State<ChartScreen>
    with SingleTickerProviderStateMixin {
  late final Ticker _ticker;
  final _data = ChartDataNotifier(capacity: 2048);
  final _source = SensorDataSource();  // 假设有原始数据源

  @override
  void initState() {
    super.initState();
    _ticker = createTicker(_onTick);
    _ticker.start();
    _source.startListening();
  }

  void _onTick(Duration elapsed) {
    // 每个 vsync 周期从源拉取最新数据
    final latest = _source.drainPending();
    if (latest.isNotEmpty) {
      _data.addBatch(latest);
    }
  }

  @override
  void dispose() {
    _ticker.dispose();
    _source.stopListening();
    _data.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    // build 只执行一次
    return RepaintBoundary(
      child: CustomPaint(
        painter: RealtimeChartPainter(data: _data),
        size: Size.infinite,
      ),
    );
  }
}
```

## 10. 必须输出的内容

- 当前需求中可能踩到的 ≥ 3 个性能风险点
- 每个风险点的:发现方式(测什么)、容忍阈值、缓解方案
- 一份 `PerformanceBudget` 清单写入 acceptance.acceptance_matrix
- 一个针对最关键页面的「滚动 / 动画」widget benchmark 测试用例

## 11. 红线

- 不要在 `build()` 里 IO / 网络 / 计算
- 不要在列表 item 里 new Controller / Provider
- 不要把整个 model 塞 `setState`,只更新最小子树
- 不要忽视 `flutter analyze --no-pub` 的提示
- 不要把 image cache 设成无限大

## 12. Flutter 3.44 性能改进

### Impeller Vulkan 优化

- **缓存内存管理**改进,减少 GPU 内存占用
- **GPU/CPU 同步**在丢帧场景下更高效
- **圆形渲染**更新为符号距离函数(SDF),消除锯齿
- **透视矩阵**处理改进,修正阴影和透视投影变换渲染

### FragmentShader 改进

- 支持通过**变量名**绑定 Uniform 参数(不再需要按索引)
- 编译器跨平台兼容性诊断增强,打包前拦截不支持旧引擎的渲染错误

### DevTools 改进

- DevTools 默认使用 **WASM** 编译,显著提升性能和稳定性
- 网络分析器新增 **Socket 数据过滤**,避免长连接高频数据刷屏
- 日志视图新增**搜索功能**

### Widget Preview（实验性）

- IDE 内存占用最多降低 **50%**
- 支持按组、名称、脚本和包 URI 筛选预览
- 详情: <https://docs.flutter.dev/tools/widget-previewer>

## 参考 / References

- Flutter 官方性能最佳实践:<https://docs.flutter.dev/perf/best-practices>
- Flutter 官方应用大小分析:<https://docs.flutter.dev/perf/app-size>
- Flutter 性能 profiling:<https://docs.flutter.dev/perf/ui-performance>
- DevTools Performance:<https://docs.flutter.dev/tools/devtools/performance>
- `cached_network_image`:<https://pub.dev/packages/cached_network_image>
- `flutter_image_compress`:<https://pub.dev/packages/flutter_image_compress>
- `infinite_scroll_pagination`:<https://pub.dev/packages/infinite_scroll_pagination>
- `flutter_native_splash`:<https://pub.dev/packages/flutter_native_splash>
- `shimmer`:<https://pub.dev/packages/shimmer>
- Impeller 渲染引擎(默认开启):<https://docs.flutter.dev/perf/impeller>
- Widget Preview: <https://docs.flutter.dev/tools/widget-previewer>
- 大列表案例 / scroll perf 文章:<https://medium.com/flutter-community/listview-performance-tips-c93476d2e60a>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **先定预算再优化**:把帧率/启动/包体写进 acceptance,可证伪。
- **测量驱动**:profile 模式 + DevTools 定位瓶颈,绝不臆测(见 mindset 模型 4)。
- **重建/重绘是主要成本**:const、`ListView.builder`、`RepaintBoundary` 三板斧。

**诚实边界:**

- 性能高度依设备/数据规模,结论需在目标机型实测,非纸面保证。
- 微优化前先确认确有瓶颈,避免过早优化。
