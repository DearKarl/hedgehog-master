# Hedgehog Master

[English](./README.md) | [中文](./README_CN.md)

Hedgehog Master 是一个本地优先的科研演示文稿 Harness。它把带证据关联的结构化语义规范，编译成可复现的科研流程图、适合论文使用的 SVG，以及可编辑的 PPTX。

在学术工作流中，通用模型不直接编写流程图几何、幻灯片布局代码或 DrawingML。模型只负责整理来源、论断和叙事结构，确定性编译器负责排版与导出。

## 主要输出

- 面向实验室汇报、学术会议和技术评审的正式英文 PPT
- 从严格 Diagram IR 编译得到的确定性数据流图
- 几何可复现、适合论文插图的 SVG
- 尽可能保留 PowerPoint 原生对象的可编辑 PPTX
- 可创建、校验、编译和导出项目的本地工作台

## 环境要求

- macOS、Linux 或 Windows
- Python 3.11 或更高版本
- Node.js 20 或更高版本
- pnpm 10 或更高版本

## 本地安装

```bash
git clone https://github.com/DearKarl/hedgehog-master.git
cd hedgehog-master

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

pnpm --dir packages/diagram-ir install
pnpm --dir packages/diagram-ir build
```

Windows PowerShell 使用 `.venv\Scripts\Activate.ps1` 激活 Python 环境。

## 启动本地工作台

```bash
python3 hedgehog.py serve --port 4173
```

打开 [http://127.0.0.1:4173](http://127.0.0.1:4173)。工作台可以创建示例科研项目、校验证据链、编译 SVG 幻灯片并导出 PPTX。

## 命令行工作流

创建一个可以直接运行的四页示例项目：

```bash
python3 hedgehog.py init reliable-research-decks \
  --title "Reliable Research Communication" \
  --audience "Research engineers and academic collaborators" \
  --venue "Lab meeting" \
  --demo
```

校验科研项目契约：

```bash
python3 hedgehog.py validate reliable-research-decks
```

编译确定性流程图和幻灯片 SVG：

```bash
python3 hedgehog.py build reliable-research-decks
```

导出可编辑 PowerPoint：

```bash
python3 hedgehog.py export reliable-research-decks
```

项目保存在 `projects/reliable-research-decks/`。幻灯片 SVG 位于 `svg_output/`，自包含 SVG 位于 `svg_final/`，PowerPoint 文件位于 `exports/`。

## 科研项目契约

```text
projects/<project-id>/
├── project.json                    # 受众、场景、语言、学术配置与策略
├── research/
│   ├── sources.json                # 论文、数据集、代码和本地证据
│   ├── claims.json                 # 与来源关联、可校验的论断
│   ├── diagrams/*.diagram.json     # 严格 Diagram IR
│   └── figures/*.svg               # 确定性编译后的流程图
├── storyboard/deck.json            # 页面顺序与注册版式 ID
├── quality/build.json              # 校验和编译记录
├── svg_output/                     # 幻灯片设计源文件
├── svg_final/                      # 自包含视觉 SVG
└── exports/                        # PPTX 输出
```

默认 `academic-conference` 配置只允许 `cover`、`section`、`diagram`、`evidence` 和 `closing` 五种版式。未注册的版式、失效的来源引用或论断引用都会导致校验失败。

## 单独编译科研流程图

```bash
python3 hedgehog.py diagram path/to/pipeline.diagram.json \
  -o path/to/pipeline.svg
```

当前 Diagram IR 支持从左到右的确定性数据流图。编译管线为：

```text
解析 -> Schema 校验 -> 语义校验 -> 规范化
     -> 分层布局 -> SVG AST -> 稳定序列化
```

相同的合法输入会生成字节稳定的 SVG；非法输入返回明确诊断，不会静默修复图结构。

## 模型边界

在 AutoResearch-PPT 路线中，Agent 只能编辑以下结构化文件：

- `project.json`
- `research/sources.json`
- `research/claims.json`
- `storyboard/deck.json`
- `research/diagrams/*.diagram.json`

Agent 不得直接生成最终流程图 SVG、任意 HTML 幻灯片布局或 DrawingML。这个边界保证科研结构可检查，并使渲染过程不依赖 LLM。

## 现有演示文稿能力

仓库同时保留了来源规范化、模板化 SVG 创作、PowerPoint 解析、视觉校验、旁白、动画和原生 PPTX 增强等本地工具。Skill 的权威入口为 [`skills/hedgehog-master/SKILL.md`](./skills/hedgehog-master/SKILL.md)。

## 架构与调研

- [AutoResearch-PPT 架构](./docs/architecture/autoresearch-ppt.md)
- [参考系统调研](./docs/research/reference-systems.md)
- [Diagram IR 规范](./packages/diagram-ir/docs/ir-spec-v0.1a.md)
- [快速开始](./docs/getting-started.md)
- [安全策略](./SECURITY.md)

## 开发校验

```bash
python3 -m py_compile hedgehog.py skills/hedgehog-master/scripts/research_harness.py
python3 hedgehog.py validate <project-id>
pnpm --dir packages/diagram-ir check
```

## 许可证

Hedgehog Master 使用 MIT License。仓库包含开源代码时所需保留的法律信息见 [`LICENSE`](./LICENSE) 和 [`NOTICE.md`](./NOTICE.md)。
