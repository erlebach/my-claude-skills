---
name: cap5771-unit-builder
description: Use when building or revising a unit or module of the CAP5771 "Introduction to Data Mining" Spring 2027 course site (~/src/2027/cap-f5771-s2027) — goal, takeaway and objectives, vocabulary, course notes, rail page, visual explainer, slides, interactive (including when the author types /design), practice quiz or module page — or when the author asks to "do the next unit", "do Module N", or to repeat the pilot unit's pattern.
---

# CAP5771 unit builder

Build one weekly unit of the CAP5771 site, in a fixed order, with fixed checks. The pilot unit is Module 2, "Data types, quality and similarity". Copy its pattern; do not invent a new one.

## Authority

These files are authoritative. This skill puts their rules in order and adds templates. If this skill and one of them disagree, the file wins; then fix this skill.

| File | What it decides |
|---|---|
| `~/src/2027/cap-f5771-s2027/CLAUDE.md` | the unit parts, their order, the verification steps, `/design` |
| `course_site/CLAUDE.md` | the unit folder layout, shortcodes, data files, Hugo rules |
| newest file in `handoffs/`, then `JOURNAL.md` | what is done, what is open, what the author decided |

Read all three at the start of a session. Trust `SNAPSHOT.md` only if its date is not older than the newest `JOURNAL.md` entry.

## Sources: the notes replace the textbook

Students do not use the textbook. The course notes replace it. They are written in our own words, so no copyright is violated.

| Source | Use |
|---|---|
| Lesson deck (`slides/`) | **Start here.** It gives the topics, their order, and many examples. |
| Textbook body (`textbook/`) | Read it before you write the notes. It fills what the deck does not cover, and the source check compares the text with it. |
| Your own knowledge | Only where the deck and the textbook are silent. List each such statement in the report. |
| Invented for the course | The running example and its numbers. |

- Do not cite textbook section numbers to students, and never point them to a Kumar deck: the decks are not ADA compliant, and the site neither links to them nor hosts them. A "Take it further" item points to a source that students can reach and that is accessible, or to nothing.
- The textbook edition matters only for the source check. The staged pages are the 1st edition (2006); the attribution names the 2nd edition (Pearson, 2019).
- The staged pages have printing defects and the author's handwritten margin notes. `references/textbook-defects.md` lists them and the form the notes use. Add each new one you find.

## How the pilot unit was built

Module 2, "Data types, quality and similarity", on 2026-11-11 (times EST, from the session record). Repeat this order, with the two corrections marked.

| # | Time | What was built | From |
|---|---|---|---|
| 1 | 16:19 | Text extracted from textbook Sections 2.1, 2.2, 2.4 and the Lesson 1 and 2 decks | the staged PDFs |
| 2 | 16:19 | Draft goal, takeaway, 9 objectives | the deck text; the textbook headings only |
| 3 | 16:46–17:15 | Vocabulary: headwords with synonyms. Author approved "data object" and "attribute" | the decks; own knowledge |
| 4 | 16:46 | Outline of the notes, 11 sections. Author approved | the decks' order of topics |
| 5 | 17:17 | Script that computes every number of the running example | the invented data |
| 6 | 17:21 | Course notes, as one page with the goal, objectives and vocabulary in its front matter | the decks (topics, order, examples); own memory of the textbook for the rest. **The textbook body was not read** (correction 1) |
| 7 | 17:59–18:00 | Rail page: the page split into `notes.md`, `unit.yaml`, `vocabulary.yaml`; then 12 `section-*.yaml` panels | **the notes**, one panel per notes section |
| 8 | 18:23 | Source check of the notes and vocabulary by a `sonnet` subagent; 9 findings fixed | the textbook text |
| 9 | 18:41–20:53 | Interactive `nearest.html`; first as a claude.ai canvas, then rewritten as HTML (correction 2) | the notes' running example; the numbers script |
| 10 | 20:55 | Explainer, long version (rejected, kept as `…-long.html`) | the textbook body, read in full for the first time; the notes |
| 11 | 21:05–21:17 | Explainer "Who is like C1?"; source check, 2 findings fixed | the notes; the textbook; the author's model posts |

