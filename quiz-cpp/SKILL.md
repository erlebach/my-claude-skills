---
name: quiz-cpp
description: Use when the user asks for C++ quiz or exam items — quiz questions, an item bank, multiple-choice or true/false questions, distractors, or a quiz on a specific C++ topic, module, homework, or demo.
---

# Quiz Authoring

## Overview

Generates quiz items in a fixed LaTeX-compatible plain-text format. The format is not negotiable — it is consumed by a LaTeX pipeline that expects numbered stems, lettered choices, and a `*` marking the key.

This file holds the format and the item-writing craft, which are the same for every course. **The composition of an actual quiz — item counts, difficulty mix, weights, scope — is per-course and lives in a course profile.**

## Course Profiles

| Course | Profile | Read it when |
|---|---|---|
| ISC5305 — Scientific Computing in C++ (Fall 2026) | `Cpp.md` | any C++ quiz for this course |

**Read the matching profile before generating anything.** Its spec overrides every default in this file. If the request names no course and more than one profile exists, ask which course — do not guess, and do not fall back to the generic defaults when a profile applies.

If no profile matches, generate to the defaults below and say so.

## When to Use

- "Write N quiz questions on X" / "make a quiz on templates"
- Building or extending an item bank for a module, lesson, or exam
- Converting homework or lecture content into self-contained assessment items
- Generating distractors for an existing stem

Not for: grading, rubrics, or homework specs.

## Gathering Inputs

Ask **only** for what neither the request nor the course profile supplies, in one message:

1. Course (only if ambiguous and profiles exist)
2. Topic, module, or coverage span
3. Number of questions — default: whatever the profile fixes
4. Question types (true/false, multiple choice, mix) — default: multiple choice
5. Number of choices — default: **5** for multiple choice

If everything needed is already known, generate immediately. Do not ask for the topic when the topic is in the prompt.

## Output Format

Emit the whole quiz inside a single fenced code block so it can be copied verbatim. Inside that block:

- Questions numbered `1.`, `2.`, `3.`, …
- Choices lettered `a)`, `b)`, `c)`, …
- The correct answer is prefixed with `*` — exactly one per question
- True/False items use exactly two choices: `True`, `False`

```
1. Every pointer in C++ occupies the same amount of memory regardless of its type.
*a) True
b) False

2. What does the following program print?
\begin{code}
std::vector<int> v{1, 2, 3};
auto it = v.begin();
v.push_back(4);
std::cout << *it << "\n";
\end{code}
a) 1
b) 4
*c) Undefined behavior — the iterator may be invalidated
d) A compile error
e) 3
```

`\begin{code}` / `\end{code}` are custom LaTeX macros wrapping a verbatim environment. Use them **only** when an item contains source code; never for prose.

## Item Quality Rules

- **Self-contained.** Supplied homework text or images are illustrative context only; the generated item must stand alone without them.
- **Maximize diversity, minimize repetition.** No two items in a set should test the same fact or share a stem pattern.
- **Distractors must be plausible** — each should correspond to a specific misconception, not be obviously wrong filler.
- **A distractor must not punish deeper knowledge.** If a stronger student can defend a second option, the item is defective, not hard. ("Which container does insertion NOT invalidate iterators for?" keyed to `std::list` fails this — `std::map` is equally correct.)
- **Prefer measurable stems to interpretive ones.** "Prints a plausible number" invites two defensible readings; naming the actual value turns the ambiguity into a clean trap.
- **Uniform choice length.** A conspicuously longer or more hedged option gives the key away.
- **No "all of the above" / "none of the above"** unless the user asks for it.
- **Code in stems must compile** (or its non-compilation must be the point of the question).
- **Key the rule, never the observed output.** A program that was run once was run on *one* platform, compiler, and optimization level. What is portable is what the standard says; what is not portable is the printed value, the failure mode (crash vs. junk vs. silent success), the exit code, the sanitizer message, and which diagnostics fire and how they are worded. Plain `char` signedness, `sizeof(long)`, and endianness are implementation-defined and differ across the machines your students actually own.

    The safe framings: *"what is guaranteed?"*, *"is this defined?"*, *"which of these is safe?"* — answers that hold everywhere. The unsafe framing is *"what does this print?"* when the answer is undefined, since it has no portable answer at all. Where an item genuinely needs an observed result, **pin the toolchain in the stem** ("compiled with g++ 13 on x86-64 Linux, no optimization") and accept that it tests that configuration only.

    A verified run tells you the item is *worth asking about*. It does not tell you the key.

