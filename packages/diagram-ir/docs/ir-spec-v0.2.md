# Diagram IR v0.2

Hedgehog Master Diagram IR v0.2 is a strict semantic contract for deterministic scientific diagrams.

```text
Diagram IR v0.2 -> schema validation -> semantic validation -> canonicalization
                -> registered semantic layout -> SVG AST -> stable SVG
```

The compiler does not infer missing nodes, repair references, call a model, or access the network.

## Root Object

Required fields:

- `irVersion`: `"0.2"`
- `id`: SVG-safe ID matching `^[A-Za-z][A-Za-z0-9_-]*$`
- `title`: non-empty string
- `kind`: `dataflow`, `cycle`, `comparison`, `architecture`, or `timeline`
- `direction`: registered direction for the selected kind
- `nodes`: node array
- `edges`: edge array
- `metadata`: object

Registered kind and direction pairs:

| Kind           | Direction       | Topology                                               |
| -------------- | --------------- | ------------------------------------------------------ |
| `dataflow`     | `left-to-right` | directed acyclic graph                                 |
| `cycle`        | `clockwise`     | directed graph; an intentional closing edge is allowed |
| `comparison`   | `left-to-right` | grouped alternatives                                   |
| `architecture` | `top-to-bottom` | layered directed acyclic graph                         |
| `timeline`     | `left-to-right` | ordered milestone graph                                |

## Node

Required fields:

- `id`: SVG-safe ID
- `label`: non-empty string
- `role`: `source`, `transform`, `model`, `metric`, or `output`

Optional fields:

- `group`: non-empty comparison or subsystem label

## Edge

Required fields:

- `id`: SVG-safe ID
- `from`: existing node ID
- `to`: existing node ID

Optional fields:

- `label`: string
- `evidenceRef`: non-empty opaque evidence key

## Validation

Schema validation rejects unknown fields, missing required fields, unsupported literals, invalid roles, and invalid IDs. Semantic validation rejects duplicate IDs, missing node references, invalid kind-direction combinations, and cycles outside `kind: cycle`.

## Determinism

Canonical node and edge ordering, fixed layout constants, an explicit SVG AST, normalized numbers, and stable attribute serialization make valid input byte-stable. Visual changes therefore require an explicit IR, compiler, or profile change.

## Compatibility

`irVersion: "0.1a"` remains accepted for `kind: dataflow` with `direction: left-to-right`. New diagram kinds require v0.2.
