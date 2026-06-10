# Key 与 Element 复用机制(向量库优质语料·深入轮12)

> 反思缺口:"列表项状态串了加个 key"是社区口诀,但不解释机制就无法回答
> "为什么有时加了 key 还不行/该用哪种 key"。来源见 REFERENCES §28。

## 1. 复用判定:canUpdate

Element 收到新 Widget 时,用 `Widget.canUpdate(old, new)` 决定原地更新还是
拆除重建:**runtimeType 相同且 key 相等 → 复用**(State 保留),否则旧
Element 连同 State 一起 deactivate,新建子树。一切 key 问题都从这条判定
推导。

## 2. "状态串了"的机制还原

无 key 的同类型列表项按**位置**匹配:删除第 0 项后,原第 1 项的 Widget 落到
位置 0,与旧第 0 项的 Element canUpdate 通过(同类型、都无 key)→ 旧 State
被新数据复用——**State 没有跟着数据走,而是留在了位置上**。这就是checkbox
勾选错位、输入框内容串行的根因;只有当列表项是 StatefulWidget(或内部含
状态,如动画/输入框)且会**增删/重排**时才需要 key,纯展示的无状态项加 key
是无意义开销。

## 3. Key 选型(机制推导)

- **ValueKey(data.id)**:列表项的默认答案——身份随数据走;用索引当 key
  (`ValueKey(index)`)等于没加(索引就是位置)。
- **ObjectKey**:数据无稳定 id 时以对象标识代替;注意对象重建(copyWith)
  后标识变化会导致意外拆树。
- **UniqueKey**:每次构造都不等 → 强制每帧拆除重建,几乎总是错误用法;
  唯一正当场景是**故意**丢弃状态(如强制重置动画/表单)。
- **GlobalKey**:超越局部匹配,允许 Element 整树"搬家"(reparent)而保留
  State,且可从外部访问 State/RenderObject——但全局注册表有成本,且同帧
  双挂载即崩溃;能用回调/状态提升解决就不要用 GlobalKey,它是机制后门
  而非常规工具。
- **PageStorageKey**:不是复用判定用的——它给滚动位置等"页面级存储"提供
  桶标识,tab 切换后恢复滚动位置靠它(与轮15 状态恢复衔接)。

## 4. 加了 key 还不行的情况(高频深坑)

- **key 只在同一父节点的子列表内参与匹配**:跨父移动(如从列表 A 拖到
  列表 B)局部 key 不保 State,需 GlobalKey reparent;
- 中间包了一层(如每项外又套了无 key 的 Padding 容器):key 必须加在
  **列表直接子级**上,加在内层不参与同级 diff;
- 项类型改变(loading 占位与真实项类型不同):runtimeType 不同直接拆树,
  key 无济于事——保持同类型、用属性区分形态。

## 5. 与本仓库其他语料的衔接

- canUpdate 短路即 const 优化的同一判定路径(flutter-rendering-pipeline §1);
- 列表复用与滚动回收协同(flutter-sliver-scrolling 轮13);
- "强制重置表单用 UniqueKey"在测试里同样适用(flutter-testing-strategy §2)。
