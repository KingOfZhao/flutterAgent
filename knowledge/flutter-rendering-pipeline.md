# Flutter 渲染管线三棵树(向量库优质语料·深入轮11)

> 反思缺口:性能/动画语料给的是"做法"(const/RepaintBoundary),但解释不了
> "为什么这些做法有效"——缺机制层语料,深问题(为什么 setState 不慢、
> 重建和重绘是不是一回事)会召回到错误层次。来源见 REFERENCES §28。

## 1. 三棵树:Widget / Element / RenderObject

- **Widget 是配置**:不可变、廉价、每帧可丢弃重建——"widget 重建很贵"是
  误解,贵的是它**引发的下游**(layout/paint)。
- **Element 是实体**:持久存在,持有 State、维护父子关系,是 BuildContext
  的真身;Widget 重建时 Element 尽量原地复用(见 flutter-element-keys)。
- **RenderObject 负责几何**:layout(算尺寸位置)与 paint(生成绘制指令);
  只有当新 Widget 的配置确实改变了 RenderObject 属性时才标记 relayout/repaint。
- 因此优化的精确表述不是"减少重建",而是**阻断"重建→relayout/repaint"的
  传播**:`const` widget 让 Element 直接跳过子树更新(canUpdate 短路),
  这就是 const 有效的机制本质。

## 2. 一帧的流水线

vsync 触发后按序执行:动画 ticker → build(脏 Element 重建)→ layout
(单遍、深度优先)→ paint(生成 Layer 树)→ 合成(Layer 树交给引擎栅格化)。

- **layout 单遍性是性能根基**:约束下行(parent 给 child min/max 约束)、
  尺寸上行(child 在约束内自报尺寸)、父定位——一遍完成,这是 Flutter
  layout 比多遍系统快的结构原因;`IntrinsicHeight`/`IntrinsicWidth` 之所以
  是性能反模式,正是因为它们强制额外的试探遍历,破坏单遍性。
- **UI 线程与 raster 线程分离**:build/layout/paint 在 UI 线程,栅格化在
  raster 线程——DevTools 帧图上两条轨道分别超预算,病因完全不同:UI 轨道
  超 = Dart 侧太重(重建半径/同步计算);raster 轨道超 = 绘制太贵
  (saveLayer、阴影、未缓存的着色器),药方对应 flutter-performance §2 的
  不同条目。

## 3. RepaintBoundary 与 Layer 的机制

- paint 产物是 Layer 树;**RepaintBoundary 切出独立 Layer**,边界内重绘
  不脏边界外——它有效的前提是"边界内频繁变、边界外稳定"且边界内容值得
  缓存;乱加边界反而增加 Layer 合成与显存成本,这是"RepaintBoundary 包一切"
  无效甚至负优化的机制解释。
- `Opacity`/`ShaderMask` 等触发 saveLayer(离屏缓冲),在 raster 线程很贵;
  动画透明度应优先 `FadeTransition`/`AnimatedOpacity`(操作 Layer 的 alpha
  而非每帧 saveLayer),与 flutter-animation-ux §2"合成层友好"同一机制。

## 4. 诊断映射(症状→树/线程→工具)

| 症状 | 机制位置 | 工具证据 |
|---|---|---|
| 整页频繁重建 | Element 树脏标记过宽 | DevTools rebuild stats / Widget Inspector |
| UI 轨道超帧预算 | build/layout 太重 | Timeline 的 Build/Layout 段 |
| raster 轨道超 | Layer 栅格化太贵 | Timeline raster 段 + checkerboardOffscreenLayers |
| 滚动时整列表重绘 | 缺 RepaintBoundary(ListView 默认已加) | debugRepaintRainbowEnabled |

## 5. 与本仓库其他语料的衔接

- 本篇是 flutter-performance 各做法的机制依据;
- Element 复用细节展开见 flutter-element-keys(轮12);
- 约束传递在滚动场景的特化见 flutter-sliver-scrolling(轮13)。