## Deliverables

Every quiz is written to its own folder, never to the chat alone. **One folder per quiz in the course, holding one folder per pipeline run:**

```
quiz-<N>/                                   # one per quiz in the course — quiz-1, quiz-2, …
    quiz_<N>_<YYYY-MM-DD_HHhMMmEST>/        # one per pipeline run; a quiz may need several
        quiz.md          # student version — no keys, options shuffled
        key.md           # instructor version — keys, point value, tier, source per item
        source_check.md  # source verification, from a key-aware subagent
        analysis.md      # key-blind review, from a separate subagent
    final_analysis_<YYYY-MM-DD_HHhMMmEST>/  # the quiz the students sit — see Selection
        selection.md     # the pool, compared across runs, for the author to cut from
        quiz.md          # merged, renumbered 1–N
        key.md           # merged, with a run-and-item provenance column
        analysis.md      # one key-blind review over the merged quiz
```

A run folder is an **input**, never the product. It is immutable once written: if an item is amended afterwards, the amendment belongs in the merge, and it re-enters review there. Source packs are shared across quizzes and sit beside the quiz folders, not inside them.

Get every timestamp from `date` — do not invent one. The course profile says where the tree lives; if there is no profile, ask.

`key.md` opens with a composition table — one row per item, carrying tier, points, module, **source**, agentic yes/no, and key. The `Source` cell is a link or path to where the material was taken from, specific enough to reopen: a demo page plus its section, a slide number, a named example. `none` is a legitimate value and means the item was invented — it must be reported, not hidden.

`QUIZ_GENERATION.md` in this directory explains the process in plain language, for the author. It is documentation, not instructions — you do not need to read it to run the pipeline.

## Models and Effort

| Stage | Produces | Model | Effort |
|---|---|---|---|
| Generation | `quiz.md` + `key.md` | Opus 5 | medium |
| Source check | `source_check.md` | Opus 5 | medium |
| Key-blind review | `analysis.md` | Opus 5 | **high** |

The review gets the highest effort because it is the stage doing genuinely hard work: constructing the strongest possible defense of an option it believes is wrong. Generation and source-checking are bounded tasks with a clear target; adversarial review is not.

These are enforced by running the pipeline as a Workflow — the Agent tool has no `effort` parameter, so individual dispatches cannot honour this table. See below.

## Running the Pipeline

**Drive steps 2–5 with the Workflow tool**, using the script in this directory:

```
Workflow({ scriptPath: "~/.claude/skills/quiz-cpp/pipeline.js", args: {...} })
```

The user has given standing authorization for this orchestration as part of this skill — no separate opt-in is needed each time.

`args` supplies: `course`, `coverage`, `itemCount`, `composition`, `sourcePaths` (the actual demo pages and slide decks, read in step 1), `profilePath`, `formatRules`, and any `extraInstructions`. The script has no filesystem access and no `Date` — take the timestamp from `date` yourself and pass anything else in through `args`.

It returns `{quiz, key, source_check, analysis, unsourced}` as text. **You write the four files**, then do step 6.

Two properties this buys, worth preserving if the script is ever edited:

- **The two checking stages run in parallel.** They depend only on the finished quiz, so nothing is gained by ordering them.
- **Blindness becomes structural.** Nothing reaches disk until the workflow returns, so at review time `key.md` does not exist and the key text never enters the reviewer's prompt. Do not "simplify" this by writing the files early and pointing the reviewer at a path.

Falling back to three separate Agent dispatches still works, but effort then inherits the session's — say so in the final report rather than implying the review ran at high effort.

### A failed run writes nothing — say so

Because the caller writes the files, a run that fails produces **no files at all**, and an empty run folder is indistinguishable from a run that never happened. Never let that pass silently: if `quiz` or `key` comes back degenerate, report the failure and state plainly that nothing was written. See `file-manifest` in the user's feedback memory — every turn ends with the list of files created or modified, including "none".

