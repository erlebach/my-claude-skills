---
name: md_to_yaml
description: Generate YAML DSL slide decks from PDF or folder input, then compile to ADA-compliant HTML using the bundled compiler in this skill folder. Use when the user wants to convert source material into a structured YAML slide deck (15-layout DSL including proof). Supports optional --detail (concise | standard | rich) to control overall deck length and how many slides are allocated per topic; outputs validated YAML plus compiled HTML; runs portably from the skill directory.
---

# YAML DSL Slide Generator

## `--help` — answer and stop

If the invocation is `/md_to_yaml --help` or `/md_to_yaml -h` (with no other
arguments), **read `HELP.md` from this skill folder and print it verbatim as your
entire reply.** Do not generate a deck, do not read any other file, do not ask a
follow-up question. `HELP.md` is the single source of the usage screen — when a flag
changes, edit that file.

Generate validated YAML DSL slide decks from source material, then compile to ADA-compliant HTML. Uses a **15-layout** type system with schema validation and accessibility-oriented HTML.

**This skill folder contains a full copy of the `compiler/` and `schema/` packages.** Run validate/compile **from this directory** so imports resolve (`compiler`, `schema`). That keeps the skill **portable** across machines without relying on an external repo path.

## How to Invoke

```
/md_to_yaml <flavor> --source path/to/file.pdf
/md_to_yaml <flavor> --source path/to/folder/
/md_to_yaml <flavor>                              -- generate from topic knowledge
```

Add **`--detail`** (optional) on any form above:

```
/md_to_yaml <flavor> --detail concise   --source path/to/folder/
/md_to_yaml <flavor> --detail standard  --source path/to/file.pdf
/md_to_yaml <flavor> --detail rich      --source path/to/folder/
```

**Extend an existing deck** with `--append`:

```
/md_to_yaml <flavor> --append path/to/existing.yaml
/md_to_yaml <flavor> --append path/to/existing.yaml --source path/to/more/material/
/md_to_yaml <flavor> --append path/to/existing.yaml --topic "deeper explanation of X"
/md_to_yaml <flavor> --append path/to/existing.yaml --source path/to/folder/ --topic "deeper explanation of X"
```

**Transform a section** of an existing deck with `--append` + `--topic` + `--task`:

```
/md_to_yaml <flavor> --append path/to/existing.yaml --topic "Section Title" --task "add diagrams"
/md_to_yaml <flavor> --append path/to/existing.yaml --topic "Section Title" --task "add a confusion matrix and worked example"
/md_to_yaml <flavor> --append path/to/existing.yaml --source notes.md --topic "X" --task "add proof slides for each theorem"
```

`--topic` locates the target section (matched against divider/title text). `--task` describes the **transformation** to apply — what new slides to insert and where within that section. Without `--task`, `--append` generates slides about the `--topic` subject and inserts them after the section divider. With `--task`, it reads the existing section slides and inserts new slides **interleaved** at the most logical positions within the section.

**Recompile without regenerating content** with `--compile-only`:

```
/md_to_yaml --compile-only path/to/existing.yaml
```

**Multiple sources with explicit output location or name:**

```
/md_to_yaml <flavor> --source path1 path2 --output-dir /path/to/output/
/md_to_yaml <flavor> --source path1 path2 --name my-deck-name
```

**Figures folder (`--figures`):**

```
/md_to_yaml <flavor> --source path/to/folder/ --figures path/to/existing-figs/
```

**`--figures path/`** — folder of pre-existing figure files (`.jpg`, `.png`, `.svg`, `.mmd`) to scan and optionally reference. LLM-generated Mermaid/SVG files are also written here. If omitted, defaults to `<output_dir>/<source_basename>-<YYYYMMDD_HHMM>-figures/`, created only if the deck contains at least one figure.

**Flavors:** `explanatory`, `implementation`, `tutorial`, `mathematical`. If no flavor is given, ask which they want before proceeding.

**Tone modifier:** add `--tone lecture` to any flavor for more narrative, sentence-like bullets (see `creating_good_presentations.md`). Examples:

```
/md_to_yaml mathematical --tone lecture --source path/to/folder/
/md_to_yaml tutorial --tone lecture --source path/to/file.pdf
```

