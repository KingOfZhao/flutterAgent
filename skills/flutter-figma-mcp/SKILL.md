---
id: flutter-figma-mcp
name: Figma UI 理解与 MCP 取数生成代码 (要素识别 / padding / 线条颜色 / 图标判定 / token 取数 / 框架映射)
version: 1.0.0
platforms: [all, mobile, desktop, web]
tags: [figma, mcp, design-to-code, padding, stroke, icon, auto-layout, token, rest-api, ui]
applies_when: 输入是 Figma 设计稿(链接/文件/截图),需要通过 MCP 或 Figma API 读取精确数据并生成 Flutter 代码
stage_hints: [spec, breakdown, implementation]
see_also: [flutter-ui-from-image, flutter-design-to-code-playbook, flutter-design-tokens-theming]
---

# Figma UI 理解与 MCP 取数生成代码

> 分工:本 skill 负责 **Figma 数据模型的理解** 与 **MCP/API 精确取数**。
> 只有截图没有源文件时的"目测读图"见 `flutter-ui-from-image`;
> 端到端流水线见 `flutter-design-to-code-playbook`;token 落地见 `flutter-design-tokens-theming`。

> 核心原则:**有 Figma 源文件就绝不目测**。截图取色/量距是近似值,Figma 节点数据是精确值。
> 读图(视觉)用于建立**整体结构假设**,MCP/API 取数用于获得**精确规格**,两者互相校验。

---

## 1. Figma 数据模型速览(理解一切的前提)

Figma 文件是一棵节点树,每个节点有 `type`,关键类型:

| 节点 type | 含义 | Flutter 对应直觉 |
|------|------|------|
| `FRAME` | 容器(可带 Auto Layout) | `Container` / `Column` / `Row` |
| `GROUP` | 无布局语义的分组 | 通常展开拍平,不直接映射 |
| `COMPONENT` / `INSTANCE` | 组件定义 / 实例 | 可复用 widget |
| `TEXT` | 文本 | `Text` + `TextStyle` |
| `RECTANGLE` / `ELLIPSE` / `LINE` | 形状 | `Container`/`DecoratedBox`/`Divider` |
| `VECTOR` / `BOOLEAN_OPERATION` | 矢量路径 | 多为图标 → SVG 导出 |

每个节点的关键字段:

- `absoluteBoundingBox`:`{x, y, width, height}` — 绝对坐标与尺寸。
- `fills`:填充(实色 `SOLID` / 渐变 `GRADIENT_LINEAR` 等 / 图片 `IMAGE`)。
- `strokes` + `strokeWeight` + `strokeAlign`:描边(= 线条/边框)。
- `cornerRadius` / `rectangleCornerRadii`:圆角(统一或四角分别)。
- `effects`:阴影(`DROP_SHADOW`/`INNER_SHADOW`)、模糊。
- `style`(TEXT 节点):`fontFamily`、`fontWeight`、`fontSize`、`lineHeightPx`、`letterSpacing`。
- Auto Layout 字段(见 §2):`layoutMode`、`padding*`、`itemSpacing`。

---

## 2. 识别 padding(优先信源:Auto Layout)

### 2.1 有 Auto Layout(精确,直接用)

`FRAME` 节点若 `layoutMode != NONE`,padding 是**显式数据**,不需要量:

```jsonc
{
  "layoutMode": "VERTICAL",        // → Column;HORIZONTAL → Row
  "paddingLeft": 16, "paddingRight": 16,
  "paddingTop": 12,  "paddingBottom": 12,
  "itemSpacing": 8,                 // 子元素间距 → SizedBox/Gap 或 spacing
  "primaryAxisAlignItems": "CENTER",   // → MainAxisAlignment
  "counterAxisAlignItems": "CENTER"    // → CrossAxisAlignment
}
```

映射:

```dart
Padding(
  padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
  child: Column(
    mainAxisAlignment: MainAxisAlignment.center,
    crossAxisAlignment: CrossAxisAlignment.center,
    spacing: 8, // Flutter 3.27+;低版本用 SizedBox/Gap
    children: [...],
  ),
)
```

### 2.2 无 Auto Layout(几何推算)

老设计稿常是绝对定位,padding 要用**父子 bounding box 差值**推算:

