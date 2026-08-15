# md_to_yaml — Invocation Reference

Quick reference for all flags and modalities. For full rules, see `SKILL.md`.

---

## Flags

| Flag | Values / Syntax | Default | Purpose |
|------|----------------|---------|---------|
| `<flavor>` | `explanatory` `implementation` `tutorial` `mathematical` | ask if omitted | Content style and rhetorical approach |
| `--source` | `path/to/file.pdf`, `path/to/folder/`, or multiple space-separated paths | — (topic knowledge only) | Source material to convert |
| `--detail` | `concise` `standard` `rich` | `standard` | Overall deck size (more slides, not denser slides) |
| `--tone` | `lecture` | default bullet style | Adds more narrative, sentence-like bullets to any flavor |
| `--append` | `path/to/existing.yaml` | — | Extend an existing deck with new slides |
| `--topic` | `"Section Title"` | — | Locates the target section for `--append` (matched against divider/title text) |
| `--task` | `"transformation description"` | — | **What to do** inside the target section (use with `--append` + `--topic`). Without `--task`, slides about `--topic` are added after the divider. With `--task`, the model reads the existing section and inserts new slides interleaved at the best positions. |
| `--compile-only` | `path/to/existing.yaml` | — | Recompile YAML → HTML without regenerating content |
| `--output-dir` | `path/to/directory/` | first source's parent dir | Override where YAML and HTML are written |
| `--name` | `my-deck-name` | first source's stem | Override the auto-derived basename for output files |

---

## Modalities

### 1. Generate from topic knowledge (no source file)

```
/md_to_yaml <flavor>
/md_to_yaml <flavor> --detail rich
/md_to_yaml <flavor> --tone lecture
```

Uses the model's knowledge of the topic. Prompts for flavor if omitted.

---

### 2. Generate from a single PDF

```
/md_to_yaml <flavor> --source path/to/paper.pdf
/md_to_yaml <flavor> --detail rich --source path/to/paper.pdf
/md_to_yaml <flavor> --tone lecture --source path/to/paper.pdf
```

Extracts text and structure from the PDF to drive slide topics.

---

### 3. Generate from a single folder

```
/md_to_yaml <flavor> --source path/to/folder/
/md_to_yaml <flavor> --detail concise --source path/to/folder/
```

Globs `**/*.{md,jpg,jpeg,png,gif,webp}` inside the folder. Auto-generates and persists a `<folder>-captions.yaml` for all images.

---

### 4. Generate from multiple sources (folders and/or markdown files)

```
/md_to_yaml <flavor> --source folderA/ folderB/
/md_to_yaml <flavor> --source folderA/ notes.md another.md
/md_to_yaml <flavor> --source folderA/ folderB/ --output-dir /path/to/output/
/md_to_yaml <flavor> --source folderA/ folderB/ --name my-deck-name
```

Output goes to the first source's parent directory unless `--output-dir` is given.
Basename derived from the first source unless `--name` is given.
**Always use `--embed-images` at compile time when sources span different directories.**

---

### 5. Extend an existing deck (`--append`)

```
/md_to_yaml <flavor> --append path/to/deck.yaml
/md_to_yaml <flavor> --append path/to/deck.yaml --topic "deeper explanation of X"
/md_to_yaml <flavor> --append path/to/deck.yaml --source path/to/more/material/
/md_to_yaml <flavor> --append path/to/deck.yaml --source path/to/folder/ --topic "deeper explanation of X"
```

Reads the existing deck, generates new slides for the target section (from `--topic` or user context), inserts them after the matching section divider, then re-validates and recompiles in-place. The `BASE` name is preserved.

---

### 5b. Transform a section (`--append` + `--topic` + `--task`)

```
/md_to_yaml <flavor> --append path/to/deck.yaml --topic "Section Title" --task "add diagrams"
/md_to_yaml <flavor> --append path/to/deck.yaml --topic "False Discovery Rate" --task "add a confusion matrix and p-value histogram"
/md_to_yaml <flavor> --append path/to/deck.yaml --source notes.md --topic "Section Title" --task "add a worked example after each theorem"
```

Use when you want to **augment a specific section** rather than append after it.

- `--topic` identifies the section (matched against divider/title text).
- `--task` describes the transformation — what slides to add and what kind.
- New slides are **interleaved** at the most logical positions within the existing section, not just appended after the divider.
- `--source` (optional) provides additional material to draw from for the new slides.
- The `BASE` name is preserved; the existing YAML and HTML are overwritten in-place.

---

### 6. Recompile only (`--compile-only`)

```
/md_to_yaml --compile-only path/to/deck.yaml
```

Skips all content generation. Validates the YAML, checks layout variety, and compiles to HTML. Use after manually editing a deck.

---

## Combining flags

All standard flags (`--detail`, `--tone`, `--output-dir`, `--name`) compose freely:

```
/md_to_yaml mathematical --tone lecture --detail rich --source folderA/ folderB/ --name quantum-svt --output-dir ~/slides/
/md_to_yaml explanatory --append deck.yaml --source extra-notes/ --topic "complexity analysis" --detail rich
/md_to_yaml mathematical --tone lecture --append deck.yaml --topic "False Discovery Rate" --task "add diagrams: confusion matrix, FDR column structure, p-value histogram" --detail rich
```

---

## Output file naming

`BASE = <source_basename>-<flavor>-<model>-<YYYYMMDD_HHMM>`

- `<source_basename>`: first source's stem/folder name, or `--name` override
- Output: `<output_dir>/<BASE>.yaml` and `<output_dir>/<BASE>.html`
- Timestamp is taken from the machine clock at generation time (`date +%Y%m%d_%H%M`)

---

## Compile manually

```bash
cd /path/to/skill/md_to_yaml
./compile.sh path/to/deck.yaml path/to/out.html --embed-images
./compile.sh path/to/deck.yaml path/to/out-full.html --embed-images --include-skipped
```

### Compiler flags

| Flag | Effect |
|------|--------|
| `--embed-images` | Base64-embed images into the HTML. Required when sources span directories. |
| `--include-skipped` | Render slides marked `skip: true` (omitted by default). |
| `--no-notes` | Omit speaker notes from the HTML entirely. |
| `--figure-layout-debug` | Red debug borders on figure panels. |
| `--bake-mermaid` | Pre-render Mermaid to inline SVG at compile time (requires `mmdc`). |

**Speaker notes are never displayed.** There is no presenter mode and no toggle: every
layout template emits `notes:` as `<aside class="slide-notes" hidden aria-hidden="true">`,
which `base.html.j2` also sets to `display: none`. The text is unreachable from the page
but plainly visible in View Source.

Read notes from the YAML, and compile anything you hand to an audience with `--no-notes`.
Then the audience copy and your own copy are byte-identical and `cp` suffices:

```bash
./compile.sh deck.yaml handout.html --embed-images --include-skipped --no-notes
```
