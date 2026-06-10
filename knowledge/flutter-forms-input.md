# 表单与输入系统(向量库优质语料·轮16)

> 反思缺口:表单是业务应用的最高频界面形态,但焦点/IME/校验/键盘遮挡
> 这条输入链路在语料中零覆盖。来源见 REFERENCES §29。

## 1. Form/FormField 的机制与边界

- `Form` + `GlobalKey<FormState>`:`validate()` 触发所有子 FormField 的
  validator 并显示错误;`save()` 触发 onSaved;`AutovalidateMode` 控制
  时机——`onUserInteraction` 是默认体验最优解(提交前别红一片);
- validator 返回 null 即通过、返回字符串即错误文案——**validator 必须是
  纯同步函数**,异步校验(用户名查重)不能塞 validator,应防抖后置于
  状态层,错误经 `forceErrorText`(3.24+)或自管错误态注入;
- 复杂表单(动态字段/跨字段联动校验)Form 的局部性会不够用,把表单
  建模为状态层的不可变对象(字段值+脏标记+错误映射)更可控
  (flutter-state-management §1),Form 适合"提交式"简单表单。

## 2. 焦点系统(FocusNode 树)

- 焦点是一棵与 Element 树平行的 FocusNode 树;`FocusScope` 划定遍历域,
  Tab/方向键遍历顺序默认按可读顺序,可用 `FocusTraversalGroup` +
  `OrderedTraversalPolicy` 显式编排(桌面/Web 必修,轮17 衔接);
- 自建 FocusNode 必须 dispose(flutter-memory-leaks §2 同类);
- "输入完自动跳下一格"用 `textInputAction: TextInputAction.next` +
  `onEditingComplete`/`FocusScope.of(context).nextFocus()`,不要手动
  requestFocus 硬编码节点链——字段增删后顺序即坏。

## 3. IME 与键盘的高频坑

- **键盘遮挡**:`Scaffold.resizeToAvoidBottomInset`(默认 true)把 body
  随键盘缩小,配合可滚动容器 + `scrollPadding` 字段自动滚入可见区;
  全屏自定义布局用 `MediaQuery.viewInsetsOf(context).bottom` 自己让位;
- **CJK 组合输入**:拼音/日文输入存在 composing 区间,在 onChanged 里
  立刻格式化/截断文本会打断组合输入——格式化用 `TextInputFormatter`
  且尊重 `TextEditingValue.composing`,这是中文用户高频 bug 源;
- `keyboardType` + `autofillHints`(用户名/邮箱/验证码 `oneTimeCode`)
  决定键盘形态与系统自动填充,漏配 autofillHints 等于放弃平台级
  密码管理集成(flutter-mobile-security §2 的正向配套);
- 金额/手机号格式化:用 formatter 维护"光标随格式化文本移动"的
  TextEditingValue,直接 setState 文本会导致光标跳到末尾。

## 4. 提交链路的工程纪律

- 提交按钮三态(idle/loading/disabled)由状态层驱动,防双击重复提交
  与幂等键配套(flutter-networking-api §2);
- 失败错误回填到字段级(服务端 422 的 field errors 映射回 FormField),
  而非只弹全局 toast——错误离字段越近修正成本越低;
- widget 测试:`tester.enterText` + `pump` 即可驱动整条校验链,表单是
  widget 测试性价比最高的覆盖对象(flutter-testing-strategy §2)。

## 5. 与本仓库其他语料的衔接

- 表单状态建模 ← flutter-state-management §1;
- 桌面端焦点遍历 → flutter-web-desktop-adaptive(轮17);
- 进程死亡时的草稿保存 ← flutter-lifecycle-state-restoration §3。
