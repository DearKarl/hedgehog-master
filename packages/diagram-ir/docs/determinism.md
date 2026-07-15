# Determinism in v0.1a

Hedgehog One v0.1a is a local deterministic Diagram IR -> SVG compiler.

The v0.1a runtime:

- does not use an LLM
- does not require network access
- does not use randomness
- does not read the current time
- does not depend on system font measurement
- does not parse external evidence files

Diagram IR is the structural source of truth. SVG is a compiled artifact. General-purpose models must not directly generate final SVG.

The deterministic boundary is:

```text
parse -> validate -> canonicalize -> layout -> buildSvgAst -> serializeSvg
```

Within that boundary:

- `parse` accepts strict JSON only.
- `validate` rejects invalid input with explicit diagnostics.
- `canonicalize` preserves semantic order and does not repair invalid input.
- `layout` uses fixed canvas, fixed node sizes, stable rank ordering, and deterministic label wrapping.
- `buildSvgAst` emits a fixed AST shape without raw SVG passthrough.
- `serializeSvg` uses stable element order, attribute order, numeric formatting, escaping, and final newline handling.

The `check` command validates the input, compiles it to memory, compiles the same input a second time, and compares the resulting SVG bytes. A mismatch returns `COMPILE_NON_DETERMINISTIC`.

v0.1a does not use PNG visual regression. Acceptance is based on LayoutModel tests, SVG AST tests, SVG string snapshots, and real `dist/cli.js` smoke tests. This keeps verification independent from browser rendering engines, rasterizers, system fonts, and machine-specific image output.
