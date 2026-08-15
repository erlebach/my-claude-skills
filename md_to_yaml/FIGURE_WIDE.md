# Layout `figure-wide` (summary + band + columns)

Narrative reference for **`layout: figure-wide`**: the gray **band** around the central graphic, **flex** behavior, and **`figure_scale`**.  
Implementation lives in **`compiler/templates/figure-wide.html.j2`** and **`compiler/templates/base.html.j2`** (search **`slide-figure-wide`**, **`figure-wide-`**).

## Structure

1. **Title** (slide **h2**)
2. Optional **summary** (Markdown **body** top section) — content scale / muted style
3. **Figure band** (`.figure-wide-figure-wrap`) — **`src`**, **alt text**, **Mermaid** / **SVG** / **raster** in `.figure-wide-media`
4. **Below** (`.figure-wide-below`) — two columns (or one) parsed from level-2 headings in the body

The slide is **`100vh`** with **`1in` padding**; the middle column **flex** stack shares height between the summary, the band, and the footer.

## Panel height (gray container)

- **`min-height: clamp(12rem, 36vh, 62vh)`** on **`.figure-wide-figure-wrap`** so the **band does not collapse** to zero when the **summary + footer** use most of the viewport, and the default is **taller** than the earlier `28vh / 50vh` cap.
- **`flex: 1 1 auto`** and **`flex-shrink: 0`** on the wrap so the figure region still participates in the flex **grow/shrink** contract.
- **`overflow: visible`** on the wrap so **scaled** graphics (see below) are not **clipped** by the rounded box.

## `figure_scale` and `--figure-scale`

- The compiler sets **`--figure-scale`** on the slide **`<section>`** for **`layout: figure-wide`** (deck default **0.25–4.0**, optional **`figure_scale`** in slide frontmatter — same as **`layout: figure`**).
- **Scaling the graphic** uses the same approach as **layout: figure** with **`.figure-asset-wrap--fill`**: a **base** **layout** box, then **visual** scale.
  - **Base box:** `max-width: 100%`, `max-height: 58vh` on **`.figure-wide-media`** **img** / **`.diagram-container svg`**
  - **Scale:** `zoom: var(--figure-scale, 1)` when **`@supports (zoom: 1)`** (e.g. Chromium), otherwise `transform: scale(var(--figure-scale, 1))` with `transform-origin: center`

### Why not `calc(100% * --figure-scale)` on `img`?

Rules like **`max-height: min(100%, calc(58vh * var(--figure-scale, 1)))`** or **`calc(100% * var(--figure-scale, 1))`** are **unreliable** for **`<img>`** in this **flex** stack: the **percentage** **height** used in **`calc(100% * …)`** often has an **indefinite** or **cyclic** base, so the browser may **drop** the **whole** declaration. Then **`--figure-scale`** looks **inert** even when set.

Using **`zoom` / `transform: scale`** avoids tying scale to a broken **%**-based **max-height** on the replaced element.

## Mermaid (`.mmd` / diagram source)

A **`forEach`** in **`base.html.j2`** (after **`mermaid.run`**) sizes **Mermaid** SVGs to **`.figure-wide-figure-wrap`** using **`FW_INSET`** (~40px). The **CSS** **zoom** / **transform** on **svg** still applies to the **rendered** diagram.

## YAML sketch

```yaml
---
layout: figure-wide
title: "The Gap between Today and Fault-Tolerance"
src: ./infographic.png
alt_text: "Infographic contrasting NISQ and FTQC eras; …"
figure_scale: 1.0   # optional; overrides deck default
proportion: 60/40
---
## Summary
Physical qubit counts are rising — but useful FTQC needs >100,000 high-fidelity qubits

## 2016-Today (NISQ)
- …

## 2028+ (FTQC)
- …
```

## Related project docs

- **[`CSS_CONTROLS.md`](../../../CSS_CONTROLS.md)** (repo root) — **Figure slide scale** and **`layout: figure-wide`** table
- **[`SKILL.md`](SKILL.md)** — high-level **figure_scale** / **typography** note

## Change history (summary, 2026-04-23)

| Topic | What changed |
|--------|----------------|
| Collapsed band | **`.figure-wide-figure-wrap`** had **`min-height: 0`**; flex could shrink the **figure** row to **0** — fixed with **`min-height` clamp** and **flex** tweaks. |
| `figure_scale` inert (early attempts) | **`min(100%, 58vh×scale)`** — when **100%** won, it **did not** include **scale**; later **`calc(100%×scale)`** on **img** — often **invalid** in browsers. |
| `figure_scale` (stable) | **Zoom** / **transform: scale** on **raster** + **file SVG** in **`.figure-wide-media`**, matching **figure --fill** behavior. |
| Taller default panel | **`clamp(12rem, 36vh, 62vh)`** on the wrap; **`.figure-wide-media`** **`align-self: stretch`**. |
| `figure_scale` on schema | **`FigureWideSlide`**: optional **`figure_scale`**; **`engine.py`**: same effective scale as **figure**. |

Recompile a deck with assets next to the YAML, for example:

```bash
cd path/to/that/folder
PYTHONPATH=/path/to/.claude/skills/md_to_yaml python -m compiler deck.yaml out.html
```

so **relative** **`src:`** paths resolve.
