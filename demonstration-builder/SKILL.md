---
name: demonstration-builder
description: >-
  Build a new cpp_labs C++ teaching "demonstration" (one HTML page for a subject)
  from YAML — topics, examples, gotchas, concepts, and optional diagrams — then build
  and verify it with the real g++-at-build-time engine. Use this whenever the author
  wants to create, draft, scaffold, or add a new cpp_labs subject / demonstration /
  topic / example / gotcha, or asks to turn a C++ concept into an interactive lab
  page, even if they don't name this skill. Also use it to polish an author's draft
  topic/demo/layout YAML, and when building an AGENTIC demonstration — a page teaching
  students to work with AI-generated code via recorded model transcripts (prompt
  contrasts, test batteries over model replies, harvest tallies).
---

# demonstration-builder

Interactive workflow for authoring a new cpp_labs teaching page (a **demonstration**).
Read this once to get the workflow; open the `reference/` docs for detail as you need it.

---

## What a demonstration is

Locked vocabulary (use these terms consistently):

| Term | Meaning |
|---|---|
| **Demonstration** | One HTML page = one subject (e.g. *Operator Overloading*). The unit of nav. |
| **Example** | One rail entry inside a demonstration (*Basic Vec2*, *Commutative multiply*). |
| **Gotcha** | An example whose point is a deliberate failure (*Null Deref*, *Double Free*). |
| **Concept** | The prose imparted — one `concept:` field per example, one per demonstration. |

Two-layer content model: a **Topic YAML** (`*.topic.yaml`) holds the C++ source and
compilation metadata for each example; a **Demo/Layout YAML** wires topics into nav
and sets per-page structure. See `reference/PATTERN.md` for the full anatomy of both
layers and how they compose.

---

## Self-contained engine

This skill **carries its own copy** of the baking engine under `engine/` (the shared
`cpp_labs` Python package + `build_labs.sh` + `requirements.txt`). It does not depend
on any pre-existing `cpp_labs/` in the project, so it works in **any** folder.

The engine discovers subjects relative to its own physical location and `build_labs.sh`
runs from the project root, so the engine must live as a `cpp_labs/` package **at the
target project root**. Step 0 installs it there.

Requirements: Python 3.10+, a C++ compiler on `PATH` (`g++`/`clang++`), and PyYAML
(`pip install -r engine/requirements.txt`).

## The interactive workflow

Work through these steps in order. Offer suggestions at each gate — the author
should never face a blank page.

### Step 0 — Install the engine (once per project)

If the target project has no `cpp_labs/` engine yet (no `build_labs.sh` at its root),
install the bundled engine into it. Safe to re-run — it merges engine files and never
touches existing subject folders:

```bash
<skill-dir>/scripts/install_engine.sh          # installs into $PWD (the project root)
```

`<skill-dir>` is wherever this skill lives — e.g. `.claude/skills/demonstration-builder`
(project-local) or `~/.claude/skills/demonstration-builder` (global). All scripts below
target the **current directory** as the project root (override with a trailing path arg
or `PROJECT_ROOT=`), so run them from the project you are authoring in.

### Step 1 — Elicit

Ask the author for:
- Subject name and a one-line goal (what should a student *understand* after reading this page?)
- The C++ concepts to cover (e.g. `std::variant`, move semantics, RAII)
- Any example code they already have — invite a paste
- Any images or diagrams they want to incorporate

If they only give a subject name, propose a goal and concept list yourself and confirm.

### Step 2 — Shape the examples

Propose 2–4 named examples + at least one gotcha. For each, sketch one sentence on
what it demonstrates and why it earns its own rail entry. Offer suggestions when the
author is unsure — a good gotcha shows what happens when the rule is violated.

**Variant mechanism (locked rule — tabs by default).** When an example's variants are
distinct, self-contained programs the student flips between (one concept per view), use
a `controls:` **dropdown** (`value_map`) so each variant becomes a real switchable
**tab** — the whole program body fills one `<<prog>>` placeholder per option. Reach for
`cases:` (which renders **stacked**, one code block below another, *not* tabbed) only
when either:
- the contrast is a **correct | mistake** pair meant to be read side-by-side (the wrong
  version sits directly under the right one), or
- a single variant genuinely needs **multiple code fragments shown together** (e.g. a
  `<<member_op>>` + `<<free_op>>` split within one case).

If you find yourself stacking several complete alternative programs in `cases:`, convert
them to dropdown tabs. See `reference/PATTERN.md` §4 (tabs) vs §5 (stacked cases).

