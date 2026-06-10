# Flutter 发布工程(向量库优质语料)

> 用途:为"打包/签名/上架/灰度/崩溃监控"类需求提供检索接地语料。来源见 REFERENCES §25。

## 1. 构建与签名

- **Android**:release 构建必须配置 upload keystore(`key.properties` 不入库,
  CI 用 secret 注入);Play 上架用 AAB(`flutter build appbundle`)而非 APK,
  Play 按设备分发优化包体。密钥丢失=无法更新应用,启用 Play App Signing 托管。
- **iOS**:证书/描述文件交给 Xcode 自动管理或 fastlane match 统一管理;
  `flutter build ipa` 产物经 Transporter/altool 上传。
- **版本号纪律**:`pubspec.yaml` 的 `version: x.y.z+n`,`+n`(build number)每次
  上传必须递增,语义版本留给用户可见的 x.y.z。

## 2. 配置与密钥

- 环境分离用 `--dart-define`/`--dart-define-from-file` 注入,不要把 staging/prod
  地址写死分支;**客户端没有真正的密钥安全**——打进包里的任何 key 都可被提取,
  真密钥留在服务端,客户端只持有可吊销的低权限令牌。

## 3. 灰度与回滚

- Android 用 Play 分阶段发布(staged rollout 百分比),iOS 用 TestFlight +
  phased release;**应用商店没有真正的"回滚"**——只能加急发新版本,所以灰度
  比例爬坡(1%→10%→50%→100%)期间的崩溃率监控是唯一的安全网。
- 远程开关(feature flag/Remote Config)让"关掉坏功能"不依赖发版——高风险
  功能上线必须带开关。

## 4. 上线观测

- 崩溃监控(Crashlytics/Sentry)在第一个版本就接,带混淆符号表上传
  (Android R8 mapping / iOS dSYM),否则线上堆栈不可读;
- 关键指标:崩溃率(crash-free users)、ANR 率(Play 政策红线)、启动时长;
  发布后 24-48 小时是回归窗口,对照灰度分桶看。
