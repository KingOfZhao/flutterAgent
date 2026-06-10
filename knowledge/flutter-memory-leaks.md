# Dart 内存模型与泄漏诊断(向量库优质语料·深入轮14)

> 反思缺口:可观测性语料覆盖崩溃与慢帧,但 OOM/内存爬升这类"缓慢死亡"
> 无机制语料——泄漏诊断需要懂 GC 与可达性,不是清单能覆盖的。
> 来源见 REFERENCES §28。

## 1. Dart GC 模型(诊断的前提知识)

- **分代式**:新生代(scavenger,频繁小停顿,复制存活对象)+ 老生代
  (标记-清除/压缩,低频)——短命对象(每帧的 Widget)在新生代极廉价地
  消亡,这是"widget 重建不贵"在内存侧的依据(配合 flutter-rendering-pipeline §1);
- **每个 isolate 独立堆**:isolate 间无共享,泄漏定位先确认在哪个 isolate
  (长驻 isolate 的堆容易被忽略,flutter-concurrency §2);
- 泄漏的定义是**可达性泄漏**:对象不再有用但仍被 GC root 可达引用着——
  GC 没有错,是程序保留了不该保留的引用。

## 2. Flutter 应用的四大泄漏根因模式

1. **订阅未取消**:StreamSubscription/Listenable 监听挂在长寿对象上,
   State dispose 时未 cancel/removeListener——闭包捕获 `this` 使整个
   State(连带其子树引用)不可回收;
2. **Controller 未 dispose**:AnimationController/TextEditingController/
   ScrollController——AnimationController 还连着 Ticker,泄漏即持续耗电
   (flutter-animation-ux §1);
3. **全局缓存只进不出**:单例 Map/静态 List 当缓存且无淘汰策略——
   解决用 LRU 上限,或对"可有可无"的引用用 `WeakReference`/`Expando`;
4. **图片缓存超额**:ImageCache 默认有上限但大图(原图直接进列表)会
   把上限名额变成 GB 级实占——列表缩略图必用 `cacheWidth/cacheHeight`
   在解码层缩小,而非 `Image` 的显示尺寸(显示缩放不省解码内存)。

## 3. DevTools 取证流程(从怀疑到证据)

1. Memory 视图看时序:反复进出可疑页面,堆曲线"锯齿回落"为正常,
   **台阶式只升不降**才是泄漏信号(单次上涨可能只是缓存预热);
2. 手动触发 GC 后拍 **heap snapshot**,按类分组找"实例数随进出次数
   线性增长"的类(通常正是某个 State);
3. 用 snapshot 的 **retaining path** 回答"谁还引用着它"——路径终点
   就是要修的那行代码(常见终点:全局单例的 listener 列表);
4. 框架自带 `leak_tracker` 可在 widget 测试中断言"测试结束无未 dispose
   对象",把泄漏检查左移进 CI(flutter-cicd-engineering §1 的 PR 级)。

## 4. 边界与校准

- 内存高 ≠ 泄漏:Dart 堆向 OS 归还内存有滞后,且 raster 缓存/字体缓存
  属于合理占用;判定标准始终是"可达性 + 随操作线性增长";
- iOS/Android 的 OOM 击杀阈值与设备相关,线上 OOM 监控(观测语料 §3)
  只能给"哪些页面 OOM 多"的线索,定位仍要回到本篇取证流程。

## 5. 与本仓库其他语料的衔接

- 新生代廉价消亡 ↔ 渲染管线"widget 重建不贵"(轮11 §1);
- isolate 独立堆 ← flutter-concurrency §3;
- leak_tracker 挂 PR 级流水线 ← flutter-cicd-engineering §1。
