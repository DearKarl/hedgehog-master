# Hedgehog Master Roadmap

This roadmap describes project direction, not a release promise. Priorities may change when validation uncovers a more fundamental problem.

## Engineering Principles

- Preserve source meaning before optimizing appearance.
- Keep public project communication in English.
- Prefer deterministic intermediate representations for diagrams.
- Keep local deployment as a first-class workflow.
- Separate authoring sources from derived preview and export artifacts.
- Make invalid output fail explicitly.
- Distinguish implemented behavior from planned behavior.

## Phase 1: Independent Project Foundation

Status: in progress

- Establish Hedgehog Master branding across repository metadata and local web surfaces.
- Maintain the GitHub repository as an independent project under the Hedgehog Master identity.
- Remove obsolete promotional content and non-English public documentation.
- Preserve legal attribution in LICENSE and NOTICE.
- Document the boundary between the presentation workflow and Diagram IR.
- Keep local installation and validation reproducible.

## Phase 2: Academic Presentation Profile

- Add a formal academic-English policy for slides and notes.
- Add narrative profiles for conference talks, defenses, lab meetings, and technical briefings.
- Preserve citations, units, uncertainty, equations, and methodological qualifiers through intake and export.
- Add review checks for unsupported claims and inconsistent terminology.
- Add source-to-slide traceability artifacts.

## Phase 3: Diagram IR Integration

- Define the handoff from presentation planning to Diagram IR.
- Add flowchart, architecture, dataflow, and experimental-protocol schemas.
- Compile deterministic SVG assets inside the presentation project.
- Support slide and paper-figure render profiles from the same semantic diagram.
- Add collision, routing, hierarchy, and label-length diagnostics.
- Preserve diagram source next to every generated vector artifact.

## Phase 4: Publication-Oriented Figure Validation

- Validate target dimensions and aspect ratios.
- Check typography at projected and printed sizes.
- Check line weight, contrast, grayscale behavior, and color-vision accessibility.
- Detect label overlap, edge ambiguity, and unsupported visual encodings.
- Export review-ready SVG and PDF figure assets.
- Add journal- or conference-specific profiles without hard-coding one publisher.

## Phase 5: Unified Local Application

- Combine project intake, generation status, gallery, live SVG editing, quality reports, and export controls.
- Keep the application local by default.
- Make project state recoverable after interruption.
- Show which artifact owns each edit.
- Provide clear boundaries for external model and image-provider calls.
- Avoid turning the local interface into a marketing landing page.

## Phase 6: Open-Source Release Quality

- Publish Hedgehog Master-owned examples.
- Add focused continuous validation for the Python and Diagram IR components.
- Add contribution templates for reproducible bugs and academic figure proposals.
- Publish versioned migration notes for compatibility-sensitive changes.
- Define a stable extension contract for new diagram types and presentation workflows.

## Current Baseline

The repository currently provides:

- a working source-to-SVG-to-PPTX presentation workflow;
- local gallery and SVG editing surfaces;
- a validated editable-PPTX example;
- deterministic Diagram IR compilation with automated tests;
- preserved Git history for incorporated open-source foundations.

The key missing connection is orchestration: Diagram IR does not yet participate directly in the presentation Executor. The roadmap treats that integration as a tested engineering project, not a documentation-only rename.

## Proposing Roadmap Work

Open an issue at [GitHub Issues](https://github.com/DearKarl/hedgehog-master/issues) with:

- the research or technical communication problem;
- a minimal example;
- the expected artifact contract;
- validation criteria;
- compatibility or migration risks.
