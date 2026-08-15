# Mermaid diagram scaling & font-size fix

## Objective

Mermaid diagrams on slides should satisfy three constraints simultaneously:

1. **Font size in node labels:** 20pt minimum, 24pt maximum.
2. **Cell/box size proportional to the font** — no tiny text floating in a huge
   cell, no cramped text in a small cell.
3. **Plotting area fills the available space** in its slide column, leaving at
   least a ~1 inch margin from the slide edge. Larger margins are acceptable
   when the diagram is small — we never violate the font constraints just to
   stretch a diagram.

Previously, diagrams either came out far too large (nodes with huge text
filling the whole slide) or too small (a tiny flowchart lost in an oversized
panel). The root cause was a conflict between Mermaid's internal font/cell
sizing and post-render CSS scaling.

## Why simple CSS scaling doesn't work

Mermaid rendering bakes both the font size **and** the node padding/cell
dimensions into the generated SVG. The cell is laid out around the font at
render time. If you then scale the SVG with CSS (e.g. `width: 100%`), you
scale font and cells together — you can't make the font bigger without also
making the cells bigger, and vice versa.

So scaling alone cannot enforce a font-size band without breaking cell
proportions.

## The fix

The fix has three coordinated pieces, applied in
`compiler/templates/base.html.j2`:

### 1. Render Mermaid with a target font (22pt)

```js
mermaid.initialize({
  themeVariables: {
    fontSize:   '22pt',
    fontFamily: "'<deck-font>', sans-serif",
  },
});
```

`themeVariables.fontSize` controls the label font Mermaid uses *during layout*,
so the generated cells are correctly proportioned around 22pt text. 22pt is
the midpoint of the allowed 20–24pt band.

(The top-level `fontSize: 16` config is ignored by flowcharts; only
`themeVariables.fontSize` actually affects node labels.)

### 2. Wait for layout to settle before measuring

```js
await mermaid.run();
await new Promise(r => requestAnimationFrame(() => requestAnimationFrame(r)));
```

