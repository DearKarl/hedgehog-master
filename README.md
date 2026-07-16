# Hedgehog Master

Local-first presentation engineering for research, technical communication, and reproducible visual explanation.

[![License: MIT](https://img.shields.io/badge/License-MIT-1F6FEB.svg)](./LICENSE)
[![Repository](https://img.shields.io/badge/GitHub-DearKarl%2Fhedgehog--master-181717.svg)](https://github.com/DearKarl/hedgehog-master)

Hedgehog Master is an open-source harness for turning papers, reports, datasets, and structured instructions into editable PowerPoint presentations. Its primary direction is scientific communication: formal English, traceable source material, deterministic vector diagrams, and visuals that can be reused in research slides or prepared for publication figures.

This repository is under active development. The inherited presentation pipeline is operational, the deterministic Diagram IR compiler is tested, and their deeper integration is the next major engineering milestone.

## Why Hedgehog Master

Research presentations need more than attractive slides. They need a repeatable process that protects meaning while making complex work easier to inspect.

Hedgehog Master is being developed around six principles:

- **Research-first structure:** claims, methods, evidence, limitations, and conclusions remain distinguishable.
- **Formal academic English:** concise headings, defined terminology, disciplined tone, and no unsupported promotional language.
- **Publication-oriented diagrams:** vector-first figures with explicit semantics, stable geometry, readable labels, and restrained styling.
- **Editable output:** presentation content should remain editable in PowerPoint whenever the target object model supports it.
- **Local-first operation:** source files, generated projects, and review artifacts stay in a local workspace.
- **Reproducible execution:** specifications, intermediate assets, quality checks, and exports are retained as project artifacts.

## Intended Workflow

```text
Research sources or instructions
        |
        v
Project intake and source normalization
        |
        v
Narrative and design specification
        |
        v
Figures, formulas, and Diagram IR
        |
        v
SVG slide authoring and validation
        |
        v
Editable PPTX, speaker notes, and reusable vector assets
```

The harness supports agent-driven work rather than a single opaque generation call. An agent reads the repository workflow, creates a project, confirms the presentation direction, builds pages in sequence, runs quality gates, and exports the final deck.

## Academic Output Contract

Hedgehog Master targets presentation and figure assets that are suitable for serious scientific communication. New workflows and examples should follow these rules:

- Use formal, idiomatic English appropriate for an international research audience.
- Preserve citations, units, variable names, uncertainty, and methodological qualifiers.
- Prefer declarative slide titles that communicate the result or purpose of the page.
- Define acronyms before reuse and keep terminology consistent across slides.
- Use vector geometry for diagrams whenever practical.
- Make process direction, dependencies, and hierarchy unambiguous.
- Avoid overlapping labels, decorative clutter, tiny text, and color-only encoding.
- Use palettes that remain legible in projection, print, and common color-vision conditions.
- Keep figure typography, line weight, spacing, and export dimensions consistent.
- Treat publication readiness as a validation target, not an automatic claim.

The deterministic compiler in [`packages/diagram-ir`](./packages/diagram-ir) is the foundation for reproducible flowcharts and system diagrams. The current package compiles structured diagram input to stable SVG output; direct orchestration from the presentation Executor is planned.

## Current Capabilities

- Convert common source formats into project-ready Markdown and extracted assets.
- Plan presentation structure through an explicit strategist and confirmation workflow.
- Author complete SVG pages with project-level design locks.
- Validate SVG structure before export.
- Export editable PowerPoint content through the repository converter.
- Produce speaker notes and optional narration or presentation behavior.
- Compile and test deterministic Diagram IR independently.
- Preview example decks and edit project SVGs through local web tools.

## Local Installation

### Requirements

- Python 3.10 or newer
- Git
- Node.js and pnpm for Diagram IR development
- PowerPoint, LibreOffice, or another PPTX viewer for final inspection

### Set Up the Repository

```bash
git clone https://github.com/DearKarl/hedgehog-master.git
cd hedgehog-master

python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

### Start the Local Gallery

```bash
python -m http.server 4173 --bind 127.0.0.1
```

Open:

- Gallery: [http://127.0.0.1:4173/](http://127.0.0.1:4173/)
- Example viewer: [http://127.0.0.1:4173/viewer.html?project=ppt169_swiss_grid_systems](http://127.0.0.1:4173/viewer.html?project=ppt169_swiss_grid_systems)

### Create a Project Workspace

```bash
python skills/ppt-master/scripts/project_manager.py init research-talk --format ppt169
python skills/ppt-master/scripts/project_manager.py validate projects/research-talk
```

To open the live SVG editor for an existing project:

```bash
python skills/ppt-master/scripts/svg_editor/server.py projects/research-talk --live --daemon
```

The local gallery and SVG editor are the current development surfaces. A unified local application for project intake, generation, review, and export is on the roadmap.

## Using the Harness With an Agent

Open the repository in an agent that can read files and execute local commands. Ask the agent to read [`AGENTS.md`](./AGENTS.md) and [`skills/ppt-master/SKILL.md`](./skills/ppt-master/SKILL.md) before modifying a presentation project.

Example request:

> Create a 12-slide research presentation from my paper for a specialist audience. Use formal academic English, preserve citations and limitations, and generate publication-oriented vector flow diagrams. Export an editable PPTX with speaker notes.

The workflow includes an explicit design confirmation stage before page generation. That gate is intentional: research communication should not silently invent visual or narrative assumptions.

## Diagram IR Development

```bash
cd packages/diagram-ir
pnpm install
pnpm build
pnpm check
```

The package currently provides schema validation, canonicalization, deterministic layout, SVG compilation, a command-line interface, and automated tests.

## Repository Layout

| Path | Purpose |
|---|---|
| [`skills/ppt-master/`](./skills/ppt-master/) | Presentation workflow, role definitions, scripts, references, and templates |
| [`packages/diagram-ir/`](./packages/diagram-ir/) | Deterministic structured-diagram compiler |
| [`projects/`](./projects/) | Local presentation workspaces and generated artifacts |
| [`examples/`](./examples/) | Reference decks and SVG examples |
| [`docs/`](./docs/) | Technical and workflow documentation |
| [`index.html`](./index.html) | Local example gallery |
| [`viewer.html`](./viewer.html) | Local SVG slide viewer |

## Roadmap

1. Integrate Diagram IR into the presentation Executor.
2. Add academic figure profiles for papers, talks, posters, and supplementary material.
3. Enforce diagram checks for label collision, contrast, typography, line weight, and print dimensions.
4. Add citation and claim-traceability checks across sources, slides, and notes.
5. Build a unified local interface for intake, generation, review, and export.
6. Publish Hedgehog Master examples and documentation under project-owned branding.

## Project Origin

Hedgehog Master is independently developed from [`hugohe3/ppt-master`](https://github.com/hugohe3/ppt-master) under the MIT License. The upstream history and attribution are preserved. This repository also incorporates the former Hedgehog Diagram IR project and its Git history.

The project is not intended to be a cosmetic mirror. Its scope, documentation, scientific standards, diagram architecture, and local tooling will evolve under the Hedgehog Master name. See [`ABOUT.md`](./ABOUT.md) for the ownership and architecture boundary.

## Contributing

Public-facing documentation, issue templates, examples, and generated sample content should be written in English. Contributions should preserve source attribution, avoid unsupported scientific claims, and include focused validation for behavior they change.

See [`CONTRIBUTING.md`](./CONTRIBUTING.md), [`CODE_OF_CONDUCT.md`](./CODE_OF_CONDUCT.md), and [`SECURITY.md`](./SECURITY.md).

## License

Released under the [MIT License](./LICENSE). Third-party work retains its original attribution and license notices.
