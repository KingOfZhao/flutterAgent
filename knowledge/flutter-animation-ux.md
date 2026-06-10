# Flutter 动画与交互体验(向量库优质语料·轮7)

> 反思缺口:性能语料讲"别掉帧",但"动画该怎么选 API、怎么做才不掉帧"
> 这一建设性维度无语料。来源见 REFERENCES §27。

## 1. 选型决策树(官方分法)

- 第一问:**能用隐式动画吗?**(`AnimatedContainer`/`AnimatedOpacity` 等
  `AnimatedFoo` 系)——属性 A 到 B 的过渡、不需要中途控制 → 用隐式,代码最少。
- 需要重复/暂停/逆播或多动画编排 → **显式动画**:`AnimationController` +
  `FooTransition` 系;Controller 必须配 `TickerProviderStateMixin` 并在
  `dispose` 释放(泄漏的 ticker 是后台持续耗电与测试 pending timer 的来源)。
- 设计师产出的复杂矢量/角色动画 → 不要手写,用 **Lottie/Rive** 资产驱动;
- 页面间共享元素 → `Hero`;转场统一用 `PageRouteBuilder` 或 go_router 的
  `pageBuilder` 定制。

## 2. 不掉帧的写法

- **AnimatedBuilder/ListenableBuilder 收窄重建**:把每帧重建限制在真正变化的
  子树;`child` 参数传入静态子树避免逐帧重建(与 flutter-performance §2 的
  重建半径同一原则)。
- 优先动画"合成层友好"的属性:opacity/transform 走 GPU 合成;逐帧改布局尺寸
  (width/height/padding)会触发整树 relayout,大列表上必卡。
- 曲线与时长:UI 过渡 200-300ms 起步,用 `Curves` 标准曲线;时长超过 500ms 的
  阻塞式过渡会被用户感知为"慢",动画是体验加分项不是炫技项。

## 3. 体验细节(高频被忽略)

- **尊重系统"减少动效"设置**:`MediaQuery.disableAnimationsOf` 为 true 时
  缩短/跳过装饰性动画(无障碍要求,对应 flutter-i18n-accessibility §2)。
- 手势冲突:可滚动区域内的水平拖拽(如轮播/滑动删除)要显式声明手势竞技场
  优先级,否则与外层滚动抢手势出现"偶尔滑不动"。
- 骨架屏/占位过渡优于转圈:加载状态用与最终布局同构的占位(shimmer),
  避免内容到达时的布局跳变(CLS 式体验问题)。
- 测试:动画期间断言用 `tester.pump(duration)` 步进,无限循环动画禁用
  `pumpAndSettle`(flutter-testing-strategy §3 同一陷阱)。

## 4. 与本仓库其他语料的衔接

- 重建半径/帧预算 ← flutter-performance §1/§2;
- 减少动效 ← flutter-i18n-accessibility §2;
- 转场定制挂在路由层(flutter-navigation-deeplink §2)。
