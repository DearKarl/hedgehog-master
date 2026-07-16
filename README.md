# Hedgehog Master

[English](./README.md) | [中文](./README_CN.md)

Hedgehog Master is a local-first harness for formal research presentations. It turns evidence-linked semantic specifications into deterministic scientific diagrams, publication-ready SVG, and editable PPTX files.

The academic route does not ask a general-purpose model to write flowchart geometry or slide layout code. The model may organize sources, claims, and narrative structure; registered compilers own rendering and export.

## What It Produces

- Formal English research decks for lab meetings, conference talks, and technical reviews
- Deterministic dataflow diagrams compiled from strict Diagram IR
- Publication-oriented SVG figures with reproducible geometry
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

Open [http://127.0.0.1:4173](http://127.0.0.1:4173). The workbench can create a seeded research project, validate evidence links, compile SVG slides, and export PPTX.

## Command-Line Workflow

Create a runnable four-slide project:

```bash
python3 hedgehog.py init reliable-research-decks \
  --title "Reliable Research Communication" \
  --audience "Research engineers and academic collaborators" \
  --venue "Lab meeting" \
  --demo
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
├── project.json                    # audience, venue, language, profile, policy
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

The default `academic-conference` profile permits only five layouts: `cover`, `section`, `diagram`, `evidence`, and `closing`. Unregistered layouts and broken source/claim references fail validation.

## Compile a Standalone Research Diagram

```bash
python3 hedgehog.py diagram path/to/pipeline.diagram.json \
  -o path/to/pipeline.svg
```

The current Diagram IR compiler supports deterministic left-to-right dataflow diagrams. Its pipeline is:

```text
parse -> schema validate -> semantic validate -> canonicalize
      -> ranked layout -> SVG AST -> stable serialization
```

The same valid input produces byte-stable SVG output. Invalid input returns explicit diagnostics rather than silently repairing the graph.

## Model Boundary

For the AutoResearch-PPT route, an agent may edit:

- `project.json`
- `research/sources.json`
- `research/claims.json`
- `storyboard/deck.json`
- `research/diagrams/*.diagram.json`

It must not generate final flowchart SVG, arbitrary HTML slide layouts, or DrawingML directly. This boundary keeps scientific structure inspectable and makes rendering reproducible without an LLM.

## Existing Presentation Workflows

The repository also retains mature local tools for source normalization, template-guided SVG authoring, PowerPoint intake, visual review, narration, animation, and native PPTX enhancement. The authoritative skill entry point is [`skills/hedgehog-master/SKILL.md`](./skills/hedgehog-master/SKILL.md).

## Architecture and Research

- [AutoResearch-PPT architecture](./docs/architecture/autoresearch-ppt.md)
- [Reference-system research](./docs/research/reference-systems.md)
- [Diagram IR specification](./packages/diagram-ir/docs/ir-spec-v0.1a.md)
- [Getting started](./docs/getting-started.md)
- [Security policy](./SECURITY.md)

## Development Checks

```bash
python3 -m py_compile hedgehog.py skills/hedgehog-master/scripts/research_harness.py
python3 hedgehog.py validate <project-id>
pnpm --dir packages/diagram-ir check
```

## License

Hedgehog Master is released under the MIT License. See [`LICENSE`](./LICENSE) and [`NOTICE.md`](./NOTICE.md) for required legal notices concerning incorporated open-source work.