```
paddingLeft   = child.x - parent.x
paddingTop    = child.y - parent.y
paddingRight  = (parent.x + parent.width)  - (child.x + child.width)
paddingBottom = (parent.y + parent.height) - (child.y + child.height)
itemSpacing   = nextChild.x - (child.x + child.width)   // 横向排列
```

注意:

- 推算值出现 15.5 / 16.2 这种零碎数 → 按设计系统常见刻度(4/8/12/16/24)**就近归整**,并在产出里标注"推算+归整"。
- 多个子元素间距不一致 → 别假设统一 spacing,逐一记录。
- 仅从**截图目测** padding 时,以相邻元素重复出现的间隔为锚(同一页面同类间距大概率相同),仍标注为近似值。

---

## 3. 识别线条颜色(stroke vs 细 fill)

"线条"在 Figma 里有两种来源,取色路径不同:

1. **描边 `strokes`**(边框/分割线最常见):

```jsonc
{
  "strokes": [{ "type": "SOLID", "color": { "r": 0.898, "g": 0.898, "b": 0.898, "a": 1 } }],
  "strokeWeight": 1,
  "strokeAlign": "INSIDE"   // INSIDE/OUTSIDE/CENTER,影响占位
}
```

   - **颜色是 0–1 浮点**,换算:`round(r*255)` → `0.898*255 ≈ 229` → `#E5E5E5` → `Color(0xFFE5E5E5)`。
   - 映射:四边边框 → `Border.all(color: ..., width: strokeWeight)`;单边 → `Border(bottom: BorderSide(...))`。

2. **细长矩形 / `LINE` 节点的 `fills`**(设计师画的分割线):高度 1–2px 的 `RECTANGLE` → 取 `fills[0].color` → 映射 `Divider(color: ..., thickness: ...)` 或 1px `Container`。

判定技巧(只有截图时):

- 分割线颜色通常是低饱和灰(`#EEEEEE`–`#E0E0E0` 区间),与背景对比微弱;别把它当文字色采集。
- 边框颜色与组件填充色相近时,确认是 stroke 还是内阴影(`effects` 里的 `INNER_SHADOW`)。
- 渐变描边:`strokes[0].type == GRADIENT_*` → Flutter 需 `GradientBoxBorder`(自绘或三方包),直接 `Border` 做不到。

---

## 4. 判定「哪些是图标」

### 4.1 有节点数据(可靠信号,按优先级)

1. `type == VECTOR` / `BOOLEAN_OPERATION` / 多个 vector 组成的小 `FRAME`。
2. **命名约定**:节点名含 `icon` / `ic_` / `icn` / 具体图标名(`arrow-left`, `search`)。
3. **尺寸特征**:宽高 ≈ 12/16/20/24/32 且近似正方形。
4. `COMPONENT`/`INSTANCE` 且来自图标库(componentSet 名为 Icon 类)。
5. `fills` 为单色 + 路径数据 → 单色图标,可换色;多色复杂路径 → 彩色插画,按图片处理。

### 4.2 只有截图(目测启发式)

- 小尺寸(<32dp)、正方形、单色、紧贴文字或按钮边缘 → 大概率图标。
- 与 Material Icons 形状吻合(放大镜/铃铛/箭头/齿轮) → 直接用 `Icons.*`,**不要**导出图片。
- 彩色、不规则、有细节渐变 → 当插画/图片处理。

### 4.3 图标落地策略

| 情形 | 做法 |
|------|------|
| 与 Material/Cupertino 内置图标吻合 | `Icon(Icons.search)` — 首选,零资源 |
| 自定义单色图标 | Figma 导出 SVG → `flutter_svg` 渲染,`colorFilter` 换色 |
| 大量自定义图标 | 打成 icon font(如 `flutter_iconpicker` 流程)或统一 SVG 目录 + 代码生成 |
| 彩色插画 | 导出 PNG @1x/2x/3x 或 SVG,按图片管理 |

导出 API:`GET /v1/images/:file_key?ids=<node_id>&format=svg`。

---

## 5. MCP 通过 Figma token 取数(最佳实践)

### 5.1 接入方式(二选一)

