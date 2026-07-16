# Reference-System Research

Research date: 2026-07-16.

This review uses public repository documentation and source code to identify reusable workflow ideas. Hedgehog Master implements original contracts and code. No templates or code were copied from the systems below.

## Sources

| System | Output model | Strongest workflow idea | Boundary for Hedgehog Master | License |
|---|---|---|---|---|
| [ian-handdrawn-ppt](https://github.com/helloianneo/ian-handdrawn-ppt) | Full-slide PNG images | Semantic slide archetypes, a locked visual DNA, strict text budget, and contact-sheet review | Useful as an optional illustration renderer; raster pages are not the editable or verifiable academic core | MIT |
| Native editable PPTX pipeline | SVG to native editable PPTX | Mature source normalization, review, post-processing, and DrawingML export | Retained MIT code is being reorganized behind Hedgehog Master identity and an evidence-first research contract | MIT |
| [beautiful-html-templates](https://github.com/zarazhangrui/beautiful-html-templates) | Agent-selected HTML deck templates | A machine-readable registry separates template discovery metadata from runnable shells and design instructions | Hedgehog Master adopts an original profile registry for academic layouts rather than copying visual templates | MIT |
| [guizang-ppt-skill](https://github.com/op7418/guizang-ppt-skill) | Polished HTML slide runtime | Named layout locks, safe zones, image-slot contracts, static validation, browser QA, and low-power presentation mode | Ideas only; AGPL code, CSS, templates, and runtime remain outside this MIT repository | AGPL-3.0 |

The linked WeChat article frames the practical problem as presentation production time being dominated by manual formatting. Its body could not be accessed in the current browser environment, so no detailed claims from the article are used here.

## Findings

### Raster image skills

The hand-drawn workflow is strongest when a page is treated as one visual composition. Its useful mechanisms are one main point per slide, explicit archetype selection, repeated style-lock text, exact text limits, separate page generation, and a contact sheet for whole-deck review.

This approach is unsuitable as the primary research output because page text and flowchart relationships become pixels. Hedgehog Master therefore treats raster generation as optional illustration support, never as the source of truth for claims or scientific diagrams.

### Template registries

The HTML template library demonstrates that selection metadata should be machine-readable. Occasion, mood, tone, formality, density, and scheme can be queried before a renderer is loaded. This is more robust than asking a model to improvise a design system for every deck.

Hedgehog Master applies this idea to academic profiles. A profile registers allowed layout IDs, typography limits, colors, and quality constraints. The renderer rejects unknown layouts.

### Locked HTML runtimes

The HTML skill demonstrates the value of layout IDs, safe areas, minimum type scales, image-slot aspect ratios, static validation, and required browser review. These are quality-control concepts rather than assets.

Because the repository is AGPL-3.0, Hedgehog Master does not import its templates, scripts, CSS, or runtime. Equivalent academic controls are implemented independently in the local Python harness and profile schemas.

### Editable PPTX pipelines

Native PPTX export is essential for research collaboration. SVG can be a precise page-design source, while the exporter maps supported structures to PowerPoint objects. The missing layer is a domain-specific evidence and semantics contract before SVG authoring.

## Product Decision

Hedgehog Master uses a structured-semantics boundary:

1. A researcher or model registers sources and claims.
2. A semantic storyboard selects registered academic layouts.
3. Flowcharts are expressed as strict Diagram IR.
4. Deterministic compilers own diagram and slide geometry.
5. Static validation runs before visual review.
6. The same project exports publication SVG and editable PPTX.

This architecture addresses formatting effort without making research structure opaque or delegating scientific geometry to an unconstrained model.
