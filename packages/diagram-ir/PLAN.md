# Hedgehog_One（刺猬一号）v0.1a 开发计划

仓库名：`hedgehog1`

本地项目根目录应为：

```text
/Users/dearkarl/Desktop/hedgehog1/
```

v0.1a 目标：构建一个完全确定性、无需 LLM 的 `Diagram IR -> SVG` 编译器。第一阶段范围严格收窄为一个 `dataflow`、`left-to-right`、`ranked layout` 图编译器。

在用户确认本计划前，不创建源码、配置文件、测试文件或目录骨架。

## 1. 核心原则

- 通用模型不直接生成最终 SVG。
- 所有图必须先经过结构化 Diagram IR。
- 相同输入必须产生字节级稳定输出。
- 科研数据、代码关系和图形结构必须可验证。
- 每个功能必须有自动化测试。
- 无效输入必须明确报错，不得静默修复。
- 最终工具必须支持无 LLM、无网络、无交互式外部服务运行。

## 2. v0.1a 范围

v0.1a 只实现一个确定性的 dataflow left-to-right ranked layout 编译器：

```text
Diagram IR v0.1a -> validate -> ranked layout -> SVG AST -> stable SVG
```

必须保留的核心架构：

```text
parse -> schemaValidate -> semanticValidate -> canonicalize -> layout -> buildSvgAst -> serializeSvg
```

v0.1a 的重点不是通用绘图，而是把一个严格、可验证的数据流图稳定编译成 SVG。

## 3. 技术栈

采用：

- TypeScript 5.x
- Node.js LTS
- pnpm
- TypeBox
- AJV
- Vitest
- fast-check
- ESLint
- Prettier

选择理由：

- TypeScript 适合表达 JSON IR、编译器内部类型、CLI 和未来 Web 复用边界。
- Node.js LTS 与 pnpm 适合构建可本地运行、可发布、无网络依赖的 CLI。
- TypeBox 可从同一套 schema 定义派生 TypeScript 类型，减少 IR schema 和代码类型漂移。
- AJV 用于严格 JSON Schema 校验，能输出稳定、路径化的结构错误。
- Vitest 覆盖单元测试、集成测试和快照测试，启动快，适合编译器项目。
- fast-check 用于属性测试，验证确定性、不变量和等价输入输出一致。
- ESLint 与 Prettier 保持代码质量和格式一致，避免风格差异影响审查。

## 4. v0.1a Diagram IR

v0.1a 根对象只支持以下字段：

- `irVersion`
- `id`
- `title`
- `kind`
- `direction`
- `nodes`
- `edges`
- `metadata`

约束：

- `kind` 只允许 `dataflow`。
- `direction` 只允许 `left-to-right`。
- `nodes` 必须是数组。
- `edges` 必须是数组。
- `metadata` 用于记录来源、证据、数据哈希或其他可验证信息，但 v0.1a 不做外部抽取。
- 未在 v0.1a 规范中声明的字段应被拒绝，不应静默忽略。

示意结构：

```json
{
  "irVersion": "0.1a",
  "id": "example-dataflow",
  "title": "Example Dataflow",
  "kind": "dataflow",
  "direction": "left-to-right",
  "nodes": [],
  "edges": [],
  "metadata": {}
}
```

## 5. Node IR

node 只支持：

- `id`
- `label`
- `role`

`node.role` 只允许：

- `source`
- `transform`
- `model`
- `metric`
- `output`

语义规则：

- `id` 必须存在、非空、全图唯一。
- `label` 必须存在、非空。
- `role` 必须是允许枚举值。
- node 不支持自定义几何、端口、形状或任意样式。

## 6. Edge IR

edge 只支持：

- `id`
- `from`
- `to`
- `label`，可选
- `evidenceRef`，可选

语义规则：

- `id` 必须存在、非空、全图唯一。
- `from` 必须引用存在的 node。
- `to` 必须引用存在的 node。
- `label` 如存在必须是字符串。
- `evidenceRef` 如存在必须可在 `metadata` 中解释或至少保留为可验证引用。
- v0.1a 只支持有向边。
- 检测到环路必须报错，不得尝试自动断边或重排修复。

## 7. v0.1a 不做

v0.1a 明确不做：

- absolute layout
- grid layout
- groups
- ports
- arbitrary style token
- circle/text/free shapes
- undirected edge
- PNG visual regression
- HTML GUI
- PPTX
- PDF / code / research extraction
- LLM planner

这些能力可以在后续版本重新评估，但不能进入 v0.1a 的完成标准。

## 8. Ranked Layout 规则

v0.1a 布局固定为 dataflow left-to-right ranked layout。

规则：

- 固定画布：`1600 x 900`。
- 图必须是 DAG。
- 使用拓扑分层。
- 方向固定为 left-to-right。
- 同层节点按输入顺序稳定排序。
- 节点使用固定尺寸。
- 长 label 必须使用确定性换行或截断策略。
- 边连接节点边界，不连接节点中心。
- 检测到环路必须报错。

建议具体化的默认几何参数：

