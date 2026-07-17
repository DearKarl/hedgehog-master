# Hedgehog Master

[English](./README.md) | [中文](./README_CN.md)

Hedgehog Master is a local-first harness for formal research presentations. It turns evidence-linked semantic specifications into deterministic scientific diagrams, publication-ready SVG, and editable PPTX files.

The academic route does not ask a general-purpose model to write flowchart geometry or slide layout code. The model may organize sources, claims, and narrative structure; registered compilers own rendering and export.

## What It Produces

- Formal English research decks for lab meetings, conference talks, and technical reviews
- Deterministic dataflow, cycle, comparison, architecture, and timeline diagrams compiled from strict Diagram IR
- Publication-oriented SVG figures with reproducible geometry
- Evidence registries extracted from PDF, DOCX, Markdown, text, and LaTeX sources
- Code structure derived from Python AST or language-neutral symbol parsing
- Formula and generated-image manifests that participate in the same build
- Editable PPTX output using native PowerPoint objects where supported
- A local workbench for creating, validating, building, and exporting projects

## Requirements

- macOS, Linux, or Windows
- Python 3.11 or newer
- Node.js 20 or newer
- pnpm 10 or newer

## Local Installation

```bash
git clone https://github.com/DearKarl/hedgehog-master.git
cd hedgehog-master

python3 -m venv .venv
source .venv/bin/activate
python -m pip install -r requirements.txt

pnpm --dir packages/diagram-ir install
pnpm --dir packages/diagram-ir build
```

On Windows PowerShell, activate Python with `.venv\Scripts\Activate.ps1`.

## Run the Workbench

```bash
python3 hedgehog.py serve --port 4173
```

