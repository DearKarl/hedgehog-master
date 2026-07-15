# Error Codes

Hedgehog One diagnostics are stable JSON objects with `code`, `severity`, `path`, `message`, and optional `hint`.

| Code                        | Layer    | Meaning                                                        | Typical path         |
| --------------------------- | -------- | -------------------------------------------------------------- | -------------------- |
| `IR_PARSE_ERROR`            | parse    | Input is not strict JSON.                                      | ``                   |
| `IR_SCHEMA_ERROR`           | schema   | Input failed schema validation without a more specific code.   | `/nodes/0/label`     |
| `IR_UNKNOWN_FIELD`          | schema   | A field is not part of Diagram IR v0.1a.                       | `/layout`            |
| `IR_MISSING_REQUIRED_FIELD` | schema   | A required field is absent.                                    | `/title`             |
| `IR_INVALID_ID`             | schema   | Diagram, node, or edge id does not match the SVG-safe id rule. | `/nodes/0/id`        |
| `IR_INVALID_NODE_ROLE`      | schema   | Node role is not one of the v0.1a allowed roles.               | `/nodes/0/role`      |
| `IR_UNSUPPORTED_KIND`       | schema   | Diagram kind is not `dataflow`.                                | `/kind`              |
| `IR_UNSUPPORTED_DIRECTION`  | schema   | Diagram direction is not `left-to-right`.                      | `/direction`         |
| `IR_DUPLICATE_NODE_ID`      | semantic | More than one node has the same id.                            | `/nodes/1/id`        |
| `IR_DUPLICATE_EDGE_ID`      | semantic | More than one edge has the same id.                            | `/edges/1/id`        |
| `IR_UNKNOWN_EDGE_FROM`      | semantic | `edge.from` does not reference an existing node.               | `/edges/0/from`      |
| `IR_UNKNOWN_EDGE_TO`        | semantic | `edge.to` does not reference an existing node.                 | `/edges/0/to`        |
| `IR_CYCLE_DETECTED`         | semantic | The dataflow graph contains a cycle.                           | `/edges`             |
| `COMPILE_NON_DETERMINISTIC` | compile  | Compiling the same input twice produced different SVG bytes.   | ``                   |
| `CLI_USAGE_ERROR`           | cli      | CLI arguments do not match the v0.1a command contract.         | ``                   |
| `CLI_READ_ERROR`            | cli      | CLI could not read the input file.                             | `input.diagram.json` |
| `CLI_WRITE_ERROR`           | cli      | CLI could not write the SVG output file.                       | `output.svg`         |