If `--tone` is omitted, use the default bullet style for the chosen flavor.

**Detail:** `concise`, `standard`, or `rich` — controls **how many slides** you plan for the **whole deck** (more topics and sub-topics get their own slides), **not** stuffing more bullets onto one slide. See **Detail level (`--detail`)** below. If the user does not pass **`--detail`**, use **`standard`**. If they ask for “more material than usual” or “I will trim later,” use **`rich`** (or ask which level they want).

## Bundled compiler (run from this folder)

1. **Install dependencies** (once per environment):

   ```bash
   cd /path/to/this/skill/md_to_yaml
   pip install -r requirements.txt
   ```

2. **Set `PYTHONPATH`** to this folder so `python3 -m compiler` resolves `compiler` and `schema`:

   ```bash
   cd /path/to/this/skill/md_to_yaml
   export PYTHONPATH="$(pwd)"
   python3 -m compiler path/to/deck.yaml path/to/out.html --embed-images
   ```

   Or use the wrapper (same effect):

   ```bash
   cd /path/to/this/skill/md_to_yaml
   ./compile.sh path/to/deck.yaml path/to/out.html --embed-images
   ```

3. **Paths:** `input.yaml` and `output.html` may be **absolute** or relative to your current working directory. Image `src` values in YAML are resolved relative to the **output HTML file’s directory** when using `--embed-images` (see compiler `engine.py`).

**Maintainers:** The `compiler/` and `schema/` trees are **copies** of the upstream `md_to_yaml` project. Re-copy from that project when fixing compiler bugs or updating templates.

## Source Types

### No `--source`

Generate slides from topic knowledge only.

### `--source path/to/file.pdf`

Path ends in `.pdf`. Extract text/structure (Read tool or PDF skill) to inform slide topics, figures, and tables.

### `--source path/to/folder/`

1. Glob markdown and image files in the folder.
2. Process images — see **Image caption/alt_text list** below.
3. Read markdown for content extraction.

### `--source path1 path2 …` (mixed: folders and/or individual markdown files)

Pass any combination of folder paths and individual `.md` files as space-separated arguments. Process each entry:
- **Folder:** Glob `**/*.{md,jpg,jpeg,png,gif,webp}` inside it; apply the image and markdown steps below.
- **Individual `.md` file:** Read it directly for content extraction.

Deduplicate paths. Process images once even if referenced from multiple sources.

**Output directory for multiple sources:** determine `<output_dir>` as follows:
- If `--output-dir path/` is given → use that directory.
- If all sources share a common parent directory → write output there.
- Otherwise → write to the **first source's parent directory**.

**Basename for multiple sources:** use the **first source**'s file stem or folder name as `<source_basename>`. If `--name <stem>` is given, that overrides `<source_basename>` entirely.

**Image paths in YAML for multi-folder sources:** record each image's **absolute path**. When writing `src` values in YAML for images that are NOT under `<output_dir>`, use the **absolute path**. This ensures `--embed-images` can locate and base64-encode them regardless of where the output HTML lives (Python's `os.path.join` ignores `base_dir` when `src` is absolute). Always use `--embed-images` when sources span different directories to avoid broken image references in the output HTML.

### Image caption/alt_text list

For **every image file** (`.jpg`, `.jpeg`, `.png`, `.gif`, `.webp`) found in any source folder:

1. **Check for an existing caption list** alongside the folder: look for a file named `<folder_name>-captions.yaml` (or `captions.yaml` inside the folder). If it exists, load it.
2. **For each image NOT already in the list:**
   a. Read the image with the Read tool (multimodal — the compiler sees it visually).
   b. Generate:
      - `caption:` — a one-sentence descriptive caption suitable for use as a slide figure caption.
      - `alt_text:` — a screen-reader-quality description (ADA/WCAG 2.1 AA: describe content, not appearance; include all data-bearing text visible in the image).
   c. Append the entry to the list.
3. **Write the caption list** back to `<folder>-captions.yaml` (next to the folder) so it persists and can be reviewed/edited by the user.
4. **Use the list** when generating YAML: any `figure` or `diagram` slide that references an image from the source folder must pull its `alt_text` (and optionally `caption`) from this list.

