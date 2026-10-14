# md_to_yaml — usage

Source material (or a topic) → validated YAML slide deck → ADA-compliant HTML.

```
/md_to_yaml <flavor> [--source PATH...] [options]
/md_to_yaml --compile-only deck.yaml
/md_to_yaml --help
```

## Flavors — pick one, or you'll be asked

| Flavor | Use for |
|---|---|
| `explanatory` | Concept-first teaching. Defines terms, one idea per slide. |
| `implementation` | Imperative bullets, concrete artifacts, code slides. |
| `tutorial` | Numbered steps with expected outcomes per step. |
| `mathematical` | Formula-first, display math, `proof` slides. |

## Options

| Option | Values | Default | Effect |
|---|---|---|---|
| `--source` | `file.pdf`, `folder/`, `file.md`, or several space-separated | topic knowledge only | Material to convert. Images in a folder get captions and alt text written to `<folder>-captions.yaml`. |
| `--detail` | `concise` `standard` `rich` | `standard` | Whole-deck size. **More slides, never denser slides.** |
| `--tone` | `lecture` | flavor default | Longer, sentence-like bullets. |
| `--figures` | `folder/` | auto-created beside output | Pre-existing `.png/.jpg/.svg/.mmd` to scan and reference. |
| `--output-dir` | `folder/` | first source's parent | Where the `.yaml` and `.html` land. |
| `--name` | `my-deck` | first source's stem | Overrides the auto basename. |
| `--append` | `deck.yaml` | — | Extend an existing deck instead of starting one. |
| `--topic` | `"Section Title"` | — | With `--append`: which section to target. |
| `--task` | `"add proof slides"` | — | With `--append --topic`: the transformation, interleaved into that section. |
| `--compile-only` | `deck.yaml` | — | Recompile an edited YAML. No content generation. |

Output is named `<basename>-<flavor>-<model>-<YYYYMMDD_HHMM>.yaml` / `.html`.

## Compiling by hand

```bash
cd ~/.claude/skills/md_to_yaml
export PYTHONPATH="$(pwd)"
python3 -m compiler deck.yaml out.html --embed-images
```

| Compiler flag | Effect |
|---|---|
| `--embed-images` | Base64 every image into the HTML. Required when sources span directories. |
| `--include-skipped` | Render slides marked `skip: true` (omitted by default). |
| `--no-notes` | **Omit speaker notes from the HTML entirely.** |
| `--figure-layout-debug` | Red borders on figure panels, for diagnosing layout. |
| `--bake-mermaid` | Pre-render Mermaid to inline SVG at compile time (needs `mmdc`). |

### Speaker notes and who can read them

A slide's `notes:` field is **never displayed** — no presenter mode, no toggle. By
default the compiler still writes it into the HTML as a hidden `<aside>`, invisible on
screen but plain in View Source.

So: read notes from the YAML, and compile **any deck you hand to an audience** with
`--no-notes`. With that flag the audience copy and your own copy are byte-identical,
and `cp` is enough to publish.

```bash
python3 -m compiler deck.yaml handout.html --embed-images --include-skipped --no-notes
```

## First run

```bash
python3 -m venv ~/.venvs/md_to_yaml
~/.venvs/md_to_yaml/bin/pip install -r ~/.claude/skills/md_to_yaml/requirements.txt tinycss2
```

`tinycss2` is not in `requirements.txt` but `bleach` needs it. A Homebrew or
system Python will refuse a plain `pip install` (PEP 668) — use the venv.

## Keys you can put in the YAML

A deck file has **two kinds of frontmatter**, and a key belongs to one, the other, or
both. Unknown keys are rejected outright, so a key in the wrong block is an error, not a
silent no-op.

```yaml
---
title: My deck              # ── DECK frontmatter: the first block, whole deck
theme: dark
content_scale: 1.1
---

---
layout: content             # ── SLIDE frontmatter: one per slide
title: First slide
content_scale: 0.9          #    overrides the deck value on THIS slide only
---
- body goes below the closing ---
```

**Deck block only** — 19 keys. `theme` · `font` · `date` · `flavor` · `accent_color` ·
`title_font_size` · `title_top_margin` · `view_scale` · `remember_view_scale` ·
`autofit_floor` · `autofit_widen_max` · `autofit_title_floor` ·
`footer_scale` · `footer_inset` · `macros` · `bake_mermaid` · `figure_layout_debug` ·
`animation_defaults` · `gsap_script_url`

**Every slide** — `layout` (required) · `title` · `subtitle` · `notes` · `skip` ·
`mermaid_scale` · `mermaid_scale_mode`

**Both blocks** — set once on the deck, override on any slide: `title_scale` ·
`content_scale` · `blockquote_scale` · `math_display_scale` · `math_display_center` · `math_display_color` ·
`figure_scale`. **A slide value replaces the deck value; it does not multiply.**
`title` and `author` also appear in both, but they are different things — the deck's
title and author, versus this slide's.

**Only on certain layouts** — using one elsewhere is a validation error:

| Key | Valid on |
|---|---|
| `src`, `alt_text` | `figure`, `figure-wide`, `diagram` (`alt_text` required there) |
| `figure_scale` | `figure`, `figure-wide` |
| `caption` | `figure-wide`, `table` |
| `headers`, `rows`, `row_headers` | `table` |
| `left`, `right`, `proportion` | `two-column` (`proportion` also `figure-wide`) |
| `panel_scale` | `diagram`, `two-column` |
| `language`, `line_numbers` | `code` |
| `attribution` | `quote` |
| `description` | `hero` |
| `author` | `title` |
| `bullet_animation`, `bullet_focus` | `content`, `transcribe` |

Full reference for the two families the generator does not set for you:

- **`CSS_CONTROLS.md`** — scaling text, figures and chrome, with each key's scope,
  range, default, and the precedence rule.
- **`ANIMATION.md`** — `bullet_animation` (staggered reveal) and `bullet_focus`
  (walk the list with `j`/`k`), plus `animation_defaults` and `gsap_script_url`.
  **Read its status note: these are inert in the current copy.**

## More

- `USAGE.md` — every flag with worked invocations
- `SKILL.md` — the authoring rules the generator follows
- `layout_rules_llm.md` — the 15 layouts and when each applies
- `equations.md` — math, and the YAML quoting traps around LaTeX
- `mermaid-best-practices.md` · `figure_rules.md` · `svg.md` — diagrams and figures