### Validate the returned documents before writing anything

`pipeline.js` enforces a floor (see `assertUsable` in the script), but check the content yourself too, because the schema only guarantees *a* string:

- **`quiz` and `key` are real documents**, not a placeholder, a path, or a summary. A generation agent has completed the entire task — read the pack, authored ten items, compiled every stem — and then emitted the literal string `placeholder` into both fields, destroying the run. The work is not the return value; only the return value is.
- **The item numbers you asked for are present** in `quiz`. Grep for them.
- **No key leaked into `quiz`** — no `*` prefixes, no tier labels, no answer list.
- **Every code stem compiles as printed.** Extract the `\begin{code}` blocks and run them through the compiler yourself. Do not accept the key's claim that it compiled them; that claim has been wrong.

If any check fails, re-run rather than repair. Bust the agent cache by editing the prompt — a `resumeFromRunId` with an unchanged prompt replays the same bad result from cache.

### The checking agents need somewhere to stop

Handed a placeholder instead of a quiz, the key-blind reviewer refused and said why: fabricating items and then reviewing its own fabrications would produce a document that looks authoritative while carrying zero information. The source-check agent did the opposite — it searched the repo, found an *older run's* `key.md`, and verified that instead, returning a detailed and entirely off-target report about items nobody had asked about. Both dispatches should carry an explicit instruction: **if the material you were given is not a quiz, stop and say so; do not go looking for a substitute.**

## Authoring Pipeline

0. **Build the source pack.** If the course profile defines packs, run its builder command to write a fresh one for this quiz's span. It is a script, not an agent: it costs nothing and finishes in under a second, so build on every run rather than hunting for a reusable pack or checking one for staleness. This step is automatic — never ask whether to build a pack, and never skip it silently.

    **A pack is never built by a subagent.** Extraction is transcription, and a model asked to transcribe into a fixed output shape will fill an empty required field with something plausible rather than leave it empty — inventing a variant label, or a path prefix that does not resolve. Both were observed. Keep this stage deterministic.

1. **Read the source material first.** Open the actual assigned demo pages and slides for the modules being covered — not the module index pages, not a summary, not your memory of them. A module page's one-line demo description is a pointer, not content: an item written from *"raw memory: decay, span, the off-the-end pointer"* is invented, not sourced, and it will be the item that fails review. If a source is missing (no slide deck exists, a demo page is unwritten), **say so before generating** and note which items therefore have no source.
2. **Dispatch one generation subagent** (`general-purpose`, `model: opus`) to author the quiz. Give it the material read in step 1. It generates roughly twice the target item count as candidates, cuts to the required number, and returns **both** `quiz.md` and `key.md` in one message, as text.

    That internal over-generate-and-cut is invisible: the candidates never reach disk and the cut is made by the same agent that wrote them. Acceptable for a small quiz, not for a full one — see **Batched generation and selection** below, where the pool becomes visible artifacts and the author makes the cut.

    **One dispatch, both files.** Never split generation across two agents or two passes — two authors produce two truths, and a stem edit that doesn't propagate to the key is the classic failure. Whatever welds them must see them together.

3. **Transcribe both files verbatim**, then check `quiz.md` yourself before going further: no `*` marks, no tier labels, no answer list, point value printed on every stem. A key that leaks into the student file invalidates every later stage.
4. **Dispatch a source-check subagent** to produce `source_check.md`. Each item's `Source` entry in `key.md` must be a real path or URL plus the section it came from — `/demos/array_pointer/ § "the off-the-end pointer"`, not `array_pointer`. The agent reads `key.md` and opens every cited source. Like the reviewer, it cannot write files: it returns its findings as text and you transcribe them verbatim into `source_check.md`.

    This agent sees the keys, so it can **never** be the key-blind reviewer — two separate dispatches, always. Run it before step 5, so an unsourced item is known before the blind review is spent on it.

    Per item it reports: the cited source; whether that source exists; whether the cited section actually supports the item's claim — `SUPPORTED` / `PARTIAL` / `UNSUPPORTED` / `NO SOURCE`; and **any term the item depends on that the source never introduces**. That last check is the one that catches items testing vocabulary the course has not taught, which no other stage in this pipeline can see.