1. **官方 Figma MCP Server(Dev Mode)**:Figma 桌面端开启 Dev Mode MCP Server,本地 SSE 端点(默认 `http://127.0.0.1:3845/sse`)。提供 `get_code`、`get_variable_defs`、`get_image` 等工具,直接基于当前选中节点。
2. **REST API 型 MCP(如 `figma-developer-mcp` / Framelink)**:基于 Personal Access Token 调 REST API,适合 CI / 无桌面端场景:

```json
{
  "mcpServers": {
    "figma": {
      "command": "npx",
      "args": ["-y", "figma-developer-mcp", "--stdio"],
      "env": { "FIGMA_API_KEY": "<personal-access-token>" }
    }
  }
}
```

### 5.2 Token 安全(红线)

- Token 在 Figma → Settings → Security → Personal access tokens 生成,scope 给**只读**(`file_content:read` 等)即可。
- **只放环境变量 / MCP server env 配置**,绝不写进仓库、代码、共享的 mcp.json 提交版本。
- Token 等同账号文件读取权限,泄漏即泄漏全部可见设计稿;定期轮换。

### 5.3 取数流程(避免一次拉爆)

Figma 文件级 `GET /v1/files/:key` 返回整棵树,大文件可达几十 MB。正确流程:

```
1. 从链接解析 file_key 与 node-id
   https://www.figma.com/design/<file_key>/<name>?node-id=<id>
2. 只取目标节点:GET /v1/files/:key/nodes?ids=<node_id>&depth=N
   (depth 控制层级,先 depth=2 看结构,再按需下钻)
3. 取样式/变量:GET /v1/files/:key/styles 、本地 variables 接口
   → 颜色/字体/间距 token 化(对应 flutter-design-tokens-theming)
4. 取图标/图片:GET /v1/images/:key?ids=...&format=svg|png
5. 节点数据 → 结构化 ui-spec(布局树/padding/颜色/字体/图标清单)
```

### 5.4 数据 → 规格的转换要点

- 颜色 0–1 浮点 → hex,记得带 `opacity` 字段(节点级透明度独立于 color.a);alpha < 1 时拼入 hex 后缀(`#RRGGBBAA`)。
- `lineHeightPx / fontSize` → Flutter `TextStyle(height: ...)` 的比值。
- 隐藏节点(`visible: false`)跳过;`GROUP` 拍平,不生成无意义容器。
- `constraints`(LEFT/RIGHT/SCALE/CENTER)→ 响应式行为提示(`Align`/`Expanded`/锚定)。
- **坐标归一化**:`absoluteBoundingBox` 是全文件绝对坐标,输出规格时减去画板原点,转成**相对画板**的 x/y,否则多画板数据无法对齐。

### 5.5 原始节点 → 精简 spec 的转换器模式

原始节点 JSON 噪声大(几百 KB/画板),不要直接塞进上下文;写一个纯函数转换器,只保留生成代码需要的字段:

```python
def simplify(node, origin_x=0, origin_y=0):
    out = {"id": ..., "name": ..., "type": ...,
           "x": bb.x - origin_x, "y": bb.y - origin_y, "width": ..., "height": ...}
    # 只在存在时输出:fills(solid/gradient+stops/imageRef)、strokes+strokeWeight、
    # cornerRadius/四角、effects(阴影)、TEXT 的 characters+textStyle、
    # auto-layout(mode/itemSpacing/padding 四元组),递归 children
```

产出结构:`{source: {figmaFile, page}, screens: [{nodeId, screenName, width, height, root}]}` ——
带溯源字段,多画板批量转换,每屏一棵精简树。这份 JSON 就是 §6 的 `ui-spec` 输入。

### 5.6 实战教训(踩过的坑)

- **画板会藏在 `SECTION`/分组里**:只扫 Page 顶层 children 会漏整组画板(如两套主题变体被收在一个 Section 里)。找不齐目标时,**递归遍历全树**按名称/尺寸(如 375×812)筛画板,再按 node-id 定向取数。
- **按文本内容反查画板**:知道界面上的独特文案(如 "SVIP专属加速中")时,在全树 `TEXT` 节点的 `characters` 里搜关键词,向上回溯到所属 FRAME——比按名称猜更可靠,设计师的图层命名经常不可信。
- **控制台丢 CJK 字形 ≠ 数据损坏**:终端打印中文被截断/丢字时,用字节长度或 code point 校验原始 JSON,别误判为编码损坏去"修"数据。
- **同一设计两套主题(如 VIP/SVIP)**:先确认是同画板变体还是独立画板组;拿不准就把已找到的转换交付 + 明说缺口,让用户补 node-id,不臆造也不猜。

