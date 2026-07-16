# About Hedgehog Master

## Project Identity

Hedgehog Master is a local-first presentation engineering harness for research and technical communication. It is designed to help an AI agent transform source material and explicit instructions into a reviewable project, a coherent slide deck, editable PowerPoint output, and reusable vector diagrams.

The project name is **Hedgehog Master**. Public documentation, examples, repository metadata, and future hosted surfaces should use that name as the primary identity.

## Purpose

The project exists to make high-quality research presentations more systematic and reproducible. Its target users include researchers, engineers, technical writers, open-source maintainers, and teams that need to explain complex systems without surrendering control of their source material or final artifacts.

Hedgehog Master prioritizes:

- formal English suitable for academic and professional audiences;
- traceable use of source material;
- editable and inspectable output;
- deterministic vector diagrams;
- explicit review gates;
- local project storage;
- reusable workflows instead of one-off prompt recipes.

## Architecture Boundary

The repository currently contains two major systems.

### Presentation Harness

[`skills/ppt-master/`](./skills/ppt-master/) owns source intake, project creation, design confirmation, sequential SVG authoring, validation, speaker notes, and PPTX export.

### Diagram IR

[`packages/diagram-ir/`](./packages/diagram-ir/) owns structured diagram schemas, canonicalization, deterministic layout, SVG compilation, and compiler tests.

The systems are intentionally separated today. The planned integration will allow the presentation workflow to request a scientific flowchart or system diagram through a structured intermediate representation, validate it independently, and then place the resulting vector asset into slides or publication-oriented figure exports.

## Scientific Communication Standard

Hedgehog Master should optimize for clarity before decoration. A research slide or figure should make the following questions easy to answer:

1. What claim, method, or process is being shown?
2. Which evidence or source supports it?
3. What is the direction of the argument or flow?
4. Which assumptions and limitations remain?
5. Can a reader inspect and reuse the visual without reconstructing it manually?

The project will treat academic English, citation retention, vector quality, print readability, accessible color, and deterministic rendering as engineering requirements.

## Origin and Attribution

Hedgehog Master is based on [`hugohe3/ppt-master`](https://github.com/hugohe3/ppt-master) and follows its MIT License obligations. The upstream Git history remains available in this repository. The former Hedgehog Diagram IR repository was also merged with its history intact.

This provenance is a foundation, not the public identity of the new project. New product language, workflows, diagrams, examples, and local tooling should be developed specifically for Hedgehog Master and should not copy upstream promotional content.

## Development Policy

- Public project communication is written in English.
- New features should serve research or technical presentation workflows.
- Generated examples must distinguish sourced facts from illustrative content.
- Diagram behavior should be deterministic where deterministic input is available.
- Quality gates should fail explicitly on invalid output and report non-blocking review concerns separately.
- Local deployment should remain a first-class path.
- Upstream changes are reviewed and merged intentionally; they do not automatically override Hedgehog Master policy or branding.

## Current Status

The repository has a working local Python environment, a validated presentation export baseline, an SVG gallery and editor, and a tested Diagram IR compiler. The next phase is to connect these pieces into a cohesive, project-owned local application and academic figure workflow.
