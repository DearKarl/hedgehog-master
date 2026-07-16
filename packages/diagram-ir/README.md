# Hedgehog Master Diagram IR

Diagram IR is the deterministic scientific-diagram compiler used by Hedgehog Master.

The v0.1a contract accepts strict JSON dataflow graphs, validates schema and graph semantics, canonicalizes input, computes a ranked left-to-right layout, builds an SVG AST, and serializes byte-stable SVG. It requires no LLM, network, or interactive service.

## Development

```bash
pnpm install
pnpm build
pnpm check
```

## CLI

```bash
node dist/cli.js validate tests/fixtures/valid/simple-dataflow.diagram.json
node dist/cli.js compile tests/fixtures/valid/simple-dataflow.diagram.json -o build/simple.svg
node dist/cli.js check tests/fixtures/valid/simple-dataflow.diagram.json
```

Use the repository-level wrapper for normal work:

```bash
python3 ../../hedgehog.py diagram input.diagram.json -o output.svg
```

Current scope is intentionally narrow: `kind: dataflow`, `direction: left-to-right`, ranked layout, and SVG output. Invalid graphs produce stable diagnostics and are never silently repaired.