**Caption list format:**
```yaml
# <folder_name>-captions.yaml
images:
  - file: relative/path/to/image.jpg
    caption: "One-sentence figure caption."
    alt_text: "Detailed description for screen readers."
  - file: relative/path/to/other.png
    caption: "…"
    alt_text: "…"
```

## Detail level (`--detail`)

**Purpose:** shift **overall deck size** by changing how aggressively you **split** the source into slides. **Per-slide rules still apply:** one main idea per slide, bullet ceilings, layout variety — detail is **more slides**, not denser slides.

| Level | When to use | Slide budget vs `standard` |
|-------|-------------|----------------------------|
| **`concise`** | Short talk, executive summary, or user explicitly wants a **small** deck | **Fewer** sections and **lower** slide counts per topic band (see step 8). Omit optional “limits / outlook / side-by-side compare” unless essential. |
| **`standard`** | Default when **`--detail`** is omitted | Baseline bands in step 8 (historical skill behavior). |
| **`rich`** | Surveys, long sources, teaching packs, or user wants **extra slides to delete by hand** | **More** slides per topic band; add **section checkpoints**, **trade-off / limits** slides, **comparison** or **table** slides where the source supports it, and **flavor-appropriate** extras (see `creating_good_presentations.md` — *Detail level and flavor*). |

**With flavors:** same **`--detail`** knob for every flavor — `rich` + **tutorial** adds more **steps** and “verify / outcome” slides; `rich` + **implementation** adds more **code** and artifact slides; `rich` + **explanatory** adds more **state → illustrate → derive** cycles. Never compensate by **longer bullets**; add **slides** instead.

## Required Steps — Follow in Order

1. **Detect source type** (PDF, single folder, mixed folder+markdown, or topic-only) and load content. For mixed sources, process each path per **Source Types → mixed** above. Load or create caption/alt_text lists for all image files before planning slides.

1b. **`--append` mode** (if present): Read the existing YAML deck at the path given to `--append`. If `--source` is also given, load that material (folder globs, markdown files, or mixed paths) as supplementary content for the new slides. Identify the target section from `--topic` (if given) or from user context.

   - **Without `--task`:** Generate new slides *about* the `--topic` subject. Insert them after the matching section divider (or at the end of the deck if no divider matches).
   - **With `--task`:** Read all existing slides in the target section to understand current content and gaps. Apply the transformation described by `--task` (e.g. "add diagrams", "add a confusion matrix", "add proof slides"). Insert the new slides **interleaved at the most logical positions within the section** — not just appended after the divider. Use `--source` material (if given) to inform the new slides.

   Then skip forward to step 13 (validate the full deck, check layout variety, compile). Do **not** change the `BASE` name — overwrite the existing YAML and HTML in-place.

1c. **`--compile-only` mode** (if present): Read the YAML at the given path. Skip steps 2–10 (no content generation). Go directly to step 13 (validate), step 14 (layout variety check), and step 15 (compile to HTML). Use the YAML file's own stem as `BASE`.

2. **Identify flavor** (`explanatory`, `implementation`, `tutorial`, or `mathematical`). If not specified, ask. Also note whether `--tone lecture` was passed — if so, apply the lecture bullet style (longer, more sentence-like) throughout, regardless of flavor.

2b. **Resolve detail level** from **`--detail`**: `concise`, `standard`, or `rich`. If the user did not specify, default to **`standard`**. If they ask for a deck that is “more comprehensive than usual” or “extra slides to trim,” treat as **`rich`** (or confirm).

3. **Read presentation-quality guidance:** `creating_good_presentations.md` (narrative arc, bullets, flavor tone).

4. **Read accessibility rules** when available alongside this skill (confirm whether the file was read):

   ```
   Read ./accessibility-core.md
   ```

   If that path does not exist in the user’s environment, rely on `layout_rules_llm.md` (accessibility section) and strict **alt_text** on all figures/diagrams.

5. **Read flavor file** when available:

   ```
   Read ../ada-slides-general/flavor-{flavor}.md
   ```

   For the **`mathematical`** flavor, this file also contains the quantitative emphasis rules (formula-first slides, display math policy, YAML quoting for math). No separate step needed.

6. **Read layout rules:**

   ```
   Read {{skill_dir}}/layout_rules_llm.md
   ```

