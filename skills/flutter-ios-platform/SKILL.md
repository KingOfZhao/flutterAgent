---
id: flutter-ios-platform
name: iOS/Apple 平台工程 (Xcode / Info.plist / 权限 / capabilities / ATS / App Store)
version: 1.0.0
platforms: [mobile]
tags: [ios, apple, xcode, info-plist, entitlements, capabilities, ats, permissions, app-store, swift, spm]
applies_when: 需要配置 iOS 工程层(Xcode/Info.plist/权限串/能力/ATS)或排查 iOS 专属问题、上架 App Store
stage_hints: [architecture, breakdown, acceptance]
---

# iOS/Apple 平台工程

Flutter 的 iOS 部分本质是一个**标准 Xcode 工程**(`ios/Runner.xcodeproj` / `.xcworkspace`)。
要配权限用途串、开能力(capabilities)、过 ATS、上 App Store,就得懂 Apple 工程层与审核规则。
本 skill 聚焦**工程配置与平台约定**;签名归档导出 IPA 的命令链见 `flutter-build-and-release`,
原生互操作见 `flutter-platform-channels`,移动端通用基线见 `flutter-mobile`。

## 0. `ios/` 目录地图

- `ios/Runner.xcworkspace`:**用它打开 Xcode**(不是 `.xcodeproj`),因为 CocoaPods 依赖在 workspace。
- `ios/Runner/Info.plist`:权限用途串、URL scheme、显示名、支持方向、ATS 等。
- `ios/Runner/Runner.entitlements`:能力开关(推送、App Groups、Keychain、关联域名等)。
- `ios/Podfile`:CocoaPods 依赖(很多插件的原生部分经它集成);Flutter 也在推进 **Swift Package Manager** 支持。
- `ios/Runner/AppDelegate.swift`:应用入口与原生注册。

## 1. 权限:必须写用途串(Usage Description)

- iOS 访问相机/相册/定位/麦克风/通讯录等,**必须在 `Info.plist` 写 `NS...UsageDescription`** 文案,否则**运行时直接崩溃**,且审核会拒。
  - 例:`NSCameraUsageDescription`、`NSLocationWhenInUseUsageDescription`、`NSPhotoLibraryUsageDescription`。
- 文案要**具体说明用途**(Apple 审核看这个);含糊的"需要权限"会被拒。
- 运行时弹窗时机:在真正要用时再请求,别一启动全要(隐私与通过率)。

## 2. Capabilities 与 Entitlements

- 推送通知、Sign in with Apple、App Groups、iCloud、关联域名(Universal Links)、后台模式等都是 **capabilities**,在 Xcode 开启后落到 `.entitlements` + 对应 provisioning profile。
- Universal Links(深链)需要关联域名 entitlement + 服务器 `apple-app-site-association` 文件(深链逻辑见 `flutter-navigation`)。
- capabilities 与签名证书/描述文件强相关,缺了会签名/安装失败。

## 3. ATS(App Transport Security)

- iOS 默认**强制 HTTPS**;明文 HTTP 会被 ATS 拦。开发期如需放行,在 `Info.plist` 配 `NSAppTransportSecurity`,但**上线应坚持 HTTPS**(协议层见 `flutter-network-protocols`,pinning 见 `flutter-security`)。
- 别为图省事全局 `NSAllowsArbitraryLoads = true`,审核与安全都不利。

## 4. 版本、Bundle ID 与签名

- `Bundle Identifier`、`Display Name`、版本(`CFBundleShortVersionString`)与 build 号(`CFBundleVersion`)在 Xcode/Info.plist 管理。
- 签名走 Apple 证书 + provisioning profile(自动或手动);团队协作建议了解 **fastlane match** 管理证书(见 `flutter-ci-cd`)。
- 归档、导出 IPA、上传 App Store Connect 的命令见 `flutter-build-and-release`。

## 5. App Store 审核要点

- 隐私:`App Privacy`(数据收集申报)+ 必要的 **Privacy Manifest(`PrivacyInfo.xcprivacy`)** 申报所用 API 与数据(Apple 已要求,部分 SDK 需带)。
- 完整度:崩溃、占位内容、缺功能、误导描述都会被拒;遵循 Human Interface Guidelines。
- 第三方登录:若用了第三方社交登录,Apple 可能要求同时提供 Sign in with Apple。
- 用 **TestFlight** 做发布前真机灰度。

## 6. 排查清单

- 一访问相机/定位就崩 → 缺对应 `NS...UsageDescription`。
- 网络请求在 iOS 不通 → ATS 拦了明文 HTTP。
- 安装/签名失败 → capabilities 与 provisioning profile / 证书不匹配。
- Pod 报错 → `cd ios && pod install`(或 `pod repo update`);`flutter clean` 后重来。
- `flutter doctor` 看 Xcode / CocoaPods 是否就绪(见 `flutter-environment-setup`)。

## 反模式

- ❌ 不写/写空 `NS...UsageDescription`,运行崩溃且被拒审。
- ❌ 全局 `NSAllowsArbitraryLoads=true` 绕过 ATS 上线。
- ❌ 一启动就把所有权限弹个遍,降低通过率与转化。
- ❌ 忽略 Privacy Manifest / App Privacy 申报,提审被拒。
- ❌ 直接打开 `.xcodeproj` 而非 `.xcworkspace`,丢失 Pod 依赖。

## 参考 / References

- iOS 部署(build & release):<https://docs.flutter.dev/deployment/ios>
- Apple Info.plist 权限键(Cocoa Keys):<https://developer.apple.com/documentation/bundleresources/information_property_list>
- 请求访问受保护资源:<https://developer.apple.com/documentation/uikit/protecting_the_user_s_privacy>
- App Transport Security:<https://developer.apple.com/documentation/security/preventing_insecure_network_connections>
- Privacy Manifest 文件:<https://developer.apple.com/documentation/bundleresources/privacy_manifest_files>
- App Review Guidelines:<https://developer.apple.com/app-store/review/guidelines/>
- Universal Links:<https://developer.apple.com/documentation/xcode/allowing-apps-and-websites-to-link-to-your-content>
- Flutter iOS SwiftPM 支持:<https://docs.flutter.dev/packages-and-plugins/swift-package-manager/for-app-developers>
- 签名/归档命令见 `flutter-build-and-release`;原生互操作见 `flutter-platform-channels`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **`ios/` 就是个标准 Xcode 工程**:Info.plist / entitlements / Podfile 用 Apple 的方式理解,Flutter 只是宿主。
- **权限串缺失=崩溃+拒审**:iOS 把隐私当硬约束,用途串和 Privacy Manifest 不是可选项。
- **审核是发布的一部分**:把 HIG、隐私申报、完整度纳入"完成定义",别等被拒才补。

**诚实边界:**

- Apple 政策(Privacy Manifest、targetOS、审核细则)变化频繁,以官方当时文档为准。
- iOS 工程改动需在真机/真签名环境验证,模拟器与 Dart 测试覆盖不到。
- 这里聚焦工程配置;UI/Cupertino 规范见 `flutter-mobile`,签名发布见 `flutter-build-and-release`。
