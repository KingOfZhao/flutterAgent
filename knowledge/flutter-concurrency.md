# Flutter 并发与 Isolate(向量库优质语料·轮6)

> 反思缺口:性能语料只给了一句"重计算用 compute()",但"什么时候 async 够用、
> 什么时候必须 isolate、isolate 的限制"这一判断链无语料。来源见 REFERENCES §27。

## 1. 先分清:async 解决等待,isolate 解决计算

- Dart 是单线程事件循环:`async/await` 只是**让出等待时间**(网络/IO),
  不会把 CPU 计算移出主 isolate——`await` 一个纯计算函数照样卡 UI。
- 判断标准:操作是"等"(IO-bound)→ async 足够;操作是"算"(JSON 大解析、
  图像处理、加解密、>几毫秒的同步循环)→ 需要 isolate,否则该帧必掉。
- 16.7ms 帧预算内,主 isolate 上任何同步段超过几毫秒就该警惕(对应
  flutter-performance §1 的帧预算)。

## 2. Isolate 使用阶梯(从简到繁)

1. **`compute()` / `Isolate.run()`**:一次性任务的默认答案——起 isolate、
   跑函数、回传结果、自动销毁;`Isolate.run` 是 Dart 2.19+ 更通用的形式。
2. **长驻 isolate(`Isolate.spawn` + SendPort/ReceivePort 双向通道)**:
   高频重复任务(每帧都要算)才值得,因为 spawn 本身有几十毫秒级开销,
   一次性任务用长驻是负优化。
3. **isolate 池**:并行批处理才需要;注意池大小对齐核数,过多 isolate 内存
   开销大(每个有独立堆)。

## 3. 限制与陷阱

- **isolate 间不共享内存**:消息传递默认深拷贝;大对象传输成本高——
  Dart 对部分不可变对象做了传输优化,但仍应传"原始数据进、结果出",
  不要把整个状态树扔过去。
- **不能传的东西**:平台插件句柄、BuildContext 等绑定主 isolate 的对象;
  **后台 isolate 默认不能直接调平台通道**(需 BackgroundIsolateBinaryMessenger
  显式打通),"在 isolate 里调插件报错"是高频踩坑。
- **错误会静默消失**:`Isolate.spawn` 的未捕获异常不会冒泡到主 isolate,
  必须挂 `onError` 端口或在入口函数内 try/catch 回传,否则后台任务失败无感知。
- Web 平台无 isolate(`compute` 退化为同 isolate 执行),跨端项目的重计算
  方案需按平台分流。

## 4. 与本仓库其他语料的衔接

- 帧预算判定标准 ← flutter-performance §1;
- 大 JSON 解析移 isolate 是网络层的标准配套(flutter-networking-api §3);
- 长驻 isolate 的生命周期归属 Repository/Service 层管理(flutter-app-architecture §1)。
