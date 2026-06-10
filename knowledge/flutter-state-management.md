# Flutter 状态管理选型(向量库优质语料)

> 用途:为语义检索提供"状态管理怎么选"的高密度判断依据。来源见 REFERENCES §25。

## 1. 选型决策树

- **先分清两类状态**(官方分法):ephemeral state(单 widget 内,`setState` 即可)
  与 app state(跨组件共享,才需要状态管理方案)。把 ephemeral state 塞进全局
  store 是最常见的过度设计。
- **小型应用 / 团队新手多**:`provider`——官方推荐入门方案,概念少(ChangeNotifier
  + InheritedWidget 封装),迁移成本最低。
- **中大型应用**:`riverpod`——provider 作者的重写版,编译期安全(无 BuildContext
  依赖、provider 未定义即编译错)、可测试性好(ProviderContainer 纯 Dart 测试)、
  支持自动销毁与依赖追踪。
- **强事件溯源 / 团队已有 Rx 经验**:`bloc`——事件→状态显式建模,转换可记录可回放,
  代价是模板代码量最大。
- **不要混用两套全局方案**:provider 与 bloc 并存会造成"谁是事实源"的歧义;
  例外是局部 ValueNotifier/setState 与任一全局方案共存,这是正常分层。

## 2. 常见错误

- 在 build 方法里创建 provider/store 实例——每次重建都新建状态,表现为"状态莫名重置"。
- 把网络请求结果直接当状态——应区分"远端数据缓存"(用 FutureProvider/AsyncValue
  或 repository 层)与"客户端状态"。
- 用全局单例 service + 手动 notifyListeners 自造一套——失去 devtools 检查与测试注入点。

## 3. 与本仓库 pipeline 的关系

skill ranker 对"状态管理/state/provider/riverpod/bloc"等需求词召回本文档时,
判断依据是上面的决策树而非单一推荐——选型输出必须解释"为什么是这个规模/团队
画像选这个方案"。
