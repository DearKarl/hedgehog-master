# AutoResearch-PPT Architecture

## Objective

AutoResearch-PPT compiles evidence-linked research semantics into publication SVG and editable PPTX without allowing a general-purpose model to own final geometry.

## Pipeline

```text
unified intake (brief + template + papers + code)
  -> project input registry
  -> optional PPTX Template Contract
  -> local semantic planner
       -> page-aware source registry
       -> evidence-linked claim registry
       -> audience-facing storyboard
       -> typed Diagram IR
       -> Formula Manifest + Image Manifest
  -> deterministic diagram compiler
  -> registered academic slide renderer
  -> static validation
  -> visual review
  -> SVG and PPTX
```

## Ownership Boundaries

| Artifact | Owner | Rule |
|---|---|---|
| Unified project inputs | Workbench or CLI | Brief, template, papers, and code are copied into project-local paths and registered once. |
| Template Contract | PPTX template adapter | Master/Layout backgrounds, theme tokens, and placeholder slots constrain the academic renderer. |
| Sources and claims | Local planner, then researcher | Extracted claims retain source IDs, page or code locators, excerpts, and confidence. |
| Storyboard | Local planner, then researcher | Slides use registered semantic layout IDs and audience-facing copy. |
| Diagram IR | Local planner, then researcher | Graph structure is strict JSON with explicit kind, roles, groups, and edges. |
| Formula Manifest | Local planner and asset resolver | LaTeX, provenance, render mode, status, and slide bindings remain auditable. |
| Image Manifest | Local planner and configured provider | External generation is policy-gated; prompts and status remain project-local. |
| Diagram geometry | Diagram IR compiler | Layout is deterministic and never inferred from arbitrary SVG. |
| Slide geometry | Academic renderer | Profile tokens and layout contracts own placement. |
| PPTX package | Export compiler | Visible SVG structure maps to editable PowerPoint objects where supported. |

## Runtime Contracts

The root CLI is `hedgehog.py`. It exposes project initialization, semantic planning, validation, SVG build, PPTX export, standalone diagram compilation, status reporting, and a local HTTP workbench.

The default academic profile is `skills/hedgehog-master/research/profiles/academic-conference.json`. It defines the allowed layout roster and restrained publication colors. A project-local `template/template.json` may override the canvas, theme tokens, background layers, and semantic content slots without changing the registered academic layout IDs. Project, template, source, claim, storyboard, formula, and image schemas live under `skills/hedgehog-master/research/schemas/`.

`research_planner.py` is deliberately local and deterministic. PDF extraction uses PyMuPDF and preserves page numbers. Python code uses `ast`; other languages use a conservative symbol parser. The planner does not generate coordinates. It emits Diagram IR v0.2, which is the only input accepted by the geometry compiler.

## Validation

Validation combines JSON Schema with cross-file checks:

- source IDs referenced by claims must exist;
- citation source IDs and page/code locators must remain registered;
- claim IDs referenced by slides must exist;
- formula and image IDs referenced by slides must exist;
- rendered or generated assets marked complete must exist inside the project;
- diagram files must stay inside the project;
- layout IDs must be registered by the selected profile;
- unverified claims generate warnings;
- malformed Diagram IR fails before geometry is produced;
- registered input files and template layers must exist inside the project boundary.

## Implemented Vertical Slice

The implementation supports cover, section, diagram, evidence, and closing layouts. Without a template it uses the built-in 16:9 academic canvas. With a PPTX template it recovers the source canvas, theme, Master/Layout background layers, and placeholder geometry before rendering. PDF and text documents become source and claim records; code becomes architecture or workflow semantics; Brief instructions select dataflow, cycle, comparison, architecture, or timeline Diagram IR. Formula and image Manifests participate in validation and Build.

## Deliberate Boundaries

- Editable formulas use mathematical PowerPoint text, not native OMML. Complex equations can use transparent raster rendering.
- Template rendering preserves recovered visual layers and constraints, not every live native Master behavior or unsupported PowerPoint object.
- Local extraction is conservative. Claims remain inspectable and must be reviewed before publication; draft Brief claims produce validation warnings.
- External image providers are opt-in. The geometry compiler and slide renderer remain deterministic when no provider is configured.