5. **Dispatch a key-blind subagent** to review the quiz — `general-purpose`, `model: opus`, high effort, run synchronously. This is the stage worth the most compute. **The subagent cannot write files** — a harness rule requires subagents to return findings as text. Ask it to return the full review in its final message, then transcribe that verbatim into `analysis.md` yourself. Do not summarize it; the per-option paragraphs are the artifact.
6. **Compare `analysis.md` against `key.md` yourself** and report, in chat, every item where the reviewer's answer differs from the key or where it judged two options defensible, together with every `UNSUPPORTED` / `NO SOURCE` item from `source_check.md`. Those are the items to rewrite. Do not silently "fix" the quiz — the disagreements are the product.

    End the report with the **file manifest** — every file created or modified, by full path, and the words "no files created or modified" when a run produced none.

An item with no source is not automatically wrong, but it is unscoped: nothing guarantees the student was taught it, or taught it in the vocabulary the item uses.

The check that matters is not "is the key right?" but **"can a strong student defend a second option?"** — a different question, and it gets skipped unless asked separately.

### The key-blind rule

**The subagent must see `quiz.md` and nothing else.** Not `key.md`, not the candidate pool, not your reasoning, not which items you already suspect. A reviewer who has seen the key cannot tell you whether the key is findable — it will rationalize toward the answer it was given. If the subagent is contaminated, the review is worthless and must be re-run from a fresh agent.

Dispatch prompt, in substance:

> Read `<path>/quiz.md` and nothing else — a file named `key.md` sits next to it, and opening it invalidates the review. You are answering this quiz cold; no answer key exists for you. Return your full review as your final message. For **every question**, give: your chosen answer and confidence; then **one paragraph per option** — a–e, including your own choice — stating the strongest case a well-prepared student could make for it and why it is finally right or wrong; the specific misconception each wrong option would catch, or `WEAK` if it would catch nobody; a difficulty estimate; and a flag `AMBIGUOUS` if two or more options are genuinely defensible, naming them. Do not skip options you consider obviously wrong — say why they are obviously wrong. Judge only from the printed item; do not consult outside sources for what the instructor "probably meant".

## Batched generation and selection

**One agent writing more than ~10 items drifts and repeats.** Above that count, generate in **batches of ~10**, each a complete pipeline run (steps 0–6) into its own run folder, each authored from the same pack and blind to the others. Number items continuously across batches — 1–10, 11–20, 21–30 — so an item keeps one identity from generation through to the final quiz.

Size the pool at roughly **1.4× the target**: enough that a defective item can be dropped rather than repaired, not so much that whole batches are wasted. Three batches of 10 for a 22-item quiz is the worked case.

Batching moves work that a single run does invisibly out into the open, and adds three stages:

