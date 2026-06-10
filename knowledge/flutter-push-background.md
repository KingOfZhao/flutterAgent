# 推送与后台任务(向量库优质语料·轮19)

> 反思缺口:进程死亡语料讲了"被杀后恢复",但"被杀后还要干活"(推送
> 唤醒/后台同步/定时任务)是另一条平台差异最大的链路,零覆盖。
> 来源见 REFERENCES §29。

## 1. 推送的双通道本质

- 推送不是 app 的能力而是 OS 的能力:Android 走 FCM,iOS 走 APNs
  (FCM 在 iOS 上也是 APNs 的封装)——国内无 GMS 设备 FCM 不可达,
  需厂商通道(华为/小米等)或自建长连接,这是国内发行的架构级前提;
- 两类消息语义完全不同:**notification 消息**(系统托盘直接展示,
  app 后台时不经过你的代码)vs **data 消息**(交给 app 处理)——
  "后台收到推送后先拉数据再展示"必须用 data 消息 + 本地通知,
  且 iOS 受 background push 节流,不保证送达;
- token 生命周期:FCM token 会轮换(`onTokenRefresh` 必须监听并上报
  服务端),只在登录时上报一次是"推送莫名收不到"的高频根因。

## 2. 点击推送的路由链路(与深链同构)

冷启动(`getInitialMessage`)/后台点击(`onMessageOpenedApp`)/前台
(`onMessage` 自己决定是否展示)三入口,与深链冷启动矩阵
(flutter-navigation-deeplink §3)同构,也同样要与状态恢复竞争初始
路由(flutter-lifecycle-state-restoration §4)——三者(深链/推送/
恢复栈)的优先级要显式定义,而不是看谁后执行谁赢。

## 3. 后台执行:平台给的是"机会"不是"保证"

- Dart 代码后台运行的前提是引擎活着;被杀后要执行,需要平台机制
  拉起一个 **headless 引擎**(独立 isolate,无 UI,插件需重新初始化,
  与主 isolate 不共享内存——flutter-concurrency §3 同规则;回调函数
  必须是顶层/静态函数,因为要跨引擎重启序列化入口点);
- 任务类型选型:延迟可观的周期任务用 workmanager(Android WorkManager
  / iOS BGTaskScheduler)——**iOS 的执行时机由系统按用户使用模式决定,
  不可指望准点**;高精度定时在移动端后台基本不存在,改为"推送唤醒 +
  服务端定时"架构;
- 省电机制(Doze/厂商激进查杀)使后台任务"测试机上跑通,线上部分
  设备不执行"成为常态——后台同步必须幂等且补偿式(下次前台启动时
  对账,flutter-offline-sync §2 的队列就是兜底)。

## 4. 工程纪律

- 权限:Android 13+ 通知运行时权限(POST_NOTIFICATIONS),iOS 首次
  申请的时机影响授权率——在解释价值后再弹系统框;
- 后台 isolate 里崩溃不会走主 isolate 的 onError 链
  (flutter-observability §1 的盲区),需单独挂错误上报;
- 测试:推送链路无法纯本地验证,发布前手测清单加"杀进程后点推送
  能否正确路由"一项(flutter-testing-strategy §4)。

## 5. 与本仓库其他语料的衔接

- 三入口路由矩阵 ← flutter-navigation-deeplink §3;headless isolate ← flutter-concurrency §3;
- 补偿式同步 ← flutter-offline-sync §2;错误出口盲区 ← flutter-observability §1。
