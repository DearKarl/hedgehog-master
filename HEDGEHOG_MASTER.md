# Hedgehog Master 开发说明

Hedgehog Master 是在 PPT Master harness 上进行研究和二次开发的工作区。仓库保留了 `hugohe3/ppt-master` 的完整历史，并把原 `hedgehog1` 的确定性 Diagram IR 编译器连同历史合并到同一仓库。

## 仓库结构

```text
hedgehog_master/
├── skills/ppt-master/       # PPT Master 的核心 skill、工作流与脚本
├── examples/                # 上游示例项目与可编辑 PPTX
├── projects/                # 本地生成项目，默认不提交
├── packages/diagram-ir/     # 原 hedgehog1：Diagram IR -> SVG 编译器
├── index.html               # 示例索引页
└── viewer.html              # SVG 幻灯片查看器
```

## 两个组件的边界

- PPT Master 负责从资料到原生可编辑 PPTX 的 agent 工作流，核心入口是 `skills/ppt-master/SKILL.md`。
- Diagram IR 编译器负责把结构化数据流图稳定编译为 SVG，同一输入必须产生字节级一致的输出。
- 当前阶段两个组件保持清晰边界。后续可在 PPT Master 的 Executor 阶段接入 Diagram IR，让流程图先经过可验证的 IR，再进入 SVG/PPTX 导出。

## 本地部署

PPT Master 使用仓库根目录的 Python 虚拟环境：

```bash
cd /Users/dearkarl/Desktop/hedgehog_master
python3 -m venv .venv
.venv/bin/python -m pip install -r requirements.txt
.venv/bin/python -m http.server 4173 --bind 127.0.0.1
```

Diagram IR 编译器独立安装和验证：

```bash
cd /Users/dearkarl/Desktop/hedgehog_master/packages/diagram-ir
pnpm install
pnpm build
pnpm check
```

## GitHub 协作

- `origin` 指向个人开发仓库 `DearKarl/hedgehog_master`。
- `upstream` 指向官方仓库 `hugohe3/ppt-master`。
- 上游更新先从 `upstream/main` 获取，再通过独立开发分支合并和验证。
- 本地 `.venv/`、`projects/` 生成物和依赖目录不进入 Git。

## 已验证基线

- Python 依赖可以在 macOS 本地安装。
- 示例索引页和 SVG viewer 可以通过本地 HTTP 服务访问。
- Swiss Grid Systems 示例可完成 14 页 SVG 后处理并导出为带 14 页备注的原生 PPTX。
- Diagram IR 编译器保留原有构建、类型检查、Lint、测试和格式检查流程。
