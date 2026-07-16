# Template Architecture

This document defines the three template identities used by Hedgehog Master: **brand**, **layout**, and **deck**. It is the contributor-facing reference for template workspaces, specification ownership, composition, and conflict handling.

For user-facing selection, see [Templates Guide](./templates-guide.md).

## Template Kinds

| Kind | Library workspace | Owns | Must not own |
|---|---|---|---|
| brand | skills/ppt-master/templates/brands/<id>/ | color, typography, logo, voice, icon style | canvas, page types, SVG roster |
| layout | skills/ppt-master/templates/layouts/<id>/ | canvas, page structure, page types, SVG roster | brand logo, official brand palette, brand voice |
| deck | skills/ppt-master/templates/decks/<id>/ | complete identity, structure, and template overview | none of the required segments |

The physical library directory and the frontmatter kind must agree. A project-scoped workspace uses the same kind even though it lives under projects/.

## Workspace Shape

Library and project output scopes use the same portable structure:

    <template-workspace>/
    |-- templates/
    |   |-- design_spec.md
    |   |-- *.svg
    |   `-- icons/
    |-- images/
    |-- icons/
    `-- exports/
        `-- <id>_template_preview.pptx

Only templates/ is mandatory. Empty optional directories are omitted. exports/ contains review artifacts and is never a template source.

Step 3 consumes the workspace root. It installs templates/ plus any existing images/ and icons/, and ignores exports/. A workspace may be moved between project and library scope without changing internal asset paths.

Before the first write, a creation workflow must:

1. resolve the final workspace root;
2. verify that the target templates/ directory is empty;
3. enumerate all image and icon destinations;
4. reject every destination collision;
5. confirm that a project-scoped target project already exists.

No template workflow may silently merge or overwrite an existing workspace.

## Structured SVG Contract

Every newly authored or restored layout/deck SVG is a complete visual preview and declares its Master and Layout keys and picker names at the root.

- Fixed Master and Layout visuals are direct root atoms.
- A semantic slot is a top-level group.
- A normal slot has positive design-zone bounds and exactly one compatible carrier.
- A composite object slot uses the explicit proxy binding.
- A zero-slot Layout is valid.
- Specialized structure markers take precedence over generic page-role markers.

standard and fidelity modes author a new SVG and a new structure contract. They do not preserve or infer source topology.

mirror restores the source roster, identity, parent relationships, placeholder facts, and supported native visual metadata. It may mechanically expand fixed-layer source groups into direct atoms, but it must not infer new semantics.

Both strict and adaptive template routes use pptx_structure.mode: structured. strict preserves the selected contract. adaptive preserves the Master and may introduce a new Layout identity during page authoring when the fixed Layout atoms or slot topology genuinely change.

Run restore-pptx-structure only when a legacy package still uses obsolete Master/Layout semantics. A flat package directory by itself is only a packaging compatibility case and does not trigger restoration.

## Segment Ownership

Composition happens at segment granularity.

| Segment | Sections | Priority owner |
|---|---|---|
| Identity | Color Scheme, Typography, Logo, Voice and Tone, Icon Style | brand |
| Structure | Canvas, Page Structure, Page Types, SVG Roster | layout |
| Overview | Template Overview, intended use, design intent, rhythm | deck |

The default operation is complete segment replacement. Field-level mixing is not performed during Step 3. A user-requested field adjustment belongs to the Strategist confirmation stage.

## Brand Specification

Required frontmatter fields:

- brand_id
- kind: brand
- summary
- primary_color

Required sections:

1. Brand Overview
2. Color Scheme, including role, HEX, provenance, and notes
3. Typography, including role, family, and weight
4. Logo, including files and usage constraints
5. Voice and Tone
6. Icon Style

A brand specification must not declare a canvas, page types, or an SVG roster.

## Layout Specification

Required frontmatter fields:

- layout_id
- kind: layout
- native_structure_mode: structured
- summary
- canvas_format
- page_count
- page_types

Required sections:

1. Template Overview
2. Canvas Specification
3. Page Structure
4. Page Types
5. SVG Page Roster

A layout specification must not declare a brand logo, brand voice, or official brand-color facts. Color and typography are confirmed by the Strategist when no brand or deck owns the identity segment.

## Deck Specification

Required frontmatter fields:

- deck_id
- kind: deck
- native_structure_mode: structured
- summary
- canvas_format
- page_count
- primary_color

Required sections:

1. Template Overview
2. Canvas Specification
3. Color Scheme
4. Typography
5. Logo
6. Voice and Tone
7. Icon Style
8. Page Structure
9. Page Types
10. SVG Page Roster

A deck is the complete union of identity, overview, and structure segments.

## Library Indexes

Project-scoped workspaces are intentionally not registered. Library workspaces use:

- brands/brands_index.json with summary and primary_color;
- layouts/layouts_index.json with summary, canvas_format, page_count, and page_types;
- decks/decks_index.json with summary, canvas_format, page_count, and primary_color.

Indexes remain compact selection aids. The workspace design specification is authoritative.

## Composition Matrix

| Supplied workspaces | Identity | Structure | Overview |
|---|---|---|---|
| none | free design | free design | none |
| brand | brand | free design | none |
| layout | free design | layout | layout overview |
| deck | deck | deck | deck |
| brand + layout | brand | layout | layout overview |
| brand + deck | brand | deck | deck |
| layout + deck | deck | layout | deck |
| brand + layout + deck | brand | layout | deck |

When the result owns both identity and structure, its fused kind is deck. Structure only yields layout; identity only yields brand.

## Same-Kind Conflicts

Two workspaces of the same kind require an explicit segment-level decision:

1. use all segments from the first workspace;
2. use all segments from the second workspace;
3. choose the source separately for each segment.

There is no implicit ordering. Field-level conflict resolution is out of scope. More than two same-kind inputs must be reduced by the user before composition.

## Provenance

A fused specification records its sources immediately below the H1:

    > **Fused from:**
    > - deck: templates/decks/research_briefing/ (base)
    > - brand: templates/brands/lab_identity/ (identity override)
    > - layout: templates/layouts/academic_core/ (structure override)
    > - conflicts resolved: Typography from lab_identity

This block is required for every multi-workspace composition and omitted for a single source.

## Step 3 Dispatch

Template selection is path-based. A bare name never triggers template loading.

| Resolved kind | Step 3 behavior |
|---|---|
| brand | install portable roots; lock identity; keep structure free |
| layout | install portable roots; lock structure; confirm identity |
| deck | install portable roots; lock complete reference |
| multiple paths | resolve conflicts, compose one specification, then install one final mapping |

If the supplied workspace root is the target project root, consume it in place. Never copy a project workspace into itself.

## Deliberate Non-Goals

- No field-level override language in the composition layer.
- No batch conflict solver for three or more same-kind workspaces.
- No additional template kind for project output scope.
- No automatic template-name lookup.
- No structure inference during export.
