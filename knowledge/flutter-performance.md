# Flutter 性能优化(向量库优质语料)

> 用途:为"卡顿/掉帧/内存/包体积"类需求提供检索接地语料。来源见 REFERENCES §25。

## 1. 诊断先于优化

- **必须在 profile 模式测**:debug 模式带断言与 JIT,性能数据无意义;release 模式
  无法接 DevTools。`flutter run --profile` + DevTools Performance 页是标准路径。
- 60fps 预算是每帧 16.7ms(120Hz 设备 8.3ms),UI 线程与 raster 线程分开看:
  UI 线程超时 → build/layout 太贵;raster 线程超时 → 绘制/着色器问题。

## 2. build 开销控制

- **缩小重建半径**:把 `setState`/监听下推到最小子树;用 `const` 构造器让框架
  跳过不变子树;长列表必用 `ListView.builder` 惰性构建,不要 `ListView(children:)`。
- **避免在 build 里做工作**:网络/解码/排序放到 state 初始化或 isolate;
  build 必须是纯函数级别的便宜操作。
- `RepaintBoundary` 隔离频繁重绘区域(如动画),避免整页重绘——但每个 boundary
  有内存代价,按 DevTools 的 repaint rainbow 证据加,不要预防性乱加。

## 3. 卡顿大户

- **着色器编译卡顿(shader jank)**:首次动画掉帧的常见原因;Impeller 引擎
  (iOS 已默认,Android 逐步默认)通过预编译管线消除此类卡顿——升级引擎优先于
  手工 warm-up。
- **大图解码**:用 `cacheWidth/cacheHeight` 按显示尺寸解码,避免全尺寸位图占内存;
  列表图片配占位与渐进加载。
- **同步 IO 与 JSON 大解析**:放 `compute()`/isolate,Dart 单线程事件循环里任何
  超过几毫秒的同步工作都直接吃帧预算。

## 4. 包体积

`flutter build apk --analyze-size` 看构成;主要手段:按 ABI 拆分(`--split-per-abi`)、
延迟加载组件(deferred components,仅 Android)、压缩/按需资源、检查传递依赖。
