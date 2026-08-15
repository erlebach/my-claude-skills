# Presentation quality: narrative, bullets, and flavors

This file complements **`layout_rules_llm.md`** (which layout to use) and **`equations.md`** (math in YAML). It focuses on **story**, **slide-to-slide flow**, and **bullet discipline**.

---

## Narrative arc

- Build a **through-line** (a temporary story): the audience should feel each slide **connects** to the one before—use section titles, dividers, or an opening phrase that callbacks to the prior idea when helpful.
- For each major learning objective, prefer a tight triple rhythm:
  1. **State** the objective (what they should know or do).
  2. **Illustrate** it (figure, diagram, table, or two-column visual + text).
  3. **Derive or explain** (short content slide: why it matters, limits, or “so what”).
- **One primary message per slide.** If the source material packs multiple ideas, **split** into additional slides rather than dense lists.

---

## Bullet points (good vs. poor)

Effective bullets are **memory cues** for the room and **prompts** for the speaker—not a full script. The speaker supplies nuance; the slide stays light.

### Structural heuristics

- **5×5 / 6×6 rules (heuristic):** aim for roughly **≤5 bullets with ~5 short words each**, or **≤6 bullets with ~6 words each**. The bundled compiler warns when a body has **more than 8** bullets—treat that as a hard ceiling.
- **One idea per bullet.** If a bullet contains “and” twice, consider splitting into two slides or two bullets.
- **Parallel structure:** start bullets with the same part of speech—especially **imperative verbs** for hands-on flavors (e.g., *Configure…*, *Run…*, *Verify…*).

### Formatting habits

- Prefer **short phrases** over full sentences; avoid bullets that wrap past **two lines** of slide body.
- **Punctuation:** omit trailing periods unless the bullet is a deliberate full sentence.
- **Legibility:** the HTML deck targets large type; still write **short** lines so scaling does not break layout.

---

## Flavor-specific tone

| Flavor | Slide titles & bullets |
|--------|-------------------------|
| **explanatory** | Concept-first; concise phrases; define terms on first use; one idea per slide. |
| **implementation** | **Imperative** bullets; concrete artifacts (modules, APIs, files); minimal prose. |
| **tutorial** | Numbered **steps** layout when possible; imperative verbs; expected outcomes per step. |
| **lecture** (optional) | Slightly longer, more sentence-like bullets allowed—still avoid dense walls; split across slides. |

---

## Optional flavor: lecture

Use when the user wants **more narrative on-slide** (e.g., a chalk-talk style). Rules relax **slightly**:

- Bullets may read more like **short sentences**.
- Still enforce **one main idea per slide** and **layout variety** from `layout_rules_llm.md`.

If the user does not specify a flavor, default to **explanatory**, **implementation**, or **tutorial** per the main skill—and only adopt **lecture** when they ask for longer on-slide prose.

---

## Detail level (`--detail`)

The main skill documents **`--detail concise`**, **`standard`**, and **`rich`**. This is a **whole-deck** control: it changes **how many slides** you create from the same source, **not** how many bullets fit on one slide.

- **concise** — prioritize brevity; merge objectives where it stays clear; skip nice-to-have elaboration.
- **standard** — balanced depth (default when `--detail` is omitted).
- **rich** — prefer **extra slides** the presenter can delete later: trade-offs, limits, small comparison **tables**, section **dividers**, short **“checkpoint”** summaries, and an extra **state → illustrate → derive** beat when the source has enough substance.

### Detail level and flavor

| Flavor | Extra moves when `--detail rich` |
|--------|-----------------------------------|
| **explanatory** | More **content** + **diagram** / **two-column** pairs per big idea; optional **quote** or **comparison** for contrasting views. |
| **implementation** | More **code** slides and **steps** for setup, run, verify; separate **failure / pitfall** slide when useful. |
| **tutorial** | More **steps** slides and explicit **expected outcome** lines; optional **summary** after each major block. |

**Lecture** tone (if used) can pair with **`rich`** for more on-slide sentences — still **one main idea per slide**.

---

## Checklist before finalizing YAML

- [ ] **`--detail`** intent reflected: **`concise`** stays short; **`rich`** adds enough **extra slides** (not longer bullet lists) that the user could trim.
- [ ] Each slide has **one** clear takeaway; title reads like a **headline**, not a topic label only.
- [ ] Slides **chain** logically (reader can infer why this slide follows the last).
- [ ] Bullets respect **5×5 / 6×6** heuristics and **parallel structure** where applicable.
- [ ] **Alt text** on every `figure` / `diagram` (and on two-column visuals) describes what matters for understanding, not filenames.
- [ ] **`two-column` Mermaid (narrow column):** multiple **unlinked** roots often render **side by side** and confuse the layout—link blocks or use subgraphs so stacked concepts read **vertically**. On **full-width** `diagram` slides, side-by-side roots **might** be OK (see `SKILL.md` — *Two-column Mermaid — twin roots and vertical stacking*).
- [ ] **Mermaid canvas shape:** consult `SKILL.md` — *Mermaid canvas aspect ratios (compiler CSS)* when choosing **`layout: diagram`** vs **`two-column`** and **`graph LR`** vs **`graph TD`**.
- [ ] No **three or more** consecutive slides with the same `layout` (see `layout_rules_llm.md`).
