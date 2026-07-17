# Hedgehog Master Diagram IR

Diagram IR is the deterministic scientific-diagram compiler used by Hedgehog Master.

The v0.2 contract accepts strict JSON scientific graphs, validates schema and graph semantics, canonicalizes input, applies a registered semantic layout, builds an SVG AST, and serializes byte-stable SVG. It supports dataflow, cycle, comparison, architecture, and timeline diagrams without an LLM, network, or interactive service. v0.1a dataflow documents remain compatible.

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

Registered v0.2 combinations are:

| Kind           | Direction       | Layout                 |
| -------------- | --------------- | ---------------------- |
| `dataflow`     | `left-to-right` | ranked                 |
| `cycle`        | `clockwise`     | radial                 |
| `comparison`   | `left-to-right` | grouped columns        |
| `architecture` | `top-to-bottom` | layered system view    |
| `timeline`     | `left-to-right` | alternating milestones |

Invalid graphs produce stable diagnostics and are never silently repaired. See [Diagram IR v0.2](./docs/ir-spec-v0.2.md).
