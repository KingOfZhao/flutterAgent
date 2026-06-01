---
id: flutter-desktop-platform
name: 桌面平台工程 (Windows / macOS / Linux 打包 / 签名 / 公证 / 原生集成)
version: 1.0.0
platforms: [desktop]
tags: [desktop, windows, macos, linux, msix, dmg, notarization, appimage, flatpak, snap, packaging, signing]
applies_when: 需要为 Windows/macOS/Linux 配置工程、打包分发、签名公证或集成桌面原生能力
stage_hints: [architecture, breakdown, acceptance]
see_also: [flutter-desktop, flutter-build-and-release]
---

> 分工:本 skill 负责**桌面三端专属工程**(打包格式/签名/公证/分发/原生集成)。
> 桌面端**通用基线**见 `flutter-desktop`;**通用构建命令链**见 `flutter-build-and-release`。

# 桌面平台工程(Win / macOS / Linux)

桌面三端各有**完全不同的打包格式、签名机制、分发渠道**,不像移动端只有两家商店。
本 skill 给"每端怎么打包/签名/公证、桌面专属能力怎么接"的地图,聚焦平台差异;
通用桌面基线见 `flutter-desktop`,通用构建命令见 `flutter-build-and-release`,
原生互操作见 `flutter-platform-channels`。

## 0. 启用与目录

```bash
flutter config --enable-windows-desktop --enable-macos-desktop --enable-linux-desktop
flutter create --platforms=windows,macos,linux .
```

- `windows/`(CMake + C++ runner)、`macos/`(Xcode 工程)、`linux/`(CMake + GTK)各是该平台的原生宿主工程。
- 桌面构建是**按当前 OS 构建**:Windows 包要在 Windows 上出,macOS 包要在 mac 上出,无法交叉编译。

## 1. Windows

- 产物:`flutter build windows` → `build/windows/.../Runner.exe` + 依赖 DLL(整个文件夹一起分发)。
- 打包格式:
  - **MSIX**(用 `msix` 包):生成 `.msix`,可上 **Microsoft Store** 或侧载;支持签名。
  - 传统安装器:**Inno Setup** / **WiX** 做 `.exe`/`.msi` 安装包。
- 签名:用代码签名证书(Authenticode)对 exe/安装器签名,避免 SmartScreen 警告。
- 注意分发 **VC++ 运行库**依赖。

## 2. macOS

- 产物:`flutter build macos` → `.app` bundle;常打包成 **DMG**(用 `create-dmg` 等)。
- **签名 + 公证(notarization)是硬要求**:Gatekeeper 会拦未签名/未公证的 app。
  - 用 Developer ID 证书签名 → `notarytool` 提交 Apple 公证 → `stapler` 装订票据。
- **App Sandbox / entitlements**:`macos/Runner/*.entitlements` 控制网络、文件访问等;上 Mac App Store 必须沙盒。
- 权限同 iOS 用 `Info.plist` 用途串(相机/麦克风等)。

## 3. Linux

- 产物:`flutter build linux` → 可执行文件 + `lib/` + `data/`(一起分发);依赖 **GTK** 等系统库。
- 打包格式(无统一标准,按发行版/渠道选):
  - **AppImage**(单文件便携)、**Flatpak**(Flathub 分发,沙盒)、**Snap**(Snap Store)、或 `.deb`/`.rpm`。
- 注意目标发行版的**运行时依赖**与 glibc 版本兼容。

## 4. 桌面专属能力(原生集成)

- 窗口管理(尺寸/标题/多窗口)、系统托盘、菜单栏、全局快捷键、文件关联、拖拽——多数通过社区插件(如 `window_manager`、`tray_manager`)或自写 platform channel(见 `flutter-platform-channels`)。
- Flutter 官方在推进实验性 **Windowing APIs**(多窗口),关注其稳定状态(见 `flutter-desktop`)。
- 文件系统访问比移动端自由,但要处理路径差异与权限(macOS 沙盒)。

## 5. 分发与更新

- 桌面没有统一的商店强制更新机制:商店渠道(MS Store / Mac App Store / Flathub / Snap)各有审核与自动更新;自分发则需自带更新方案(如 `auto_updater` / Sparkle/Squirrel 思路)。
- CI 上按 OS 分 job 出各端产物(见 `flutter-ci-cd`):Windows job、macOS job(含公证)、Linux job。

## 6. 排查清单

- macOS 双击打不开/被拦 → 未签名或未公证(Gatekeeper)。
- Linux 在别的机器跑不起来 → 缺 GTK/系统库或 glibc 版本不匹配。
- Windows 报缺 DLL → 没带全运行库/依赖 DLL。
- 构建报错先确认在**对应 OS** 上构建,且 `flutter doctor` 对应桌面 toolchain 就绪(见 `flutter-environment-setup`)。

## 反模式

- ❌ 以为能交叉编译(在 Linux 出 Windows/mac 包)。
- ❌ macOS 直接分发未签名未公证的 `.app`,用户被 Gatekeeper 拦还以为是 bug。
- ❌ 只测自己机器,不验证目标发行版/干净系统的依赖。
- ❌ 桌面专属能力全自己写 channel,无视成熟的 window/tray 插件。
- ❌ 把移动端的权限/沙盒假设照搬到桌面(模型不同)。

## 参考 / References

- 桌面支持总览:<https://docs.flutter.dev/platform-integration/desktop>
- 构建与发布 Windows:<https://docs.flutter.dev/deployment/windows>
- 构建与发布 macOS:<https://docs.flutter.dev/deployment/macos>
- 构建与发布 Linux:<https://docs.flutter.dev/deployment/linux>
- `msix` 打包:<https://pub.dev/packages/msix>
- macOS 公证(notarytool):<https://developer.apple.com/documentation/security/notarizing-macos-software-before-distribution>
- AppImage:<https://appimage.org/> · Flatpak:<https://flatpak.org/> · Snapcraft:<https://snapcraft.io/>
- `window_manager`:<https://pub.dev/packages/window_manager>
- 通用桌面基线见 `flutter-desktop`;构建命令见 `flutter-build-and-release`;原生互操作见 `flutter-platform-channels`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **三端是三套世界**:打包/签名/分发各不相同,别套用一个心智模型。
- **按 OS 构建,不能交叉**:CI 必须分 OS job,本地也得在对应系统出包。
- **签名公证是 macOS 的发布门槛**:不签不公证=用户打不开,纳入完成定义。

**诚实边界:**

- 桌面打包工具链多为社区方案,成熟度与维护度参差,选型要看活跃度(见 `flutter-dependency-maintenance`)。
- Linux 发行版碎片化,"能在我机器跑"不代表通用,需在目标环境验证。
- Windowing/多窗口等仍实验性,API 可能变,以官方状态为准。
