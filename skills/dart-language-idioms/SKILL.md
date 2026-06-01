---
id: dart-language-idioms
name: Dart 语言地道写法 (Effective Dart + 现代特性)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [dart, language, idioms, effective-dart, null-safety, records, pattern-matching, sealed, extension-types, style]
applies_when: 写或改 Dart 代码时,想把语言层写地道、用对现代特性、避免坏味道
stage_hints: [architecture, breakdown]
---

# Dart 语言地道写法

"会用 Flutter"不等于"会写 Dart"。很多可维护性问题其实是语言层没写地道:
该用 `final` 用了 `var`、该用 sealed class 穷尽却用 `if-else` 兜底、把可空当非空用。
本 skill 收敛到 **Effective Dart** 官方规范 + 现代语言特性(Dart 3+),是
`flutter-engineering-workflow` 阶段 1 实现时的"语言层手册"。库设计层面与
`architecture-design` 配合,代码生成相关见 `flutter-codegen`。

## 0. 总原则(Effective Dart 四象限)

Effective Dart 把规则分成 **Style / Documentation / Usage / Design**,优先级从高到低记忆:
**先正确(Usage)→ 再清晰(Design/Doc)→ 后风格(Style,交给 `dart format`)。**
风格不用背——`dart format` 与 `flutter analyze` 会替你执行;真正要内化的是 Usage 与 Design。

## 1. 不可变优先 & 命名

- 默认 `final`(运行时常量)/ `const`(编译期常量);只有真要重新赋值才用 `var`。
  - widget 构造、字面量集合能 `const` 就 `const`,省 rebuild 也省内存。
- 命名:类型用 `UpperCamelCase`,成员/变量/函数用 `lowerCamelCase`,常量也用 `lowerCamelCase`(不是 `SCREAMING_CAPS`),库/文件用 `snake_case`。
- 别给类型名加冗余前后缀(`AbstractX` / `XImpl` / `XInterface` 多数时候是坏味道)。

## 2. 空安全(null safety)写地道

- 类型默认非空;只有"真的可能没有"才标 `?`。不要用 `late` 绕过空检查来图省事。
- 取值优先 `?.` / `??` / `??=`,少用 `!`(强制解包)——每个 `!` 都是一句"我担保非空",担保错了就崩。
- `late` 只用于"声明时还没有、使用前一定会被赋值"的场景(如 `initState` 里初始化),并清楚它会把空检查从编译期推到运行期。

## 3. Dart 3 现代特性(优先用,能消除一类样板/bug)

- **Records(记录)**:返回多个值不用再造一次性 class:`(int, String) f() => (1, 'a');`,解构 `var (n, s) = f();`。
- **Pattern matching + switch 表达式**:`switch` 当表达式用,配合 sealed 类型可**穷尽**,编译器帮你保证不漏分支:
  ```dart
  String label(Shape s) => switch (s) {
    Circle(:final r) => 'circle $r',
    Square(:final side) => 'square $side',
  };
  ```
- **Sealed / final classes**:用 `sealed` 表达"封闭的一组子类型"(状态机、AST、结果类型),换来 `switch` 穷尽检查;`final`/`base`/`interface` 显式控制可继承性,别让继承关系靠默契。
- **Extension types**:零开销包装一个底层类型做类型安全(如给 `String` 包一层 `UserId`),比 `typedef` 更强、比真包装类更省。
- 集合用 spread (`...`)、collection-if/for 构造,别在 `build()` 里写命令式拼 list。

## 4. 异步写地道

- `async`/`await` 优先于裸 `.then()` 链;并发用 `Future.wait` 而不是顺序 `await` 串行。
- 流用 `Stream` + `await for` / `StreamSubscription`;**订阅必取消**(见 `flutter-resource-lifecycle`)。
- 不要 `async` 不 `await`(fire-and-forget)而吞掉异常;确需如此要显式 `unawaited(...)` 并处理错误。

## 5. 函数与 API 设计

- 参数多于 1~2 个、或同类型并排,优先**命名参数** + `required`,可读且防传错位。
- 返回类型、公共 API 显式写类型;局部变量可交给类型推断。
- 别用布尔位置参数当"模式开关"(`build(true)` 读不懂),用命名参数或枚举。
- 公共 API 写 `///` dartdoc(见 `flutter-documentation`)。

## 6. 让工具替你执行规范

```bash
dart format .                 # 风格,别手动纠结
dart analyze                  # 静态规则(基于 analysis_options.yaml)
dart fix --apply              # 自动套用可修复的 lint/迁移
```

- `analysis_options.yaml` 启用 `flutter_lints` 或更严的 `very_good_analysis`;新规则尽量开,别 `// ignore:` 掩盖。

## 反模式

- ❌ 到处 `var` + `dynamic`,放弃类型系统给的保护。
- ❌ 用 `!` / `late` 绕开空安全,把编译期问题推到运行时崩溃。
- ❌ 对 sealed 类型还写 `default:` 兜底,丢掉穷尽检查的价值。
- ❌ 手动调格式 / 与 `dart format` 对着干,制造 diff 噪音。
- ❌ 多返回值硬塞进 `Map<String, dynamic>` 而不用 record / 具名类型。

## 参考 / References

- Effective Dart(总览):<https://dart.dev/effective-dart>
- Effective Dart · Usage:<https://dart.dev/effective-dart/usage>
- Effective Dart · Design:<https://dart.dev/effective-dart/design>
- 空安全(sound null safety):<https://dart.dev/null-safety>
- Records:<https://dart.dev/language/records>
- Patterns / pattern matching:<https://dart.dev/language/patterns>
- Branches(switch 表达式):<https://dart.dev/language/branches>
- Class modifiers(sealed/final/base/interface):<https://dart.dev/language/class-modifiers>
- Extension types:<https://dart.dev/language/extension-types>
- `dart fix`:<https://dart.dev/tools/dart-fix>
- Linter rules:<https://dart.dev/tools/linter-rules>

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **类型系统是免费的测试**:把约束写进类型(非空 / sealed / extension type),编译器就替你挡掉一类 bug。
- **风格交给工具,脑力留给设计**:`format`/`analyze`/`fix` 能自动的别用人脑。
- **现代特性多为消除样板**:records/patterns/sealed 的价值是"少写易错代码",不是炫技。

**诚实边界:**

- 语言地道 ≠ 架构正确;分层与状态管理见 `architecture-design` / `state-management`。
- Dart 3 特性需 SDK 版本支持;老项目升级前先看 `flutter-dependency-maintenance`。
- 规范有取舍空间,团队既有约定优先于个人偏好。
