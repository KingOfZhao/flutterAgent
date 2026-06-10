# 滚动与 Sliver 协议(向量库优质语料·深入轮13)

> 反思缺口:"无限列表用 ListView.builder"是做法语料,但折叠头、嵌套滚动、
> "为什么 Column 套 ListView 报 unbounded height"这类问题需要协议层解释。
> 来源见 REFERENCES §28。

## 1. 为什么盒协议放不下滚动

盒(box)layout 协议传的是 min/max 宽高约束(flutter-rendering-pipeline §2);
滚动内容在主轴方向逻辑上无限长,盒协议的"给约束→报尺寸"无法表达"只实例化
可见部分"。**Sliver 协议**为此而生:Viewport 给每个 sliver 传
`SliverConstraints`(剩余可绘制空间 remainingPaintExtent、滚动偏移
scrollOffset 等),sliver 回 `SliverGeometry`(占用的滚动长度 scrollExtent、
实际绘制长度 paintExtent 等)——尺寸协商带上了"滚动位置"这一维度,
惰性按需实例化由此成为可能。

## 2. 常见报错的协议层还原

- **"unbounded height"(Column 套 ListView)**:Column 在主轴给子级无界
  约束,而 Viewport 必须知道自己的有限视口尺寸才能算 remainingPaintExtent
  → 用 `Expanded` 给出有限约束,或目录页等短列表用 `shrinkWrap: true`
  (代价:shrinkWrap 强制布局全部 children 求总长,**惰性被取消**,
  长列表上是性能事故);
- **嵌套同向滚动各滚各的**:两个独立 ScrollPosition 互不知晓——正解是
  合并为一棵 sliver 树(`CustomScrollView` + 多个 SliverList/SliverGrid),
  或页头+tab 列表场景用 `NestedScrollView` 协调内外 position;
- **ListView 套 ListView 的"为什么不卡了/卡了"**:内层 shrinkWrap 时
  失去回收,项多必卡——机制同上,不是玄学。

## 3. 折叠头与吸顶的机制

`SliverAppBar`/`SliverPersistentHeader` 的 pinned/floating 行为,本质是
sliver 根据 scrollOffset 动态报告 paintExtent≠scrollExtent:吸顶 = 滚动
长度已消耗但绘制长度保持 minExtent。理解这一点后,自定义吸顶段只需实现
`SliverPersistentHeaderDelegate`,不需要监听滚动手动摆位(后者会有一帧
延迟且破坏惯性同步)。

## 4. 回收与缓存语义(修正"懒加载"直觉)

- builder 列表**只实例化视口±cacheExtent 内的项**;滚出范围的 Element
  被回收,**State 一起销毁**——这就是"滚回来 checkbox 没了"的根因:
  列表项 State 只能放在项外(状态提升到列表数据,flutter-state-management §1),
  key 解决的是"串位",解决不了"回收销毁"(flutter-element-keys §2 的边界);
- `addAutomaticKeepAlives`/`AutomaticKeepAliveClientMixin` 可声明项常驻,
  代价是内存随项数增长,等于局部放弃回收——默认应状态提升而非 keepAlive;
- `itemExtent`/`prototypeItem` 直接告知项高,跳过逐项 layout 协商,
  长列表滚动条定位与跳转性能显著改善(机制:scrollExtent 可直接计算)。

## 5. 与本仓库其他语料的衔接

- SliverConstraints/SliverGeometry 是盒协议(轮11 §2)在滚动维度的扩展;
- 回收销毁 State 与 key 串位是两类不同问题(轮12 §2/§4);
- shrinkWrap 取消惰性是 flutter-performance §2 列表条目的机制依据。