Immediately after `mermaid.run()`, `getBoundingClientRect()` sometimes returns
`0` for the diagram column width (layout hasn't flushed). Two RAF ticks
guarantee the browser has computed the grid geometry, so we can read real
column widths.

### 3. Clamp the SVG scale to the font-size band

Since scaling the SVG scales font and cells together, we allow the SVG to
scale *only* within a narrow range that keeps the rendered font inside
[20pt, 24pt]:

```
MIN_SCALE = 20 / 22 ≈ 0.909   // smaller than this → font < 20pt
MAX_SCALE = 24 / 22 ≈ 1.091   // larger than this  → font > 24pt
```

For each Mermaid SVG we:

1. Read its natural rendered width/height.
2. Compute `fitScale = min(availW / W, availH / H)`.
3. Clamp to `[MIN_SCALE, MAX_SCALE]`.
4. Apply the clamped scale as `width` / `height` in pixels.

Effect:

| Situation                         | Result                               |
|-----------------------------------|--------------------------------------|
| Diagram easily fits in the column | Scales up to 24pt (MAX_SCALE)        |
| Diagram fits at natural size      | Renders at 22pt                      |
| Diagram slightly too large        | Scales down to ≥ 20pt (MIN_SCALE)    |
| Diagram far too large             | Stays at MIN_SCALE (font = 20pt),<br>panel overflow becomes scrollable |

We never trade font legibility for “fitting” — going below 20pt is disallowed.

### Available space

For each Mermaid SVG we compute the available box:

- **Standalone `layout: diagram` slides:** full slide content area minus slide
  padding (`96px` = 1 inch), minus the `<h2>` title height, minus an optional
  caption height, minus the panel's internal padding (`48px` combined).
- **Two-column diagrams:** the actual column width measured from the
  `.diagram-container` (after the RAF wait), minus the panel inset. Height is
  the slide height minus the title and slide padding.

This means two-column Mermaid diagrams now scale up to fill the column height
(matching the vertical extent of the adjacent equations / bullets column), but
always within the 20–24pt font band.

## Diagram types that ignore `themeVariables.fontSize`

Some Mermaid diagram types — notably **timeline**, and (by the same argument)
**gantt**, **pie**, **quadrantChart**, **journey**, and **mindmap** — do not
honor `themeVariables.fontSize` the way flowcharts and sequence diagrams do.
Their natural rendered SVG size is therefore arbitrary (often very small),
and the `[MIN_SCALE, MAX_SCALE]` clamp that works correctly for flowcharts
would leave these diagrams unusably tiny.

For these types we use an alternative sizing function, `sizeSvgFit`, which
scales the SVG to fully fill the available panel with **no upper cap**.

Routing is done **before** `mermaid.run()` by reading the first keyword of
each `<pre class="mermaid">` source text (`timeline`, `flowchart`,
`sequenceDiagram`, …) and stashing it on the parent `.diagram-container` as
`dataset.diagramType`. `aria-roledescription` on the post-render SVG is an
unreliable fallback in Mermaid v11 (some diagram types, including
`timeline`, don't set it). `pickSizer` checks both:

```js
const UNCLAMPED_TYPES = new Set([
  'timeline', 'gantt', 'pie', 'quadrantchart', 'journey', 'mindmap',
]);
// Pre-run: tag container with diagram type from source text.
document.querySelectorAll('.diagram-container pre.mermaid').forEach(pre => {
  const line = pre.textContent.trim().split('\n')
    .find(l => l.trim() && !l.startsWith('%%'));
  const type = line && line.trim().split(/[\s:({]/)[0].toLowerCase();
  const c = pre.closest('.diagram-container');
  if (c && type) c.dataset.diagramType = type;
});
function pickSizer(svg) {
  const c = svg.closest('.diagram-container');
  const type = (c && c.dataset.diagramType || '').toLowerCase();
  const role = (svg.getAttribute('aria-roledescription') || '').toLowerCase();
  return (UNCLAMPED_TYPES.has(type) || UNCLAMPED_TYPES.has(role))
    ? sizeSvgFit : sizeSvg;
}
```

For the unclamped types we also set `useMaxWidth: false` in
`mermaid.initialize`; without it Mermaid emits `width="100%"` and the
diagram collapses to the container's current width rather than its natural
layout. `sizeSvgFit` also prefers `viewBox` over the `width`/`height`
attributes (which may still be `"100%"`) to get true content geometry.

### Timeline: width-dominant fill

Even with `sizeSvgFit`, Mermaid's `timeline` diagrams look too small because
their natural `viewBox` contains a lot of vertical whitespace above the
title and below the bottom connectors. Height-based fit therefore picks a
scale dominated by that empty space, leaving small text.

For `timeline` specifically we use `sizeSvgFillWidth`: set `width =
availW`, let `height = auto` (browser preserves viewBox aspect), and cap
with `max-height: availH`. The diagram fills the panel's full width and
scales its fonts up proportionally, which is what we want for a readable
roadmap.

```js
const WIDTH_FILL_TYPES = new Set(['timeline']);
```

Add other diagram types here if they show the same "shrunk by vertical
whitespace" symptom.

Flowcharts, sequence diagrams, state diagrams, class diagrams, ER diagrams
and others continue through the clamped `sizeSvg` path untouched.

If a new Mermaid diagram type turns up that also looks stuck tiny, add its
`aria-roledescription` value to `UNCLAMPED_TYPES` rather than loosening the
flowchart clamp.

## File-based SVG figures

The fix above applies **only to Mermaid-generated SVGs**. The JS selector
is scoped by `svg[id^="mermaid"]`, because Mermaid gives every rendered SVG
an id like `mermaid-123`.

File-based SVGs (`layout: figure` with `src: foo.svg`, or SVG content used in
two-column columns) are treated differently:

1. They pass through `compiler/renderers/svg.py::_normalize_svg_dimensions`,
   which rewrites the root `<svg>` tag with `width="100%" height="auto"` so
   the browser scales the SVG responsively while preserving the author's
   `viewBox` (aspect ratio and internal font sizes).
2. They are **not** processed by the font-size clamping JS. The author's
   `font-size` choices in the SVG file are respected — we don't attempt to
   enforce a 20–24pt band on content we didn't generate.

Rationale: a file-based SVG is a designed asset. Overriding its font by
scaling the whole SVG would distort the author's intended proportions. If a
file-based SVG's text is too small or too large for the slide, fix it in the
SVG source rather than post-processing in the browser.

## Files touched

- `compiler/templates/base.html.j2`
  - `mermaid.initialize({ themeVariables: { fontSize, fontFamily } })`
  - RAF-based layout-settle wait after `mermaid.run()`
  - `sizeSvg(svg, availW, availH)` helper with clamped scale
  - Scoped selectors: `svg[id^="mermaid"]` for both standalone and
    two-column diagram slides
  - Panel background (`--fig-panel`) added to `.slide-diagram` and
    `.slide-two-column` diagram containers (separate change, same file)

## How to tune

If the font band needs to change:

- Edit the three constants at the top of the Mermaid post-render block in
  `base.html.j2`:
  ```
  const NATURAL_PT = 22, MIN_PT = 20, MAX_PT = 24;
  ```
- Also update `themeVariables.fontSize` in `mermaid.initialize` to match
  `NATURAL_PT` (the two must stay in sync — the clamp is relative to the
  rendered natural font).
