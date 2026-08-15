# CSS controls — scaling text, figures, and chrome

Every key here is optional. Ranges are enforced by the schema: out-of-range values fail
validation with a message, they do not clamp silently. Unknown keys are rejected outright
(`extra='forbid'`), so a typo is an error, never a no-op.

Two scopes:

- **Deck metadata** — the first YAML block, applies to every slide.
- **Per slide** — that slide's frontmatter, same indentation as `layout:`.

**Per-slide values replace the deck value on that slide. They do not multiply.**

---

## Text

| Key | Scope | Range | Default | Effect |
|---|---|---|---|---|
| `title_scale` | deck + slide | 0.75 – 4.0 | `1.0` | Heading band: slide titles and subtitles. Emitted as `--title-scale`. |
| `content_scale` | deck + slide | 0.75 – 4.0 | `1.0` | Body band: bullets, prose, code, captions, tables. Emitted as `--content-scale`. |
| `title_font_size` | deck | — | `2.4rem` | Base title size the scale multiplies. Any CSS length. |
| `title_top_margin` | deck | — | `0.5rem` | Space above the title. Any CSS length. |

Splitting the two bands is the point: a slide with one dense table wants
`content_scale: 0.9` without shrinking its heading.

```yaml
---
layout: table
title: Six-case probe results
content_scale: 0.85      # this slide only; every other slide keeps the deck value
---
```

## Math

| Key | Scope | Range | Default | Effect |
|---|---|---|---|---|
| `math_display_scale` | deck + slide | 0.75 – 2.0 | `1.0` | Size of `$$…$$` block math relative to body text. |
| `math_display_center` | deck + slide | — | `true` | Center display equations. |
| `math_display_color` | deck + slide | — | unset | CSS color for block MathML, e.g. `cyan` or `#6cf`. |

These are **top-level** slide keys. Nested under `title:` they are silently ignored —
a common authoring mistake.

## Figures and diagrams

| Key | Scope | Range | Default | Effect |
|---|---|---|---|---|
| `figure_scale` | deck + `figure` / `figure-wide` | 0.25 – 4.0 | `1.0` | On `figure`: viewport-height and width caps. On `figure-wide`: `zoom`/`transform: scale` on the media — see `FIGURE_WIDE.md`. Emitted as `--figure-scale`. |
| `panel_scale` | `diagram`, `two-column` | 0.2 – 1.0 each | unset | Shrinks the diagram **panel**, not the diagram. One fraction for both axes, or `[horizontal, vertical]`. |
| `mermaid_scale` | any slide | 0.25 – 4.0 | compiler default | Multiplier on the rendered Mermaid SVG. Still capped to the panel. |
| `mermaid_scale_mode` | any slide | `measured` \| `fit` | compiler default | `measured` targets a readable on-screen label size; `fit` only fits the panel. See `MERMAID_SCALE_FIX.md` for the reasoning. |

`panel_scale` and `mermaid_scale` solve different problems. A diagram that is too small
inside a correctly-sized panel wants `mermaid_scale`; a panel crowding the slide edges
wants `panel_scale`.

```yaml
---
layout: diagram
title: Build pipeline
alt_text: "Four-stage pipeline from source to deployed site"
panel_scale: [0.9, 0.75]     # narrower and much shorter panel
mermaid_scale: 1.2           # bigger diagram inside it
---
graph LR
  A[Source] --> B[Compile] --> C[Verify] --> D[Deploy]
```

## Page chrome

| Key | Scope | Range | Default | Effect |
|---|---|---|---|---|
| `view_scale` | deck | 0.25 – 4.0 | `1.0` | In-page view scale for slide content. **Not** browser zoom. Written to `<html data-deck-default-view-scale>`. |
| `remember_view_scale` | deck | — | `false` | Persist viewer scale changes in `localStorage`. |
| `footer_scale` | deck | 0.5 – 2.5 | `1.0` | Font size and padding of the fixed bottom bar (page counter, view-scale control, go-to). |
| `footer_inset` | deck | — | `0.5in` | Distance from the viewport bottom to the footer. Any CSS length. |
| `accent_color` | deck | — | `#f0a500` dark, `#b06800` light | Sets `--accent`, used in ~22 places. Verify contrast if you change it. |

`view_scale` is the one to reach for when a deck is projected in a large room: it scales
content inside the page, so the layout still reflows correctly, unlike browser zoom.

## Debugging

| Key | Scope | Effect |
|---|---|---|
| `figure_layout_debug` | deck | Red borders separating the figure panel from the image or diagram container. Also available as `--figure-layout-debug` on the command line. Never ship a deck with it on. |

---

## Precedence

1. Compiler defaults
2. Deck metadata
3. Slide frontmatter — **replaces** the deck value, does not compose with it

The one exception is `figure_scale` on `figure-wide`, which applies a CSS `zoom`, so it
interacts with the browser's own scaling — check that one visually.

## Accessibility floor

Scaling down is the fastest way to break WCAG. `accessibility-core.md` requires body text
at 21 px and code at 20 px minimum. `content_scale: 0.75` on a deck whose base is already
21 px lands at ~16 px, which fails. Prefer splitting a crowded slide into two — that is
what `--detail` exists for.

## See also

- `FIGURE_WIDE.md` — how `figure_scale` behaves on `figure-wide`
- `MERMAID_SCALE_FIX.md` — the constraints behind `mermaid_scale_mode`
- `ANIMATION.md` — `bullet_animation` and `bullet_focus`
- `accessibility-core.md` — contrast and minimum sizes