7. **Read equation guidelines:**

   ```
   Read {{skill_dir}}/equations.md
   ```

   Use `\log`, `\sin`, `\cos`, etc. (not bare `log`, `sin`) and brace arguments where helpful, e.g. `N\log{d}` (see **Standard functions** in `equations.md`).

8. **Plan slide depth per topic** — do **not** default to one slide per topic. Assess each topic’s complexity and allocate slides using the **detail level** from step 2b (still aligned with `ada-slides-general` — split, do not cram):

   **`--detail concise`**

   - **Simple / narrow:** **1** slide
   - **Moderate:** **1–2** slides
   - **Complex / deep:** **2–3** slides

   **`--detail standard`** (default)

   - **Simple / narrow:** **1** slide
   - **Moderate:** **2–3** slides
   - **Complex / deep:** **3–5** slides

   **`--detail rich`**

   - **Simple / narrow:** **1–2** slides (e.g. definition + example or quick “so what”)
   - **Moderate:** **3–5** slides (e.g. separate compare, limits, or diagram + explanation)
   - **Complex / deep:** **5–9** slides (sub-mechanisms, resource tables, failure modes, checkpoints — as the source allows)

   Each slide should present **one idea** clearly. When in doubt, prefer **more slides with less content** each — especially under **`rich`**.

9. **Plan slide structure:** apply step 8’s **detail-aware** depth plan when ordering slides; choose layouts using the decision tree in `layout_rules_llm.md`. Follow **progressive disclosure**: title/hero → content → diagram/two-column → content → summary. Apply **state → illustrate → derive** per objective (`creating_good_presentations.md`). Under **`rich`**, add **divider** or **summary** checkpoints between major parts so the deck stays navigable when long.

   If the deck will contain **`diagram`** or **`two-column`** slides with Mermaid, read:

   ```
   Read ./mermaid-best-practices.md
   ```

   This file covers canvas aspect ratios, two-column stacking rules, color budgets, alt text, and diagram type selection.

   If the deck will contain any figures (any `layout: figure`, `diagram`, or `two-column` with visuals), or if `--figures` was passed, read:

   ```
   Read ./figure_rules.md
   ```

   If the deck will contain **SVG diagrams with mathematical notation** (i.e. you plan to author an `.svg` file with `<foreignObject>` + MathML instead of Mermaid), read:

   ```
   Read ./svg.md
   ```

   Key rules from `svg.md`: use explicit pixel `width`/`height` on the `<div>` inside `foreignObject` (not `100%`) for reliable vertical centering; use **22 px** font for single-line boxes and **21 px** for two-line boxes; generate MathML via `latex2mathml` and strip the `xmlns` attribute.

9b. **Resolve figures folder and get timestamp** — follow `figure_rules.md § Resolving the figures folder` and `§ Scanning pre-existing files`.

10. **Generate YAML** following the **YAML Format Reference** below.

10b. **Write generated figure files and update `captions.yaml`** — follow `figure_rules.md § Generating figure files` and `§ captions.yaml`.

11. **Choose one basename** (shared by YAML and HTML):

    `BASE = <source_basename>-<flavor>-<llm_model>-<YYYYMMDD_HHMM>`

    **`<source_basename>`:** stem of the source file, or folder name. When `--source` has **multiple paths**, use the **first source**’s stem/folder name. If `--name <stem>` is given, that overrides `<source_basename>` entirely.

    **Timestamp rule:** use the `<YYYYMMDD_HHMM>` obtained in step 9b — do **not** re-run `date` here. This keeps the figures folder name and the YAML/HTML filenames in sync. Use the same **`BASE`** for both `.yaml` and `.html`. Bump the suffix only when the user wants a **new** revision artifact.

12. **Write YAML** to `<output_dir>/<BASE>.yaml`. Determine `<output_dir>` as follows:
    - If `--output-dir path/` was given → use that directory.
    - If all sources share a common parent directory → write output there.
    - Otherwise → write to the **first source’s parent directory**.
    - No `--source` (topic-only) → current working directory.

