# Hedgehog One Roadmap

This roadmap keeps Hedgehog One focused on deterministic, verifiable intermediate representations before presentation surfaces.

## v0.1a: Diagram IR -> SVG CLI

Status: done.

v0.1a provides a deterministic local CLI that compiles structured Diagram IR into SVG:

```text
Diagram IR -> validate -> canonicalize -> ranked layout -> SVG AST -> stable SVG
```

The v0.1a runtime does not require an LLM or network access. Final SVG is generated only by the compiler.

## v0.2: CodeGraph Foundation

Status: planned.

v0.2 introduces CodeGraph IR as a verifiable code relationship input layer:

```text
CodeGraph IR -> validate -> Diagram IR -> SVG
```

The goal is to represent code structure deterministically before visualization. Code relationships must not be drawn directly by an LLM.

## v0.3: Research Evidence Graph

Status: future.

v0.3 should introduce a structured evidence graph for research claims, citations, datasets, methods, and result relationships. The emphasis should be provenance, validation, and traceability before diagram generation.

## v0.4: Deck IR + HTML Deck

Status: future.

v0.4 should introduce a deterministic Deck IR and an HTML deck renderer. Deck output should consume verified graph and diagram artifacts rather than raw model-generated slides.

## v0.5: PPTX Exporter

Status: future.

v0.5 should add PPTX export from Deck IR. PPTX should remain an output artifact, not the source of truth.

## v1.0: Hedgehog Studio

Status: future.

v1.0 should provide a user-facing studio for composing, inspecting, validating, and exporting verified diagrams and decks. Studio workflows should remain backed by structured IR.

## v1.1: Agent Harness / Skills

Status: future.

v1.1 should explore agent harnesses and skills that help create or inspect IR, while preserving the rule that agents do not directly generate final SVG, deck, or PPTX artifacts.
