# AutoResearch-Future Architecture

## Objective

AutoResearch-Future compiles evidence-linked research semantics into publication SVG and editable PPTX without allowing a general-purpose model to own final geometry.

## Pipeline

```text
content intake
  -> external-LLM JSON contract (recommended, no app API key)
       OR rules/cloud/local/external Content Provider (optional automation)
  -> project input registry
  -> optional PPTX Template Contract or built-in academic profile
  -> page-aware source registry
  -> evidence-linked claim registry
  -> audience-facing storyboard
  -> typed Diagram IR when requested
  -> Formula Manifest + Image Manifest + page image mapping
  -> semantic and evidence guardrails
  -> deterministic diagram compiler
  -> registered academic slide renderer
  -> static validation
  -> visual review
  -> SVG and PPTX
```

## Ownership Boundaries

| Artifact | Owner | Rule |
|---|---|---|
| External content contract | User-selected LLM, then researcher | The model fills registered page IDs, copy, LaTeX, image requirements, sources, and notes. It never returns geometry. |
| Unified project inputs | Workbench or CLI | Filled content, brief, template, papers, code, and page images are copied into project-local paths and registered once. |
| Template Contract | PPTX template adapter | Master/Layout backgrounds, theme tokens, and placeholder slots constrain the academic renderer. |
| Sources and claims | Rules/model provider, then researcher | Extracted claims retain source IDs, page or code locators, excerpts, and confidence. Unknown evidence IDs are rejected. |
| Storyboard | Content contract or Content Provider, then guardrails and researcher | Slides use registered semantic layout IDs and audience-facing copy. Text limits are validated before build. |
| Diagram IR | Diagram Provider, guardrails, then researcher | Graph structure is strict JSON with explicit kind, roles, groups, and edges. Broken references fall back to rules. |
| Formula Manifest | Content compiler, local planner, and asset resolver | LaTeX, provenance, render mode, status, and slide bindings remain auditable. |
| Image Manifest | Content compiler, page image mapper, and configured provider | User uploads or external generation are policy-gated; prompts, files, page bindings, and status remain project-local. |
| Diagram geometry | Diagram IR compiler | Layout is deterministic and never inferred from arbitrary SVG. |
| Slide geometry | Academic renderer | Profile tokens and layout contracts own placement. |
| PPTX package | Export compiler | Visible SVG structure maps to editable PowerPoint objects where supported. |

## Runtime Contracts

The root CLI is `hedgehog.py`. It exposes project initialization, semantic planning, validation, SVG build, PPTX export, standalone diagram compilation, status reporting, and a local HTTP workbench.

The default academic profile is `skills/hedgehog-master/research/profiles/academic-conference.json`. It defines the allowed layout roster and restrained publication colors. A project-local `template/template.json` may override the canvas, theme tokens, background layers, and semantic content slots without changing the registered academic layout IDs. Project, template, source, claim, storyboard, formula, and image schemas live under `skills/hedgehog-master/research/schemas/`.

`content_spec.py` defines the copyable external-model JSON contract. `content_intake.py` validates a filled contract and compiles it into Sources, Claims, Storyboard, Formula Manifest, Image Manifest, speaker notes, and explicit image-to-slide mappings. The approved contract remains at `inputs/content/content-spec.json`; rerunning `Plan` cannot silently replace it.

`research_planner.py` remains the optional automatic route and keeps extraction local and deterministic. PDF extraction uses PyMuPDF and preserves page numbers. Python code uses `ast`; other languages use a conservative symbol parser. `content_provider.py` may route semantic synthesis to rules, a cloud model, a local OpenAI-compatible LLM, or an external Agent. Provider output never contains coordinates. It emits constrained slide semantics and Diagram IR v0.2, which is the only input accepted by the geometry compiler.

Provider credentials and routing live in the user-only `~/.hedgehog-master/settings.json` file. API responses never expose saved secrets. Project manifests record provider and model names, while `analysis/provider_trace.json` records guardrails, status, warnings, and fallback decisions.

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
- provider output must match the constrained content or Diagram IR contract;
- generated claims may reference only registered evidence identifiers;
- requested prose length is checked and reported before rendering;
- external content contracts must preserve unique slide and image IDs and contain no unresolved placeholders;
- every uploaded page image must map to a registered slide;
- registered input files and template layers must exist inside the project boundary.

## Implemented Vertical Slice

The implementation supports cover, section, diagram, evidence, and closing layouts. Without an uploaded template it uses one of four built-in 16:9 academic profiles. With a PPTX template it recovers the source canvas, theme, Master/Layout background layers, and placeholder geometry before rendering. The external contract path supports configurable page counts, optional titles and subtitles, body copy, LaTeX formulas, image requests, sources, notes, and exact page image uploads. PDF and text documents can still become source and claim records; code can still become architecture or workflow semantics. Formula and image Manifests participate in validation and Build.

## Deliberate Boundaries

- Editable formulas use mathematical PowerPoint text, not native OMML. Complex equations can use transparent raster rendering.
- Template rendering preserves recovered visual layers and constraints, not every live native Master behavior or unsupported PowerPoint object.
- Local extraction is conservative. Claims remain inspectable and must be reviewed before publication; draft Brief claims produce validation warnings.
- Content, diagram, image, stock, and narration providers are opt-in. The rules engine, geometry compiler, and slide renderer remain deterministic when no provider is configured.
