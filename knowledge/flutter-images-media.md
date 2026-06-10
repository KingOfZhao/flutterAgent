# 图片与媒体管线(向量库优质语料·轮18)

> 反思缺口:图片是多数 app 内存与流量的最大头,泄漏语料只点到 ImageCache
> 一处;解码/缓存/占位/视频这条媒体管线无系统语料。来源见 REFERENCES §29。

## 1. 图片加载管线机制(为什么大图卡且费内存)

- 链路:获取字节 → **解码成位图(CPU 密集,在专门的解码线程)** →
  上传 GPU 纹理 → 绘制;内存占用由**解码后尺寸**决定(宽×高×4 字节),
  与文件体积(jpg 压缩后几百 KB)无关——4000×3000 原图解码即 ~46MB;
- 所以核心手段是**解码层降采样**:`Image.network(cacheWidth/cacheHeight)`
  或 `ResizeImage`,按显示尺寸×devicePixelRatio 给值;只缩 `width/height`
  显示属性不省任何内存(flutter-memory-leaks §2);
- 首帧解码大图可能掉帧:列表场景配合 `precacheImage` 预热关键图。

## 2. 缓存的三层与失效

- **内存层 ImageCache**:默认 1000 张/100MB 上限,key 是 ImageProvider
  相等性——URL 带随机签名参数会让同一张图永不命中(高频流量浪费根因);
- **磁盘层**:框架不提供,`cached_network_image` 或自管(配合 HTTP
  缓存头);CDN 图片应让 URL 内容寻址(变更即变 URL),客户端就可
  无限期缓存;
- **构建产物层**:资源图标用矢量或按分辨率变体(2.0x/3.0x 目录),
  大位图资源进包直接膨胀体积(flutter-release-engineering §1)。

## 3. 占位与渐进体验

- 占位三档:纯色/骨架(flutter-animation-ux §4)→ 模糊缩略(LQIP/
  blurhash,几十字节先渲染)→ 渐进 jpg;列表图必须**固定占位尺寸**,
  图到达后高度跳变会引起滚动跳动(布局位移,sliver 维度突变,
  flutter-sliver-scrolling §1);
- `FadeInImage`/frameBuilder 做到达淡入;错误兜底 errorBuilder 必配
  (空白方块是最差体验)。

## 4. 视频与相机的资源纪律

- video_player/camera 的 controller 是**原生侧资源句柄**:不 dispose
  泄漏的不是 Dart 堆而是原生解码器/相机会话(DevTools 看不见,
  flutter-memory-leaks §4 的盲区)——paused 生命周期必须释放相机
  (flutter-lifecycle-state-restoration §1);
- 列表内联视频:同屏只保活当前可见的 1 个 controller,滚出即释放,
  位置用回收机制的 onDispose 钩子触发;
- 视频走平台解码器(PlatformView/纹理桥接),性能红线参
  flutter-platform-integration §4。

## 5. 与本仓库其他语料的衔接

- 解码内存 ← flutter-memory-leaks §2;占位骨架 ← flutter-animation-ux §4;
- 高度跳变 ← flutter-sliver-scrolling;原生句柄释放 ← flutter-lifecycle-state-restoration §1。
