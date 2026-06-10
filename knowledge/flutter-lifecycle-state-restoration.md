# 应用生命周期与进程死亡恢复(向量库优质语料·深入轮15)

> 反思缺口:离线/状态管理语料都假设进程活着;"后台被系统杀掉再回来"
> 是移动端独有且测试环境里几乎不会自然复现的状态丢失源,无语料覆盖。
> 来源见 REFERENCES §28。

## 1. 生命周期模型(Flutter 视角)

- `AppLifecycleState`:resumed / inactive(失焦但可见,如来电横幅)/
  hidden / paused(完全后台)/ detached;用 `AppLifecycleListener`
  (3.13+)或 `WidgetsBindingObserver` 订阅;
- 三个语义不同的"离开",处理也不同:
  - **inactive**:别停音视频(可能只是下拉通知栏),但该打隐私遮罩
    (任务切换器截图,flutter-mobile-security §2);
  - **paused**:释放相机/传感器等独占资源,落盘未保存数据——这是
    "最后可靠的保存时机";
  - **进程死亡**:paused 之后系统随时可能直接杀进程,**没有任何 Dart
    回调会执行**——这是与桌面/Web 心智模型的根本差异。

## 2. 进程死亡:被低估的常态

Android 低内存即回收后台进程(用户切去拍照再切回是高频触发路径);
回来时系统重建 Activity,Flutter 引擎冷启动,**所有内存状态归零但用户
期望"接着用"**。bug 表现:填了一半的表单清空、回到首页而非原页面。
测试不会自然复现的原因:开发机内存充裕。**人工复现手段**:Android
开发者选项"不保留活动",或后台时 `adb shell am kill <package>`——
该场景应纳入发布前手测清单(flutter-testing-strategy §4)。

## 3. 恢复的两层机制(不要混为一谈)

1. **RestorationManager(会话级,系统托管)**:`restorationScopeId` +
   `RestorationMixin` 把瞬态 UI 状态(导航栈、滚动位置、文本框草稿)
   注册进系统的保存实例状态;**只在"进程死亡后恢复"时还原,正常冷启动
   不还原**——语义对应 Android 的 saved instance state,小而瞬态,
   不要塞业务数据;
2. **本地持久化(应用级,自己托管)**:登录态、草稿、购物车走数据库/
   偏好存储(flutter-offline-sync §1),冷启动也要在;
- 判别准则:**"用户重启手机后还应该在"的进库,"只是切走一下不该丢"的
  进 restoration**。导航栈恢复需配 go_router 的 `restorationScopeId`
  与页面级 RestorationMixin 配合,只持久化"路径"而非页面对象。

## 4. 高频陷阱

- `dispose` 不是保存时机:进程被杀时不调用;依赖 dispose 落盘 = 线上
  随机丢数据;保存挂 paused(或字段级随改随存的防抖落盘);
- iOS 没有等价的"保留活动"调试开关,但同样会杀后台进程——只在
  Android 测过 restoration 不代表 iOS 行为已验证;
- 引擎冷启动恢复时,深链/通知点击可能与 restoration 竞争初始路由:
  深链优先级应高于恢复栈(flutter-navigation-deeplink §3 的冷启动
  矩阵需加"进程死亡恢复"一列)。

## 5. 与本仓库其他语料的衔接

- 持久化层选型 ← flutter-offline-sync §1;
- 滚动位置恢复的 PageStorageKey 是 restoration 的近亲机制(flutter-element-keys §3);
- 隐私遮罩 ← flutter-mobile-security §2;冷启动深链矩阵 ← flutter-navigation-deeplink §3。
