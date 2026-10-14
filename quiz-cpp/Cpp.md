# Course Profile — ISC5305, Scientific Computing in C++ (Fall 2026)

Read alongside `SKILL.md`. Where the two differ, this file wins.

## Subject matter

Modern C++: classes, functions, pointers and memory, concurrency, data structures, the STL, templates, and the C++11/14/17/20 additions. Roughly 30% of the course is *agentic* — working with AI-generated code — and the quizzes reflect that (see below).

## Fixed composition — every quiz, without exception

**22 items, 15 minutes**, pen and paper, closed computer, five-choice multiple choice.

**Three difficulty tiers, weighted:**

| Tier | Count | Points each | What it is | Time |
|---|:---:|:---:|---|---|
| **L1** | 14 | 1 | recall / concept — definitions, rules, complexity facts | ~25–35 s |
| **L2** | 5 | 2 | short code, single concept — 3–6 printed lines; the answer is a value or a named error | ~45–60 s |
| **L3** | 3 | 3 | multi-step trace — several objects, lifetime or aliasing across them | ~75–120 s |

**33 points total; full credit at 30/33.** The three forgiven points are insurance against a defective item, not a mastery bar. Below 30 the score is proportional — there is no pass/fail cliff.

Generate the tiers in the stated proportion and **label each item's tier** in the instructor key, since the weights depend on it.

**Print the point value on every stem of `quiz.md`** — `1. (3 points) …` — and state the total and the full-credit threshold in the header. Students need the weights to budget 15 minutes rationally, and printing them is safe *because* the allowance is point-based: skipping an L3 item consumes the entire grace, so the weights create no skip-the-hard-ones strategy. **Never print the tier label** (`L1`/`L2`/`L3`) in `quiz.md` — it adds nothing the point value doesn't and invites "L3 = skip it". Tier labels stay in `key.md`.

## Difficulty: err hard

**Unless the author names a difficulty for this quiz** — "medium", say — in which case that request wins: it is passed as the pipeline's `difficulty` argument, which every generator and regenerator receives. Otherwise: a quiz that proves too hard is curved upward afterwards; one that proves too easy cannot be curved down. The correction is one-directional, so pitch high. This is also why L3 items are affordable — a missed trace costs the grace, not the grade.

## Scope

Only **the slides (where provided) and the assigned demonstration pages** for the modules being covered. Nothing outside that scope appears — this is published to students.

Quizzes are **cumulative**: each centres on its three modules, but earlier material stays fair game.

## Agentic items — ~30% of every quiz

The agentic demos run from Module 1 onward (`agentic_spec`, `ag_testgate`, `ag_repair`, `ag_diff`, `ag_evidence`, `ag_explain`), so there is no ramp — every quiz carries the full 30%, starting with Quiz 1.

**Test principles, not recorded tallies.** Never key an item to a number like "0/8 vs 8/8". LLM outputs are distributions; the numbers move with model and temperature, and a student who understands sampling is pushed *away* from the key.

**Judgment is not the same as difficulty:**

- ❌ *"Was this refactor a good idea?"* — an opinion, no defensible key, unusable in MC.
- ✅ *"The agent accepted a patch that deleted a boundary check and all three tests passed — what is the defect?"* — one defensible answer, and hard.

## The strongest L3 pattern in this course

One undefined program, two inputs — one crashes, one prints a clean, correct-looking answer. The trap option is what a student concludes from *running* the code; the key is that **both** runs are undefined.

This is the course's thesis in miniature: passing on the input you happened to try is not evidence. It tests the rule rather than a remembered outcome, and it cannot be answered by pattern-matching.

The built ❌ demo variants are the natural stem source — `pointers_basic`'s dangling return, `class_structure`'s shallow copy, `stl`'s erase-in-loop, `ag_grounding`'s invented API, `ag_context`'s conflicting instructions. Their behavior is machine-verified, which tells you the item is worth asking about — the key still comes from the rule (see below). The stem reproduces the code it needs, as a program or a fragment: the item must be answerable by a student who never saw the demo (the standalone rule in `SKILL.md`).

## Resolving sources — the author names a quiz, not a file list

Given only "Quiz 1", resolve the source list yourself:

1. **Quiz → modules.** The per-quiz coverage table below.
2. **Modules → demos and slides.** `course_site/content/modules/module-NN/_index.md` names each lesson's demo, assigned reading, self-study demos, and slide deck. The module page is an *index* — never quote it as a source.
3. **Demo → YAML.** Each demo lives at `cpp_demos/cpp_labs/<demo>/`:
    - `topics/*.topic.yaml` — the teaching content: `explanation`, plus `✅ correct` / `❌ mistake` code variants under `controls`. **This is the source to cite and quote.**
    - `demos/*.demo.yaml` — the runnable program bound to a topic.
    - `layouts/<demo>.rail.yaml` — which topics appear on the page, in order.
