# Hedgehog One / 刺猬一号 Agent Rules

## Project Identity

- Project name: Hedgehog One
- Chinese name: 刺猬一号
- Repository: hedgehog1
- GitHub: DearKarl/hedgehog1
- v0.1a goal: deterministic Diagram IR -> SVG compiler
- Runtime must work without LLM, network, or interactive external service.

## Frozen v0.1a Scope

v0.1a only implements:

Diagram IR v0.1a -> validate -> ranked layout -> SVG AST -> stable SVG

Only support:

- kind: dataflow
- direction: left-to-right
- layout: ranked
- output: SVG

Do not implement in v0.1a:

- HTML GUI
- PPTX
- PDF extraction
- code extraction
- research extraction
- LLM planner
- absolute layout
- grid layout
- groups
- ports
- arbitrary style tokens
- circle/text/free shapes
- undirected edges
- PNG visual regression

## Core Principles

- The model must never directly generate final SVG.
- Every diagram must go through structured Diagram IR.
- Same input must produce byte-stable output.
- Invalid input must produce explicit diagnostics.
- Never silently fix invalid input.
- Every feature must have automated tests.
- Scientific data, code relationships, and graph structure must remain verifiable.
- Runtime must not require Codex, ChatGPT, or any LLM.

## Required Compiler Pipeline

The core compiler pipeline must remain:

parse -> schemaValidate -> semanticValidate -> canonicalize -> layout -> buildSvgAst -> serializeSvg

Rules:

- parse reads strict JSON only.
- schemaValidate rejects unknown fields.
- semanticValidate checks duplicate IDs, missing references, invalid roles, unsupported kind/direction, and cycles.
- canonicalize must not repair invalid input.
- layout must not use randomness, current time, network, file system, or system font measurement.
- buildSvgAst must not allow arbitrary SVG passthrough.
- serializeSvg must produce stable element order, stable attribute order, stable numeric format, stable escaping, and no timestamps.

## v0.1a IR

Root fields:

- irVersion
- id
- title
- kind
- direction
- nodes
- edges
- metadata

Node fields:

- id
- label
- role

Allowed node roles:

- source
- transform
- model
- metric
- output

Edge fields:

- id
- from
- to
- label optional
- evidenceRef optional

v0.1a evidenceRef rule:

- If present, evidenceRef must be a non-empty string.
- Do not parse external files.
- Do not access network.
- Preserve evidenceRef exactly.
- If metadata.evidence exists later, validation may check it, but v0.1a should not require a full provenance system.

## CLI Scope

Only these commands are allowed in v0.1a:

hedgehog1 validate input.diagram.json
hedgehog1 compile input.diagram.json -o output.svg
hedgehog1 check input.diagram.json

Command semantics:

- validate = parse + schemaValidate + semanticValidate
- compile = full compiler pipeline and write SVG
- check = validate + compile to memory + compile a second time + byte-for-byte comparison

## Testing Rules

Each implementation step must include relevant tests.

At minimum, v0.1a must eventually cover:

- valid dataflow IR
- duplicate node ID
- duplicate edge ID
- edge references unknown node
- cycle detection
- missing required field
- invalid node role
- long label handling
- byte-stable compile output
- equivalent canonical input output consistency
- CLI success and failure exit codes

Tests should assert stable diagnostic codes and paths, not only natural-language messages.

## Development Discipline

Before modifying code:

- State the intended change.
- Keep each task small.
- Do not implement future milestones early.
- Do not introduce large dependencies without explaining why.
- Do not change PLAN.md scope unless explicitly asked.

After each completed task:

- Run relevant checks.
- Run git status.
- Commit with a clear message.
- Push to origin main.
- Report the commit hash.

## GitHub Sync Rule

Every completed checkpoint must be synchronized to GitHub.

Required sequence:

1. Run relevant checks.
2. git status
3. git add <changed files>
4. git commit -m "<clear message>"
5. git push origin main
6. Report commit hash and summary.

Do not claim a task is complete until it has been pushed to GitHub.
