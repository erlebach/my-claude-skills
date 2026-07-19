# Diagram Decision Reference

Authoritative source: spec decisions 3 and 3b in
`docs/superpowers/specs/2026-07-05-demonstration-builder-skill-design.md`.

---

## Table of Contents

1. [The 3-case triage](#1-the-3-case-triage)
2. [Renderer catalog — two families](#2-renderer-catalog--two-families)
3. [PTRDATA convention (drives live renderers)](#3-ptrdata-convention-drives-live-renderers)
4. [Optional zero-JS interaction layer](#4-optional-zero-js-interaction-layer)
5. [Case-2 seam: where diagram-generation attaches](#5-case-2-seam-where-diagram-generation-attaches)

---

## 1. The 3-case triage

The organizing question is pedagogical: **does this subject have a spatial/structural
mental model worth drawing?** The triage is keyed on **renderer availability** — not on
whether the topic involves pointers. Pointers are not privileged; they are simply the
only family for which a renderer exists today.

```
Does a diagram help this subject?
    |
    |--NO---> diagram: false (Case 3)
    |
    YES
    |
    Does a built-in renderer already fit?
        |
        |--YES---> emit PTRDATA line + pick type= (Case 1)
        |
        NO
            |
            Has the author (or agent) supplied an image / SVG sketch?
                |--YES---> redraw as hand-authored SVG wrapped via _wrap_svg (Case 2a)
                |
                NO
                    |----> diagram: false, concept fills right column (Case 2b)
```

### Case 1 — renderer exists, use it

Pick a `type=` from the built-in inventory (see §2). Emit the correct `PTRDATA:` line
in the program. Set `diagram: true` (the default) on the page block.

Works today for all pointer/reference/smart-pointer topics and for call-stack /
memory-layout topics.

### Case 2 — diagram would help, but no renderer exists yet

This is the **common case** for most of a C++ course: linked lists, graphs, trees,
array & vector memory layout, class composition, iterator ranges, and more.

- If an author image or SVG sketch is available, the skill can redraw it as a
  **hand-authored SVG** in the vertical-diagram style, wrapped via `html_renderer._wrap_svg`.
  This is the manual seed of the future `diagram-generation` sub-skill.
- Otherwise fall back to **`diagram: false`**; supply a `concept:` arg on the `topic`
  block so the explanation prose fills the otherwise-empty right column.

The engine block that injects a hand-authored/static custom SVG into the diagram column
is **documented here but not built in v1**. The v1 deliverable uses `diagram: false`.

### Case 2c — a step-by-step trace (sequential, not spatial)

When the mental model is a **sequence** rather than a picture — an expression evaluating,
a chain of states, a call order — use a `steps:` **text stepper** as the diagram. It needs
no SVG renderer: set `diagram: true` and author a per-variant `steps:` block (expression
header + caption + paced `{summary, detail}` reveals); the Key Idea moves to a `concept:`
button. This is a real, built-in diagram type (unlike Case 2a's not-yet-built SVG path).
Full schema: **PATTERN.md §7 → "The `steps:` diagram"**. Live example: `op_chaining`.

### Case 3 — no diagram helps

Use `diagram: false` on every `topic` block. Supply `concept:` to use the right column
for prose.

### Why most subjects fall in Case 2 today

The built-in inventory (memory + stackframe families) is narrow relative to the many
structural subjects in a C++ course. Growing the inventory is the `diagram-generation`
sub-skill's job. Do not treat `diagram: false` as a failure — it is the correct honest
choice until a real renderer exists.

---

## 2. Renderer catalog — two families

All renderers live in `cpp_labs/html_renderer.py`. The main entry point is
`svg_renderer(ptrdata: dict | None, svg_id: str = "d") -> str`, which dispatches on
`ptrdata["type"]`.

### Family A — memory renderers

Six vertical renderers for pointer/reference/smart-pointer subjects. Diagrams are
drawn tall and narrow: source box on top, arrow pointing down, target below.

| `type=` | Function | Required PTRDATA keys |
|---|---|---|
| `raw` | `_svg_raw` | `ptr_addr`, `target_addr`, `target_val` |
| `null` | `_svg_null` | `ptr_addr` (fallback `0x0`) |
| `ref` | `_svg_ref` | `ref_addr`, `target_addr`, `target_val` |
| `unique` | `_svg_unique` | `ptr_addr`, `target_addr`, `val`, `is_null` (`"0"`/`"1"`) |
| `shared` | `_svg_shared` | `ptr_addr`, `target_addr`, `val`, `use_count`; optional `ptr2_addr` draws two owners |
| `weak` | `_svg_weak` | `ptr_addr`, `expired`, `use_count` |

Missing keys degrade to `"?"` and never raise. An unrecognized `type=` hits `_svg_unknown`.

### Family B — stackframe renderers

Two renderers for call-stack and memory-layout subjects.

| `type=` | Function | Purpose |
|---|---|---|
| `frames` | `_svg_frames` | Call-stack frame sequence snapshot |
| `memmap` | `_svg_memmap` | Process memory map (stack / heap / globals regions) |

Note: `_svg_frames_anatomy` is not a PTRDATA type — it is rendered indirectly by the
`frames_anatomy_details` and `stepped_frames` components (see the interaction layer below).

Reference: `html_renderer.py::svg_renderer`, `_stack_svg`.

---

## 3. PTRDATA convention (drives live renderers)

A program prints **one line** to stdout; `compiler_runner.py::parse_ptrdata` reads it
at build time to produce the `ptrdata` dict passed to `svg_renderer`.

```
printf("PTRDATA: type=<kind> key1=%... key2=%...\n", ...);
```

Regex: `^\s*PTRDATA:\s*(.+)$` — only the **first** match is used. Keys are split on
whitespace and `=` into a `{key: value}` string dict.

### Emit examples
```cpp
// raw pointer
printf("PTRDATA: type=raw ptr_addr=%p target_addr=%p target_val=%g\n",
       (void*)&ptr, (void*)ptr, (double)val);

// reference (ref_addr == target_addr == &x; reference has no storage of its own)
printf("PTRDATA: type=ref ref_addr=%p target_addr=%p target_val=%d\n",
       (void*)&r, (void*)&x, x);

// null pointer
printf("PTRDATA: type=null ptr_addr=%p\n", (void*)ptr);
```

No PTRDATA line → `ptrdata=None` → `_demo_variant_body` skips the diagram
(`diagram_html = memory_diagram(...) if pd else ""`) → the right cell is empty.
(`svg_renderer` is not called in this path; called directly with `None` it would return
a 'no diagram' placeholder SVG, not an empty string.)

See `PATTERN.md §6` for the full PTRDATA key table and §7 for diagram gating rules.

---

## 4. Optional zero-JS interaction layer

A static SVG is a perfectly good default. The engine provides a **reusable,
zero-JS interaction layer** (CSS-radio + native `<details>`) that wraps **any** SVG —
not just the stackframe ones. All components are in `cpp_labs/components.py`.

Offer interactivity when it genuinely aids comprehension; do not impose it by default.
The layer degrades gracefully: JS-off browsers see the static SVG.

Because each mechanism is "a radio / `<details>` selects a state, CSS restyles the
SVG," the same patterns generalize to changing **colors, emphasis, shapes, or
connectivity** on a Case-2 hand-drawn SVG too.

### Component catalog

#### `stepped_frames(comp_id, steps, *, with_anatomy=False)`
Ordered student-paced snapshot reveals. Elements present at a deeper step but gone at
the current one draw **ghosted** (reclaimed). Use for:
- Stack-frame push/pop sequences.
- Any subject where you want to step through **ordered states** (add/remove nodes,
  change emphasis, mutate a diagram).

#### `zoomable(comp_id, inner_html, *, label="⤢ Enlarge")`
Click-to-fullscreen overlay with radio-controlled zoom levels:
0.5× / 0.75× / 1× / 1.5× / 2×. The `inner_html` is promoted as-is, so nested SVGs
keep their `role="img"` (WCAG diagram invariant is preserved). Use for large diagrams
that need to be readable at small default sizes.

#### `frames_anatomy_details(comp_id, pd)` and `progressive_steps(comp_id, steps)`
Native `<details>` disclosures that reveal an expanded, more-detailed view beneath the
figure (e.g. full per-frame anatomy, step-by-step textual annotations). Zero-JS;
browser-native.

#### `before_after_toggle(...)` and `variant_tabs(comp_id, panels, *, selected=0)`
Switch a diagram between two or more states (before/after, per-variant). CSS-radio
mechanism; no JS.

### When to suggest each compositor

| Need | Compositor |
|---|---|
| Step through ordered states (push/pop, mutation) | `stepped_frames` |
| Diagram is large, needs zoom | `zoomable` |
| Show more detail below on demand | `frames_anatomy_details` / `progressive_steps` |
| Toggle between two or more named states | `before_after_toggle` / `variant_tabs` |
| None of the above | plain static SVG (default) |

---

## 5. Case-2 seam: where diagram-generation attaches

The **`diagram-generation` sub-skill** (future, not built in v1) is the seam for
turning an author concept or image into a new SVG renderer family.

When it exists, it plugs in at Case 2: instead of the author hand-drawing an SVG, the
sub-skill generates one from a structural description or sketch. The result is wrapped
via `html_renderer._wrap_svg` and injected into the diagram column.

The engine block that injects a static/custom SVG into the diagram column is also
**deferred to v1+** — the current engine only handles renderers that emit via
`svg_renderer`. Until that block is built, Case-2 falls back to `diagram: false`.

Mark this seam in authoring notes so future work knows where to extend: the skill's
DIAGRAMS.md (this file) documents the contract; a later `diagram-generation` sub-skill
implements it.

### 5a. The `diagram_spec:` box-chain seam (built 2026-07-10)

Case-2 structural diagrams no longer require hand-authored SVG. A demo `topic:`
block may carry a per-variant **`diagram_spec:`** map (keyed by variant label,
exactly like `steps:`). Each entry is a declarative description — no SVG markup,
no coordinates:

- `nodes`: `[{id, label, rows?}]` — a vertical stack of labelled boxes (optional
  `rows` are extra lines inside a box; a `●` in a label/row marks a port).
- `links`: `[{from, to, label?, live?}]` — downward arrows between node `id`s;
  `live: true` draws that arrow in the accent color (the path that actually runs).
- `note`: optional caption drawn under the chain.

`html_renderer._svg_boxchain` renders it to a vertical, self-contained SVG
(auto-width, `role="img"` via `_wrap_svg`), reusing the shared `_vbox`/`_arrow_v`
helpers and the module-level style constants — so one edit restyles every box-chain
diagram across the whole curriculum (the decisive advantage over SVG-in-YAML). When
a variant has both `diagram_spec:` and `steps:`, they render as `Structure` /
`Dispatch walk` sub-tabs inside a `zoomable` panel; either alone fills the column.

Schema is deliberately Mermaid-shaped (a `nodes`/`links` graph) but rendered in
Python — no client-side JS, no `mmdc`/Node build dependency, so the page stays
self-contained and deterministic. First consumer: `inh_virtual` (the vtable). v1
box-chain assumes a linear top-to-bottom chain. Non-linear structures are handled
by three sibling renderers (built 2026-07-14/15): `_svg_tree` (binary tree — map;
in-order-x layout, `kind: tree`), `_svg_buckets` (hash-bucket array with collision
chains — unordered_map, `kind: buckets`), and `_svg_set` (a DISCONNECTED sorted
collection `{ … }` with rejected duplicates ghosted+struck — `std::set`, `kind:
set`; drawn disconnected because a set has no hierarchy between elements, unlike
its red-black-tree implementation). All dispatch on the `kind:` field of a
`diagram_spec` entry (default `chain` → `_svg_boxchain`); each mirrors the
box-chain fixed-size / constant-14px-font invariant (fixed node dimensions,
`natural=True`, note as a `.dia-note` HTML caption, structure-driven viewBox).
First consumers: `stl_assoc` (map tree + unordered_map buckets + set collection).
