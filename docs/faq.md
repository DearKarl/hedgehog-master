# Frequently Asked Questions

## What is Hedgehog Master?

Hedgehog Master is a local-first presentation engineering harness. It helps an AI coding agent turn research sources and structured instructions into reviewable SVG slides, editable PPTX files, speaker notes, and reusable vector figures.

The repository is designed for technical and academic communication. It emphasizes explicit specifications, formal English, traceable sources, deterministic artifacts, and validation before export.

## Is Hedgehog Master a hosted presentation service?

No. The current system runs from a local repository. The example gallery and SVG editor are local web interfaces, while the generation workflow is driven by an agent that can read files and execute commands.

A unified local application for intake, generation, review, and export is planned, but it is not yet the primary interface.

## What inputs can the workflow use?

The source pipeline supports common research and office formats, including PDF, DOCX, PPTX, HTML, Markdown, LaTeX, EPUB, and plain text. A project can also begin from a topic, but source documents are preferred whenever evidence, terminology, or citations matter.

Always inspect converted material before generation. Conversion preserves useful structure, but it cannot guarantee that every equation, table, reference, or layout relationship has been interpreted correctly.

## What output does the project produce?

A normal project can contain:

- normalized source material and extracted assets;
- a narrative and design specification;
- editable SVG slide sources;
- self-contained SVG files for review;
- an editable PPTX export;
- speaker notes and optional narration artifacts;
- quality reports and timestamped backups.

The exact artifacts depend on the selected workflow and export options.

## Can figures be inserted directly into a paper?

Hedgehog Master aims to generate publication-oriented vector figures, but publication readiness is a validation target rather than an automatic guarantee. Before submission, verify typography, dimensions, line weights, contrast, accessibility, terminology, data accuracy, and the target venue's figure requirements.

The deterministic compiler in `packages/diagram-ir/` is intended for reproducible flowcharts and system diagrams. Deeper orchestration between Diagram IR and the presentation workflow remains active development work.

## Does it write in academic English?

The project standard is formal English suitable for international research communication. A good request should identify the audience, venue, field, presentation length, and required terminology. The agent should preserve uncertainty, limitations, units, variable names, citations, and methodological qualifiers from the source.

Generated language still requires expert review. The harness must not invent evidence or turn a qualified result into an unqualified claim.

## Are exported PowerPoint objects editable?

The SVG-to-PPTX pipeline converts supported slide content into PowerPoint DrawingML objects. Text, colors, geometry, and many diagram elements remain editable. Unsupported SVG features may require fallback handling, so final inspection in PowerPoint or another target viewer is required.

For layout-sensitive pages, `--no-merge` preserves each visual line as a separate text frame:

```bash
python skills/ppt-master/scripts/svg_to_pptx.py <project_path> --no-merge
```

The default export merges compatible body-text lines into editable paragraph frames.

## Why does the internal path still use `skills/ppt-master/`?

That path is a compatibility boundary retained while the repository is being migrated. Existing scripts, tests, project metadata, and agent instructions depend on it. The public product identity is Hedgehog Master; changing the internal namespace will be handled as a tested migration instead of a cosmetic rename.

## How do I install or update the repository?

Clone the standalone repository and install its Python dependencies:

```bash
git clone https://github.com/DearKarl/hedgehog-master.git
cd hedgehog-master
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

Update a Git clone with:

```bash
git pull --ff-only
python skills/ppt-master/scripts/update_repo.py
```

The project does not currently publish a separate marketplace package or lightweight skill archive. Use the repository as the canonical distribution until a project-owned release process is documented.

## How do I start the local interfaces?

Start the example gallery from the repository root:

```bash
python -m http.server 4173 --bind 127.0.0.1
```

Then open `http://127.0.0.1:4173/`.

For a project-specific SVG editor:

```bash
python skills/ppt-master/scripts/svg_editor/server.py projects/<project_name> --live --daemon
```

The editor normally opens on `http://127.0.0.1:5050/`.

## How do I create and validate a project?

```bash
python skills/ppt-master/scripts/project_manager.py init research-talk --format ppt169
python skills/ppt-master/scripts/project_manager.py validate projects/research-talk
```

Ask the agent to read `AGENTS.md` and `skills/ppt-master/SKILL.md` before it begins presentation work. The confirmation stage should be completed before slide authoring so that narrative, format, typography, palette, and output requirements are explicit.

## Can I use an existing presentation as a template?

Yes. Use the create-template workflow when the source deck should become a reusable visual system. Use the template-fill workflow when content should be placed into an existing PowerPoint structure. These are different operations and should not be treated as interchangeable.

See [Template Guide](./templates-guide.md) and [Template Architecture](./templates-architecture.md).

## Can the workflow use generated or web-sourced images?

Yes. Image providers are configured through local environment variables, and web search can retrieve candidate assets. Every selected image still requires checks for relevance, resolution, licensing, attribution, and scientific appropriateness. For research work, supplied figures or manually reviewed sources are usually more reliable than an automatically selected image.

## Which AI model should I use?

Use a model that can follow long repository instructions, inspect images, reason about structured layouts, and execute local validation commands. Model quality affects language, geometry, and consistency, but it does not replace the repository's quality gates or subject-matter review.

Hedgehog Master is model-agnostic and does not endorse a paid model provider.

## What should I do when text overflows or objects overlap?

1. Run the SVG quality checker and project validation.
2. Inspect the affected SVG at the target presentation size.
3. Shorten or restructure the content instead of shrinking text below the project standard.
4. Correct geometry, alignment, or wrapping in the source SVG.
5. Re-export and inspect the final PPTX in the target application.

Treat layout failures as fixable project defects. Do not waive them because the content was generated by an AI model.

## Where should bugs and feature requests go?

Use [GitHub Issues](https://github.com/DearKarl/hedgehog-master/issues). Include the operating system, Python and Node.js versions, the command that failed, the relevant project validation output, and the smallest reproducible example that can be shared safely.