7. **Build the selection sheet** — `final_analysis_<timestamp>/selection.md`. This is the first time anything compares the batches against each other; no reviewer in any run could see across that boundary.

    **First decide which runs are in the pool.** The default is every `quiz_<N>_<ts>/` folder under `quiz-<N>/`, but the author may name a subset, and the default is not always right: a quiz folder accumulates abandoned pilots and scaled-down test runs alongside the real batches. Before reading anything, list each run folder with the item numbers its `quiz.md` contains, and apply these rules:

    - **Colliding item numbers mean STOP.** If two runs both contain an item 3, they are two different item 3s — the numbering is supposed to be continuous across batches precisely so this cannot happen. Do not merge, do not renumber, do not pick one. Show the author the table of runs and item ranges and ask which runs belong in the pool. A silently merged collision corrupts every table in the sheet.
    - **A run missing `source_check.md` is a pilot, not a batch.** It never completed the pipeline, so its items carry no source verdicts and cannot be compared on equal terms. Flag it and ask.
    - **Record the decision in the sheet.** Open `selection.md` with the list of run folders included and, if any were excluded, which and why. A reader must be able to tell what the pool was made of without opening five directories.

    Then read the `quiz.md`, `key.md` and `source_check.md` verdict lines of each **included** run, and write:

    - **One table per tier**, every item as a row: number, points, module, source demo and topic, a one-line summary of what it asks, agentic yes/no, and flags.
    - **The tier arithmetic** — pool count, slots, cuts required, per tier. State which tier binds; it is usually the highest one, where the pool is thinnest and the flags concentrate.
    - **Overlap clusters**, ordered by how strongly they collide. Two items from the same topic file testing one principle from both sides is the common case, and neither batch's reviewer could have caught it. Say what choosing one over the other costs.
    - **Coverage** — items per demo and per module across the whole pool. Name any demo represented by a single item, since cutting it drops that demo from the quiz.
    - **Defects** — items that do not compile as printed, `PARTIAL`/`UNSUPPORTED` source-check verdicts, and any item amended by hand after its batch review.
    - **A worksheet** — the item numbers listed by tier, for the author to strike through, plus the agentic numbers for the ~30% count.

    Summarize nothing away. Flags are reported per item; the sheet is a comparison instrument, not a recommendation.

    **A later sheet supersedes an earlier one; it never edits it.** When a new batch widens the pool, write a **new** `final_analysis_<ts>/` and leave the old sheet untouched — its timestamp records the pool as it stood, and editing 30 items' worth of tables under a name that says `19h24` makes the name a lie. Carry the unchanged rows forward **verbatim from the old sheet** rather than re-deriving them from the run folders: the rows were already checked once, and re-transcription is where errors enter. Note at the top which sheet this one supersedes.

8. **The author selects.** Not an agent, and not you. Present the sheet and stop. If a tier comes up short after the cuts, the author names the tier and its demos, and you run **one more batch of that tier only** — which returns to step 7 for the new items.

9. **Merge, then review once more.** Renumber the survivors 1–N, rebalance the key letters (each batch was internally balanced, so a subset will not be), carry a provenance column in the merged `key.md` giving each item's run folder and original number, and run **one fresh key-blind review over the merged quiz**. That final review is also what covers any item amended by hand after its batch review — the state the pipeline otherwise exists to prevent.

**An item edited after its review is unreviewed.** This is the rule the whole structure protects. Amendments made in response to a source check are edits like any other: they do not go back into the run folder, they go into the merge, and the merged review is what clears them.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Generating before reading the course profile | Profile first; its spec overrides these defaults |
| Giving the review subagent the key, or "just a hint" | Key-blind means blind; re-run from a fresh agent if contaminated |
| Emitting the quiz only in chat | Always write the three files to the quiz folder |
| Inventing the folder timestamp | Take it from `date` |
| Editing flagged items without telling the user | Report every disagreement; the author decides |
| Cutting the pool down to 22 yourself | The author selects; you build the sheet and stop |
| Amending an item after its review and shipping it | The amendment is unreviewed until the merged review clears it |
| One agent asked for 22 items in one pass | Batches of ~10, numbered continuously, pool at ~1.4× |
| Writing a run folder's items straight into the final quiz | Run folders are inputs; the quiz is built in `final_analysis_<ts>/` |
| Asking for the topic when it was already given | Generate; ask only for genuinely missing inputs |
| Four choices by default | Five, unless specified |
| Marking the key with bold, `(correct)`, or an answer list at the end | Only the `*` prefix, inline |
| `\begin{code}` around plain prose | Code only |
| Answer key positionally biased toward `c)` | Distribute keys across all letters |
| Writing the returned `quiz`/`key` to disk unchecked | Validate first: real documents, right item numbers, no key leak, every stem compiles |
| Trusting `key.md`'s claim that the stems compile | Extract the code blocks and compile them yourself |
| Resuming a failed run with the prompt unchanged | Cached agents replay the same bad result; edit the prompt to bust the cache |
| A checking agent hunting for a substitute when handed no quiz | Tell both checkers to stop and report, never to go find another target |
| Reporting a failed run without saying no files were written | An empty run folder is invisible; state the manifest, including "none" |
| Pooling every run folder because the default says "all" | List runs and item ranges first; colliding numbers or a missing `source_check.md` means stop and ask |
| Editing an existing `selection.md` when the pool grows | Write a new `final_analysis_<ts>/`; carry unchanged rows forward verbatim |
