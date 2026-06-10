# Flutter 移动安全(向量库优质语料·轮4)

> 反思缺口:发布工程语料只有一句"客户端没有真密钥",但存储/传输/平台加固的
> 具体边界无语料,这是检索接地最怕给错答案的领域。来源见 REFERENCES §26。

## 1. 威胁模型先行(OWASP MAS 框架)

按 OWASP Mobile Application Security 的分法,移动端要防的是:不安全存储、
不安全通信、被逆向篡改、平台 API 误用。先判断应用的敏感级别
(普通内容应用 vs 金融/医疗),再决定下面哪些层级必须做——给内容应用上
全套加固是成本错配,给支付应用只用 prefs 存 token 是事故。

## 2. 本地存储安全

- **令牌/凭据**:`flutter_secure_storage`(iOS Keychain / Android Keystore 加密),
  绝不放 `shared_preferences`(明文 XML/plist,root/越狱设备直接可读)。
- **数据库加密**:敏感结构化数据用 SQLCipher 系(drift 可换加密执行器);
  加密密钥本身存 Keychain/Keystore,不要硬编码或派生自设备 ID。
- **缓存泄漏面**:截图/最近任务预览(Android `FLAG_SECURE`)、键盘学习、
  日志(`print` 的内容 logcat 全局可读)都是被忽略的泄漏通道——发布构建
  禁掉敏感日志。

## 3. 传输与服务端信任

- TLS 是底线;**证书锁定(pinning)只对高敏应用做**(dio 的
  `badCertificateCallback`/平台配置),并准备好密钥轮换与备用 pin——
  pin 失效等于自我拒绝服务,这是 pinning 最常见的事故方式。
- **客户端没有真正的密钥安全**(与 flutter-release-engineering §2 同一结论的
  安全侧表述):`--dart-define`、混淆、资产加密都只是提高提取成本;第三方 API
  的真密钥必须经服务端代理,客户端只持可吊销的低权限令牌。

## 4. 代码与运行时加固

- `flutter build --obfuscate --split-debug-info=...`:混淆 Dart 符号,
  保留映射文件用于还原崩溃堆栈——只防"随手逆向",不防有决心的攻击者。
- root/越狱检测、调试器检测属于"提高成本"层,可被绕过,不能作为安全边界;
  真正的边界在服务端校验(关键业务决策不信任客户端上报)。
- 依赖供应链:锁定 `pubspec.lock` 入库、CI 跑 `dart pub outdated` 与安全公告
  比对——被投毒的传递依赖比逆向更现实。

## 5. 与本仓库其他语料的衔接

- 真密钥留服务端 ← flutter-release-engineering §2;
- 加密数据库选型挂在本地存储选型之上(flutter-offline-sync §1);
- 错误建模决定"安全失败如何呈现给用户"(flutter-networking-api §2)。
