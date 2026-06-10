---
id: flutter-permissions-and-config
name: 权限判断与编译期配置(宏 / flavor / dart-define 一体化)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [permissions, permission_handler, runtime-permission, dart-define, flavor, manifest, info-plist, build-config, 宏配置, 权限, 编译开关, feature-flag]
applies_when: 需求涉及相机/定位/通知/麦克风/存储等系统权限,或权限/功能受 flavor、dart-define、编译期宏开关控制
stage_hints: [architecture, implementation, review, acceptance]
---

# 权限判断与编译期配置

权限相关的 bug 极少出在"忘了调 `request()`",而是出在**三层配置不一致**:
运行时判断、平台声明(Manifest / Info.plist)、编译期宏(flavor / dart-define / Build Configuration)。
模型生成权限代码时最常见的错误就是**只写运行时判断,忽略宏配置这一层**——
本 skill 要求三层必须同时核对,缺一层就视为方案不完整。

## 1. 三层模型(任何权限方案必须逐层核对)

| 层 | 内容 | 出错表现 |
|---|---|---|
| L1 编译期宏 / flavor | `--dart-define`、`flutter build --flavor`、Android `buildConfigField` / manifestPlaceholders、iOS Build Configuration / xcconfig | 功能在某个 flavor 被裁剪,但运行时代码仍然请求权限 → 审核被拒或崩溃 |
| L2 平台声明 | `AndroidManifest.xml` `<uses-permission>`、iOS `Info.plist` usage description(`NSCameraUsageDescription` 等) | 没声明 → Android 直接 denied、iOS 直接崩溃 |
| L3 运行时判断 | `permission_handler` 的 `status` / `request()`、`shouldShowRequestRationale`、`openAppSettings()` | 只检查 granted/denied,漏 `permanentlyDenied` / `restricted` / `limited` |

**核对顺序必须 L1 → L2 → L3**:先确认该 flavor/宏下功能是否启用,再确认声明存在,最后才写运行时逻辑。

## 2. L1:编译期宏与 flavor 正确接入

- Dart 侧读取宏:`const bool.fromEnvironment('ENABLE_CAMERA', defaultValue: false)`,必须是 `const` 才能参与 tree-shaking,把被裁剪功能的权限代码一起裁掉。
- 批量注入用 `--dart-define-from-file=config/prod.json`(<https://docs.flutter.dev/deployment/flavors>)。
- Android:flavor 维度用 `manifestPlaceholders` 把权限声明随 flavor 注入/移除,例如免费版不含 `<uses-permission android:name="android.permission.CAMERA"/>`。
- iOS:每个 Build Configuration 配独立 xcconfig;usage description 不能用宏裁剪时,用 build phase 脚本或独立 Info.plist。
- **权限入口必须被宏 gate**:
  ```dart
  const kCameraEnabled = bool.fromEnvironment('ENABLE_CAMERA');

  Future<void> openScanner() async {
    if (!kCameraEnabled) return;            // L1: 宏关闭直接短路
    final status = await Permission.camera.request();  // L3
    ...
  }
  ```
  反过来,UI 上的入口(按钮/路由)也要用同一个常量隐藏,避免"按钮在、功能宏被关"的死按钮。

## 3. L2:平台声明清单

- Android:`<uses-permission>` 按 targetSdk 区分(如 33+ 的 `READ_MEDIA_IMAGES` 替代 `READ_EXTERNAL_STORAGE`,<https://developer.android.com/about/versions/13/behavior-changes-13>);后台定位、通知(13+ `POST_NOTIFICATIONS`)都要单独声明。
- iOS:每个权限对应的 `NS*UsageDescription` 缺失会在请求时直接 crash;描述文案需说明用途(审核要求)。
- 桌面/Web:macOS 需要 entitlements(沙盒);Web 没有 Manifest,权限由浏览器 prompt 决定,运行时代码要按平台分支(`kIsWeb` / `defaultTargetPlatform`)。

## 4. L3:运行时状态机(不要只判断 granted)

`permission_handler`(<https://pub.dev/packages/permission_handler>)的状态必须全覆盖:

| 状态 | 处理 |
|---|---|
| `granted` / `limited`(iOS 照片) | 继续,`limited` 要提示可扩大授权 |
| `denied` | 可再次 `request()`,配合 rationale 说明 |
| `permanentlyDenied` | **不要**再 `request()`(无效),引导 `openAppSettings()` |
| `restricted`(iOS 家长控制) | 功能降级,不弹设置引导(用户改不了) |

- 请求时机:**用到才请求**(point-of-use),不要启动时批量轰炸。
- 权限逻辑收敛到单一 service/repository,禁止散落在各 widget 里重复判断。

## 5. 评审清单(review 阶段逐条核对)

1. 每个权限是否三层齐备:宏 gate + 平台声明 + 运行时状态机?
2. 被 flavor/宏关闭的功能,其权限声明与 UI 入口是否一并移除?
3. `permanentlyDenied` / `restricted` / `limited` 是否有独立分支?
4. targetSdk 升级后的权限替代(存储/通知/蓝牙)是否核对?
5. 多平台分支:Web/桌面是否复用了移动端的权限假设?

## 反模式

- ❌ 只写 `Permission.camera.request()`,不检查该 flavor / dart-define 下功能是否启用(国产模型最高频错误)。
- ❌ 用运行时变量而非 `const bool.fromEnvironment` 读宏,导致死代码无法 tree-shake、权限代码进了被裁剪的包。
- ❌ `permanentlyDenied` 还在循环 `request()`,永远弹不出框。
- ❌ Manifest/Info.plist 声明了所有权限"以防万一"——商店审核与隐私扫描直接亮红。
- ❌ 权限判断散落在多个 widget,各自维护状态,互相不一致。
- ❌ Web/桌面直接复用移动端权限代码,不做平台分支。

## 参考 / References

- permission_handler:<https://pub.dev/packages/permission_handler>
- Flutter flavors / dart-define:<https://docs.flutter.dev/deployment/flavors>
- Android 权限最佳实践:<https://developer.android.com/training/permissions/requesting>
- Android 13 行为变更(细分媒体权限/通知):<https://developer.android.com/about/versions/13/behavior-changes-13>
- iOS 权限 usage description:<https://developer.apple.com/documentation/bundleresources/information-property-list/protected-resources>
- macOS entitlements / 沙盒:<https://developer.apple.com/documentation/security/app_sandbox>
- Android/iOS 平台工程细节见 `flutter-android-platform` / `flutter-ios-platform`;打包与 flavor 注入见 `flutter-build-and-release`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)使用。

**透镜(怎么想):**

- **权限是配置问题,不是 API 调用问题**:先问"这个 flavor/宏下功能开吗、声明在吗",最后才写 `request()`。
- **三层一致性**:任何一层单独改动(加宏、删声明、改状态机)都要回头核对另外两层。
- **状态机思维**:权限不是布尔值,是含 `permanentlyDenied`/`restricted`/`limited` 的状态机。

**诚实边界:**

- 各厂商 ROM(MIUI/EMUI 等)的权限弹窗行为有私有差异,本 skill 只覆盖 AOSP/官方行为,厂商兼容需真机验证。
- 商店审核策略随时间变化,清单仅代表写作时的要求,上架前以最新官方文档为准。