---

## 6. 生成代码框架的最佳实践

1. **先规格后代码**:MCP 数据先转成 `ui-spec`(树 + token 表 + 图标清单),再生成代码;不要让节点 JSON 直接一对一翻译成 widget——Figma 树 ≠ 理想 widget 树。
2. **结构映射规则**:
   - Auto Layout `VERTICAL/HORIZONTAL` → `Column/Row`;`layoutWrap: WRAP` → `Wrap`。
   - 重叠的绝对定位子节点 → `Stack` + `Positioned`。
   - `INSTANCE` 重复出现 → 提取为一个 widget + 参数,而不是复制 N 份。
   - 可滚动内容(子内容超出 frame)→ `ListView`/`SingleChildScrollView`,不能写死高度。
3. **token 先行**:颜色/字号/圆角先落 `ThemeExtension`/`ColorScheme`(见 `flutter-design-tokens-theming`),widget 只消费 token;Figma Variables 有定义的优先用变量名而非裸值。
4. **官方 MCP `get_code` 输出当草稿**:它生成的代码偏"描述性还原",需人工重构——抽组件、接主题、删除写死尺寸、补四态(空/加载/错误/正常,见 `flutter-error-handling`)。
5. **校验闭环**:生成后用 `get_image`/导出图与运行截图叠图比对;关键组件加 golden test(见 `flutter-design-to-code-playbook` S7/S8)。

## 反模式

- ❌ 有 Figma 源文件却对着截图目测取色量距。
- ❌ 把整个文件 `GET /v1/files/:key` 全量拉下来塞进上下文。
- ❌ Figma 节点树一对一翻译成 widget 树(GROUP 套 GROUP → 无意义嵌套 Container)。
- ❌ 把 0–1 浮点色直接当 0–255 用,或丢掉节点 opacity。
- ❌ 图标全部导出 PNG,放着 `Icons.*` 和 SVG 不用。
- ❌ 无 Auto Layout 时推算出 15.5px 这种值直接写死,不按设计刻度归整也不标注。
- ❌ Figma token 写进仓库或提交 mcp.json。
- ❌ 信任 `get_code` 直出代码不重构、不接主题、不补状态。
- ❌ 只扫 Page 顶层就断定"文件里没有这些画板"——Section/分组嵌套会隐藏整组节点。
- ❌ 把原始节点 JSON 不经精简直接喂给模型/写进交付物。

## 参考 / References

- Figma REST API:<https://www.figma.com/developers/api>
- Figma Dev Mode MCP Server:<https://help.figma.com/hc/en-us/articles/32132100833559>
- Figma node types / Auto Layout 数据:<https://www.figma.com/developers/api#node-types>
- Personal access tokens:<https://help.figma.com/hc/en-us/articles/8085703771159>
- flutter_svg:<https://pub.dev/packages/flutter_svg>
- 目测读图方法见 `flutter-ui-from-image`;端到端流程见 `flutter-design-to-code-playbook`;token 落地见 `flutter-design-tokens-theming`。

## 心智模型与诚实边界

> 配合 `flutter-engineer-mindset`(通用思维底座)与 `flutter-skill-distillation`(女娲蒸馏法)使用。

**镜片(怎么想):**

- **数据优先于目测**:Figma 节点字段是精确事实,截图观察只是假设;能取数就取数。
- **Figma 树是绘制结构,widget 树是布局语义**:转换是"翻译重写",不是逐节点照抄。
- **padding 的三级信源**:Auto Layout 显式字段 > bounding box 推算+归整 > 截图目测近似。
- **图标判定看类型+命名+尺寸三信号**,单一信号都可能误判。

**诚实边界:**

- MCP 工具(`get_code` 等)的输出质量随 Figma 文件规范程度浮动:无 Auto Layout、乱命名的稿子,生成结果需大量人工修正。
- Figma Variables / Dev Mode 功能依账号 plan(部分需付费席位),REST API 字段随版本演进,以当时官方文档为准。
- 交互、动效、滚动行为不在节点静态数据里,需 prototype 数据或与设计确认。
- 本 skill 给方法与映射规则,不绑定某个具体 MCP server 实现。