Open [http://127.0.0.1:4173](http://127.0.0.1:4173). A new project accepts a PPTX template, a presentation brief, research documents, code files, and pasted code in one intake. The planner extracts page-aware evidence, creates the source and claim registries, derives a storyboard, selects a Diagram IR type, and registers formula and image assets. `Plan`, `Validate`, `Build SVG`, and `Export PPTX` are repeatable project operations.

The workbench can switch between English and Chinese from the header and remembers the selection in the local browser. `Settings` configures provider routing, models, endpoints, and optional API keys. `Guide` explains the complete project workflow, while `Updates` displays the bilingual release history. The lower-left version is read from [`VERSION`](./VERSION); release notes are maintained in [`CHANGELOG.md`](./CHANGELOG.md).

## Content and Diagram Providers

Hedgehog Master runs in rules mode without an API key. In `Settings`, content planning and scientific diagram planning can independently use OpenAI, Gemini, Qwen, Zhipu, a local OpenAI-compatible LLM, or an external Agent endpoint. Model names and base URLs remain editable so users are not locked to a hard-coded model release.

Provider output is deliberately constrained. A content model returns page IDs, text, evidence IDs, counts, and confidence; a diagram model returns Diagram IR v0.2. The Harness rejects unknown evidence, invalid identifiers, excessive text, broken graph references, and unregistered layouts. Models never return slide coordinates or final SVG. Valid Diagram IR is compiled locally and inserted into the PPT storyboard automatically.

Credentials are stored only on the local computer in `~/.hedgehog-master/settings.json` with user-only file permissions. The settings API returns masked status rather than secret values. Project manifests record provider and model names for reproducibility but never store API keys. When a provider cannot run or violates the contract, planning falls back to the deterministic rules engine and records the reason in `analysis/provider_trace.json`.

### macOS one-click launcher

Create an HM desktop application linked to the current checkout:

```bash
packaging/macos/build_app.sh \
  --output "$HOME/Desktop/Hedgehog Master.app" \
  --linked-root "$PWD"
```

Double-clicking the app starts the local service when necessary and opens the workbench. Build a portable evaluation directory and ZIP with `packaging/release/build_release.sh`. See [`packaging/README.md`](./packaging/README.md) for the delivery layout, first-run setup, exclusions, and signing boundary.

## Command-Line Workflow

Create and automatically plan a research project:

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

Rebuild the semantic plan after editing the brief or replacing inputs:

```bash
python3 hedgehog.py plan reliable-research-decks
```

Validate the structured research contract:

```bash
python3 hedgehog.py validate reliable-research-decks
```

Compile deterministic diagrams and slide SVG:

```bash
python3 hedgehog.py build reliable-research-decks
```

Export an editable PowerPoint file:

```bash
python3 hedgehog.py export reliable-research-decks
```

The project is stored under `projects/reliable-research-decks/`. SVG pages appear in `svg_output/`, publication previews in `svg_final/`, and PowerPoint files in `exports/`.

## Research Project Contract

```text
projects/<project-id>/
├── project.json                    # brief, inputs, contracts, profile, and policy
├── inputs/
│   ├── instructions.md             # authoritative presentation brief
│   ├── template/*.pptx             # optional PowerPoint template
│   ├── papers/*                    # papers and research documents
│   └── code/*                      # code and pasted pseudocode
├── template/
│   ├── template.json               # semantic layout bindings and slot constraints
│   └── workspace/                  # recovered Master, Layout, theme, and SVG layers
├── analysis/
│   ├── plan.json                   # planner result, counts, warnings, and selected diagram type
│   └── provider_trace.json         # provider/model route, guardrails, fallback, and warnings
├── images/
│   ├── formula_manifest.json       # LaTeX, source locator, render mode, and slide bindings
│   └── image_prompts.json          # auditable external-image prompts and status
├── research/
│   ├── sources.json                # papers, datasets, code, and local evidence
│   ├── claims.json                 # verifiable statements linked to sources
│   ├── diagrams/*.diagram.json     # strict Diagram IR
│   └── figures/*.svg               # deterministic compiled figures
├── storyboard/deck.json            # slide order and registered layout IDs
├── quality/build.json              # validation and build record
├── svg_output/                     # editable slide-design source
├── svg_final/                      # self-contained visual SVG
└── exports/                        # PPTX output
```

The default `academic-conference` profile permits only five layouts: `cover`, `section`, `diagram`, `evidence`, and `closing`. When a PPTX template is present, the renderer binds those semantic layouts to recovered Master/Layout backgrounds, theme colors, fonts, and placeholder geometry. Unregistered layouts, missing inputs, invalid template layers, broken citations, and unknown formula or image IDs fail validation.

## Formula and Image Policies

The default formula mode converts a conservative LaTeX subset to editable PowerPoint text using a math font. Select `raster` for transparent publication PNG output through the configured formula provider chain. Editable text is not native OMML; complex equations should currently use the raster path.

External images are generated only when the brief requests a visual and the project policy is `auto`. The generated prompt remains in `images/image_prompts.json`. The preferred path is to select OpenAI, Gemini, Qwen, Zhipu, or MiniMax under `Settings`; the saved provider configuration is forwarded to the existing image build. Environment variables remain available for automation:

```bash
export IMAGE_BACKEND=openai
export OPENAI_API_KEY="..."
export OPENAI_MODEL="gpt-image-2"  # optional; this is the repository default
python3 hedgehog.py build reliable-research-decks
```

Other registered image backends remain available through `image_gen.py`. Pexels/Pixabay credentials and ElevenLabs/MiniMax/Qwen narration credentials can also be stored in `Settings`; they are optional and do not affect the base evaluation path. Manual image mode writes the same auditable Manifest but never calls an external API.

## Compile a Standalone Research Diagram

```bash
python3 hedgehog.py diagram path/to/pipeline.diagram.json \
  -o path/to/pipeline.svg
```

Diagram IR v0.2 supports `dataflow`, `cycle`, `comparison`, `architecture`, and `timeline`. Each type has a registered direction and deterministic semantic layout. Its pipeline is:

```text
parse -> schema validate -> semantic validate -> canonicalize
      -> semantic layout -> SVG AST -> stable serialization
```

The same valid input produces byte-stable SVG output. Invalid input returns explicit diagnostics rather than silently repairing the graph.

## Model Boundary

For the AutoResearch-Future route, a semantic planner or agent may edit:

- `project.json`
- `research/sources.json`
- `research/claims.json`
- `storyboard/deck.json`
- `research/diagrams/*.diagram.json`
- `images/formula_manifest.json`
- `images/image_prompts.json`

It must not generate final diagram SVG, arbitrary HTML slide layouts, or DrawingML directly. This boundary keeps scientific structure inspectable and makes rendering reproducible without an LLM. The built-in planner is local and deterministic; optional external models may enrich semantics or generate registered raster assets, but they do not own geometry.

## Current Template Boundary

Template intake recovers slide size, theme tokens, Master/Layout visual layers, and placeholder geometry. The academic renderer uses those elements as constraints and backgrounds. It does not yet preserve every native PowerPoint Master behavior, transition, macro, or unsupported object as a live editable template feature.

## Existing Presentation Workflows

The repository also retains mature local tools for source normalization, template-guided SVG authoring, PowerPoint intake, visual review, narration, animation, and native PPTX enhancement. The authoritative skill entry point is [`skills/hedgehog-master/SKILL.md`](./skills/hedgehog-master/SKILL.md).

## Architecture and Research

- [AutoResearch-Future architecture](./docs/architecture/autoresearch-future.md)
- [Reference-system research](./docs/research/reference-systems.md)
- [Diagram IR v0.2 specification](./packages/diagram-ir/docs/ir-spec-v0.2.md)
- [Getting started](./docs/getting-started.md)
- [Security policy](./SECURITY.md)

## Development Checks

```bash
python3 -m py_compile hedgehog.py skills/hedgehog-master/scripts/research_harness.py skills/hedgehog-master/scripts/research_planner.py skills/hedgehog-master/scripts/provider_settings.py skills/hedgehog-master/scripts/content_provider.py
python3 -m unittest tests.test_research_harness
python3 hedgehog.py validate <project-id>
pnpm --dir packages/diagram-ir check
```

## License

Hedgehog Master is released under the MIT License. See [`LICENSE`](./LICENSE) and [`NOTICE.md`](./NOTICE.md) for required legal notices concerning incorporated open-source work.
