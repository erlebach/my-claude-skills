# Slides

The author teaches with the slides, the interactives and the explainers together (author, 2026-11-16). The slides must therefore show the same story and the same pictures as the explainer, so that in class the author can move between a slide and the matching explainer section or interactive.

## The rule (decided 2026-11-16)

1. **Write the slides after the explainers.** Follow each explainer's order: one lesson's slides follow that lesson's explainer, section by section.
2. **Use the explainer's figures.** Each explainer section whose figure carries the idea gets a figure slide with that figure. Do not draw new figures for the slides.
3. **Add slides from the notes where the explainer is silent.** The explainers are short by design. Add a slide from the notes wherever a definition, the steps of a procedure, or an example that the explainer leaves out is needed (for example the Gaussian fraud score and the enrichment test in Module 7).
4. **Text and tables are not enough.** The Module 2–6 decks and the first Module 7 deck were text and tables only; the author asked why. A lecture deck needs the key pictures on screen, even when the explainer has them.

## How: export the explainer figures

The explainer build scripts draw every figure from the numbers script, so export them; never copy SVG from a generated page. Pattern: `build/module-07/build_slide_figures.py`.

- Import the explainer build scripts and call their figure functions. Some return `(svg, data)`; take the SVG.
- Interactive figures are exported in their **default state**. If another state is the lesson (for example power instead of FDR), export that state too, or keep a table slide for it.
- Make each file standalone: add `xmlns`, a `<title>` and a `<desc>` (the desc states the data, for screen readers), and a `<style>` with the explainer's light colors.
- **Scope the style** to a class on the root (`class="m7f"`, rules `.m7f text {…}`). The compiler inlines the SVG into the deck, and an unscoped `<style>` would apply to the whole deck.
- Copy the page rule `svg text { fill: var(--ink) }` into the scoped style. It decides which label colors show, so the slide then looks the same as the explainer.
- **Use PNG, not SVG, on the slide.** The compiler cleans an inlined SVG against an allowlist: it drops `<style>`, CSS `fill` in `style=`, `stroke-dasharray` and `font-weight`, so the figure loses its colors (bars turn black) and dashed lines. Render each standalone SVG to a PNG at twice the size with headless Chromium (`to_png()` in `build_slide_figures.py`), keep the SVG as the source, and put the PNG on the slide with the SVG's description as `alt_text`.
- **No body on a figure slide.** A figure slide without a body uses the pinned-panel mode, which fits the image below the title. With a body, the image keeps a fixed maximum height (576 px) and overflows into the text. Put the slide's message in a one-line title; a two-line title leaves the figure smaller. `figure_scale` does not fix the overflow.
- Write the files to `build/module-NN/slide-figures/` and reference them by absolute path in the deck YAML (`layout: figure`, `src:`, `alt_text:`). Compile with `--embed-images`.
- A defect found on a slide figure is fixed in the explainer script, then both are rebuilt (Module 7: a cut-off axis label on the 40 p-values figure).

## Compile and check

- Deck source: `build/module-NN/<unit>-explanatory-opus55-<YYYYMMDD>.yaml`. Output: `course_site/static/kits/module-NN/<unit>-slides.html`; set `materials.slides` in `unit.yaml`.
- Compile with `--embed-images --no-notes` (no speaker notes reach students), from a virtual environment with the md_to_yaml `requirements.txt` (the system Python lacks `markdown` and `tinycss2`).
- Validate, fix any run of 3 or more slides with the same layout, and run `check_autofit.py`: no slide may hit the floor, and none may cross an edge. Look at a screenshot of the fullest slides.
- Every number comes from the notes or the numbers script. The slides are part of the second source check (`verification.md` §3c).
