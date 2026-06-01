---
id: flutter-auth-protocols
name: 认证授权协议 (OAuth2 / OIDC / PKCE / JWT / 刷新令牌 / 生物识别)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [auth, oauth2, oidc, pkce, jwt, token, refresh, sso, biometric, secure-storage, login]
applies_when: 实现登录/第三方授权/单点登录/令牌管理,或设计客户端如何安全持有与刷新凭证
stage_hints: [architecture, breakdown]
---

# 认证授权协议

登录与授权有成熟标准协议,**绝不要自创**。本 skill 给"用哪个协议、移动/桌面/web
各自怎么落地、令牌怎么安全存与刷新"的判断。协议传输层见 `flutter-network-protocols`,
令牌的安全存储与攻击面见 `flutter-security`,刷新拦截器的并发实现见 `flutter-network`。

## 0. 先分清概念

- **认证(Authentication)= 你是谁**;**授权(Authorization)= 你能做什么**。
- **OAuth2** 是**授权**框架(拿 access token 访问资源);**OIDC(OpenID Connect)** 在 OAuth2 上加一层**认证**(拿 ID token 证明身份)。要"用第三方登录"就是 OIDC。
- **JWT** 是一种**令牌格式**(自包含、可验签),常被用作 access/ID token,但 JWT ≠ OAuth。

## 1. 客户端首选:Authorization Code + PKCE

- 移动/桌面/SPA 都是**公共客户端**(无法安全保存 client secret),所以用 **Authorization Code 流 + PKCE**,**不要**用已废弃的 Implicit 流。
- PKCE(Proof Key for Code Exchange):客户端生成 `code_verifier` → 哈希成 `code_challenge` 发起授权 → 用 `code_verifier` 换 token,防授权码被截获。
- 不要把 client secret 硬编码进 app(可被逆向,见 `flutter-security`)。

## 2. Flutter 落地

- 推荐用经过验证的库而非手搓:`flutter_appauth`(封装 AppAuth,原生级 OAuth2/OIDC + PKCE)、`oauth2`、或各家 SDK(Firebase Auth / Auth0 / Cognito)。
- **回调机制**:授权完成要回到 app——
  - 移动:自定义 URL scheme 或 **App Links/Universal Links**(配置见 `flutter-android-platform` / `flutter-ios-platform`,深链见 `flutter-navigation`)。
  - 桌面:本地回环 `http://localhost:<port>` 重定向。
  - web:重定向 URL。
- 用系统浏览器 / `flutter_web_auth_2` 做授权页,**别用内嵌 WebView 收集第三方账号密码**(被各家禁止且不安全)。

## 3. 令牌管理

- **access token**:短期、放 `Authorization: Bearer`,过期就用 refresh token 换新(刷新拦截器+竞态处理见 `flutter-network`)。
- **refresh token**:长期、最敏感——**存进安全存储**(`flutter_secure_storage`:iOS Keychain / Android Keystore-backed),绝不放明文 SharedPreferences/`localStorage`(见 `flutter-security`)。
- **ID token(OIDC,JWT)**:验签(签发者 `iss`、受众 `aud`、过期 `exp`)后取用户信息;别信未验签的 JWT。
- 登出要**撤销/清除**本地令牌,可调撤销端点。
- 注意时钟偏移与 `exp` 判断;refresh token 轮换(rotation)时妥善替换。

## 4. JWT 的正确认知

- JWT 是 base64 编码、**默认不加密**——别在 payload 放敏感信息(任何人能解码读)。
- 安全性来自**签名验证**(服务端验,客户端通常只读 claims 不做信任决策)。
- 不要拿 JWT 当 session 万能药;无状态意味着**难以即时失效**,需配合短有效期 + 刷新 + 黑名单策略(服务端职责)。

## 5. 生物识别 / 本地认证

- `local_authentication` 用指纹/Face ID/Windows Hello 做**本地二次确认**(解锁 app、确认支付),它**不替代**服务端鉴权——只是本地门禁。
- 真正的凭证仍由 OAuth/OIDC 令牌承载;生物识别用来保护"本地存的令牌何时可用"。

## 6. 平台与 SSO

- 企业 SSO 多走 OIDC/SAML 对接 IdP(Azure AD/Okta/Keycloak);移动端仍是 Code+PKCE。
- Sign in with Apple:若 iOS 上提供了第三方社交登录,Apple 审核可能**要求**也提供它(见 `flutter-ios-platform`)。

## 反模式

- ❌ 自己发明 token/登录协议,或用已废弃的 OAuth Implicit 流。
- ❌ 把 client secret / refresh token 明文存(SharedPreferences/`localStorage`/硬编码)。
- ❌ 用内嵌 WebView 直接收集第三方账号密码。
- ❌ 信任未验签的 JWT,或把敏感数据塞进 JWT payload。
- ❌ 把生物识别当成服务端鉴权的替代(它只是本地门禁)。

## 参考 / References

- OAuth 2.0:<https://oauth.net/2/> · 授权框架 RFC 6749:<https://datatracker.ietf.org/doc/html/rfc6749>
- PKCE(RFC 7636):<https://datatracker.ietf.org/doc/html/rfc7636>
- OAuth 2.0 for Native Apps(BCP,RFC 8252):<https://datatracker.ietf.org/doc/html/rfc8252>
- OpenID Connect:<https://openid.net/developers/how-connect-works/>
- JWT(RFC 7519):<https://datatracker.ietf.org/doc/html/rfc7519> · <https://jwt.io/introduction>
- `flutter_appauth`:<https://pub.dev/packages/flutter_appauth>
- `flutter_secure_storage`:<https://pub.dev/packages/flutter_secure_storage>
- `local_auth`(生物识别):<https://pub.dev/packages/local_auth>
- OWASP MASVS(认证存储):<https://mas.owasp.org/MASVS/>
- 令牌安全存储见 `flutter-security`;刷新竞态见 `flutter-network`;回调深链见 `flutter-navigation`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **永不自创鉴权协议**:用 OAuth2/OIDC + PKCE 等标准,把安全交给被审计过的协议与库。
- **客户端是公共客户端**:没有安全的 secret 存放处,所以 PKCE、安全存储、系统浏览器是默认。
- **JWT 安全靠验签不靠保密**:payload 公开可读,别放敏感信息,失效策略是服务端的事。

**诚实边界:**

- 鉴权的安全边界大头在**服务端**;客户端做对协议与存储,但不能替服务端兜底。
- 各 IdP/SDK 实现细节差异大,以其官方文档为准,这里给协议骨架。
- 安全是攻防演进领域,需结合 OWASP MASVS 与当时最佳实践复核,不能一劳永逸。