- **Correction 1:** read the textbook body before step 6, not after the notes. The source check found 9 differences because of this gap.
- **Correction 2:** write the interactive as HTML from the start.
- **The rail panels come from the notes, not directly from the slides.** The slides reach the panels through the notes.
- Slides and the practice quiz were not made for the pilot.

## The second unit: what it added

Module 2, "Data preprocessing" (2026-11-12), followed the order of work above with the corrections, and added these patterns:

- **Two datasets** (grocery store and weather stations), because one could not show every step. The author approved the split of the sections between them before the outline.
- **Two explainers**, one per lesson, each on its own question. `materials.explainer` in `unit.yaml` then takes a list of `{file, title}`.
- **Generator scripts** in `build/module-02/` of the workspace (in git; see its `README.md`): `unit_numbers.py` (every number), `build_explainers.py` (both explainers, every figure coordinate from the same data) and `build_interactive.py` (copies the data into the interactive). A fix goes into the script, then the script is rerun.
- **An interactive in stages** (`preprocess.html`): ten algorithms, each stepped through with N; 20 Predict questions, each with a `check()` that recomputes its answer; 30 flash cards.
- **A textbook gap check** after the notes, which found 5 major gaps in the pilot's notes (see step 3d).

## Module 4: a whole module in one session

Module 4 (basic cluster analysis, three units, 2026-11-14) was built past the approval gates, as the author allowed for Modules 3 and 4. It added these patterns:

- **One module, three agents.** I designed the running example and computed the unit 1 numbers myself. Then three forked agents wrote one unit each, in two phases: (1) notes and rail panels; (2) explainer, interactive, slides and quiz. Fresh `sonnet` agents ran the source check and the gap check on each unit's notes, then a second source check on the other parts (`references/verification.md` §3c). I confirmed each quoted finding before I sent the fix back to the unit's agent.
- **The data serves the whole module.** `build/module-04/store_data.py` gives C1–C24 two new attribute sets (shopping: three segments and one outlier; home locations: four neighbourhoods of different density), and reuses age and income as data with no cluster structure. The author chose it from three options.
- **A script checks each displayed formula** against its displayed inputs, not only the numbers script (`check_displayed_unit1.py`, `check_arithmetic_unit2.py`, `unit3_display_check.py`).
- **Predict questions stand alone**, with a Given box and a Derivation (`references/interactive.md`).
- **A practice quiz for the module**, in addition to each unit's quiz (`references/unit-files.md` §7).

## Before you start a unit