4. **Slides → `cpp_demos/course_materials/week<N>_lesson<M>_<slug>/SLIDES-*.yaml`**, the deck's source (the module page links the compiled `course_site/static/kits/weekNN/slides-lessonM.html`; never read that). `weekNN` means module NN. Report a module with no deck rather than substituting.
5. **A demo split across modules** is tagged by what each module page assigns, not by demo. `class_structure` is Module 2 except *Move operations* (Module 4); the pack builder tags a whole demo with one module, so check the module page before writing an item's `Module` cell.

**Do not read the rendered HTML** in `dist_labs/` or on the deployed site. It is generated from the YAML, it is far longer, and it adds nothing the YAML lacks.

Cite sources as `cpp_labs/<demo>/topics/<topic>.topic.yaml`. A `❌ mistake` variant is the strongest stem material in the repository — a real defect, already written, with the correct form beside it for contrast. Cite it as where the rule is taught; the item itself prints everything the student needs.

**But the recorded behavior is not the answer key.** These variants were run on the author's Mac (arm64, clang). The same program on x86-64 Linux or under gcc or at `-O2` may print a different value, fail differently, or not fail at all; diagnostics and sanitizer output vary by toolchain. The `❌` variant tells you what to *ask about*; the `explanation` field and the standard tell you what to *key*. See the portability rule in `SKILL.md`.

## Source packs — read once, reuse all term

Reading the assigned demos means opening ~114 files for Quiz 1 alone, paid again on every run. A **source pack** collapses that to one file:

```
cpp_demos/quizzes/source_packs/modules_1-3_<YYYY-MM-DD_HHhMMmEST>.md
```

The saving is *files*, not tokens — the pack runs ~40k tokens against ~67k for the raw YAML, a 1.7× reduction. Its real value is one read instead of 114, complete coverage by construction, and a stable citation surface.

**Build it with the script. Never with an agent.**

```bash
cd cpp_demos && python3 -m cpp_labs.make_source_pack \
    --coverage "Modules 1-3" \
    --demo agentic_spec:1 --demo class_structure:2 ... \
    --out quizzes/source_packs/modules_1-3_<timestamp>.md
```

It runs in under a second and costs nothing, so **rebuild on every quiz run** and skip staleness checks entirely — there is no cache to invalidate and no stale pack to detect. Pass `packPath` to `pipeline.js` instead of `sourcePaths`.

This was an LLM distillation step until 2026-07-26. It produced two defects on its only run: it invented a variant label (`Region ordering probe`) to fill a required output field for a topic that has no variants, and it wrote an unresolvable path prefix on all six `function_args` topics. Both are the same failure — an agent filling a slot with something plausible rather than leaving it empty. Transcription is not a job worth a model.

`FILE_CACHING_FOR_QUIZZES.md` specs SHA-256 per-topic caching so only changed topics re-distil. **Obsolete** — a sub-second rebuild has nothing to cache.

**The pack is verbatim, and now provably so.** Each topic's `explanation` and every variant's C++ are byte-identical to what the demonstration page renders, because the builder calls the site's own `expand_variants` / `variant_label` / `generate_source`. `cpp_labs/tests/test_source_pack.py` pins this: every cited path resolves, every label traces to the topic's own YAML, and the emitted source equals the generator's output.

**Cite the topic's own path, never the pack.** And the source-check agent always opens the original YAML, so the pack is never verified against itself. Keep that rule — it is what caught both defects above.

## Where quiz folders live

In the **parent `cpp_demos` repo**, alongside `course_analysis/` and `handoffs/`, one folder per quiz in the course:

```
cpp_demos/quizzes/
    quiz-1/  quiz-2/  quiz-3/  quiz-4/     # matching the coverage table below
        build_<YYYY-MM-DD_HHhMMmEST>/      # one per verification loop
            rounds/round-1/  round-2/  …   # the trace; immutable once written
    source_packs/                          # shared across all four quizzes
```

All four quiz folders exist from the start, so a build never has to decide where to put itself. See `SKILL.md` for what goes in a build folder and in each round.

Folders named `quiz_<N>_<ts>/` or `final_analysis_<ts>/` are from the **retired** batch-and-cut process. Quiz 1 has several, plus the author's own hand-cut notes. They are history: read them if you need provenance, never write into them, and never treat them as inputs to a new build.

**Never under `course_site/`.** That repo is a deployed Hugo site: anything placed in `content/` or `static/` is published, and publishing `key.md` hands students the answers. The two repos are separate git repos and must never be staged across.

## Per-quiz coverage

| Quiz | Module | Date | Covers |
|:---:|:---:|---|---|
| 1 | 4 | Tue Sep. 22 | Modules 1–3 |
| 2 | 7 | Tue Oct. 13 | Modules 4–6 |
| 3 | 10 | Tue Nov. 3 | Modules 7–9 |
| 4 | 13 | Tue Nov. 24 | Modules 10–12 |
