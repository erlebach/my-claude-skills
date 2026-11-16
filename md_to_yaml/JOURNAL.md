# md_to_yaml — Journal

Chronological log of features, bug fixes, and architectural decisions.

## 2026-11-16 — SVG figures keep their styles; figure slides with a body fit

Found while making the CAP5771 Module 7 deck, whose figures come from explainer pages.

- **SVG `<style>` kept, cleaned and scoped** (`compiler/renderers/svg.py`). bleach removed `<style>`, CSS `fill`/`stroke` in `style=`, and `stroke-dasharray`/`font-weight`, so a page-drawn SVG rendered with black bars, solid lines and plain labels, with no message. Now: the `<style>` blocks are extracted before bleach, cleaned with tinycss2 (at-rules and external `url()` dropped, `url(#…)` kept), scoped to `#<slide-id>-svg` (with a `#id:is(first)` form for selectors that name the root), and put back. SVG paint properties are allowed in `style=`, and paint attributes on shapes and text. The compiler prints a warning naming whatever the sanitizer still removes.
- **Figure slides with a body** (`base.html.j2`). Only figure-only slides had the pinned panel; with a body the image kept the fixed 576/612 px caps and painted over the body text (66–131 px on 1280×720). New class `figure-with-body`: the content area is a column, the body keeps its height, the figure panel takes the rest (`min-height: 60%`), and the media fits it (`max-height: 100%`, no zoom). Tested on a 4-slide deck (SVG with style + body, PNG + body, figure-only, two-line title + two-item list); a 39-slide deck with figure-only slides gives the same autofit report as before.
- **Upstream:** the project copy under `~/src/2026/claude-code/n8n/md_to_yaml/.claude/skills/md_to_yaml` is older than this skill copy (base.html.j2 and engine.py differ from before this change); port both changes when the two are synced.

## 2026-08-26 — Autofit fits title and content separately; limits move to the deck front matter

- **`autofitAll()` in `base.html.j2` rewritten.** The old routine zoomed the whole `<section>` by a
  ratchet computed from one stale measurement, so a title's size depended on how many bullets sat
  under it (35–70 px across one deck) and slides landed 26–50 % smaller than they needed to be.
  Now the heading stack keeps its declared size (shrunk, floor 0.8, only if it does not fit one
  line) and `.slide-content-area` is zoomed by bisection to the largest value that fits the
  height the title leaves. Measured on nine decks: h2 titles 70–86 px, no boundary offenders.
- **Two things measurement found that the analysis had not.** A flex item's `min-height:auto` let
  the content area grow instead of reporting overflow (pinned to 0 during fit); a table scrolls
  inside its wrapper rather than overflowing (a scrolling wrapper now counts as overflow, so
  tables shrink to fit as before).
- **Decoupling the title costs the content height.** An 86 px title band on a 720 px canvas is
  ~20 % of the content's budget, so dense slides keep their old body size and gain a full-size
  title rather than gaining body size. The lever is `title_scale` on the deck, not the floor.
- **Deck keys `autofit_floor` (0.5), `autofit_widen_max` (1.6), `autofit_title_floor` (0.8)** —
  `CSS_CONTROLS.md` § Autofit. Below the floor the content scrolls under the title and the slide
  is reported (`console.warn`, `window.__mdToYamlAutofitReport()`).
- **`check_autofit.py`** (skill root) prints the per-slide report headlessly; exit 1 on a floored
  slide. `accessibility-core.md` records the fixed-height exception the canvas format needs.
- **`blockquote_scale`** (deck + slide, 0.25–4.0, default 1.0) multiplies `>` blockquotes on top of
  `content_scale`. Added for a slide whose 44px quote was what forced the whole content area to
  the floor; the author wants per-element control for special cases until a general rule exists.

## 2026-05-06 — Project initialized

- Project created at `/Users/erlebach/src/2026/claude-code/n8n/md_to_yaml/standalone/skills/md_to_yaml`