13. **Validate** (from **this skill directory**):

    ```bash
    cd /path/to/this/skill/md_to_yaml
    export PYTHONPATH="$(pwd)"
    python3 -c "from schema.parser import parse_deck_file; deck = parse_deck_file('<yaml_path>'); print('VALID:', len(deck.slides), 'slides')"
    ```

    - On failure: fix YAML and retry (up to 3 attempts).
    - Common issues: `body:` inside YAML frontmatter (move below `---`), invalid `layout`, missing `alt_text` on figure/diagram/two-column visual.

14. **Check layout variety:**

    ```bash
    cd /path/to/this/skill/md_to_yaml
    export PYTHONPATH="$(pwd)"
    python3 -c "from schema.parser import parse_deck_file; from compiler.validators import validate_deck; deck = parse_deck_file('<yaml_path>'); errors, warnings = validate_deck(deck); [print(w) for w in warnings]"
    ```

    Address **3+ consecutive same-layout** warnings when practical.

15. **Compile to HTML** (same **`BASE`** as in steps 11–12):

    ```bash
    cd /path/to/this/skill/md_to_yaml
    ./compile.sh '<source_dir>/<BASE>.yaml' '<source_dir>/<BASE>.html' --embed-images
    ```

    **Speaker notes:** a slide's `notes:` field is emitted into the HTML as a hidden
    `<aside>` that nothing in the page can display, but View Source shows. Add
    **`--no-notes`** for any deck handed to an audience; the notes stay in the YAML,
    where they are meant to be read. See `USAGE.md` — *Compiler flags*.

    To render slides marked `skip: true` (e.g. to produce a "full proof" version):

    ```bash
    ./compile.sh '<source_dir>/<BASE>.yaml' '<source_dir>/<BASE>-full.html' --embed-images --include-skipped
    ```

    Use absolute paths if the deck is outside this folder.

## YAML Format Reference

### Critical Rules

