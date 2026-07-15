# Hedgehog One / 刺猬一号

Hedgehog One (`hedgehog1`) is a deterministic Diagram IR to SVG compiler.

Current status: v0.1a local deterministic CLI.

The v0.1a scope is intentionally narrow: it compiles structured dataflow Diagram IR into left-to-right ranked SVG output. The runtime works without an LLM, network access, or an interactive external service.

General-purpose models must not directly generate the final SVG. Every diagram must first pass through structured Diagram IR, and the same input must produce byte-stable output.

Current development is focused only on the Diagram IR -> SVG compiler for v0.1a. HTML GUI, PPTX, PDF/code/research extraction, LLM planning, absolute/grid layout, groups, ports, free shapes, undirected edges, and PNG visual regression are outside the v0.1a scope.

## Development

```sh
pnpm install
pnpm build
pnpm check
```

## CLI

After building, the v0.1a CLI exposes only three commands:

```sh
node dist/cli.js validate examples/simple-dataflow.diagram.json
node dist/cli.js compile examples/simple-dataflow.diagram.json -o build/simple.svg
node dist/cli.js check examples/simple-dataflow.diagram.json
```

`validate` parses and validates Diagram IR. `compile` writes deterministic SVG output. `check` validates, compiles in memory twice, and verifies byte-for-byte deterministic output.
