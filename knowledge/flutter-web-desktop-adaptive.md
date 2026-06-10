# Web 与桌面端适配(向量库优质语料·轮17)

> 反思缺口:全部语料默认移动端;Flutter 的多平台卖点落到 Web/桌面时
> 有一整套不同的输入模型/渲染后端/布局范式,零覆盖。来源见 REFERENCES §29。

## 1. 自适应(adaptive)与响应式(responsive)的区分

- 响应式 = 同一布局随尺寸伸缩;自适应 = 按平台/输入方式换交互范式
  (触摸 vs 鼠标悬停/右键,底部导航 vs 侧边栏);
- **按窗口尺寸而非按设备类型分支**:平板/桌面窗口/折叠屏让"设备类型
  推断尺寸"失效——用 `MediaQuery.sizeOf` 或 `LayoutBuilder` 按 Material
  断点(compact <600 / medium / expanded ≥840)切布局;
- `sizeOf`/`viewInsetsOf` 等切面方法比整只 `MediaQuery.of` 重建半径小
  (flutter-rendering-pipeline §1 的传播阻断同理);
- 导航自适应的标准形态:compact 用 NavigationBar,expanded 用
  NavigationRail/抽屉——路由结构不变,只换壳(flutter-navigation-deeplink §1)。

## 2. 鼠标/键盘输入模型(移动端心智的盲区)

- 桌面/Web 用户期望:悬停反馈(`MouseRegion`/InkWell 自带 hover)、
  右键上下文菜单(`ContextMenuRegion`)、滚轮、文本可选中
  (`SelectionArea` 包根部,移动端默认不可选是合理的,桌面不可选是 bug);
- 键盘快捷键走 `Shortcuts`/`Actions`(Intent 映射)而非裸 KeyboardListener,
  与焦点遍历(flutter-forms-input §2)同属桌面必修;
- 触摸目标 48dp 准则在鼠标场景可放宽,但同一代码两端跑时取严。

## 3. Flutter Web 的渲染后端与启动成本

- 两种后端:**CanvasKit**(wasm 渲染引擎,保真度高/初始包大)与
  HTML renderer 已弃用,3.29+ 默认 CanvasKit,wasm GC 路线(skwasm)
  是性能方向;
- 结构性代价:首包体积与冷启动远高于原生 Web 框架——Flutter Web 适合
  "应用型"站点(工具/后台/已有 Flutter 代码复用),不适合内容型/SEO
  敏感站点(文本是画布绘制,SEO 基本不可用,这是选型级结论);
- Web 平台差异点:无 dart:io(条件导入 `kIsWeb` 分支)、CORS 约束下
  dio/http 走浏览器 fetch(证书锁定不可用,flutter-mobile-security §3
  的边界)、deep link 即 URL 路由(go_router 天然契合)。

## 4. 桌面端工程要点

- 窗口管理(最小尺寸/记忆位置)需插件(window_manager 等),引擎不管;
- 多窗口支持仍在演进,架构上别把"单窗口"假设焊死在状态层;
- 桌面发行(MSIX/dmg/AppImage)是另一条发布管线,flutter-release-engineering
  的移动签名纪律不直接迁移,但"密钥不进仓库"原则同样适用。

## 5. 与本仓库其他语料的衔接

- 焦点/快捷键 ← flutter-forms-input §2;布局断点与重建半径 ← 轮11;
- Web 无证书锁定 ← flutter-mobile-security §3;URL 即深链 ← flutter-navigation-deeplink §2。
