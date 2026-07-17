# Hedgehog Master

[English](./README.md) | [中文](./README_CN.md)

Hedgehog Master 是一个本地优先的科研演示文稿 Harness。它把带证据关联的结构化语义规范，编译成可复现的科研流程图、适合论文使用的 SVG，以及可编辑的 PPTX。

在学术工作流中，通用模型不直接编写流程图几何、幻灯片布局代码或 DrawingML。模型只负责整理来源、论断和叙事结构，确定性编译器负责排版与导出。

## 主要输出

- 面向实验室汇报、学术会议和技术评审的正式英文 PPT
- 从严格 Diagram IR 编译得到的数据流图、循环图、对比图、系统架构图和时间线
- 几何可复现、适合论文插图的 SVG
- 从 PDF、DOCX、Markdown、文本和 LaTeX 中提取的证据注册表
- 基于 Python AST 或通用符号解析生成的代码结构
- 进入统一 Build 流程的公式与外部图片 Manifest
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

打开 [http://127.0.0.1:4173](http://127.0.0.1:4173)。新建项目时可以一次性提交 PPTX 模板、演示指令、论文或文档、代码文件以及粘贴的代码。规划器会提取带页码定位的证据，生成 Sources、Claims 和 Storyboard，根据 Brief 与代码选择 Diagram IR 类型，并登记公式和图片资产。`Plan`、`Validate`、`Build SVG` 和 `Export PPTX` 都可以重复执行。

工作台右上角可以切换中英文，并会在本地浏览器中记住选择。左侧“设置”用于选择 Provider、模型、端点和可选 API Key；“说明”介绍完整项目流程，“更新”展示双语版本记录。左下角版本号来自 [`VERSION`](./VERSION)，完整发布记录维护在 [`CHANGELOG.md`](./CHANGELOG.md)。

## 内容与流程图 Provider

Hedgehog Master 默认使用纯规则模式，不需要 API Key。在“设置”中，内容规划与科研流程图规划可以分别选择 OpenAI、Gemini、Qwen、智谱、本地 OpenAI 兼容 LLM 或外部 Agent 端点。模型名与基础 URL 都可编辑，不会被固定在某个模型版本上。

Provider 输出受到严格约束。内容模型只返回页面 ID、文本、证据 ID、长度与置信度；流程图模型只返回 Diagram IR v0.2。Harness 会拒绝不存在的证据、非法 ID、超长文本、断裂的图引用和未注册版式。模型不返回页面坐标或最终 SVG；合法 Diagram IR 会在本地确定性编译，并自动进入 PPT 故事板。

凭据只保存在本机 `~/.hedgehog-master/settings.json`，文件权限仅限当前用户。设置 API 只返回遮蔽后的配置状态。项目 Manifest 会记录 Provider 与模型名以便复现，但绝不保存 API Key。Provider 无法调用或结构化输出不合格时，规划会自动退回确定性规则引擎，并将原因写入 `analysis/provider_trace.json`。

### macOS 一键启动器

生成一个关联当前仓库的 HM 桌面应用：

```bash
packaging/macos/build_app.sh \
  --output "$HOME/Desktop/Hedgehog Master.app" \
  --linked-root "$PWD"
```

双击应用后，它会在需要时启动本地服务并打开工作台。运行 `packaging/release/build_release.sh` 可以生成可移交的测试目录和 ZIP。交付结构、首次安装、排除项和签名边界详见 [`packaging/README.md`](./packaging/README.md)。

## 命令行工作流

创建并自动规划科研项目：

```bash
python3 hedgehog.py init reliable-research-decks \
  --title "Reliable Research Communication" \
  --audience "Research engineers and academic collaborators" \
  --venue "Lab meeting" \
  --brief "Explain the method, evidence, and implementation pipeline." \
  --template path/to/lab-template.pptx \
  --paper path/to/paper.pdf \
  --code path/to/pipeline.py
```

修改 Brief 或替换输入后重新生成语义规划：

```bash
python3 hedgehog.py plan reliable-research-decks
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
├── project.json                    # 指令、输入、契约、学术配置与策略
├── inputs/
│   ├── instructions.md             # 权威演示指令
│   ├── template/*.pptx             # 可选 PowerPoint 模板
│   ├── papers/*                    # 论文和研究文档
│   └── code/*                      # 代码和粘贴的伪代码
├── template/
│   ├── template.json               # 语义版式绑定与内容槽约束
│   └── workspace/                  # 恢复后的 Master、Layout、主题和 SVG 图层
├── analysis/
│   ├── plan.json                   # 规划器结果、数量、警告和图类型
│   └── provider_trace.json         # Provider/模型路由、约束、回退与警告
├── images/
│   ├── formula_manifest.json       # LaTeX、来源定位、渲染模式和页面绑定
│   └── image_prompts.json          # 可审计的外部图片提示词和状态
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

默认 `academic-conference` 配置只允许 `cover`、`section`、`diagram`、`evidence` 和 `closing` 五种版式。存在 PPTX 模板时，渲染器会将这些语义版式绑定到恢复后的 Master/Layout 背景、主题色、字体和占位符几何。未注册版式、缺失输入、失效模板图层、错误引用以及未知公式或图片 ID 都会导致校验失败。

## 公式与图片策略

默认公式模式会把保守的 LaTeX 子集转换成使用数学字体的可编辑 PowerPoint 文本。选择 `raster` 时，系统会通过已配置的公式服务生成透明科研 PNG。可编辑文本目前不是原生 OMML；复杂公式建议使用栅格路径。

只有 Brief 明确要求视觉内容并且项目图片策略设为 `auto` 时，Build 才会调用外部图片 API；提示词始终保留在 `images/image_prompts.json`。推荐在“设置”中选择 OpenAI、Gemini、Qwen、智谱或 MiniMax，保存的 Provider 配置会传入现有图片构建流程。自动化场景仍可使用环境变量：

```bash
export IMAGE_BACKEND=openai
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-image-2"  # 可选；这是仓库当前默认值
python3 hedgehog.py build reliable-research-decks
```

`image_gen.py` 还保留其他已注册后端。“设置”也可以保存 Pexels/Pixabay 图库密钥，以及 ElevenLabs/MiniMax/Qwen 旁白密钥；这些都是可选项，不影响基础测评。手动图片模式会生成同一份可审计 Manifest，但不会调用外部 API。

## 单独编译科研流程图

```bash
python3 hedgehog.py diagram path/to/pipeline.diagram.json \
  -o path/to/pipeline.svg
```

Diagram IR v0.2 支持 `dataflow`、`cycle`、`comparison`、`architecture` 和 `timeline`。每种类型都有固定方向和确定性语义布局。编译管线为：

```text
解析 -> Schema 校验 -> 语义校验 -> 规范化
     -> 语义布局 -> SVG AST -> 稳定序列化
```

相同的合法输入会生成字节稳定的 SVG；非法输入返回明确诊断，不会静默修复图结构。

## 模型边界

在 AutoResearch-Future 路线中，语义规划器或 Agent 只能编辑以下结构化文件：

- `project.json`
- `research/sources.json`
- `research/claims.json`
- `storyboard/deck.json`
- `research/diagrams/*.diagram.json`
- `images/formula_manifest.json`
- `images/image_prompts.json`

Agent 不得直接生成最终流程图 SVG、任意 HTML 幻灯片布局或 DrawingML。这个边界保证科研结构可检查，并使几何渲染不依赖 LLM。内置规划器在本地确定性运行；外部模型可以增强语义或生成已登记的栅格资产，但不拥有布局几何。

## 当前模板边界

模板接入会恢复画布、主题 token、Master/Layout 视觉图层和占位符几何，并把它们作为学术渲染器的背景与约束。当前还不会把所有 PowerPoint 母版行为、切换效果、宏或不支持对象完整保留为可编辑模板功能。

## 现有演示文稿能力

仓库同时保留了来源规范化、模板化 SVG 创作、PowerPoint 解析、视觉校验、旁白、动画和原生 PPTX 增强等本地工具。Skill 的权威入口为 [`skills/hedgehog-master/SKILL.md`](./skills/hedgehog-master/SKILL.md)。

## 架构与调研

- [AutoResearch-Future 架构](./docs/architecture/autoresearch-future.md)
- [参考系统调研](./docs/research/reference-systems.md)
- [Diagram IR v0.2 规范](./packages/diagram-ir/docs/ir-spec-v0.2.md)
- [快速开始](./docs/getting-started.md)
- [安全策略](./SECURITY.md)

## 开发校验

```bash
python3 -m py_compile hedgehog.py skills/hedgehog-master/scripts/research_harness.py skills/hedgehog-master/scripts/research_planner.py skills/hedgehog-master/scripts/provider_settings.py skills/hedgehog-master/scripts/content_provider.py
python3 -m unittest tests.test_research_harness
python3 hedgehog.py validate <project-id>
pnpm --dir packages/diagram-ir check
```

## 许可证

Hedgehog Master 使用 MIT License。仓库包含开源代码时所需保留的法律信息见 [`LICENSE`](./LICENSE) 和 [`NOTICE.md`](./NOTICE.md)。
