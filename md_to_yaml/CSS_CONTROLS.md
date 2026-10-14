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
| `content_scale` | deck + slide | 0.25 – 4.0 | `1.0` | Body band: bullets, prose, code, captions, tables. Emitted as `--content-scale`. Code is `20px × 1.35 × content_scale`, so values below ~0.75 go under the 20px ADA floor — deliberate, and yours to judge. |
| `blockquote_scale` | deck + slide | 0.25 – 4.0 | `1.0` | `>` blockquotes only, **on top of** `content_scale`. A blockquote is 44px against 28px body, so `0.64` makes it body-sized. Emitted as `--blockquote-scale`. A large quote is the usual reason a `content` slide overflows and is shrunk by the autofit; this key lets the quote come down while the prose around it stays up. |
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

## Autofit

A slide whose content does not fit the 1280×720 canvas is shrunk at view time by
`autofitAll()` in the compiled deck. Title and content are fitted **separately**: the title
keeps its declared size (`title_scale`) and is shrunk only if it does not fit one line; the
content area is zoomed to the largest value at which it fits the height the title leaves.
A slide that fits is not touched. These three deck keys bound that process; they are
written to `<html data-deck-autofit-*>` and read by the deck's JavaScript.

| Key | Scope | Range | Default | Effect |
|---|---|---|---|---|
| `autofit_floor` | deck | 0.25 – 1.0 | `0.5` | Smallest zoom applied to the content area. Below it the content is left at the floor, starts under the title, and the section scrolls; the slide is reported in the browser console and by `check_autofit.py`. Raise it to be told sooner that a slide is over-full; lower it to let dense slides shrink further. |
| `autofit_widen_max` | deck | 1.0 – 3.0 | `1.6` | How much wider than the canvas the content area may become while shrinking, so text re-wraps into fewer lines. Bounds line length: at 1.6 the longest line is about 90 characters. `1.0` never widens — a wide table then cannot fit at any zoom. |
| `autofit_title_floor` | deck | 0.5 – 1.0 | `0.8` | Smallest zoom applied to a title that does not fit on one line. A title that still does not fit at the floor takes two lines at full size instead. |

The lever that matters most is not here: **`title_scale`**. The reserved title band costs
the content its height on every slide, so a deck whose bodies come out small is usually a
deck whose title is too large, not one whose floor is too high. `title_scale: 0.8` on the
deck gives uniform 69 px titles (at the default `--font-scale` 1.35) and 6–13 % larger
bodies on the slides that were being shrunk.

```yaml
---
title: The AI contract
theme: dark
title_scale: 0.8          # uniform 69px titles, more height for the content
autofit_floor: 0.5        # defaults shown; omit any you do not want to change
autofit_widen_max: 1.6
autofit_title_floor: 0.8
---
```

**Check a compiled deck:** `python3 check_autofit.py deck.html` (skill root; needs
`playwright` with Chromium) prints the zoom applied to every slide, the rendered title
size, and `FLOOR` on any slide that did not fit. Exit status 1 if one did. That is the
signal to split the slide; the autofit will not hide it.

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
