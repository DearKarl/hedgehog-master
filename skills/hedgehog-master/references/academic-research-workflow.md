# Academic Research Workflow

Use this route for formal English research talks, publication-oriented flowcharts, and evidence-linked PPTX output.

## Authoring Boundary

The model may create or revise only structured semantic artifacts:

- `project.json`
- `research/sources.json`
- `research/claims.json`
- `storyboard/deck.json`
- `research/diagrams/*.diagram.json`

The model must not write final flowchart SVG, HTML layout code, or DrawingML for this route. Geometry is owned by the Diagram IR compiler and the registered academic slide renderer.

## Required Sequence

1. Initialize a research project with `python3 hedgehog.py init <name>`.
2. Register every source in `research/sources.json`.
3. Record substantive statements and evidence in `research/claims.json`.
4. Build the narrative in `storyboard/deck.json` using registered layouts only.
5. Express each process figure as Diagram IR.
6. Run `python3 hedgehog.py validate <project>`.
7. Run `python3 hedgehog.py build <project>` and inspect every SVG.
8. Run `python3 hedgehog.py export <project>` and inspect the PPTX.

## Quality Gates

- Formal English is concise, grammatical, and suitable for an academic audience.
- Every substantive evidence slide references at least one verified claim.
- Every claim references an existing source and includes a short evidence statement.
- Diagrams are generated from strict Diagram IR and compile deterministically.
- Layout IDs come from the selected profile; unregistered layouts fail validation.
- SVG and PPTX receive visual review before release.
