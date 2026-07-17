# Changelog / 更新日志

Hedgehog Master follows a bilingual release process. Every user-facing release records its English and Chinese notes here and in the local workbench.

Hedgehog Master 采用双语版本流程。每个面向用户的版本都会在本文件和本地工作台中同步记录中英文说明。

## v0.3.0-beta - 2026-07-17

### English

- Added a local Content Provider layer for rules, OpenAI, Gemini, Qwen, Zhipu, local LLMs, and external Agents.
- Added constrained semantic JSON and Diagram IR contracts with evidence, text-length, format, and graph-reference validation.
- Connected provider-generated scientific diagrams to the deterministic SVG and PPTX build instead of allowing models to control geometry.
- Added masked local credential storage and optional routing for image generation, stock libraries, and narration services.
- Added provider traces and automatic rules-mode fallback when credentials, endpoints, or structured outputs are invalid.

### 中文

- 新增本地 Content Provider 层，支持纯规则、OpenAI、Gemini、Qwen、智谱、本地 LLM 与外部 Agent。
- 新增受约束的语义 JSON 与 Diagram IR 契约，并校验证据、文本长度、格式和图结构引用。
- 模型生成的科研流程图已接入确定性 SVG 与 PPTX 构建，模型不控制几何排版。
- 新增密钥遮蔽的本地凭据存储，以及图片、图库和旁白服务的可选路由。
- 新增 Provider Trace；密钥、端点或结构化输出无效时自动退回纯规则模式。

## v0.2.1-beta - 2026-07-17

### English

- Added the HM application icon, browser favicon, and workbench home link.
- Added a one-click macOS launcher that starts the local service and opens the workbench.
- Added reproducible source packaging, first-run setup, integrity manifests, and bilingual handoff instructions.
- Reduced delivery size by excluding Git history, development environments, caches, and large examples.

### 中文

- 新增 HM 应用图标、浏览器图标和工作台主页链接。
- 新增 macOS 一键启动器，可自动启动本地服务并打开工作台。
- 新增可复现源码封装、首次安装、完整性清单和双语交付说明。
- 交付包排除 Git 历史、开发环境、缓存和大型示例，以降低体积。

## v0.2.0-beta - 2026-07-17

### English

- Added persistent English and Chinese workbench modes.
- Added automatic Brief, paper, and code planning with cited claims and storyboards.
- Integrated formula and image manifests into the unified build.
- Expanded Diagram IR with cycle, comparison, architecture, and timeline layouts.
- Added an in-app guide, release notes, and centralized version reporting.

### 中文

- 新增可持久化的中英文工作台模式。
- 新增 Brief、论文和代码自动规划，可生成带引用论点与故事板。
- 将公式与图片 Manifest 接入统一构建流程。
- Diagram IR 新增循环图、对比图、系统架构图和时间线。
- 新增界面使用说明、更新日志与统一版本信息。

## v0.1.0-alpha - 2026-07-16

### English

- Introduced the local AutoResearch-Future workbench and research project contracts.
- Added deterministic dataflow diagrams, evidence validation, SVG build, and PPTX export.

### 中文

- 建立本地 AutoResearch-Future 工作台与科研项目契约。
- 实现确定性数据流图、证据校验、SVG 构建与 PPTX 导出。