1. Find the unit in `content/modules/module-NN/_index.md`: its `unit:` text, its lessons, its dates. The unit's `## ` heading on the module page must be the same text.
2. Find its sources in `course_materials/module-NN_*/` (`slides/`, `textbook/`). Read `course_materials/README.md` for the file names. Extract the deck and the textbook section with `pdftotext -layout`, and read both in full.
    - Map each lesson of the unit to its deck slides and its textbook sections. A lesson can have no deck of its own: in 2026 some topics had one lecture, and the 2027 schedule gives them two. Then find the slides for its topics in the other lesson's deck or in the chapter deck, and say so in the report.
    - The Spring 2026 unit folders (`~/src/2025/cap-f5771-s2026_hugo-zen-experiments/content/module/…`) hold Python files in `src/` of unknown origin (AI-written or the author's). Do not use them as a source for the notes. They may serve later as demos; mention them only when the author asks for demos.
3. Check open questions in the newest handoff that block the unit. Ask the author before you write text that depends on them.
4. Run `git status` in each of the three repositories. Commit an author's edit by itself first.

## The order of work, with gates

Each step ends at a gate. Do not start the next step until the gate is passed.

| # | Part | Made with | Gate |
|---|---|---|---|
| 1 | Goal, main takeaway, objectives (`unit.yaml`) | the deck first, then the textbook body | **Author approves.** Stop and ask. |
| 2 | Vocabulary (`vocabulary.yaml`) | the deck's terms; the textbook definitions | one headword per idea, used in every later part. Author approves the headwords |
| 3a | Outline of the notes: one `## ` section per main idea | the deck's order of topics | **Author approves.** |
| 3b | Course notes (`notes.md`) | the deck, then the textbook body; a script for every number | source check by a fresh `sonnet` subagent; findings confirmed and fixed |
| 3c | Rail panels (`section-NN-*.yaml`) | the notes: one panel per notes section | build clean |
| 3d | Textbook gap check (`verification.md` §3b) | a fresh agent per unit reads the whole textbook section and lists what the notes leave out, as major, medium or minor | **Author decides** what to add; add it with the script; source-check only the new passages |
| 4 | Visual explainer (`static/explainers/<unit>.html`), with interactive figures where changing the figure is the lesson (`references/explainer.md`, "Interactive figures") | `visual-explainer` skill; a build script | source check; `__verify()`; browser check of every control |
| 5 | Slides, after the explainers: in the explainer's order, with the explainer's figures exported as SVG, plus slides from the notes for definitions and procedures (`references/slides.md`) | `md_to_yaml` skill | `check_autofit.py` clean; set `materials.slides` in `unit.yaml` |
| 6 | Interactives (`static/interactives/<name>.html`) | written directly; see `references/interactive.md` | browser check at 16:9 and 390 px, served from an empty folder |
| 6b | Second source check | a fresh `sonnet` agent: explainer, interactive text, slides, quiz (`verification.md` §3c) | findings confirmed and fixed |
| 7 | Practice quiz | a page under the site; set `materials.practice`. After the last unit: the module quiz, `module-NN/practice.md` | build clean; the link resolves |
| 8 | Module page | links to the parts above. The Materials page lists the unit by itself, from `unit.yaml` | build clean |

After step 8: report to the author with the verification results (`references/verification.md`). Then update `JOURNAL.md` and `SNAPSHOT.md` together, and write a handoff if the session ends.

## Quick reference

| Task | Where |
|---|---|
| Unit folder files, with templates from the pilot | `references/unit-files.md` |
| Source check prompt, build checks, browser checks, report | `references/verification.md` |
| Interactive pattern (16:9 stage, modes, magnifier, list entry) | `references/interactive.md` |
| Explainer pattern | `references/explainer.md` |
| Slides: order, figures from the explainers, compile | `references/slides.md` |
| Hugo behaviours that break templates silently | `references/hugo-gotchas.md` |
| Defects in the staged textbook, and the form the notes use | `references/textbook-defects.md` |
| Gap check prompt (textbook against notes) | `references/verification.md` §3b |
| Check build | `cd course_site && hugo --noBuildLock -d scratch/checkbuild` |
| Browser preview | `hugo server -p 1314 ...` — never port 1313 (the author's preview) |
| Install the magnifier | `python3 interactives/add_lens.py <name>` (from the workspace folder) |
| Prose format check | `python3 ~/.claude/skills/plain-technical-english/scripts/check_prose.py <file>` |
| Notes heading map for links from an interactive | `build/notes_headings.py` (inserted at `/*__HEADINGS__*/`) |
| Check those links against a check build | `python3 build/check_notes_anchors.py` |
| Round half up in Python | `r()` and `fmt()` in `build/module-04/store_data.py` |

## Required skills

- **REQUIRED:** `plain-technical-english` for every text: notes, YAML text, captions, replies, commit messages.
- **US spelling** in every student-facing text (author, 2026-11-14): neighbor, neighborhood, color, behavior, center, gray, modeling. `build/us_spelling.py` converts a file set (dry run by default) and keeps `aria-labelledby`.
- `visual-explainer` (step 4), `md_to_yaml` (step 5), `playwright-cli` (browser checks), `pdf` or `pdftotext -layout` (sources).
- `hugo-course-builder` only before a change to a template or shortcode. A new unit needs no template change.
- Do **not** use `frontend-design`. Do **not** make a claude.ai Design canvas, even for `/design`.

## Common mistakes (each one happened on the pilot)

| Mistake | Rule |
|---|---|
| Notes written from the deck and memory, with only the textbook headings read | Read the textbook body. State the source of each part in the report. |
| A number worked by hand (a date difference was wrong) | Compute every number with a script in `build/module-NN/`. |
| `/design` made a claude.ai canvas, which then had to be rewritten | An interactive is one standalone HTML file. Write it directly. |
| The first explainer covered the book section by section | An explainer is an illustrated post on one question, about 10–12 minutes. |
| A page chose "link" or "planned" with `fileExists` and went stale in `hugo server` | Put `planned: true` in `data/interactives.yaml`. |
| An interactive file was written to `static/interactives/` before its list entry; the author's preview failed to start (Module 4, 2026-11-14) | Add the `data/interactives.yaml` entry first, then write the file. Keep the site buildable at every step. |
| A displayed formula gave a different result from its displayed inputs ((1.610 − 0.453)/1.610 printed as 0.718; it gives 0.719) | Recompute every displayed computation from its printed inputs with a script (`build/module-04/check_displayed_unit1.py`), and make the check fail once. |
| Playwright test browsers used the real Chrome app; the author's Dock icon then brought a headless test browser forward and Chrome showed no window | Close test browsers when a check ends (`playwright-cli close-all`). The author can start their own Chrome with `open -n -a "Google Chrome"`. |
| A fix made a nearby sentence false | Read the text around each fix. |
| A quote from the source check "not found" | `pdftotext` keeps the ligatures U+FB01 (fi) and U+FB02 (fl). Search for part of the word. |
| The author's hand edit of `calendar.yaml` was overwritten | `git status` first; edit by exact replacement. |
| A build check was trusted without a test | Make each new check fail once, then restore the files. |
| A Kumar deck linked or cited for students | The decks are not ADA compliant. Students get the `md_to_yaml` slides; the notes never send them to a deck. |
| Asked the author which textbook edition students use | Students do not use the textbook. Cite no textbook sections to them. |
| Asked the author several decisions in one message | Ask one decision at a time, and wait for the reply. |
| The slides were text and tables only, written from the notes (Modules 2–6, first Module 7 deck); the author teaches with slides, explainers and interactives together | Write the slides after the explainers, in their order, with their figures (`references/slides.md`). |
| Asked about the content of the notes (PCA depth) before the vocabulary | Follow the steps in order. A question about the notes waits for step 3a. |
| The pilot's notes had passed a source check, but left out 5 major textbook ideas (cosine as an angle, extended Jaccard, data that is not in records, …) | A source check finds wrong statements, not missing ones. Run the gap check (step 3d) on every unit. |
| One random sample "showed" that stratified sampling is better; the sample actually drawn was worse | Never argue from one random draw. Compare methods by their spread over all samples (computed, or enumerated), and say that one draw can still be far off. |
| Unit 1 called hypothetical customers C9 and C10; unit 2 used C9 and C10 for real customers with other values | A label in a running example means the same object in every unit. Give hypothetical objects no label ("another customer", "a second row for C2"). |
| Number cards put a median income next to a mean purchase amount; the author read them as a mean and a median of one quantity | Group numbers by attribute, with a label, and compare like with like. |
| The interactive showed 19.22 where the notes have 19.23 (the stored double was 19.224999…) | Round halves up in every script and page; in JavaScript add a tiny epsilon before rounding; in Python use `Decimal` with `ROUND_HALF_UP` for money. |
| `Decimal` with `ROUND_HALF_UP` still printed 1.707 for 1.7075, because the float was 1.70749999… (Module 4) | Round to 9 decimals first, then round half up: `Decimal(repr(round(x, 9)))`, as `store_data.r` and `fmt` do. Compare every script output before and after such a change. |
| A Predict or quiz question could be answered only from the answer to the question before it | Each question stands alone: it restates its setting and gives every value it needs. |
| The notes named "the textbook" to students (the Hopkins statistic) | Students never see the textbook named. Write "some texts" when a variant must be mentioned. |
| An interactive linked to the top of the notes | Link to the most specific heading, through the heading map, and run `check_notes_anchors.py`. |
| Scatter points fell outside their panels; random data did not have the correlation printed under it | Build example data to have the exact value its label states; scale each panel to its own data; look at a screenshot of every figure. |
| Text said "the book notes that…", "the book's Example 2.20" | Only one attribution line, at the top. Inside the text, state the fact plainly. |


## Three repositories

The workspace (`erlebach/cap5771-s2027-workspace`), `course_site/` (`erlebach/cap5771-s2027`) and `course_site/figures/` (`erlebach/cap5771-s2027-figures`) are separate. Commit and push each one by itself. Commit only when the author asks.
