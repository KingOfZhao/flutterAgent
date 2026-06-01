---
id: flutter-domain-modeling
name: Flutter/Dart 领域建模(让非法状态不可表达 / 状态机 / 值对象与不变量)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [domain, modeling, sealed, state-machine, invariant, value-object, types, illegal-states, ddd]
applies_when: 业务规则复杂、状态多、容易出现"不可能但还是发生了"的状态时——用类型把业务约束编码进数据结构
stage_hints: [architecture, breakdown, implementation, review]
see_also: [dart-language-idioms, flutter-error-handling, state-management]
---

# Flutter/Dart 领域建模

本 skill 负责**用类型表达业务规则**:让非法状态在编译期就无法构造(make illegal states
unrepresentable),用 sealed 类建模有限状态机,用值对象守住不变量。它是
`flutter-engineering-workflow` 实现阶段的横切能力,聚焦"数据该长什么样"。
语言机制(sealed/records/pattern matching)见 `dart-language-idioms`;
失败如何建模为返回值见 `flutter-error-handling`;运行期状态怎么存放/通知 UI 见 `state-management`。

## 0. 核心命题:让非法状态不可表达

布尔标志的组合会产生"语义上不可能、类型上却合法"的状态。例如同时
`isLoading=true` 且 `error != null` 且 `data != null`——三个字段 8 种组合,
其中大半无意义,却要靠 if 散落各处去"约定"。把它收敛成一个 sealed 联合:

```dart
sealed class LoadState<T> {}
class Loading<T> extends LoadState<T> {}
class Loaded<T> extends LoadState<T> { final T data; Loaded(this.data); }
class Failed<T> extends LoadState<T> { final Failure failure; Failed(this.failure); }
```

- 现在只有 3 种合法状态,`switch` 穷尽(见 `dart-language-idioms`)逼你处理每一种。
- UI 三态(加载/数据/错误)直接对位,不会出现"既在加载又有错误"的矛盾。

## 1. 值对象(Value Object):把校验收进构造

不要让 `String email` 满天飞、每个用到的地方各校验一遍。建一个**自校验**的值对象:

```dart
class Email {
  final String value;
  Email._(this.value);
  static Result<Email> tryParse(String raw) =>
      raw.contains('@') ? Ok(Email._(raw)) : const Err(InvalidEmail());
}
```

- 一旦构造成功,后续代码可以**信任**它合法——不变量(invariant)在边界处守一次即可。
- 用 `==`/`hashCode`(或 freezed/Equatable,见 `flutter-codegen`)给值语义,别用引用相等。

## 2. 有限状态机(FSM):显式建模转移

订单、上传、连接、向导流程……凡"状态有限 + 转移有规则"的,显式建模:

- 状态用 sealed 子类;**转移**写成纯函数 `Next next(Current, Event)`,非法转移返回原态或 `Err`。
- 好处:转移逻辑集中、可单测(纯函数,见 `flutter-testability-design`)、新增状态时编译器提示所有 `switch` 待补。
- 复杂可视化流程可考虑 `statecharts`/`flutter_bloc` 的状态机思路,但**先用 sealed + 纯函数**,不够再上库。

## 3. 用类型表达"二选一"和"必有其一"

- 互斥用 sealed 联合(上面的 LoadState),不要并列可空字段。
- "至少有一个"的集合用非空类型表达(如自建 `NonEmptyList`,或在构造处校验)。
- 可空 `T?` 只用于"真的可能没有";不要用 `null` 兼表"加载中""出错了""空"。

## 4. 分层落位

- 领域模型放 **domain 层**:纯 Dart、不依赖 Flutter/IO,可独立单测。
- data 层负责把 DTO/JSON 翻译成领域模型(并在此校验不变量),见 `flutter-error-handling` §1。
- presentation 层只消费领域状态,不重新发明业务规则。

## 反模式

- ❌ 用一堆并列 bool(`isLoading/isError/isEmpty`)表达本应互斥的状态。
- ❌ 把校验逻辑散落在每个调用点,而不是收进值对象/工厂构造。
- ❌ 领域模型里 import `package:flutter`,导致无法纯 Dart 单测。
- ❌ 用 `null` 同时兼表"无值/加载中/出错",语义塌缩。
- ❌ 状态转移用散落的 if 改字段,而非集中的转移函数——新增状态必漏改某处。

## 参考 / References

- Dart sealed classes / 穷尽 switch:<https://dart.dev/language/class-modifiers>
- Pattern matching:<https://dart.dev/language/patterns>
- Effective Dart(类型与设计):<https://dart.dev/effective-dart/design>
- `freezed`(sealed/union 代码生成):<https://pub.dev/packages/freezed>
- "Make illegal states unrepresentable"(类型驱动设计,跨语言通用理念):<https://fsharpforfunandprofit.com/posts/designing-with-types-making-illegal-states-unrepresentable/>
- 失败建模见 `flutter-error-handling`;运行期状态见 `state-management`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **能在编译期挡住的错误,就别留到运行期**:类型是最便宜的测试。
- **不变量守在边界,核心信任之**:构造时校验一次,内部代码不再到处防御。
- **状态有限就显式枚举它**:模糊的"标志位组合"是 bug 的温床。

**诚实边界:**

- 过度建模也是负担:简单 CRUD 别硬套状态机/值对象,按复杂度投入。
- 类型只能表达"结构性"约束;跨字段的复杂业务规则仍需运行期校验 + 测试兜底。
- Dart 类型系统不如纯函数式语言强(无依赖类型、union 需 sealed 模拟),别强求极致。