- canvas width: `1600`
- canvas height: `900`
- node width: `220`
- node height: `72`
- rank left margin: `120`
- rank right margin: `120`
- rank horizontal gap: 根据层数确定，结果必须稳定。
- vertical gap: 根据同层节点数确定，结果必须稳定。
- edge route: 默认使用稳定折线，起点为 source 右边界中点，终点为 target 左边界中点。

长 label 策略建议：

- 使用固定最大字符宽度估算，不依赖系统字体测量。
- 最多两行或三行，具体数量在实现前固定。
- 超出部分使用稳定截断，例如 `...`。
- 同一 label 在任意机器上产生相同换行结果。

## 9. 编译管线

### 9.1 parse

- 读取 JSON。
- JSON 语法错误直接失败。
- 不接受 JSON5、注释或隐式修复。

### 9.2 schemaValidate

- 使用 TypeBox 定义 v0.1a schema。
- 使用 AJV 严格校验。
- 拒绝未知字段。
- 报错包含稳定错误码和 JSON path。

### 9.3 semanticValidate

校验：

- node ID 唯一。
- edge ID 唯一。
- edge `from` 和 `to` 引用存在节点。
- `kind` 和 `direction` 符合 v0.1a。
- 图为 DAG。
- required field 存在且类型正确。
- `metadata` 与 `evidenceRef` 的最小一致性规则。

### 9.4 canonicalize

只做非语义规范化：

- 保留节点输入顺序作为同层排序依据。
- 对错误列表、内部索引和输出属性做稳定排序。
- 不修复无效输入。
- 不补全用户遗漏的语义字段。

### 9.5 layout

- 对 DAG 做拓扑分层。
- 生成固定画布内的节点坐标。
- 生成边的边界连接点和折线路径。
- 输出独立的 LayoutModel，供测试直接断言。

### 9.6 buildSvgAst

- 将 LayoutModel 转为内部 SVG AST。
- 输出固定 SVG 层级：defs、background、edges、nodes、labels。
- 不允许任意 SVG passthrough。

### 9.7 serializeSvg

- 使用自定义稳定 SVG serializer。
- 固定元素顺序、属性顺序、数字格式、缩进和换行。
- 正确转义文本和属性值。
- 不输出时间戳、机器路径、随机 ID 或环境相关信息。

## 10. 核心数据结构

### 10.1 DiagramDocumentV01a

```ts
type DiagramDocumentV01a = {
  irVersion: "0.1a";
  id: string;
  title: string;
  kind: "dataflow";
  direction: "left-to-right";
  nodes: NodeV01a[];
  edges: EdgeV01a[];
  metadata: Record<string, unknown>;
};
```

### 10.2 NodeV01a

```ts
type NodeRole = "source" | "transform" | "model" | "metric" | "output";

type NodeV01a = {
  id: string;
  label: string;
  role: NodeRole;
};
```

### 10.3 EdgeV01a

```ts
type EdgeV01a = {
  id: string;
  from: string;
  to: string;
  label?: string;
  evidenceRef?: string;
};
```

### 10.4 LayoutModel

建议包含：

- canvas 尺寸。
- rank 列表。
- 每个节点的最终矩形。
- 每条边的折线路径。
- 每个 label 的确定性换行结果。
- role 到样式的内置映射。

LayoutModel 是测试重点之一，因为它能在不解析 SVG 字符串的情况下验证图形几何。

### 10.5 SvgAst

建议包含：

- `ElementNode`
- `TextNode`
- 有序属性数组。
- 有序子节点数组。

SVG AST 必须足够小，不做通用 SVG 编辑器，只服务 v0.1a 输出。

### 10.6 Diagnostic

建议错误对象：

```ts
type Diagnostic = {
  code: string;
  severity: "error";
  path: string;
  message: string;
  hint?: string;
};
```

第一批错误码建议：

- `IR_PARSE_ERROR`
- `IR_SCHEMA_ERROR`
- `IR_UNKNOWN_FIELD`
- `IR_MISSING_REQUIRED_FIELD`
- `IR_DUPLICATE_NODE_ID`
- `IR_DUPLICATE_EDGE_ID`
- `IR_UNKNOWN_EDGE_FROM`
- `IR_UNKNOWN_EDGE_TO`
- `IR_CYCLE_DETECTED`
- `IR_UNSUPPORTED_KIND`
- `IR_UNSUPPORTED_DIRECTION`
- `IR_INVALID_NODE_ROLE`

测试应断言错误码和 path，不依赖完整自然语言 message。

## 11. CLI v0.1a

只需要三个命令：

```text
hedgehog1 validate input.diagram.json
hedgehog1 compile input.diagram.json -o output.svg
hedgehog1 check input.diagram.json
```

命令语义：

- `validate`：只执行 parse、schemaValidate、semanticValidate，不生成 SVG。
- `compile`：完成完整编译并写入 SVG。
- `check`：用于 CI，语义上等同严格 validate，可额外检查 deterministic readiness。

退出码：

- 成功：`0`
- 输入无效：非 `0`
- 写文件失败：非 `0`
- CLI 参数错误：非 `0`

失败输出必须包含稳定诊断信息，不应只打印 stack trace。

## 12. 推荐项目目录结构