- **YAML and HTML filenames:** use the **same** basename for both — `<source_basename>-<flavor>-<depth>-<YYYYMMDD_HHMM>.yaml` and `.html` — so each compiled pair is unambiguous (see steps 11–15).
- Slide body content goes **below** the closing `---` of each slide’s frontmatter, **never** as a `body:` key in YAML.
- Slides are separated by `---` lines.
- First block is deck metadata (`title`, `author`, `date`, `theme`, `font`, …). **Which keys belong to the deck block, which to a slide, which to both, and which only to certain layouts: see `HELP.md` — *Keys you can put in the YAML*.** A key in the wrong block is a validation error, not a silent no-op.
- **Display math (`$$...$$`)** — optional deck metadata: **`math_display_scale`** (float, default `1.0`, allowed ~0.75–2.0) scales block-math font size relative to body text; **`math_display_center`** (bool, default `true`) centers display equations; **`math_display_color`** (string, e.g. `cyan` or `#6cf`, default omit) sets the CSS `color` of `$$...$$` block MathML in body/hero/columns/tables. Override per slide in that slide’s frontmatter with the same keys (`null` / omit = inherit from deck).
- **`math_display_*` placement:** use **top-level** keys in each slide’s YAML (same indentation as **`layout:`** / **`title:`**). Nesting under **`title:`** will not apply.
- **Typography & figure scale:** deck metadata **`title_scale`** / **`content_scale`** (~0.75–4.0) split heading-band vs body-band font sizes (see `CSS_CONTROLS.md`). Optional **per-slide** `title_scale` / `content_scale` **replace** the deck values on that slide (they do not stack). Deck **`figure_scale`** (~0.25–4.0) and optional per-slide **`figure_scale`** on **`layout: figure`** and **`layout: figure-wide`** set **`--figure-scale`** ( **`layout: figure`**: vh/width caps; **`layout: figure-wide`**: **zoom** / **transform: scale** on the media — see **[`FIGURE_WIDE.md`](FIGURE_WIDE.md)** ).
- **Figure layout debug:** deck **`figure_layout_debug: true`** *or* compile with **`--figure-layout-debug`** — red borders on **`layout: figure`** panel (`figure`) vs **`img`** / **`.diagram-container`**. Omit both for production.
- Valid **`layout`** values: `title`, `hero`, `content`, `transcribe`, `divider`, `figure`, `diagram`, `two-column`, `quote`, `comparison`, `code`, `steps`, `summary`, `table`, `proof`. Use **`content`** for normal presentation slides (omit deck **`flavor`**). Use **`proof`** for derivation/proof slides in the **`mathematical`** flavor (renders identically to `content`; distinguished for future visual styling). For **`transcribe_to_html`**, set **`flavor: transcript`** in metadata and use **`layout: content`** (and **`divider`** as needed); **`layout: transcribe`** remains valid as **legacy** with the same styling.
- **`skip: true`** on any slide: the slide is validated but excluded from compiled HTML. Use `./compile.sh ... --include-skipped` to render a version that includes skipped slides. Typical use: proof/derivation slides that are in the YAML for reference but not shown to the audience.
- `alt_text` is **required** on `figure` and `diagram` slides, and on `two-column` columns that use `figure` or `diagram`.
- `table` slides use `headers:` and `rows:` in YAML (not a Markdown table in the body). **Table cells support** `$...$` / `$$...$$` and light Markdown — the compiler runs **math then Markdown** on each cell (same as slide bodies). **Table math quoting:** use **single quotes** and **one** backslash per LaTeX macro (e.g. `'$\tilde{O}(\sqrt{N})$'`). **`'\\tilde'` / `'\\sqrt'`** in single quotes load as TeX **`\\`** (line break) + letters — `\sqrt` / `\tilde` will not render. See **`equations.md` (YAML quoting and LaTeX)**.
- **YAML quoting vs LaTeX** (titles, subtitles, captions, table cells, short frontmatter strings): In **`"…"`** scalars, YAML interprets escapes (`\t` → tab, so **`"\tilde"`** breaks; **`"\alpha"`** corrupts). Use **single quotes** for strings rich in **`$\command…$`**, e.g. `title: '$\alpha$ — scaling'`. In **single quotes**, do **not** double backslashes before macros — **`'\\sqrt'`** is wrong; use **`'\sqrt'`**. In **double quotes** only, a literal backslash is **`\\`** (e.g. `"$\\alpha$"` for one `\alpha` in the loaded string; **`"$\\tilde{O}(\\sqrt{N})$"`** for `\tilde` and `\sqrt`). Full tables and pitfalls: **`equations.md`** (**YAML quoting and LaTeX**).
- `diagram` slide body = raw Mermaid **without** triple-backtick fences.
- Avoid **3+ consecutive** slides with the same `layout`.
- **No bracket numeric citations on slides:** do not put `[12]`, `[42–44]`, etc. in slide bodies, **figure captions**, **`alt_text`**, **table cells**, or **hero `description`**. Name ideas on-slide; put references in the paper, speaker notes, or a bibliography document. Optionally add one **“good vs bad”** content slide teaching this rule.
- **Markdown bold:** write `**word**` with **no space** after `**` or before `**` (wrong: `** word**`).
- **Bullet subheaders (accent in HTML):** Put each bullet’s **subheader** in **one** `**...**` run. If the headline includes a formula, keep it inside the same run (e.g. `**Score matrix $L = \cdots$** …`), not `**Score matrix** $L = \cdots$` — otherwise the math stays body-colored. After the colon, keep explanation text and its math in normal weight unless you intend extra accent words. See **`equations.md` → Bullet subheaders** for good/bad examples.
- **Mermaid node labels:** avoid raw `|`, `<`, `>` in **unquoted** `[bracket]` labels (e.g. ket `|ψ⟩` breaks parsers). Use **double-quoted** labels: `["PQC prepares q, k, v registers"]`.
- **Sub-bullet indentation:** always use **4 spaces** to indent sub-items, never 2. The Python-Markdown parser requires 4-space indentation by default; 2-space indentation silently collapses sub-items into the parent list. Example — correct:
  ```
  - Parent item
      - Sub-item A
      - Sub-item B
  ```
  Wrong (2 spaces — sub-items rendered flat):
  ```
  - Parent item
    - Sub-item A
    - Sub-item B
  ```

### Examples

**Deck metadata + title slide:**

```yaml
---
title: Topic Title
author: Author Name
date: 2026-01-01
theme: dark
font: IBM Plex Sans
---

---
layout: title
title: Main Title
subtitle: Optional Subtitle
---
```

**Content slide with body:**

```yaml
---
layout: content
title: Key Concepts
---
- **Term one**: Definition here
- **Term two**: Another definition
- **Term three**: Third point
```

