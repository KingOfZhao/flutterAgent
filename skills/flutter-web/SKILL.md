---
id: flutter-web
name: Flutter Web 工程规范
version: 1.0.0
platforms: [web]
tags: [web, pwa, seo, wasm, canvaskit, html-renderer, cors, font, deploy]
applies_when: 需求目标平台包含 Web / PWA / 浏览器
stage_hints: [spec, architecture, breakdown]
---

# Flutter Web 工程规范

你正在为一个 **面向浏览器的 Flutter Web** 项目产出工程设计。

> 直接依据:
> * Flutter Web 部署: **[docs.flutter.dev/deployment/web](https://docs.flutter.dev/deployment/web)**
> * Flutter Web FAQ: **[docs.flutter.dev/platform-integration/web](https://docs.flutter.dev/platform-integration/web)**
> * Flutter Web 渲染器: **[docs.flutter.dev/platform-integration/web/renderers](https://docs.flutter.dev/platform-integration/web/renderers)**
> * CanvasKit / Skia WASM: **[skia.org/docs/user/modules/canvaskit](https://skia.org/docs/user/modules/canvaskit/)**
> * MDN PWA Guide: **[developer.mozilla.org/en-US/docs/Web/Progressive_web_apps](https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps)**

---

## 1. 渲染器选型（最关键决策）

Flutter Web 有三种渲染后端,Flutter 3.22+ 默认自动选择:

| 渲染器 | 二进制产物 | 首屏加载 | 视觉一致性 | SEO | 适用场景 |
|--------|----------|---------|-----------|-----|---------|
| **HTML (html)** | 小 (~300KB gzip) | 快 | 低（依赖浏览器排版） | DOM 可见 | 内容型 / SEO 优先 / 老旧浏览器 |
| **CanvasKit** | 大 (~2MB+ gzip) | 慢 | 高（像素级一致） | DOM 不可见 | 动画密集 / 跨端视觉一致 |
| **SkWasm** (WASM) | 中 (~1.5MB) | 中 | 高 | DOM 不可见 | Flutter 3.22+ 推荐,性能最优 |

```bash
# 指定渲染器构建
flutter build web --web-renderer html       # HTML 渲染
flutter build web --web-renderer canvaskit   # CanvasKit
flutter build web --wasm                     # SkWasm (WASM, 推荐)
```

### 选型决策树

```
需要 SEO / 爬虫抓取?
  ├── 是 → HTML renderer + 服务端预渲染 (或 SSG)
  └── 否 → 需要像素级跨端一致性?
        ├── 是 → SkWasm (首选) 或 CanvasKit (fallback)
        └── 否 → Auto (框架自动选择)
```

### Flutter 3.44 更新

- `flutter run -d chrome --base-href /app/` 支持本地调试子目录部署,避免路由 404
- DevTools 默认 WASM 编译
- iOS 26 Safari 自动填充支持

---

## 2. 首屏加载优化

Web 应用首屏速度直接影响用户留存率。

### 2.1 加载预算

| 指标 | 目标 | 测量 |
|------|------|------|
| FCP (First Contentful Paint) | < 2s (3G) / < 1s (4G) | Lighthouse |
| TTI (Time to Interactive) | < 3.5s (3G) | Lighthouse |
| gzip 传输体积 | < 2MB (CanvasKit) / < 500KB (HTML) | DevTools Network |
| Lighthouse Performance 评分 | ≥ 70 | Lighthouse |

### 2.2 加载策略

```html
<!-- web/index.html — 分阶段加载 -->
<body>
  <!-- 1. 原生 HTML 骨架屏 (0ms 可见) -->
  <div id="loading">
    <style>
      #loading { display: flex; justify-content: center; align-items: center;
                 height: 100vh; font-family: system-ui; }
      .spinner { width: 40px; height: 40px; border: 4px solid #e0e0e0;
                 border-top-color: #1976d2; border-radius: 50%;
                 animation: spin 0.8s linear infinite; }
      @keyframes spin { to { transform: rotate(360deg); } }
    </style>
    <div class="spinner"></div>
  </div>

  <!-- 2. Flutter 引擎初始化完成后隐藏骨架 -->
  <script src="flutter_bootstrap.js" async></script>
</body>
```

```dart
// main.dart — 通知 loading 完成
void main() {
  runApp(const MyApp());
  // 首帧绘制完成后移除原生 loading
  WidgetsBinding.instance.addPostFrameCallback((_) {
    final loading = html.document.getElementById('loading');
    loading?.remove();
  });
}
```

### 2.3 Deferred Components（按需加载）

```dart
// 重路由的页面使用 deferred import
import 'package:myapp/features/dashboard/dashboard_page.dart' deferred as dashboard;

GoRoute(
  path: '/dashboard',
  builder: (context, state) {
    return FutureBuilder(
      future: dashboard.loadLibrary(),
      builder: (_, snap) {
        if (snap.connectionState != ConnectionState.done) {
          return const CircularProgressIndicator();
        }
        return dashboard.DashboardPage();
      },
    );
  },
);
```

---

## 3. Tree Shaking 与包体积

### 3.1 图标 Tree Shaking

```bash
# 自动剔除未使用的 Material Icons (默认开启)
flutter build web --tree-shake-icons
```

### 3.2 分析体积构成

```bash
flutter build web --source-maps
# 使用 source-map-explorer 分析
npx source-map-explorer build/web/main.dart.js.map
```

### 3.3 缩减依赖

- 移除仅移动端使用的包(`camera`, `geolocator` 等)
- 使用条件导入隔离平台代码:

```dart
// lib/platform/storage.dart
export 'storage_stub.dart'
    if (dart.library.html) 'storage_web.dart'
    if (dart.library.io) 'storage_io.dart';
```

---

## 4. 字体加载策略

中文 Web 场景字体是最大痛点(完整中文字体 10MB+)。

### 4.1 策略对比

| 方案 | 加载体积 | 首屏表现 | 适用场景 |
|------|---------|---------|---------|
| 系统字体 fallback | 0 | 最快 | 对字体一致性无要求 |
| Google Fonts (动态子集) | 按需 100-500KB | 闪烁后显示 | 常规中英文内容 |
| 静态子集 woff2 | 500KB-2MB | 预加载稳定 | 品牌字体、固定内容 |
| `font-display: swap` | 同上 | 先显系统字体再替换 | 平衡方案 |

### 4.2 推荐模式

```yaml
# pubspec.yaml — 使用 Google Fonts 包
dependencies:
  google_fonts: ^6.0.0
```

```dart
// 延迟加载中文字体,不阻塞首屏
MaterialApp(
  theme: ThemeData(
    textTheme: GoogleFonts.notoSansSCTextTheme(),
  ),
);
```

```html
<!-- web/index.html — 预连接 Google Fonts CDN -->
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
```

---

## 5. SEO 与元数据

CanvasKit/SkWasm 渲染器下 DOM 不可见,搜索引擎无法抓取内容。

### 5.1 应对方案

| 方案 | 复杂度 | 效果 |
|------|--------|------|
| HTML renderer | 低 | 内容在 DOM 中,可被爬虫抓取 |
| `<noscript>` fallback 内容 | 低 | 基础 SEO 兜底 |
| 服务端预渲染 (SSR/SSG) | 高 | 完整 SEO + 社交分享预览 |
| 动态 `<meta>` 注入 | 中 | Open Graph / Twitter Card |

### 5.2 基础 SEO 模板

```html
<!-- web/index.html -->
<head>
  <title>My App</title>
  <meta name="description" content="...">
  <!-- Open Graph -->
  <meta property="og:title" content="My App">
  <meta property="og:description" content="...">
  <meta property="og:image" content="https://myapp.com/og-image.png">
  <meta property="og:url" content="https://myapp.com">
  <!-- 给搜索引擎提供 fallback -->
  <noscript>
    <h1>My App</h1>
    <p>需要启用 JavaScript 才能运行此应用。</p>
  </noscript>
</head>
```

---

## 6. PWA 配置

### 6.1 manifest.json

```json
{
  "name": "My Flutter App",
  "short_name": "MyApp",
  "start_url": ".",
  "display": "standalone",
  "background_color": "#ffffff",
  "theme_color": "#1976d2",
  "icons": [
    { "src": "icons/Icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icons/Icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icons/Icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" }
  ]
}
```

### 6.2 Service Worker 策略

Flutter 默认生成 `flutter_service_worker.js`,采用 **cache-first** 策略:

```dart
// 自定义缓存策略 (web/index.html)
_flutter.loader.load({
  serviceWorkerSettings: {
    serviceWorkerVersion: serviceWorkerVersion,
    // 'offline-first': 缓存优先 (默认)
    // 'none': 禁用 service worker
  },
});
```

---

## 7. 部署

### 7.1 子目录部署

```bash
# 构建到子路径 (如 https://example.com/myapp/)
flutter build web --base-href /myapp/

# Flutter 3.44 支持本地调试子路径
flutter run -d chrome --base-href /myapp/
```

### 7.2 路由策略

```dart
// URL 策略: hash (#) vs path
GoRouter(
  // Path URL: /products/42 (需要服务器配置 SPA fallback)
  // Hash URL: /#/products/42 (无需服务器配置)
);
```

```nginx
# Nginx SPA fallback (path URL 必须)
location / {
  try_files $uri $uri/ /index.html;
}
```

### 7.3 CORS 处理

```dart
// 开发环境 proxy 或使用 shelf_proxy
// 生产环境: API 网关配置 Access-Control-Allow-Origin
```

---

## 8. 浏览器兼容性

| 浏览器 | CanvasKit | HTML | SkWasm |
|--------|-----------|------|--------|
| Chrome 84+ | ✅ | ✅ | ✅ |
| Firefox 72+ | ✅ | ✅ | ✅ |
| Safari 14.1+ | ✅ | ✅ | ⚠️ (需 SharedArrayBuffer) |
| Edge 84+ | ✅ | ✅ | ✅ |
| IE 11 | ❌ | ❌ | ❌ |
| Mobile Safari (iOS 14.5+) | ✅ | ✅ | ⚠️ |

> **Safari/SkWasm 注意**: SkWasm 需要 `SharedArrayBuffer`,要求服务器设置 `Cross-Origin-Embedder-Policy: require-corp` 和 `Cross-Origin-Opener-Policy: same-origin` 响应头。

---

## 9. Web 特有性能注意

- **鼠标滚轮 / 触控板**: Flutter Web 默认使用 custom scroll physics,与浏览器原生滚动体感不同;考虑 `PageView` 等场景的 `ScrollBehavior` 适配
- **文本选择**: `SelectionArea` 包裹后可被浏览器选中、复制
- **键盘快捷键**: 避免与浏览器默认快捷键(Ctrl+F, Ctrl+P 等)冲突
- **右键菜单**: 默认被 Flutter 拦截,需显式处理 `BrowserContextMenu`
- **Tab 导航**: Web 用户习惯用 Tab 键导航,确保 `FocusTraversalGroup` 有序
- **打印**: `window.print()` 对 Canvas 渲染器无效,需要生成 PDF 替代

---

## 10. 必须产出

1. **渲染器选型与理由**
2. **首屏加载策略**: 骨架屏 HTML + deferred components 拆分方案
3. **字体方案**: 选用哪种字体加载策略,中文场景尤其要明确
4. **SEO 方案**: 是否需要爬虫抓取,对应选 HTML/预渲染/fallback
5. **部署配置**: base-href、URL 策略、CORS、SPA fallback
6. **PWA 清单**: 是否需要离线,manifest 配置

## 11. 红线

- 不要用 CanvasKit/SkWasm 期望 SEO 可用(DOM 不可见)
- 不要忽略字体加载(中文全量字体 > 10MB)
- 不要硬编码 base URL,必须用 `--base-href` 参数
- 不要假设 `dart:io` 在 Web 可用(必须条件导入)
- 不要在 Web 端使用 `File` / `Directory` 类(用 `html.File` 或 `cross_file`)
- 不要忽略 Safari SharedArrayBuffer 限制(SkWasm 需要特殊响应头)
- 不要在 Web 端使用 `Isolate.spawn`(用 `compute` 或 Web Workers)

---

## 参考

- Flutter Web 部署: <https://docs.flutter.dev/deployment/web>
- Flutter Web 渲染器: <https://docs.flutter.dev/platform-integration/web/renderers>
- Flutter Web FAQ: <https://docs.flutter.dev/platform-integration/web>
- PWA: <https://developer.mozilla.org/en-US/docs/Web/Progressive_web_apps>
- Google Fonts: <https://pub.dev/packages/google_fonts>
- url_strategy: <https://pub.dev/packages/url_strategy>
- Lighthouse: <https://developer.chrome.com/docs/lighthouse>