**Tab-label glyphs (locked rule — correct vs mistake).** When an example contains a
**mistake** variant — one the lesson warns against, whether it fails at **compile**,
**link**, *or* **runtime** (a crash, UB, a leak, or plain wrong output) — prefix a glyph
to **every** tab label of that example so the precomputed verdict is visible in the tab
bar: `✅ ` on each correct/recommended variant, `❌ ` on the mistake. The glyph is a
*pedagogical* verdict, not the compile outcome: a `❌` tab may compile fine and only fail
at runtime (e.g. a double-free), and a `✅` tab may deliberately fail to compile (e.g.
adding `override` to surface a typo). Leave an example **unglyphed** when all its tabs are
legitimate variations with no wrong side (different types, sizes, ownership counts, or a
pure mechanism contrast) — glyphing those is noise. The glyph goes in the dropdown
`options:` entry *and* its matching `value_map:` key (and the `default:` if it names that
option) — they must stay byte-identical. This is the manual convention that resolved the
tab-compile-status request; the engine does not auto-render these glyphs.

Confirm the list before generating any files.

### Step 3 — Diagram triage

Read `reference/DIAGRAMS.md` before deciding. Ask: does a diagram clarify the memory
model, object graph, or control flow better than prose or code alone? If yes, propose
the diagram type and its content. Offer the zero-JS interaction layer (stepper /
enlarge / detail-reveal) only when it adds genuine pedagogical value — it is always
optional. Set `diagram: false` on examples where prose + code is clearer.

**Where the Key Idea goes (locked rule).** The Key Idea and the diagram are separate
regions and never share space. Placement is an *example-level* decision, uniform across
all variant tabs — it follows directly from the diagram decision above:

| Example has a diagram? | Key Idea placement | Canonical YAML |
|---|---|---|
| **Yes** (`diagram: true`) | Fold-out **button** (top-left); the diagram owns the right column | `- concept: {id, text}` block **plus** `- topic: {…, diagram: true}` (no `concept:` on the topic) |
| **No** (`diagram: false`) | Right-panel **aside** | `- topic: {…, diagram: false, concept: "${x.explanation}"}` (no separate `concept:` block) |
| **No, with per-tab aside content** (`diagram: false` + `aside_html:`) | Aside moves **inside each tab**, below that tab's slot HTML (e.g. its verbatim prompt) | Same as above **plus** `aside_html: {…}` keyed by exact tab labels — `reference/PATTERN.md` §7a |

A "diagram" is defined by the **slot it occupies** (the right column), not how it is built
(a memory-model SVG, a text/HTML stepper, or a figure). The Key Idea is the point of the
*whole* example — its `explanation` — never a caption describing the diagram. Full rule,
anti-patterns, and the enforcing test: `reference/PATTERN.md` §7.

### Step 4 — Generate the files

Start from a consistent, buildable skeleton — don't hand-create the paths (that is
where id/filename references drift out of sync):

```bash
<skill-dir>/scripts/scaffold_subject.sh <subject>    # writes into $PWD/cpp_labs/<subject>
```

This creates the package below with ONE working example (`<subject>_ex1`, printing
`x = 42`) that builds and tests green immediately — a known-good baseline to grow from:

```
cpp_labs/<subject>/topics/                       # one *.topic.yaml per example
cpp_labs/<subject>/demos/                         # one *.demo.yaml (wires topics → page)
cpp_labs/<subject>/layouts/<subject>.rail.yaml    # nav style + demo list
cpp_labs/<subject>/tests/test_<subject>.py        # exact-baked-stdout assertions
```

Then grow it: duplicate the example topic/demo per example, add at least one gotcha,
and list every demo in the layout — **standalone gotcha examples go last** in the
`demos:` list (see Guardrails). Apply the C++ style guardrails (see **Guardrails**
below) while filling placeholders. The worked exemplar at `cpp_labs/template_subject/`
shows a complete 2-example + 1-gotcha set with `diagram: false` — copy its shape.

### Step 5 — Build and verify

Follow `reference/CHECKLIST.md` for the exact commands. The key loop is:

```bash
./build_labs.sh <subject>                              # bake to dist_labs/ (real g++)
pytest cpp_labs/<subject>/tests/test_<subject>.py -q   # green = content correct
```

Report the REAL baked stdout/stderr — do not summarise or paraphrase compiler output.

### Step 6 — Iterate to green

Fix any compile errors, YAML validation failures, or test failures. Re-run the checklist
until all tests pass and the baked page renders correctly in a browser. Then hand off to
the author for a content review.

---

## Agentic demonstrations

A second genre: pages that teach students to **work with AI-generated code**, where
the C++ comes from a **real recorded model transcript** (prompt → reply, verbatim)
embedded in an author-written test harness, and every claim on the page is
build-derived or traced to a harvest file. Same engine, same YAML, extra discipline.

