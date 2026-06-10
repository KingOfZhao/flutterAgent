# Dart 语言进阶(向量库优质语料·轮21)

> 反思缺口:全部语料站在 Flutter 框架层;Dart 3 的语言能力(records/
> patterns/sealed/null safety 边界)直接决定状态与错误建模质量,零覆盖。
> 来源见 REFERENCES §29。

## 1. sealed class + 穷尽 switch:状态建模的语言级保障

- `sealed` 限定子类必须在同库声明,编译器因此**知道全部子类**,switch
  漏分支直接编译报错——把"新增一种状态忘了处理"从运行时 bug 变成
  编译错误;
- 这正是网络层三类错误建模(flutter-networking-api §3)与 UI 状态
  (loading/data/error)的标准载体:
  ```dart
  sealed class LoadState<T> {}
  class Loading<T> extends LoadState<T> {}
  class Data<T> extends LoadState<T> { final T value; ... }
  class Failure<T> extends LoadState<T> { final AppError error; ... }
  // switch (state) { ... }  // 漏写 Failure 分支 → 编译错误
  ```
- `final class`(禁继承)/`base`/`interface` 是 API 边界控制;库内部
  状态层级默认用 sealed。

## 2. records 与 patterns(解构)

- record `(int, {String name})` 是轻量多返回值/临时组合,**值语义**
  (==按内容)——适合"返回两个东西"而不值得开类的场合;但 record
  无名字无方法,跨模块传播的领域数据仍应建类;
- pattern matching 把"判型+取值+守卫"压成声明式:
  `case Data(value: final v) when v.isNotEmpty:`;解构 JSON
  `case {'id': int id, 'name': String name}:` 比链式 `as`/`[]` 安全;
- `switch` 表达式(非语句)+ 穷尽性 = 状态到 UI 的映射可以是一个
  无 default 的表达式,default 分支会**吞掉穷尽性检查**,sealed 体系里
  慎写 default。

## 3. null safety 的边界(为什么还会 NPE)

- 健全性边界:`!` 强转、`late` 未初始化即读、与原生/JSON 的边界
  (`dynamic` 进来的值)——运行时空错误几乎全来自这三处;
- `late` 的语义是"我保证用前已赋值",编译器不验证该承诺——能用
  nullable + 局部提升(if 判空后自动 promote)就不用 late;字段不
  promote(可能被其他代码改),模式 `if (x case final y?)` 或先取
  局部变量;
- JSON 反序列化是 dynamic 渗入的最大口子——代码生成序列化
  (flutter-networking-api §4)的价值有一半在于把这条边界收窄到
  生成代码内。

## 4. 代码生成生态与宏的现状

- build_runner(json_serializable/freezed/riverpod_generator)是当前
  生态主干;freezed 把"不可变+copyWith+union"打包,与 sealed/patterns
  原生能力重叠度上升,新代码可先用语言原生能力,复杂 copyWith 再上
  freezed;
- **宏(macros)实验已于 2025 年初被官方放弃**——押注"宏将取代
  build_runner"的架构决策已失效,官方转向增强 build_runner 性能与
  数据类语言特性,这是依赖治理(轮22)中"跟踪官方路线再下注"的实例。

## 5. 与本仓库其他语料的衔接

- 三类错误 sealed 建模 ← flutter-networking-api §3;JSON 边界 ← 同 §4;
- isolate 消息的值传递与 record 值语义同源 ← flutter-concurrency §3。
