# Flutter 导航与深链(向量库优质语料·轮2)

> 反思缺口:已有语料覆盖状态/数据/性能/测试/发布/架构,但"路由怎么设计、深链怎么接"
> 这一高频需求无知识级语料(只有 skill)。来源见 REFERENCES §26。

## 1. 选型:Navigator 1.0 / 2.0 / go_router

- **Navigator 1.0(命令式 push/pop)**:无深链、无 web URL 同步需求的小应用仍然
  够用且最简单——不要为"以后可能要"提前引入声明式路由。
- **Navigator 2.0(Router API)**:声明式、功能完备但样板极重,官方自己也承认
  直接使用门槛高;一般通过封装库使用而非裸写。
- **go_router**:官方维护的 Router API 封装,URL 路由表 + 重定向 + ShellRoute,
  是"需要深链/web/受守卫路由"场景的默认答案。需要路由栈完全可编程控制
  (如复杂向导流)时才考虑 auto_route 或裸 Router API。

## 2. go_router 实践要点

- **守卫用 redirect,不要在页面里弹回**:登录态等前置条件写在顶层/路由级
  `redirect`,并配 `refreshListenable`(监听认证状态变化自动重算重定向)——
  在 build 里手动 `context.go('/login')` 会闪现受保护页面。
- **路径参数 vs 查询参数**:资源身份用路径段(`/order/:id`),可选过滤用 query;
  深链恢复要求"页面所需的最小状态都能从 URL 重建",不能依赖内存里的上一页状态。
- **ShellRoute 管 tab 框架**:底部导航 + 各 tab 独立栈用 StatefulShellRoute,
  不要在 tab 切换时重建整个子树(丢滚动位置/状态)。
- 路由表是单一事实源:页面间跳转一律走命名路由/typed routes(go_router_builder
  生成类型安全 API),裸字符串路径散落各处是重构噩梦。

## 3. 深链接入

- **Android App Links / iOS Universal Links** 需要域名验证文件
  (`assetlinks.json` / `apple-app-site-association`)托管在 HTTPS 根路径,
  缺这一步只能得到可被任意应用劫持的 custom scheme;custom scheme 仅用于
  OAuth 回调等内部流转。
- 冷启动深链与运行中深链路径不同:必须分别测试(应用未运行时点链接是最常漏测的)。
- 深链落地页要做降级:目标资源不存在/无权限时跳兜底页,不能白屏或崩溃。

## 4. 与本仓库其他语料的衔接

- 守卫依赖认证状态 → 状态槽位见 flutter-state-management;
- "URL 可重建最小状态"与架构层"ViewModel 不持 BuildContext"同源(flutter-app-architecture §3);
- 深链回归属于 integration 层金路径用例(flutter-testing-strategy §1)。
