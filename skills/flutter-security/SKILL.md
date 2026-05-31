---
id: flutter-security
name: Flutter 安全与合规规范
version: 1.0.0
platforms: [all]
tags: [security, obfuscation, pinning, owasp, masvs, gdpr]
applies_when: 任何处理用户数据 / 上架商店 / 涉及登录或支付的项目
stage_hints: [architecture, breakdown, acceptance]
---

# Flutter 安全规范

> 直接依据:
> * Flutter 代码混淆:**[docs.flutter.dev/deployment/obfuscate](https://docs.flutter.dev/deployment/obfuscate)**
> * OWASP MASVS(Mobile Application Security Verification Standard):<https://mas.owasp.org/MASVS/>
> * OWASP MSTG(测试手册):<https://mas.owasp.org/MASTG/>
> * Android Security Best Practices:<https://developer.android.com/topic/security/best-practices>
> * iOS Security:<https://developer.apple.com/documentation/security>
> * 中国《个人信息保护法》《数据安全法》:<https://www.gov.cn/xinwen/2021-08/20/content_5632486.htm>
> * GDPR:<https://gdpr.eu>

## 1. 数据存储

| 数据类型 | 存储位置 | Flutter 包 | 加密 |
|---|---|---|---|
| 用户 token / refresh token | iOS Keychain / Android EncryptedSharedPreferences | **[flutter_secure_storage](https://pub.dev/packages/flutter_secure_storage)** | 系统级 |
| 用户偏好(非敏感) | `shared_preferences` | <https://pub.dev/packages/shared_preferences> | 不加密 |
| 业务数据 | drift / sqflite | 自加密:`sqflite_sqlcipher`(<https://pub.dev/packages/sqflite_sqlcipher>) | 必要时加密 |
| 大文件 / 缓存 | `path_provider` + 磁盘 | — | 视敏感度 |

**禁止**:
- 把 token / 密码塞进 `shared_preferences`
- 把数据库放在 `getApplicationCacheDirectory()`(可能被系统清理)
- 把敏感字段写进日志(包括 `Logger.d(user.toJson())`)

## 2. 网络

- **强制 HTTPS**:Android 14+ 默认禁明文,需要时显式声明 `networkSecurityConfig`;iOS ATS 默认开启
- **证书锁定(certificate pinning)**:对自有 API 强烈推荐
  - `dio` + `dio_certificate_pinning`(<https://pub.dev/packages/dio_certificate_pinning>)或自实现 `badCertificateCallback`
  - 备份证书 + 远程下发可轮换(SPKI hash pinning,而非证书指纹)
- **不要**自实现 TLS 校验绕过逻辑(debug 也别开)
- **CORS / Origin**:Web 端校验由后端做

参考:OWASP MSTG-NETWORK-1 ~ 6 <https://mas.owasp.org/MASTG/0x05g-Testing-Network-Communication>

## 3. 代码混淆与符号

```bash
flutter build apk --release --obfuscate --split-debug-info=./symbols/android
flutter build ipa --release --obfuscate --split-debug-info=./symbols/ios
```

- `--obfuscate` 会重命名 Dart 符号
- `--split-debug-info` 输出 `*.dSYM` / `app.android-arm64.symbols`,**必须存入构建产物**,否则上报的栈无法解
- Sentry / Crashlytics 上传符号文件:`sentry-cli upload-dif`

> Flutter 官方明确:obfuscation 只增加逆向门槛,**不能**作为密钥保护手段。任何嵌在 binary 里的字符串都视为公开。

## 4. 密钥管理

- **不要**把 API key / OAuth client secret 嵌进客户端 — 永远从后端中转
- 必须嵌入(如 Maps、地图 SDK key)的:走 `--dart-define` 注入 + 平台后台 referrer/bundle id 限制
- 私有签名密钥(支付、上链):放 HSM / KMS,客户端只拿一次性 token

## 5. 平台权限最小化

| 平台 | 文件 | 工具 |
|---|---|---|
| Android | `AndroidManifest.xml` | `permission_handler` |
| iOS | `Info.plist` (`NS<...>UsageDescription`) | — |
| macOS | `*.entitlements`(沙箱) | — |
| Web | Permission API | — |

**强制**:
- 每个权限必须给用户可读的用途文案(iOS 是审核硬要求)
- **首次请求权限**前必须有「教育对话框」说明用途
- 拒绝后必须有降级路径(不能用就退出)
- 不要请求不用的权限(Play Store 数据安全表会曝光)

## 6. 越狱 / Root / 模拟器检测

- 处理金融、支付:必须做,推荐 `flutter_jailbreak_detection`(<https://pub.dev/packages/flutter_jailbreak_detection>)+ Google **Play Integrity API**(<https://developer.android.com/google/play/integrity>)
- 普通 App:不强制
- **不要**只在客户端阻断,服务端 Integrity API 验签才靠谱

## 7. 隐私清单与合规

| 场景 | 文件 | 来源 |
|---|---|---|
| iOS 17+ | `PrivacyInfo.xcprivacy` 必填 | <https://developer.apple.com/documentation/bundleresources/privacy_manifest_files> |
| Android Play | "Data safety" 表 | <https://support.google.com/googleplay/android-developer/answer/10787469> |
| 国内上架 | 隐私政策 + 用户协议 + 第三方 SDK 清单 | 各应用商店审核要求 |

合规清单(GDPR / 个保法通用):
1. 收集前显式同意(opt-in,不是默认勾选)
2. 数据最小化(只收必要数据)
3. 可注销账户 + 删除数据(必须有入口)
4. 第三方 SDK 列表(SDK 名 / 用途 / 收集数据 / 隐私政策链接)
5. 跨境传输:中国大陆数据出境需走「个人信息出境标准合同」或安评

## 8. 必须产出

每个产出含:
1. 数据分级表(敏感 / 一般 / 公开),对应存储方案
2. 网络通信清单(每个域名、是否 pinning、备份策略)
3. 权限清单 + 文案 + 拒绝降级方案
4. 密钥管理流程图
5. 混淆 / 符号上传 / 崩溃解栈链路
6. 合规清单(隐私清单 / Data safety / 第三方 SDK)
7. 安全测试用例(至少:登录爆破、token 篡改、CSRF / clickjacking 在 web、深链接攻击)

## 9. 红线

- 不要把任何用户 PII 写入日志
- 不要在客户端做敏感计算(支付价格、积分增减)
- 不要相信客户端发的任何字段没经过校验
- 不要使用未审计的「破解版」依赖(pub-cache 必须从 pub.dev)
- 不要禁用 SSL 证书校验(就算只在 debug 也不行,易被忘记)

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **不信任客户端**:任何客户端输入/字段在服务端都要再校验。
- **敏感数据有归属**:密钥/令牌进 secure storage,绝不硬编码或明文。
- **传输默认加密+校验**:TLS/证书校验不可在任何环境关闭。

**诚实边界:**

- 客户端无法保管真正的秘密;高价值逻辑/密钥应在服务端。
- 合规(GDPR/隐私)需法务参与,本 skill 给工程红线,非法律意见。
