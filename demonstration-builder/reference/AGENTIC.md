# Agentic Demonstration Reference

How to build an **agentic demonstration** — a page that teaches students how to work
with AI-generated code, using **real recorded model transcripts** as the teaching
artifact. This genre was developed across the `agentic_spec` pilot and the `ag_*`
modules (testgate, numverify, evidence, hallucination, models, grounding); the series
catalog and per-module specs live in the course repo (`AGENTIC_DEMO_DESCRIPTIONS.md`).

The engine is unchanged: an agentic page is ordinary topic/demo/layout YAML. What
differs is where the C++ comes from (a harvested model reply, not the author) and the
honesty discipline that protects the page's credibility.

## Table of Contents

1. [Anatomy and folder shape](#1-anatomy-and-folder-shape)
2. [Honesty invariants (locked)](#2-honesty-invariants-locked)
3. [The failure-elicitation problem](#3-the-failure-elicitation-problem)
4. [Two-axis principle: model AND system message](#4-two-axis-principle)
5. [Page grammar](#5-page-grammar)
5a. [Replay exhibit: one recorded sequence, step by step](#5a-replay-exhibit-one-recorded-sequence-step-by-step)
6. [Harvest discipline](#6-harvest-discipline)
6a. [Two-turn transcripts & system-append disclosure](#6a-two-turn-transcripts--system-append-disclosure)
7. [Recorded platform gotchas](#7-recorded-platform-gotchas)

---

## 1. Anatomy and folder shape

An agentic subject extends the standard folder with two directories:

```
cpp_labs/<subject>/topics/        # model code embedded in author harnesses
cpp_labs/<subject>/demos/          # page wiring incl. prompt disclosure
cpp_labs/<subject>/layouts/
cpp_labs/<subject>/tests/          # + byte-sync + invariant tests (see §2)
cpp_labs/<subject>/transcripts/    # one file per roll, one- or two-turn (§6a):
                                   #   prompts + replies verbatim, with
                                   #   capture-metadata frontmatter
cpp_labs/<subject>/harvest/        # README + protocol, tally.md → tally_summary.md,
                                   #   scripts/ (roll + classify tooling)
```

**Topic structure:** the model's code sits between marker lines inside the author's
program — includes above, `harness`/`main` below, both author-written and identical
across variants:

```cpp
// === BEGIN model output (verbatim) ===================================
...model code, byte-for-byte as replied...
// === END model output ================================================
```

The author harness prints one PASS/FAIL verdict line per spec clause, so the page's
claims are build-derived, never asserted in prose alone.

## 2. Honesty invariants (locked)

These are non-negotiable; every shipped agentic module carries tests for the
mechanical ones.

1. **Model code is verbatim.** A test extracts the region between the BEGIN/END
   markers and asserts **character-exact equality** with the archived transcript.
   Never edit model code — not formatting, not includes, nothing.
2. **Replies are immutable; frontmatter is editable.** Capture-time stamps are never
   updated. The transcript file is the artifact of record.
3. **Re-rolls are allowed, with disclosed selection.** Rolls are independent samples;
   each is a real prompt→reply, so selecting one that exhibits the target behavior is
   legitimate — **provided the page discloses the selection and the approximate
   frequency** ("the bug appeared in ~N of M runs"). The tally is itself a datum.
   What stays forbidden: silently implying a cherry-picked rare event is typical.
   Re-rolling a transcript that feeds multiple embeds means regenerating the FULL
   demo, not one variant.
4. **Every numeral on the page traces to a harvest file.** Tallies flow
   `harvest/tally.md → tally_summary.md → page text`; no number appears on the page
   that cannot be found in the harvest record.
5. **Provenance is visible on-page:** model id, tool + version, effort setting,
   capture date, session hygiene (fresh session per prompt, clean directory, whether
   global config was present). A callout block near the top is the convention.
6. **Author code is labeled as author code.** Harnesses, foils, and run frames are
   clearly attributed; the reader must never wonder which code the model wrote.
7. **Language:** plain words on the page; avoid "honest/honesty" in student-facing
   prose (show the discipline, don't name it); topic `explanation:` prose is
   backtick-free; hand-authored `<pre>` blocks wrap `<samp>`/`<code>` for a11y.

## 3. The failure-elicitation problem

**Capable models write correct code.** A lesson that *needs* a bug ("the weak test
battery hides a defect") can silently break when every roll is correct — even cheap
models at low effort produce working solutions to pinned interfaces. Design levers,
in order of preference:

1. **Point the battery at an UNPINNED edge** the prompt never specifies (an empty
   stream's mean, an odd interval count). An unpinned edge always forces the model
   into a silent choice, so a strong battery **always reveals something** — robust
   even when all rolls are "correct". Frame the resulting FAIL as an **unasked
   question** (a spec gap), not "the model is buggy".
2. **Author-written naive foil**, clearly labeled, that always demonstrates the
   failure (e.g. the E[x²]−E[x]² variance foil vs. the model's Welford). The model's
   own choice then becomes the object of review.
3. **Disclosed re-roll selection** (§2.3) — sample until the behavior appears, ship
   the tally.
4. **Cheaper models / lowest effort settings** — and harvest with the **cheapest
   adequate model** regardless (token economy is a standing objective; "most
   powerful" is a moving target).
5. **Two-branch exhibits:** when outcomes genuinely vary across rolls (hallucinate
   vs. decline), show one roll of each branch side by side with the tally — the
   variance is the content.

Harder language features are NOT a good lever for a course's early stage; prefer
spec gaps over syntax difficulty.

## 4. Two-axis principle

**The system message is an experimental variable of equal rank with the model.**
Same system message + different models → different output; same model + different
system messages → different output. Any comparison shown to students must state
which axis varied and hold the other fixed — or **disclose on the page** when it
can't (e.g. packaged local models baking in their own prompts). When harvesting
local models, always capture `ollama show <model> --system` alongside the rolls.

**Context is layered, and prior turns are a variable of the same rank.** The model
answers the FULL context plus the last prompt — vendor system message, harness
instructions, installed skills/config files, prior conversation turns, then the
final prompt — with a **different entity responsible for each layer**. The series'
fresh-session protocol deliberately zeroes the history layer (that is what makes
tallies iid) and so diverges from real multi-turn usage; disclose that when it
matters. A comparison that varies history must hold the other layers fixed, like
any other axis.

## 5. Page grammar

Conventions students see, proven across the series:

- **Uniform example skeleton (locked, author-approved at A6).** Every example
  follows ONE recognizable top-to-bottom form, so the whole structure is visible
  without scrolling:
  1. Orientation intro ("Example N — label", ~45 words).
  2. Code tabs + consoles (engine variant topic; Key Idea box beside).
  3. Changes section — bold-lead heading ("The change" / "Both changes"), per-arm
     scope lines, then a **real tab strip** of per-arm diffs.
  4. Tally section ("&lt;model&gt; tally, both arms" — numerals from
     `tally_summary.md`).
  5. Complete-replies **tab strip** ("❌ … — complete reply" / "✅ … — complete
     reply", prose + code verbatim — the code panels embed only each reply's code).
  6. Final example only: a closing questions frame.
  Everything below the code tabs starts **unexpanded** (no tab preselected).
- **"Tabs" from the author means REAL tab strips — never collapsed `<details>`.**
  "Unexpanded by default" means a radio+label strip with NO radio checked (nothing
  shows until a click), not a details block. Strips must **toggle-to-close**
  (clicking the open tab closes it) — radios alone can't; use the pure-CSS
  twin-label none-radio trick or a minimal content-local script. Single-exhibit
  examples merge their diff + reply buttons SIDE BY SIDE into one strip, not two
  stacked one-button strips. The ONE `<details>` exception: prompt panels.
- **Prompts are disclosed verbatim, beside the code.** Use the topic block's
  `aside_html:` map (see PATTERN.md §7a): one collapsed, labeled
  `<details class="prompt-panel">` per variant, keyed by the exact tab label. The
  prompt switches with the tab.
- **Page density: more, smaller examples.** Too much information per example turns
  students off. Each example gets one to three tabs (author, 2026-10-16) and one job; split a larger example.
  Label every example visibly ("Example 1 — …") — never let an "Example 2"
  reference appear without a visible "Example 1". Sidebar: **ONE** Main Takeaway
  concept per page (the engine renders each sidebar concept as its own panel, so
  multiple concepts = a wall of takeaway boxes); separate its paragraphs with
  blank lines inside the single concept.
- **Per-arm content stays inside its tab.** Anything below a reply (its tally half,
  its interpretation) must match the tab the reader is on; only content that
  explicitly **compares** the arms stays shared below the tabs.
- **Tabs judiciously; hierarchical over flat.** Never one-tab-per-cell for a result
  matrix (a 6×3 grid is a summary table first, then two-level tabs — outer = model,
  inner = framework — if per-cell browsing is needed). Hierarchical tabs are
  buildable content-locally with the CSS radio+label pattern; the engine stays
  frozen.
- **Whole-arm tabs (advanced):** to tab *entire arms* including engine-rendered
  panels, hand-author a page-local `<style>` using `body:has(#radio:checked)` rules
  against the engine's stable baked-panel ids (`<bakekey>-ccp`). Pin the ids AND the
  rules with a module test so an engine rename fails loudly. Browsers without
  `:has()` degrade to the stacked layout — acceptable.
- **Glyph grammar** carries over from the C++ series (SKILL.md Step 2) with one
  caveat the author has not yet ruled on: there, the glyph reports what the compiler
  and the run did. On an agentic page the contrast pair usually marks the **prompt**
  (`⚠️ vague/ungrounded/unverified` vs `✅ pinned/grounded/verified`), which is a
  different axis — several vague-prompt arms print `PASS` on every line, so nothing
  about their build is amber. Until that is settled, keep the glyph consistent with
  the tab's badge and put the judgement of the prompt in the label, in words.

## 5a. Replay exhibit: one recorded sequence, step by step

A replay exhibit shows one recorded process whose steps happen in a fixed order, where each
step's input contains the previous step's output: a pipeline run, a repair loop, a
multi-turn session. The student walks the steps in order and opens any detail of a step.
First built for `ag_pipeline` (2026-07-23); made a reusable engine block on 2026-10-17.

**When to use it, and when not.** Use it for a sequence. Do not use it for a contrast
between arms (a vague prompt against a pinned one, one model against another): there the
comparison is the point, and the uniform example skeleton (§5) keeps the arms side by side.
Author decision, 2026-10-17: the existing contrast pages keep their layout.

**Shape.**

- **Outer strip:** one tab per step ("Iteration 1", "Iteration 2", …). Step 1 is
  preselected, so the sequence is always visible.
- **Head line:** above each step's tabs, one line that says where the step ended, for
  example "Iteration 3 of 3 — verdict: `compile: pass, run: pass, tests: FAIL`".
- **Inner strip:** the step's own tabs, in the order the step happened, toggle-to-close,
  none preselected. For a pipeline run the order is **Prompt · Reply · Diff · Output · Notes**:
    - **Prompt:** the prompt sent, verbatim. From step 2 on, highlight the evidence fed back.
      On a replay page the prompt is a real tab, not a `<details>` panel: it is primary evidence.
    - **Reply:** the model's complete reply, verbatim, prose and code.
    - **Diff:** in step 1 the full extracted code with line numbers; later, the change
      against the previous step, then the full code with line numbers.
    - **Output:** what the gates said: compiler log, test output, verdict.
    - **Notes:** the author's commentary, ending with a closed "Where these notes point in
      the code" fold that cites Diff-tab line numbers.
- **Key Idea** beside the strip (the block's `concept`), as on every other example.
- **Below the strip:** the example's figure, the tally of every roll (disclosed
  selection), a stop panel if the run ended on a stopping rule, and suggested experiments.
- **No glyphs** on step tabs: a replay shows a tool at work, not a right and a wrong variant.

**YAML.**

```yaml
blocks:
  - replay:
      id: rpl_success_spine      # block id; the Key Idea panel gets the id <id>-ccp
      strip_id: rps              # short CSS id; step k's inner strip is rps-i<k>-tabs
      step_label: Iteration      # the word on the outer tabs (this is the default)
      concept: "..."             # optional Key Idea beside the strip
      steps:
        - head: "<p><strong>Iteration 1 of 2</strong> — verdict: <code>compile: FAIL</code></p>"
          tabs:
            - {label: Prompt, html: "<pre>...</pre>"}
            - {label: Reply, html: "<pre>...</pre>"}
            - {label: Diff, html: "..."}
            - {label: Output, html: "..."}
            - {label: Notes, html: "..."}
```

Engine: `components.replay_strip` and `replay_inner_strip`; builder `render_page._build_replay`;
catalog entry in `yaml_engine/interface_catalog.py`; unit test `cpp_labs/tests/test_replay_block.py`.

**Generate the YAML; do not copy recorded text by hand.** The steps come from the recorded
run's files (`prompt_sent.txt`, `reply.md`, `extracted.cpp`, `compile.log`,
`battery_output.txt`, `verdict.txt`). Write a small `harvest/scripts/gen_page.py` that reads
the run folder and the author's notes file (`harvest/notes/<example>.notes.yaml`: title,
intro, `key_idea`, per-step notes, optional `figure`, tally caption, stop panel,
experiments) and writes `demos/<example>.demo.yaml`. The model is
`cpp_labs/ag_pipeline/harvest/scripts/gen_page.py`. Never edit the generated YAML:
`cpp_labs/tests/test_generators_authoritative.py` regenerates each page and fails on any
difference. Register a new generator there.

**Honesty.** One complete run per example. Never join steps from different runs: step 2's
Prompt must contain step 1's Output word for word, so a joined run is false on its own tabs.
Show the tally of every roll beside the selected run.

**Tests to add** (the `ag_pipeline` module test is the model):

- byte-sync: each Prompt and Reply tab equals its recorded file;
- structure: step 1 checked, every inner "none" radio checked, an open label and a close
  twin for every tab;
- a Key Idea beside each strip, and the figure below the right strip;
- in a browser: copy `harvest/scripts/playwright_toggle_check.py`. Find rail entries by
  their title, not by `lab-rN` ids: the ids shift when the sidebar changes (the old check
  failed for this reason, found 2026-10-17).

## 6. Harvest discipline

- **Harvest scripts are permanent, reusable assets.** Commit them under
  `<subject>/harvest/scripts/`; never clean them up. Start a new module's harvest
  from the most recent module's scripts (the course repo's `ag_models` toolkit:
  streamed bare rolls, OpenCode rolls, Claude Code rolls, resumable sweeps, a
  multi-gate classify harness).
- **Headless rolls:** `claude -p --model <m> --effort <e>` in a fresh directory per
  roll; record tool version and settings in the transcript frontmatter.
- **Local models:** Claude Code drives Ollama **directly** — no proxy: Ollama serves
  the Anthropic Messages API natively
  (`ANTHROPIC_AUTH_TOKEN=ollama ANTHROPIC_BASE_URL=http://localhost:11434 claude -p
  --model <tag> "..."`). Set the env vars **per-invocation only** — exported, they
  redirect ALL Claude Code traffic.
- **Run harvests and page builds in the MAIN session**, not subagents (approval
  prompts for project scripts cannot surface in a subagent and auto-deny).
- **Classify with a script, not by eye** — a `classify.py` applying explicit gates
  (compiled? called the real API? passed the battery?) writes the tally; the page
  quotes the tally.

## 6a. Two-turn transcripts & system-append disclosure

Proven at A12 (`ag_context`); use when a lesson **measures the history layer** —
prior conversation turns as the experimental variable (§4). This is the narrow
two-turn subset, not a general multi-turn format; adopting it decides nothing
about longer sessions.

**Body layout** — four sections, in this order, all present, all verbatim:

```
## Turn 1 — Prompt (verbatim)
## Turn 1 — Reply (verbatim)
## Turn 2 — Prompt (verbatim)
## Turn 2 — Reply (verbatim)
```

**Frontmatter:** `turns: 2` (absent means 1), plus `session:` — the linkage proof
that both turns ran in ONE real session: the Claude Code session id, the resume
mechanism (`claude -p --resume <session-id>` in the same cwd), and the raw log
paths for both turns.

**Honesty extensions (binding):**

- **No fabricated assistant turns, ever.** Turn-1 replies are model-generated,
  verbatim, immutable. If turn 1 fails or is interrupted, discard the whole
  session — a discarded generation, not a sample.
- **The sample unit is the session.** A re-roll redoes both turns; selection
  tallies count sessions.
- **Byte-sync binds the embedded code to the turn-2 reply's code block.** The
  turn-1 reply is archived in full and shown in the replies tab strip.
- Turn-1 replies vary across rolls (they are generations too); any page claim
  about turn-1 content must be checked against ALL rolls, not the exhibit roll
  alone. The tally records turn-2 outcomes.

**Mechanics:** capture the session id from the turn-1 stream-json log; send
turn 2 with `--resume <session-id>` in the **same cwd**; keep both raw logs
(`harvest/rolls/<arm>/rN_t1.log` / `rN_t2.log`). Parallel rolls via `xargs -P4`
are safe when per-roll paths are disambiguated.

**Single-turn `system_append:` extension:** when an arm passes text via
`--append-system-prompt`, a `system_append:` frontmatter field records that text
**verbatim**, and the page discloses it. The rest of the single-turn contract is
unchanged.

## 7. Recorded platform gotchas

Hard-won; check before writing assertions or page wording.

| Gotcha | Consequence |
|---|---|
| ASan on libc++ reports a vector read-past-size as **`container-overflow`** | Encode that string (not `heap-buffer-overflow`) in recorded-reality tests |
| A `sanitize: true` crash console shows **stderr only** (stdout is replaced) | Page wording must not claim printed values are visible on that tab |
| darwin/arm64: `long double` == `double` | A "higher-precision reference" in long double is degenerate — use hard-coded analytic truths from written decimals instead |
| Welford at mean 1e9 has ~7e-9 genuine relative error | An rtol of 1e-9 red-flags CORRECT code; use 1e-8 |
| The engine has no stdin plumbing and inherits a TTY | For cin-reading model code, use the disclosed author frame: `#define main model_main` + `cin.rdbuf` on a fixed dataset |
| `left_rail` renders **one panel per sidebar concept** | Locate a demo's panel by a distinctive block id, never by positional index |
| Box-chain diagrams render at a fixed node width | Do not reintroduce content-driven sizing; notes are HTML captions, not SVG text (DIAGRAMS.md §5a) |
| Engine code windows carry `tabindex="0" role="region" aria-label="Code listing"` (keyboard a11y, 2026-07-20) | Never pin a bare `<pre>` in test regexes — write attribute-tolerant matches |
| In a `left_rail` layout, panels inside **inactive** rail entries have zero client rects | Playwright measurements (tab switch, toggle-to-close, visibility) must first activate the example's rail entry; serve over localhost — `file://` is blocked |
| The engine emits ids only for `callout_note` / `variant_tabs` blocks | Locate hand-authored `html` blocks by distinctive text, not by id or position |