**Diagram slide (Mermaid, no fences):**

```yaml
---
layout: diagram
title: Process Flow
alt_text: "Flowchart showing the three-step process from input to output"
---
graph LR
  A[Input] --> B[Process]
  B --> C[Output]
```

**Two-column slide:**

```yaml
---
layout: two-column
title: Comparison
proportion: 60/40
left:
  type: diagram
  alt_text: "Architecture diagram showing system components"
  source: |
    graph LR
      A --> B --> C
---
- Supporting point one
- Supporting point two
```

**Table slide (structured fields, no body):**

```yaml
---
layout: table
title: Results Summary
caption: "Performance metrics across three methods"
headers: [Method, Accuracy, Speed]
rows:
  - [DBSCAN, "94.2%", "1.2s"]
  - [K-means, "91.5%", "0.8s"]
  - [OPTICS, "93.8%", "1.5s"]
---
```

**Figure slide** — `src` extension determines rendering automatically:

```yaml
# Raster image (.jpg / .png / .gif / .webp) → <img> tag
---
layout: figure
title: Experimental Results
src: path/to/figure.png
alt_text: "Bar chart comparing accuracy of three clustering algorithms"
---

# SVG file → inline SVG with ADA title/desc wrapper
---
layout: figure
title: System Architecture
src: path/to/architecture.svg
alt_text: "Architecture diagram showing three-tier system"
---

# Mermaid file (.mmd) → Mermaid JS rendering
---
layout: figure
title: Process Flow
src: path/to/flowchart.mmd
alt_text: "Flowchart showing the three-step ingestion pipeline"
---
```

Any figure type also works in `two-column` columns via `src:`:

```yaml
---
layout: two-column
title: Comparison
proportion: 60/40
left:
  type: figure
  src: path/to/chart.png       # raster
  alt_text: "Bar chart showing baseline performance"
right:
  type: figure
  src: path/to/diagram.mmd     # Mermaid from file
  alt_text: "Flowchart showing improved pipeline"
---
Supporting bullets or body text here.
```

**Steps slide:**

```yaml
---
layout: steps
title: Implementation Process
---
1. Set up development environment
2. Install dependencies from requirements.txt
3. Configure the schema validators
4. Run the test suite
```

**Quote slide:**

```yaml
---
layout: quote
title: Expert Perspective
attribution: "Dr. Jane Smith, Stanford University"
---
The key insight is that density-based methods naturally handle noise points without requiring a predefined number of clusters.
```

## Design Guidance

- **Slide depth:** match topic complexity to slide count (step 8) — avoid cramming; split rather than one dense slide per section.
- **Progressive disclosure:** hero/title → content → diagram/two-column → content → summary.
- **Layout selection:** decision tree in `layout_rules_llm.md`.
- **Rhetoric and bullets:** `creating_good_presentations.md`.
- **Math:** `equations.md` — use `$...$` inline; `$$...$$` when the equation is the focal point of the slide. For the **`mathematical`** flavor, see **`mathematical` flavor: quantitative emphasis** below — the `$$...$$` frequency rule is relaxed.
- **Mermaid:** see `mermaid-best-practices.md` (read in step 9) for canvas aspect ratios, two-column stacking rules, color budgets, alt text, and diagram type selection.
- **Figures and embedding:** `layout: figure` slides embed with `--embed-images` when `src` is relative to the output HTML directory. Two-column **figure** columns still emit a plain `<img src="...">` (not base64); prefer standalone `figure` slides for fully embedded decks.
- **Multi-folder sources:** when `--source` spans different directories, always compile with `--embed-images`. Write image `src` values as **absolute paths** in the YAML so the compiler can locate them regardless of where the output HTML lives.

### Hero slides

- Optional Markdown **body** below `---` for a short hook (1–2 sentences).
- Keep hero slides **sparse**—not a second content slide.

## Error Recovery

- **"body field in YAML frontmatter":** move body Markdown below the closing `---`.
- **"discriminator 'layout'":** use one of the valid `layout` values listed above.
- **"missing alt_text":** add descriptive `alt_text` on figure/diagram (and two-column visuals).
- After 3 failed validation attempts, show the error and ask the user for guidance.
