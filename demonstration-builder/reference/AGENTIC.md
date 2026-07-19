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
6. [Harvest discipline](#6-harvest-discipline)
7. [Recorded platform gotchas](#7-recorded-platform-gotchas)

---

## 1. Anatomy and folder shape

An agentic subject extends the standard folder with two directories:

```
cpp_labs/<subject>/topics/        # model code embedded in author harnesses
cpp_labs/<subject>/demos/          # page wiring incl. prompt disclosure
cpp_labs/<subject>/layouts/
cpp_labs/<subject>/tests/          # + byte-sync + invariant tests (see §2)
cpp_labs/<subject>/transcripts/    # one file per roll: prompt + reply, verbatim,
                                   #   with capture-metadata frontmatter
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

## 5. Page grammar

Conventions students see, proven across the series:

- **Prompts are disclosed verbatim, beside the code.** Use the topic block's
  `aside_html:` map (see PATTERN.md §7a): one `<details class="prompt-panel">` per
  variant, keyed by the exact tab label. The prompt switches with the tab.
- **Complete replies** (prose + code, verbatim) live in a `<details>` block at the
  bottom of the example — the code panels embed only each reply's code block.
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
- **❌/✅ glyph grammar** carries over from the C++ series (SKILL.md Step 2): the
  contrast pair is usually `❌ vague/ungrounded/unverified` vs `✅ pinned/grounded/
  verified`.

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
