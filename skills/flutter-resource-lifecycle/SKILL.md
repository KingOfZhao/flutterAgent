---
id: flutter-resource-lifecycle
name: Flutter 资源生命周期与内存管理规范
version: 1.0.0
platforms: [all]
tags: [lifecycle, dispose, memory, image, video, controller, performance, leak, cache]
applies_when: 需求涉及大图片加载、视频播放切换、多 TextEditingController、长列表多媒体、或需要防内存泄漏
stage_hints: [architecture, breakdown, acceptance]
---

# Flutter 资源生命周期与内存管理规范

> 直接依据:
> * Flutter 官方 Memory View: **[docs.flutter.dev/tools/devtools/memory](https://docs.flutter.dev/tools/devtools/memory)**
> * Flutter 官方 Performance best practices: **[docs.flutter.dev/perf/best-practices](https://docs.flutter.dev/perf/best-practices)**
> * Flutter ImageCache breaking change: **[docs.flutter.dev/release/breaking-changes/imagecache-large-images](https://docs.flutter.dev/release/breaking-changes/imagecache-large-images)**
> * Flutter 官方 Cookbook — Cached images: **[docs.flutter.dev/cookbook/images/cached-images](https://docs.flutter.dev/cookbook/images/cached-images)**
> * StatefulWidget lifecycle: **[api.flutter.dev/flutter/widgets/State-class.html](https://api.flutter.dev/flutter/widgets/State-class.html)**
> * video_player package: **[pub.dev/packages/video_player](https://pub.dev/packages/video_player)**
> * leak_tracker: **[pub.dev/packages/leak_tracker](https://pub.dev/packages/leak_tracker)**

---

## 1. StatefulWidget 生命周期基础

```
createState()
  └── initState()          ← 初始化 controller / subscription / 资源获取
       └── didChangeDependencies()  ← InheritedWidget 变化时触发
            └── build()
                 └── didUpdateWidget()  ← parent rebuild 且 widget 配置变化时
                      └── deactivate()  ← 从 widget 树中移除(可能重新挂回)
                           └── dispose()  ← 永久移除,必须释放所有资源
```

### 强制规则

| 创建位置 | 必须 dispose 位置 | 典型资源 |
|---------|-----------------|---------|
| `initState()` | `dispose()` | TextEditingController, AnimationController, ScrollController, FocusNode |
| `didChangeDependencies()` | `dispose()` + 条件性重建 | 依赖 MediaQuery/Theme 的资源 |
| 外部传入 (parent owns) | **不在本 State dispose** | 传入的 controller、stream |

---

## 2. 大图片场景 — 内存管理

### 2.1 ImageCache 机制

Flutter 内置 `ImageCache` 默认:
- `maximumSize` = 1000 张
- `maximumSizeBytes` = 100 MB

**大图片(4K+ / 高分辨率相册)会快速撑爆**。

```dart
// 调整全局 ImageCache 限制
void main() {
  // 在 runApp 之前配置
  PaintingBinding.instance.imageCache.maximumSizeBytes = 200 * 1024 * 1024; // 200MB
  PaintingBinding.instance.imageCache.maximumSize = 50; // 只缓存 50 张
  runApp(const MyApp());
}
```

### 2.2 大图片正确加载模式

```dart
// ❌ 错误: 直接加载 4K 原图到内存
Image.network('https://cdn.example.com/photo_4k.jpg');

// ✅ 正确: 指定 cacheWidth/cacheHeight 降采样
Image.network(
  'https://cdn.example.com/photo_4k.jpg',
  cacheWidth: 800,  // 解码到内存的尺寸,不是显示尺寸
  cacheHeight: 600,
);

// ✅ 正确: ResizeImage 包装(同等效果,适用于 ImageProvider)
Image(
  image: ResizeImage(
    NetworkImage('https://cdn.example.com/photo_4k.jpg'),
    width: 800,
    height: 600,
  ),
);
```

> **关键**: `cacheWidth` / `cacheHeight` 控制的是**解码后在 GPU 内存中的尺寸**,不是 widget 显示尺寸。一张 4000x3000 的 JPEG 解码后占 ~48MB (RGBA),降采样到 800x600 只占 ~1.9MB。

### 2.3 列表中大量图片

```dart
// ✅ 使用 cached_network_image 管理磁盘+内存缓存
CachedNetworkImage(
  imageUrl: item.imageUrl,
  memCacheWidth: 400,   // 内存中最大宽度
  maxWidthDiskCache: 800, // 磁盘缓存最大宽度
  placeholder: (_, __) => const ShimmerPlaceholder(),
  errorWidget: (_, __, ___) => const Icon(Icons.broken_image),
);

// ✅ 离屏图片自动清理: ListView.builder 自带,项离开视口后可被 GC
// 如果用 PageView/GridView 且 keepAlive,需要限制 cacheExtent
PageView.builder(
  controller: PageController(viewportFraction: 1.0),
  // 减少预加载范围,避免同时缓存太多大图
  // 默认 cacheExtent = viewport高度的250%
  itemBuilder: (context, index) => _buildPage(index),
);
```

### 2.4 主动清除缓存

```dart
// 内存压力时主动清除
void _handleMemoryPressure() {
  PaintingBinding.instance.imageCache.clear();
  PaintingBinding.instance.imageCache.clearLiveImages();
}

// 监听内存警告 (iOS: didReceiveMemoryWarning, Android: onTrimMemory)
@override
void didHaveMemoryPressure() {
  super.didHaveMemoryPressure();
  _handleMemoryPressure();
}
```

---

## 3. 视频播放器切换 — Controller 生命周期

### 3.1 核心问题

`VideoPlayerController` 每次初始化会:
1. 分配原生纹理 (Surface/CALayer)
2. 打开解码器
3. 建立网络连接或文件句柄

**切换视频时如果不正确 dispose 旧 controller,会导致**:
- 原生内存泄漏(纹理不释放)
- 文件句柄耗尽
- GPU 内存 OOM (尤其在 Android 低端机)

### 3.2 单视频切换模式

```dart
class _VideoPageState extends State<VideoPage> {
  VideoPlayerController? _controller;
  bool _isInitialized = false;

  @override
  void initState() {
    super.initState();
    _initVideo(widget.videoUrl);
  }

  @override
  void didUpdateWidget(covariant VideoPage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (oldWidget.videoUrl != widget.videoUrl) {
      _switchVideo(widget.videoUrl);
    }
  }

  Future<void> _initVideo(String url) async {
    final controller = VideoPlayerController.networkUrl(Uri.parse(url));
    try {
      await controller.initialize();
      if (!mounted) {
        // widget 已被销毁,不要 setState
        controller.dispose();
        return;
      }
      setState(() {
        _controller = controller;
        _isInitialized = true;
      });
    } catch (e) {
      controller.dispose();
      if (mounted) setState(() => _isInitialized = false);
    }
  }

  Future<void> _switchVideo(String newUrl) async {
    // 1. 暂停旧的
    await _controller?.pause();
    // 2. 标记未初始化 (显示 loading)
    setState(() => _isInitialized = false);
    // 3. dispose 旧的
    await _controller?.dispose();
    _controller = null;
    // 4. 初始化新的
    await _initVideo(newUrl);
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (!_isInitialized || _controller == null) {
      return const Center(child: CircularProgressIndicator());
    }
    return AspectRatio(
      aspectRatio: _controller!.value.aspectRatio,
      child: VideoPlayer(_controller!),
    );
  }
}
```

### 3.3 列表/Feed 中多视频(一次只播一个)

```dart
/// 只有可见视频自动播放,离开视口自动暂停+dispose
class VideoFeedItem extends StatefulWidget {
  final String videoUrl;
  final bool isVisible; // 通过 VisibilityDetector 计算

  const VideoFeedItem({required this.videoUrl, required this.isVisible});
  @override State<VideoFeedItem> createState() => _VideoFeedItemState();
}

class _VideoFeedItemState extends State<VideoFeedItem> {
  VideoPlayerController? _controller;

  @override
  void didUpdateWidget(covariant VideoFeedItem oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.isVisible && !oldWidget.isVisible) {
      _activate();
    } else if (!widget.isVisible && oldWidget.isVisible) {
      _deactivate();
    }
  }

  void _activate() async {
    if (_controller != null) return;
    final c = VideoPlayerController.networkUrl(Uri.parse(widget.videoUrl));
    await c.initialize();
    if (!mounted) { c.dispose(); return; }
    c.play();
    setState(() => _controller = c);
  }

  void _deactivate() {
    _controller?.pause();
    _controller?.dispose();
    _controller = null;
    if (mounted) setState(() {});
  }

  @override
  void dispose() {
    _controller?.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    if (_controller == null || !_controller!.value.isInitialized) {
      return const AspectRatio(
        aspectRatio: 16 / 9,
        child: ColoredBox(color: Colors.black12, child: Center(child: Icon(Icons.play_arrow))),
      );
    }
    return AspectRatio(
      aspectRatio: _controller!.value.aspectRatio,
      child: VideoPlayer(_controller!),
    );
  }
}
```

### 3.4 预加载策略

```dart
/// 预初始化下一个视频(不播放),切换时零延迟
class VideoPreloader {
  final Map<String, VideoPlayerController> _cache = {};
  static const int maxPreloaded = 2;

  Future<VideoPlayerController> getOrCreate(String url) async {
    if (_cache.containsKey(url)) return _cache[url]!;
    // 淘汰最老的
    while (_cache.length >= maxPreloaded) {
      final oldest = _cache.keys.first;
      await _cache.remove(oldest)?.dispose();
    }
    final c = VideoPlayerController.networkUrl(Uri.parse(url));
    await c.initialize();
    _cache[url] = c;
    return c;
  }

  Future<void> disposeAll() async {
    for (final c in _cache.values) {
      await c.dispose();
    }
    _cache.clear();
  }
}
```

---

## 4. 多 TextEditingController 管理

### 4.1 问题场景

动态表单(如注册多字段、聊天中多输入框)中频繁创建/销毁 `TextEditingController`:
- 每个 controller 注册原生平台通道监听
- 未 dispose 的 controller = 内存泄漏 + 可能的 widget binding 错误

### 4.2 静态已知数量的 Controllers

```dart
class _ProfileFormState extends State<ProfileForm> {
  // ✅ 在 State 中声明,dispose 中释放
  late final TextEditingController _nameCtrl;
  late final TextEditingController _emailCtrl;
  late final TextEditingController _phoneCtrl;
  late final TextEditingController _bioCtrl;

  @override
  void initState() {
    super.initState();
    _nameCtrl = TextEditingController(text: widget.profile.name);
    _emailCtrl = TextEditingController(text: widget.profile.email);
    _phoneCtrl = TextEditingController(text: widget.profile.phone);
    _bioCtrl = TextEditingController(text: widget.profile.bio);
  }

  @override
  void dispose() {
    _nameCtrl.dispose();
    _emailCtrl.dispose();
    _phoneCtrl.dispose();
    _bioCtrl.dispose();
    super.dispose();
  }
}
```

### 4.3 动态数量 Controllers (列表/动态表单)

```dart
class _DynamicFormState extends State<DynamicForm> {
  final List<TextEditingController> _controllers = [];
  final List<FocusNode> _focusNodes = [];

  @override
  void initState() {
    super.initState();
    _addField(); // 至少一个
  }

  void _addField() {
    final ctrl = TextEditingController();
    final node = FocusNode();
    setState(() {
      _controllers.add(ctrl);
      _focusNodes.add(node);
    });
  }

  void _removeField(int index) {
    // ✅ 移除前必须 dispose
    _controllers[index].dispose();
    _focusNodes[index].dispose();
    setState(() {
      _controllers.removeAt(index);
      _focusNodes.removeAt(index);
    });
  }

  @override
  void dispose() {
    // ✅ 全部 dispose
    for (final c in _controllers) { c.dispose(); }
    for (final n in _focusNodes) { n.dispose(); }
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      itemCount: _controllers.length,
      itemBuilder: (_, i) => Row(
        children: [
          Expanded(
            child: TextField(
              controller: _controllers[i],
              focusNode: _focusNodes[i],
            ),
          ),
          IconButton(
            icon: const Icon(Icons.remove_circle),
            onPressed: () => _removeField(i),
          ),
        ],
      ),
    );
  }
}
```

### 4.4 使用 Riverpod/BLoC 管理 Controllers

```dart
// ✅ Riverpod autoDispose: 页面离开自动清理
@riverpod
class FormControllers extends _$FormControllers {
  final List<TextEditingController> _ctrls = [];

  @override
  List<TextEditingController> build() {
    // autoDispose 时清理
    ref.onDispose(() {
      for (final c in _ctrls) { c.dispose(); }
    });
    _ctrls.add(TextEditingController());
    return List.unmodifiable(_ctrls);
  }

  void addField() {
    _ctrls.add(TextEditingController());
    state = List.unmodifiable(_ctrls);
  }

  void removeField(int index) {
    _ctrls[index].dispose();
    _ctrls.removeAt(index);
    state = List.unmodifiable(_ctrls);
  }
}
```

---

## 5. 通用生命周期最佳实践

### 5.1 Disposable 资源清单

| 资源类型 | 创建 | 必须 dispose | 常见泄漏原因 |
|---------|------|-------------|-------------|
| `TextEditingController` | initState / 动态 | dispose() | 动态表单中忘记清理被移除的 |
| `AnimationController` | initState (需 vsync) | dispose() | TabBar 切换时未清理 |
| `ScrollController` | initState | dispose() | 嵌套滚动场景多个 controller |
| `FocusNode` | initState / 动态 | dispose() | 搜索框 + 列表场景 |
| `VideoPlayerController` | initState / 切换时 | dispose() | 切换视频未 dispose 旧的 |
| `StreamSubscription` | initState | cancel() | 忘记取消 → 回调引用旧 State |
| `Timer` / `Timer.periodic` | initState / 方法 | cancel() | 后台轮询未停止 |
| `ChangeNotifier` (自建) | 外部或 initState | dispose() | Provider 自动; 手动持有需自行清理 |
| `WebSocket` / `IOWebSocketChannel` | initState | sink.close() | 页面退出连接未断 |
| `Isolate` / `ReceivePort` | spawn | kill() + close() | 后台计算未终止 |

### 5.2 `mounted` 检查模板

```dart
Future<void> _loadData() async {
  final data = await repository.fetchHeavyData();
  // ✅ 异步操作后必须检查 mounted
  if (!mounted) return;
  setState(() => _data = data);
}
```

### 5.3 Mixin 简化多 controller 管理

```dart
mixin DisposableMixin<T extends StatefulWidget> on State<T> {
  final List<ChangeNotifier> _disposables = [];

  /// 注册一个 disposable 对象,在 dispose 时自动清理
  C track<C extends ChangeNotifier>(C obj) {
    _disposables.add(obj);
    return obj;
  }

  @override
  void dispose() {
    for (final d in _disposables) {
      d.dispose();
    }
    super.dispose();
  }
}

// 使用
class _MyState extends State<MyWidget> with DisposableMixin {
  late final nameCtrl = track(TextEditingController());
  late final emailCtrl = track(TextEditingController());
  late final scrollCtrl = track(ScrollController());
  // 无需手动 dispose,mixin 自动处理
}
```

---

## 6. 内存泄漏检测

### 6.1 DevTools Memory View

```bash
# 启动 DevTools 并连接到正在运行的 app
flutter run --debug
# 打开 DevTools → Memory tab → 观察:
# 1. Heap 是否持续上升
# 2. 特定类型 instance 数量是否只增不减
# 3. 切换页面后是否存在 "not GCed" 的旧 State 对象
```

### 6.2 leak_tracker (自动检测)

```dart
// pubspec.yaml
dev_dependencies:
  leak_tracker: ^10.0.0
  leak_tracker_flutter_testing: ^3.0.0

// 测试中启用
testWidgets('no memory leaks in video page', (tester) async {
  await tester.pumpWidget(const MaterialApp(home: VideoPage()));
  // 操作页面...
  await tester.pumpWidget(const SizedBox()); // 销毁
  // leak_tracker 自动检测未 dispose 的对象
});
```

### 6.3 Flutter 3.44 自动检测

Flutter 框架内部在 debug 模式下会对已知 disposable 类型(如 `TextEditingController`, `AnimationController`)进行泄漏追踪,控制台会打印警告:

```
A TextEditingController was used after being disposed.
Once you have called dispose() on a TextEditingController, it can no longer be used.
```

---

## 7. 性能优化模式

### 7.1 图片 + 视频混合列表

```dart
class MediaFeed extends StatelessWidget {
  @override
  Widget build(BuildContext context) {
    return ListView.builder(
      // 限制预加载区域,减少同时解码的媒体数
      cacheExtent: MediaQuery.of(context).size.height * 0.5,
      itemBuilder: (_, index) {
        final item = items[index];
        return item.isVideo
            ? _VideoTile(url: item.url, isVisible: /* VisibilityDetector */)
            : CachedNetworkImage(
                imageUrl: item.url,
                memCacheWidth: 400,
                placeholder: (_, __) => const ShimmerPlaceholder(),
              );
      },
    );
  }
}
```

### 7.2 页面切换时的资源释放

```dart
// 使用 AutomaticKeepAliveClientMixin 时,切换 Tab 不 dispose
// 如果含重资源,应主动在 deactivate 释放、activate 重建
class _HeavyTabState extends State<HeavyTab>
    with AutomaticKeepAliveClientMixin {
  @override
  bool get wantKeepAlive => true; // 保活

  VideoPlayerController? _video;

  @override
  void activate() {
    super.activate();
    _video = VideoPlayerController.networkUrl(Uri.parse(widget.url));
    _video!.initialize().then((_) { if (mounted) setState(() {}); });
  }

  @override
  void deactivate() {
    _video?.dispose();
    _video = null;
    super.deactivate();
  }
}
```

### 7.3 Isolate 处理大图解码

```dart
import 'dart:isolate';
import 'package:image/image.dart' as img;

/// 在独立 Isolate 中解码+缩放大图,避免阻塞 UI 线程
Future<Uint8List> decodeAndResize(Uint8List rawBytes, int targetWidth) async {
  return await Isolate.run(() {
    final decoded = img.decodeImage(rawBytes)!;
    final resized = img.copyResize(decoded, width: targetWidth);
    return Uint8List.fromList(img.encodePng(resized));
  });
}
```

---

## 8. 必须产出

涉及多媒体 / 多 controller 场景时,architecture 和 breakdown 必须包含:

1. **资源生命周期表**: 每种资源(controller/player/subscription)的创建时机、归属、dispose 时机
2. **内存预算**: 图片缓存上限、同时存在的视频 controller 数量上限
3. **切换策略**: 视频切换时 dispose → init 的完整时序
4. **降级方案**: 低端设备内存警告时的降级行为(清缓存、降画质、停止预加载)
5. **泄漏检测**: CI 中加入 `leak_tracker` 测试用例

## 9. 红线

- 不要在 `build()` 中创建 Controller(每次 rebuild 都会泄漏)
- 不要忘记 `mounted` 检查(async 回调中 setState 必检)
- 不要把 4K 图片原尺寸解码(必须设 `cacheWidth` / `cacheHeight` 或 `ResizeImage`)
- 不要在列表中同时初始化 N 个 VideoPlayerController(一次最多 1-2 个活跃)
- 不要用 `GlobalKey` 跨页面持有 State(会阻止 GC)
- 不要忽略 `didUpdateWidget` 中的资源切换(parent rebuild 时 url 可能已变)
- 不要手动 dispose 由 Provider/Riverpod 管理的 controller(框架负责)

---

## 参考

- Flutter 官方 Memory DevTools: <https://docs.flutter.dev/tools/devtools/memory>
- Flutter 官方 Performance best practices: <https://docs.flutter.dev/perf/best-practices>
- Flutter ImageCache 大图策略: <https://docs.flutter.dev/release/breaking-changes/imagecache-large-images>
- Flutter Cookbook — Cached images: <https://docs.flutter.dev/cookbook/images/cached-images>
- StatefulWidget lifecycle: <https://api.flutter.dev/flutter/widgets/State-class.html>
- video_player package: <https://pub.dev/packages/video_player>
- cached_network_image: <https://pub.dev/packages/cached_network_image>
- visibility_detector: <https://pub.dev/packages/visibility_detector>
- leak_tracker: <https://pub.dev/packages/leak_tracker>
- Flutter Don't Fear the Garbage Collector: <https://medium.com/flutter/flutter-dont-fear-the-garbage-collector-d69b3ff1ca30>
- ResizeImage API: <https://api.flutter.dev/flutter/painting/ResizeImage-class.html>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **凡 create 必 dispose**:controller/stream/animation 的释放是契约。
- **资源有重量**:大图/视频按需加载、及时释放、限制并发。
- **泄漏是累积的**:用 leak_tracker / DevTools Memory 早查早治。

**诚实边界:**

- 泄漏定位需运行时剖析,静态规范无法替代 DevTools 实测。
- GC 行为不可精确预测,关注趋势而非单点数字。