If the author asks for a demo about prompts, model comparisons, hallucination,
grounding, test gates over AI code, or anything embedding model output: **read
`reference/AGENTIC.md` before shaping examples.** It carries the locked honesty
invariants (verbatim code + byte-sync tests, disclosed re-roll selection, on-page
provenance), the folder shape (`transcripts/`, `harvest/`), the design levers for
when capable models refuse to produce the failure your lesson needs, and the page
grammar (the uniform example skeleton, real tab strips with toggle-to-close,
prompts beside code via `aside_html`, per-arm diff/reply tabs, page density).

---

## The worked exemplar

`cpp_labs/template_subject/` is a complete worked example (2 examples + 1 gotcha,
`diagram: false`). Open it and copy its shape when starting a new subject. The
`templates/` directory contains the raw copy-me skeletons with fill-in markers
(`my_topic`, `Human name`, `my_subject`) to replace.

---

## Guardrails

These rules exist for good reasons — don't skip them.

| Rule | Why |
|---|---|
| Use `class`, not `struct` | `class` defaults to private — models encapsulation; `struct` lets sloppy direct-member access compile "by accident", hiding missing `friend`/accessor lessons. |
| Comments on their own line above the code they describe | Trailing end-of-line comments are easy to miss; above-the-line comments read as natural prose. Tests assert byte-identical stdout — trailing comments can shift column widths. |
| Break long `<<` chains at `<<` boundaries, aligned | Long stream statements on one line are unreadable at course font sizes. Rule: break when 3+ `<<` or >~55 chars; align continuation lines under the first `<<`. |
| Never commit `dist_labs/` | It is gitignored — the baked HTML is always regenerated from YAML. Committing it creates merge conflicts and bloats the repo. |
| Do NOT modify engine code | Authoring is purely YAML content. The bundled `engine/cpp_labs/` Python is a vendored copy — editing it here diverges from upstream. Engine changes belong in the source repo with their own TDD cycle. |
| Order standalone gotcha examples **last** in the rail | A gotcha is a deliberate failure that only makes sense after the correct behavior it violates — end on it as the cautionary capstone (`op_overload` groups its gotchas last). In `layouts/<subject>.rail.yaml`, list every example whose `group:` is `Gotchas` (titled `Gotcha — …`) at the end of `demos:`, after all correct examples; multiple gotchas trail as a group. Does **not** force reordering of a normal teaching example that merely carries a correct\|mistake `cases:` pair (e.g. `class_structure`'s `cls_copy_ctor`). |

---

## Accessibility (ADA — WCAG 2.1 Level A/AA)

Pages are held to WCAG 2.1 **Level A/AA**; AAA findings are explicitly out of
scope. The engine covers the structural items — authored content must not undo
them:

- **Heading ladder — no level skips.** Hand-authored HTML inside an example must
  not jump heading levels. For section headings within an example, use a
  **bold-lead paragraph** (`<p><strong>Section name.</strong> …</p>`), not an
  `<h4>`/`<h5>`.
- **Engine code windows are keyboard-accessible** — every rendered code `<pre>`
  carries `tabindex="0" role="region" aria-label="Code listing"`. Tests must not
  pin a bare `<pre>`; write attribute-tolerant matches.
- **Hand-authored `<pre>` blocks wrap their content in `<samp>`** (program output)
  **or `<code>`** (source) so assistive tech announces them correctly.
- **Interactive widgets built content-locally** (tab strips, toggles) need real
  labels and keyboard reachability — verify by measurement, not by eye
  (`reference/CHECKLIST.md`).
- An a11y gap in engine-rendered markup is an **engine issue**: surface it as an
  ENGINE_REQUEST for the source repo rather than patching per-page (see the
  engine guardrail above).

---

## Reference map

| Doc | What it covers |
|---|---|
| `INSTALL.md` | Plain-language setup guide (prerequisites, install, first build) |
| `reference/PATTERN.md` | Full YAML anatomy of topic/demo/layout files + test families |
| `reference/DIAGRAMS.md` | Diagram triage guide + zero-JS interaction layer options |
| `reference/AGENTIC.md` | Agentic demonstrations: transcripts, honesty invariants, harvests, page grammar |
| `reference/CHECKLIST.md` | Build/verify commands + ordered pre-commit checklist |
| `engine/` | Vendored baking engine: `cpp_labs/` package + `build_labs.sh` + `requirements.txt` |
| `scripts/install_engine.sh` | Install the bundled engine into a target project (Step 0) |
| `scripts/sync_engine.sh` | Maintainer-only: re-vendor `engine/` from a live source engine |
| `scripts/scaffold_subject.sh` | Create a consistent, buildable `<subject>` skeleton to grow from |
| `templates/` | Copy-me skeletons (`topic.topic.yaml`, `demo.demo.yaml`, `layout.rail.yaml`, `test_subject.py`) |
| `cpp_labs/template_subject/` | Worked exemplar (2 examples + 1 gotcha, diagram:false) — in the source repo |