确认计划后，建议创建：

```text
hedgehog1/
  PLAN.md
  README.md
  package.json
  pnpm-lock.yaml
  tsconfig.json
  eslint.config.js
  prettier.config.js
  .gitignore
  src/
    index.ts
    cli.ts
    ir/
      schema.ts
      types.ts
      validate.ts
      diagnostics.ts
      canonicalize.ts
    compiler/
      compile.ts
      layout-model.ts
      ranked-layout.ts
      svg/
        ast.ts
        serialize.ts
        escape.ts
        numeric.ts
    errors/
      codes.ts
      format.ts
    utils/
      stable-sort.ts
  schemas/
    diagram-ir.v0.1a.schema.json
  docs/
    ir-spec-v0.1a.md
    determinism.md
    errors.md
  examples/
    simple-dataflow.diagram.json
  tests/
    fixtures/
      valid/
      invalid/
    unit/
      ir/
      compiler/
      svg/
    integration/
    property/
    snapshots/
```

目录理由：

- `src/ir/` 负责 v0.1a IR schema、类型、校验和规范化。
- `src/compiler/` 负责 ranked layout、LayoutModel、SVG AST 构建。
- `src/compiler/svg/` 负责稳定序列化，不接触 IR 校验。
- `schemas/` 发布可被外部工具复用的 JSON Schema。
- `docs/` 固化 IR、确定性和错误码规范。
- `examples/` 是用户示例，也必须进入测试。
- `tests/fixtures/invalid/` 锁定失败行为，避免静默修复。

## 13. 测试策略 v0.1a

必须覆盖：

- 合法 dataflow IR。
- 重复节点 ID。
- 重复边 ID。
- 边引用不存在节点。
- 环路。
- 缺少必填字段。
- 长 label。
- 同一输入两次 compile 字节级一致。
- equivalent canonical input 输出一致。
- CLI 成功和失败退出码。

测试分层：

- schema tests：字段、类型、枚举、未知字段。
- semantic tests：ID、引用、DAG、evidenceRef 规则。
- layout tests：rank、坐标、边界连接点、同层输入顺序。
- serializer tests：属性顺序、数字格式、文本转义、换行。
- snapshot tests：锁定典型 SVG 输出。
- property tests：重复编译和等价规范输入输出一致。
- CLI tests：命令成功、失败诊断和退出码。

不做 PNG visual regression。v0.1a 的视觉正确性通过 LayoutModel、SVG AST 和 SVG 字符串快照验证。

## 14. 确定性要求

v0.1a 必须满足：

- 不使用随机数。
- 不读取当前时间。
- 不读取网络。
- 不依赖系统字体测量。
- 不在 SVG 中写入机器路径。
- 不让对象枚举顺序决定输出。
- 同层节点按输入顺序稳定排序。
- SVG 元素顺序固定。
- SVG 属性顺序固定。
- 数字格式固定。
- 错误列表排序固定。

验收时必须证明：

- 同一输入连续编译两次，SVG 字节完全一致。
- 等价 canonical input 编译结果一致。
- 无效输入失败并给出稳定错误码。
- 检测到环路时不生成 SVG。

## 15. 里程碑

### M0 scaffold

- 初始化 TypeScript、pnpm、Vitest、ESLint、Prettier。
- 建立最小 package scripts。
- 不引入运行时 LLM 或网络依赖。

### M1 IR v0.1a schema

- 定义 TypeBox schema。
- 生成或维护 JSON Schema。
- 编写 v0.1a IR 规范文档。
- 添加最小 valid/invalid fixtures。

### M2 validation + diagnostics

- 实现 parse、schemaValidate、semanticValidate。
- 定义 Diagnostic 和错误码。
- 覆盖重复 ID、未知引用、缺字段、非法枚举、环路。

### M3 ranked layout

- 实现 DAG 拓扑分层。
- 实现 left-to-right 坐标计算。
- 实现固定节点尺寸和稳定同层排序。
- 实现边界连接点和稳定折线路径。
- 实现长 label 确定性换行或截断。

### M4 SVG AST + stable serializer

- 实现最小 SVG AST。
- 实现稳定 SVG serializer。
- 固定属性顺序、数字格式、转义和输出布局。
- 添加 SVG 快照测试。

### M5 CLI + tests

- 实现 `hedgehog1 validate`。
- 实现 `hedgehog1 compile`。
- 实现 `hedgehog1 check`。
- 覆盖 CLI 成功和失败退出码。
- 示例进入集成测试。

### M6 deterministic acceptance

- 验证同一输入两次 compile 字节级一致。
- 验证 equivalent canonical input 输出一致。
- 验证 invalid input 不产生 SVG。
- 验证无 LLM、无网络运行路径。

## 16. 代码创建前待确认

开始创建源码前，需要确认：

1. 本计划是否作为 v0.1a 范围冻结。
2. 本地项目根目录是否确定为 `/Users/dearkarl/Desktop/hedgehog1/`。
3. CLI 名称是否确定为 `hedgehog1`。
4. IR 文件扩展名是否确定为 `.diagram.json`。
5. v0.1a 是否采用上述固定画布与默认节点尺寸。
