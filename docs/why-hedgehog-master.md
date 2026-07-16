# Why Hedgehog Master

Hedgehog Master exists for people who need to explain research and technical systems with more discipline than a one-shot slide generator can provide.

## Research Communication Is an Engineering Problem

A credible deck must preserve meaning while changing form. It must decide what belongs in the narrative, which claims require evidence, how a method should be visualized, and whether a figure remains readable outside the slide where it was created.

Hedgehog Master treats these decisions as an inspectable workflow:

1. normalize source material;
2. define the audience, claim structure, and design contract;
3. create figures and slide pages from explicit specifications;
4. validate the SVG source;
5. export editable presentation objects;
6. retain the project artifacts required to review or reproduce the result.

## Academic English Is Part of the Output Contract

The target is not generic business copy. Research decks should use:

- formal, idiomatic English;
- stable terminology and defined acronyms;
- explicit methods, evidence, limitations, and conclusions;
- measured claims rather than promotional exaggeration;
- retained citations, units, equations, and qualifiers.

This standard applies to slides, notes, diagrams, examples, and public project documentation.

## Diagrams Need Structure

Complex flowcharts are difficult to maintain when they exist only as drawing commands. Hedgehog Master includes a Diagram IR package so a scientific diagram can have:

- validated nodes and edges;
- canonical ordering;
- deterministic layout;
- stable SVG serialization;
- independent compiler tests;
- a future path to paper-figure and slide-specific render profiles.

The presentation workflow and Diagram IR compiler are currently separate components. Their integration is a declared roadmap item, not a hidden capability claim.

## Local-First by Default

Projects live in the local repository workspace. Source conversion, project artifacts, SVG pages, quality reports, and PPTX exports remain inspectable on disk.

External model or image services may still receive the prompts or material explicitly sent to them. Local-first means the harness does not require a project-hosting service; it does not mean every configured AI provider is offline.

## Editable Output Matters

The generated PPTX route maps authored SVG content into PowerPoint's object model. Editable output makes review practical: researchers can correct wording, adjust figures, update labels, and adapt a deck after generation.

Editability is not a promise of perfect application parity. PowerPoint, Keynote, LibreOffice, and WPS may render advanced objects differently, so release validation must name the target application.

## Reproducibility Over Hidden Automation

Hedgehog Master keeps the design specification, execution lock, SVG author source, notes, assets, and export backups. A reviewer can inspect what was generated and determine which artifact owns a correction.

This is slower than an opaque single-call generator. The tradeoff is intentional: important scientific communication benefits from explicit assumptions and visible quality gates.

## Current Limitations

- The local gallery and SVG editor are separate development surfaces, not yet one unified application.
- Diagram IR is tested independently but is not yet orchestrated by the presentation Executor.
- Publication readiness still requires target-journal or conference validation.
- Real-time multi-user collaboration is not provided.
- Output quality still depends on source quality, model capability, and human review.

## The Direction

Hedgehog Master is being developed as an open research-presentation harness with four connected outputs:

1. an editable slide deck;
2. formal speaker notes;
3. reusable vector diagrams;
4. a reproducible local project record.

That combination defines the project: a research-focused workflow with explicit artifacts, deterministic diagram infrastructure, and local review surfaces.
