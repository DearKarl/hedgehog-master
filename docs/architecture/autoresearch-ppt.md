# AutoResearch-PPT Architecture

## Objective

AutoResearch-PPT compiles evidence-linked research semantics into publication SVG and editable PPTX without allowing a general-purpose model to own final geometry.

## Pipeline

```text
research brief
  -> source registry
  -> claim registry
  -> semantic storyboard
  -> Diagram IR
  -> deterministic diagram compiler
  -> registered academic slide renderer
  -> static validation
  -> visual review
  -> SVG and PPTX
```

## Ownership Boundaries

| Artifact | Owner | Rule |
|---|---|---|
| Sources and claims | Researcher or agent | Every substantive claim links to an existing source. |
| Storyboard | Researcher or agent | Slides use registered semantic layout IDs. |
| Diagram IR | Researcher or agent | Graph structure is strict JSON with explicit roles and edges. |
| Diagram geometry | Diagram IR compiler | Layout is deterministic and never inferred from arbitrary SVG. |
| Slide geometry | Academic renderer | Profile tokens and layout contracts own placement. |
| PPTX package | Export compiler | Visible SVG structure maps to editable PowerPoint objects where supported. |

## Runtime Contracts

The root CLI is `hedgehog.py`. It exposes project initialization, validation, SVG build, PPTX export, standalone diagram compilation, status reporting, and a local HTTP workbench.

The default academic profile is `skills/hedgehog-master/research/profiles/academic-conference.json`. It defines the allowed layout roster and restrained publication colors. Project, source, claim, and storyboard schemas live under `skills/hedgehog-master/research/schemas/`.

## Validation

Validation combines JSON Schema with cross-file checks:

- source IDs referenced by claims must exist;
- claim IDs referenced by slides must exist;
- diagram files must stay inside the project;
- layout IDs must be registered by the selected profile;
- unverified claims generate warnings;
- malformed Diagram IR fails before geometry is produced.

## Current Vertical Slice

The initial implementation supports formal English 16:9 decks with cover, section, diagram, evidence, and closing layouts. Diagram IR v0.1a supports deterministic left-to-right dataflow figures. The architecture is intentionally extensible through new versioned IR kinds and profile registrations rather than arbitrary generated layout code.
