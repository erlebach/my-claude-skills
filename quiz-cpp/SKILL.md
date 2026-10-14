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

`quiz.md` is written in this format — the skill's only quiz file, which the author's own script turns into LaTeX. Inside it:

- Questions numbered `1.`, `2.`, `3.`, …
- Choices lettered `a)`, `b)`, `c)`, …
- The correct answer is prefixed with `*` — exactly one per question
- True/False items use exactly two choices: `True`, `False`
- **Code comes before the question.** An item with code opens `N. (P points) Consider the program:` or `N. (P points) Consider the code fragment:` — or, for an agentic item, a one-line scenario in their place ("A model wrote `stem` below:") — then the code block, then the question sentence, then the choices. Keep `N. (P points)` on the first line — `cpp_labs/quiz_parse.py` and the author's LaTeX script key on it.
- **Show code, do not describe it.** A stem that would say "`Shape` declares `virtual double area() const = 0;` and `Square` derives publicly from it" writes those declarations as a fragment instead. A fragment need not be a whole program — no `main`, no includes — but it must compile once a harness adds the standard includes and, for bare statements, wraps them in a function. Items with no code at all stay as prose.

```
1. (1 point) A reference must be bound to an object when it is declared.
*a) True
b) False

2. (2 points) Consider the code fragment:
\begin{code}
std::vector<int> v{1, 2, 3};
auto it = v.begin();
v.push_back(4);
std::cout << *it << "\n";
\end{code}
Which statement about the last line is correct?
a) It prints 1, because it still refers to the first element.
b) It prints 4, because push_back moved it to the new element.
*c) Its behavior is undefined, because push_back may have invalidated it.
d) It does not compile, because it was invalidated by push_back.
e) It prints 3, because it now refers to the last original element.
```

`\begin{code}` / `\end{code}` are custom LaTeX macros wrapping a verbatim environment. Use them **only** when an item contains source code; never for prose.

## Item Quality Rules

- **Standalone: knowledge of C++ and reasoning, never memory of an example.** A student must be able to answer from the item itself plus the C++ rules the course teaches. Every fact the answer needs is either such a rule or printed in the item. Never require the student to remember a specific demo, slide or homework example — its class names, its values, its story, or a line it showed that the item does not. Supplied homework text or images are illustrative context only.

    Code in a stem must contain whatever triggers the behaviour asked about. Quiz 2 (Oct) item 14 showed `class Grid1D : public std::vector<double>` with only a constructor and asked what problem the design creates; the problem — a `g.resize(8)` that breaks the grid's invariant — lived only in the demo, so the item tested recall of the demo, not reasoning. Item 21 hinged on what `-DNDEBUG` does, which the stem never mentioned and the course said once. A defined course term (a named rule, a gate of a taught checklist) is knowledge and may be used; a particular example is not.

    A demo's ❌ variant may supply the raw material, but the stem reproduces whatever it needs, in full, and is answerable by someone who never saw the demo.
- **Maximize diversity, minimize repetition.** No two items in a set should test the same fact or share a stem pattern.
- **Distractors must be plausible** — each should correspond to a specific misconception, not be obviously wrong filler.
- **A distractor must not punish deeper knowledge.** If a stronger student can defend a second option, the item is defective, not hard. ("Which container does insertion NOT invalidate iterators for?" keyed to `std::list` fails this — `std::map` is equally correct.)
- **Prefer measurable stems to interpretive ones.** "Prints a plausible number" invites two defensible readings; naming the actual value turns the ambiguity into a clean trap.
- **Uniform choice length.** A conspicuously longer or more hedged option gives the key away.
- **No "all of the above" / "none of the above"** unless the user asks for it.
- **Code in stems must compile** (or its non-compilation must be the point of the question) — a whole program as printed, a fragment once a harness adds the standard includes and, for bare statements, wraps them in a function.
- **Key the rule, never the observed output.** A program that was run once was run on *one* platform, compiler, and optimization level. What is portable is what the standard says; what is not portable is the printed value, the failure mode (crash vs. junk vs. silent success), the exit code, the sanitizer message, and which diagnostics fire and how they are worded. Plain `char` signedness, `sizeof(long)`, and endianness are implementation-defined and differ across the machines your students actually own.

    The safe framings: *"what is guaranteed?"*, *"is this defined?"*, *"which of these is safe?"* — answers that hold everywhere. The unsafe framing is *"what does this print?"* when the answer is undefined, since it has no portable answer at all. Where an item genuinely needs an observed result, **pin the toolchain in the stem** ("compiled with g++ 13 on x86-64 Linux, no optimization") and accept that it tests that configuration only.

    A verified run tells you the item is *worth asking about*. It does not tell you the key.

## Deliverables

Every quiz is written to its own folder, never to the chat alone. **One folder per quiz in the course, holding one folder per verification loop:**

```
quiz-<N>/                                    # one per quiz in the course — quiz-1, quiz-2, …
    build_<YYYY-MM-DD_HHhMMmEST>/            # one per loop; the quiz is built here, start to finish
        quiz.md          # CURRENT quiz — every item, correct choice marked `*`; the instructor's script makes the LaTeX sheets from it
        key.md           # CURRENT instructor version — keys, points, tier, source per item
        source_check.md  # current source verification
        analysis.md      # current key-blind review
        quiz_blind.md    # quiz.md with the `*` removed — the key-blind reviewer's input, never a deliverable
        loop_state.json  # THE LOOP'S OWN STATE — see below
        rounds/
            round-1/                 # immutable snapshot of the round, written when it ends
                quiz.md  key.md  source_check.md  analysis.md
                quiz_blind.md        # the round's reviewer input (same rule as the top-level copy)
                facts.txt            # one line per item: the single fact it tests — the ledger
                verdicts.json        # per-item source verdict, machine-readable
                duplication.json     # item pairs testing the same fact, with confidence
            round-2/                 # …plus replacements.json: which items were regenerated, and why
```

**`loop_state.json` is not optional bookkeeping — without it the loop's state lives only in the session's head.** Write it at the build root and update it every round. It carries: the round number and the cap; per-item regeneration attempts (so the two-attempt escalation limit is checkable, not remembered); each round's gate result, verdict counts, disagreements, ambiguous items, `same_fact` pairs and blocking set; the measured cost; **every termination rule evaluated at the end of each round with its verdict and the resulting decision**; the items kept despite a flag and why; and any decision outstanding for the author.

The test: a fresh session must be able to open that one file and say what round it is on, which items are near escalation, why the loop did not stop last round, and what it has chosen not to fix. Re-deriving that from four round folders is how a resumed loop repeats a round or blows past its cap.

**An incomplete round folder must say so.** A round that has been regenerated and gated but whose checks are still running looks exactly like a round that died — same four missing files. Drop a `STATUS.txt` naming which artifacts are final, which are pending, and the words *incomplete, not failed*; delete it when the check artifacts land. This is the same rule as "a failed run writes nothing — say so", one level down.

The **top-level files are the product**; the `rounds/` folders are the trace. A round folder is immutable once written — a later round writes a *new* folder and refreshes the top-level copies. Never overwrite a round; the whole point is that the repair history is inspectable.

Source packs are shared across quizzes and sit beside the quiz folders (`quizzes/source_packs/`), not inside them.

**A second question set for the same quiz** is a new `build_<timestamp>/` in the same `quiz-<N>/` folder. Hand the generators the earlier set's `quiz.md` path with the instruction not to reuse its stems or code, and not to test the same fact from the same angle. They never open its `key.md`.

Write files with `command cp` / `command rm`: in this shell both are aliased to interactive, and a plain `rm` waits on a prompt nobody answers.

Get every timestamp from `date` — do not invent one. The course profile says where the tree lives; if there is no profile, ask.

`key.md` opens with a composition table — one row per item, carrying tier, points, module, **source**, agentic yes/no, and key. The `Source` cell is a link or path to where the material was taken from, specific enough to reopen: a demo page plus its section, a slide number, a named example. `none` is a legitimate value and means the item was invented — it must be reported, not hidden.

`QUIZ_GENERATION.md` in this directory explains the process in plain language, for the author. It is documentation, not instructions — you do not need to read it to run the pipeline.

## Models and Effort

| Stage | Produces | Model | Effort |
|---|---|---|---|
| Generation — one agent per tier, L3 → L2 → L1 | `quiz.md` + `key.md` + `facts.txt` | Opus 5 | medium |
| Source check | `source_check.md` + `verdicts.json` | Opus 5 | medium |
| Key-blind review | `analysis.md` | Opus 5 | **high** |
| Duplication | `duplication.json` | Opus 5 | **high** |

The review and the duplication pass get the highest effort because they are the stages doing genuinely hard work: constructing the strongest possible defense of an option it believes is wrong, and finding a shared fact under two items that cite different files. Generation and source-checking are bounded tasks with a clear target; adversarial work is not.

These are enforced by running the pipeline as a Workflow, which sets each stage's effort. A plain Agent dispatch may set effort only when the author explicitly asks for it, so separate dispatches cannot honour this table on their own. See below.

## Running the Pipeline

**Drive the generation and check stages — steps 2 and 4–6 — with the Workflow tool**, using the script in this directory. Step 3's gate and step 7's decision stay with you, because the script has no filesystem and cannot compile C++:

```
Workflow({ scriptPath: "~/.claude/skills/quiz-cpp/pipeline.js", args: {...} })
```

The user has given standing authorization for this orchestration as part of this skill — no separate opt-in is needed each time.

`args` supplies: `course`, `coverage`, `itemCount`, `composition`, `tiers` (the tier/count/points list, in **descending** order), `packPath` (the source pack built in step 0 — preferred) or `sourcePaths` (the topic YAML and slide-deck files, read in step 1), `profilePath`, `formatRules`, `difficulty` (only when the author named one — it overrides the profile's default and reaches every generator and regenerator), and any `extraInstructions`. The script has no filesystem access and no `Date` — take the timestamp from `date` yourself and pass anything else in through `args`.

It returns `{quiz, key, facts, source_check, verdicts, analysis, duplication, unsourced}` as text and data. **You write the files**, then do step 6.

**Rounds 2 and later skip generation entirely.** Pass `preAuthoredPaths` (or `preAuthored`) with the current `quiz`/`key`/`facts` plus `blindQuiz` — the path to that round's starless `quiz_blind.md`, which the script requires because `quiz.md` carries the `*` key — and the script re-runs only the three checks over the quiz that already exists. Without this the loop is not a loop: every round would rewrite all 22 items and throw away the ones that already passed.

Three properties this buys, worth preserving if the script is ever edited:

- **The three checking stages run in parallel.** They depend only on the finished quiz, so nothing is gained by ordering them.
- **Generation is sequential and tier-descending**, because each tier is handed the facts ledger of the tiers above it. That dependency is the point; do not "optimize" it into a `parallel()`.
- **Blindness is structural in round 1 only.** Nothing reaches disk until the workflow returns, so at review time `key.md` does not exist. From round 2 on the files are on disk and the reviewer *could* find the key — the prompt therefore says the key exists, says not to look, and says why, rather than asserting something false. Do not restore the false claim.

Falling back to separate Agent dispatches still works, but effort then inherits the session's — say so in the final report rather than implying the review ran at high effort.

### Watching a round while it runs

**Nothing reaches disk until the workflow returns**, because the sandbox has no filesystem — `pipeline.js` cannot write a file, and the caller writes everything from the returned values. On Quiz 2's round 1 that meant generation finished at 22:50 and the files appeared at 22:56. Two channels exist in the meantime:

- **`journal.jsonl` — live, updated during the run.** One `{"type":"result",...}` line per agent, carrying its *full* return value, appended the moment that agent finishes. This is how you read the L3 items while the L1 author is still writing. Path:

    ```
    <session>/subagents/workflows/wf_<runId>/journal.jsonl
    ```

    The `runId` comes back in the Workflow tool result. `log()` lines do **not** appear here — only agent results.

- **The task output file — `log()` lines, written when the run completes.** Top-level `logs` array, alongside `workflowProgress` (per-agent timing, tokens, tool calls). Path:

    ```
    /private/tmp/claude-501/<project-slug>/<session-id>/tasks/<taskId>.output
    ```

**Because `log()` is the only channel out of a running workflow, log the items themselves, not a count of them.** The tier loop emits each tier's full `quiz` text and its facts ledger as they land, so the live `/workflows` display shows the actual questions. Do not "tidy" these back into summary counts — a count tells you a stage finished, which you already knew from the progress tree.

### A failed run writes nothing — say so

Because the caller writes the files, a run that fails produces **no files at all**, and an empty round folder is indistinguishable from a round that never happened. Never let that pass silently: if `quiz` or `key` comes back degenerate, report the failure and state plainly that nothing was written. See `file-manifest` in the user's feedback memory — every turn ends with the list of files created or modified, including "none".

### Validate the returned documents before writing anything

`pipeline.js` enforces a floor (see `assertUsable` in the script), but check the content yourself too, because the schema only guarantees *a* string:

- **`quiz` and `key` are real documents**, not a placeholder, a path, or a summary. A generation agent has completed the entire task — read the pack, authored ten items, compiled every stem — and then emitted the literal string `placeholder` into both fields, destroying the run. The work is not the return value; only the return value is.
- **The item numbers you asked for are present** in `quiz`. Grep for them.
- **Exactly one `*` per item in `quiz`**, on a lettered choice line — and no tier labels, no answer list.
- **Every code stem compiles** — a whole program as printed, a fragment once a harness adds the standard includes and, for bare statements, wraps them in a function. Extract the `\begin{code}` blocks and run them through the compiler yourself. Do not accept the key's claim that it compiled them; that claim has been wrong.

If any check fails, re-run rather than repair. Bust the agent cache by editing the prompt — a `resumeFromRunId` with an unchanged prompt replays the same bad result from cache.

### The checking agents need somewhere to stop

Handed a placeholder instead of a quiz, the key-blind reviewer refused and said why: fabricating items and then reviewing its own fabrications would produce a document that looks authoritative while carrying zero information. The source-check agent did the opposite — it searched the repo, found an *older run's* `key.md`, and verified that instead, returning a detailed and entirely off-target report about items nobody had asked about. Both dispatches should carry an explicit instruction: **if the material you were given is not a quiz, stop and say so; do not go looking for a substitute.**

## Authoring Pipeline

0. **Build the source pack.** If the course profile defines packs, run its builder command to write a fresh one for this quiz's span. It is a script, not an agent: it costs nothing and finishes in under a second, so build on every run rather than hunting for a reusable pack or checking one for staleness. This step is automatic — never ask whether to build a pack, and never skip it silently.

    **A pack is never built by a subagent.** Extraction is transcription, and a model asked to transcribe into a fixed output shape will fill an empty required field with something plausible rather than leave it empty — inventing a variant label, or a path prefix that does not resolve. Both were observed. Keep this stage deterministic.

1. **Read the source material first.** Open the actual assigned demo pages and slides for the modules being covered — not the module index pages, not a summary, not your memory of them. A module page's one-line demo description is a pointer, not content: an item written from *"raw memory: decay, span, the off-the-end pointer"* is invented, not sourced, and it will be the item that fails review. If a source is missing (no slide deck exists, a demo page is unwritten), **say so before generating** and note which items therefore have no source.
2. **Generate exactly the target count, one agent per tier, hardest tier first.** No pool, no over-generation, no cut. Each tier agent gets the material read in step 1 and returns **`quiz`, `key` and `facts` for its own items in one message**.

    **Tier-descending — L3, then L2, then L1 — is the load-bearing decision.** An L3 item is a multi-step trace whose fact-set is a *superset* of several L1 facts, so writing the small items first leaves the big ones nothing to build from. Every cross-tier collision in Quiz 1's original 40-item pool ran higher-contains-lower, with no counterexample.

    **The facts ledger is what makes it work.** Each tier returns one line per item — *"shallow copy leaves two objects pointing at one block, and both destructors free it"*, not *"copy semantics"* — and every later tier is handed every line already spent, with instructions not to test any of them, nor a narrower version of one. A vague ledger line causes a duplicate item two tiers later.

    **One dispatch per tier, both files together.** Never split a tier's quiz and key across two agents or two passes — two authors produce two truths, and a stem edit that doesn't propagate to the key is the classic failure. Whatever welds them must see them together.

    This replaces the batch-and-cut process — see **The verification loop** below for why generating a pool and cutting it could not work.

3. **Transcribe the files verbatim**, then run the **deterministic gate before anything else**: parse `quiz.md` with `cpp_labs/quiz_parse.py` (it reads the `*` into each item's `key`) and compile every code block with the engine's own `g++ -std=c++20` — whole programs as printed; fragments with the standard includes prepended and bare statements wrapped in a function. It costs about a second and it is the only check in the pipeline that cannot be wrong. Then check `quiz.md` yourself: exactly one `*` per item, on a choice line; no tier labels, no answer list; point value printed on every stem. Write `quiz_blind.md` beside it — the same text with the `*` removed — for the key-blind reviewer.

    A stem that does not compile is a blocking finding **unless non-compilation is the item's key** — Quiz 1's item 5 is keyed to "rejected at compile time", and the gate must not be allowed to regenerate it.

4. **Source check** → `source_check.md` **and `verdicts.json`**. Each item's `Source` entry in `key.md` must be a real path or URL plus the section it came from — `cpp_labs/array_pointer/topics/ptr_decay.topic.yaml § "the off-the-end pointer"`, not `array_pointer`. The agent reads `key.md` and opens every cited source.

    This agent sees the keys, so it can **never** be the key-blind reviewer — separate dispatches, always.

    Per item it reports: the cited source; whether that source exists; whether answering needs memory of that specific example rather than the rule it teaches (`example_recall`); whether the cited material supports the item — `SUPPORTED` / `PARTIAL` / `UNSUPPORTED` / `NO SOURCE`; whether the key rests on a recorded observation rather than a rule (`platform_dependent`); and **any term the item depends on that no source in the corpus introduces**. That last check catches items testing vocabulary the course has not taught, which no other stage can see.

    **The criterion is "are the premises taught?", never "is the conclusion stated?"** The quiz tests deduction, so an L2 or L3 item is properly grounded when the corpus teaches every fact the student must *combine* — the combination itself appearing nowhere is the exercise, not a gap. Run the other way and the rule bites harder: **for an L3 item, a key stated verbatim in the corpus is a defect** — a recall item priced at three points.

    This distinction is what separates two findings that look identical. Quiz 2's item 5 was correctly killed: its key needed *name hiding*, a concept absent from the whole corpus, so no chain of taught reasoning reached the answer — the student could not even read the question properly. Item 3 was flagged three rounds running and correctly kept: it needs `tpl_special`'s "pointers take the partial" plus `tpl_deduce`'s argument deduction, both taught, composed into a conclusion stated nowhere. **An untaught premise or an untaught word blocks; an underived conclusion is the point of the item.**

    When a `PARTIAL` turns out to be this — a derived step the checker wanted verbatim — the fix is usually to widen the `Source` cell to name every topic the derivation draws on, and to make the key's rationale argue the student's route rather than the instructor's. Quiz 2's item 3 needed exactly that: cite `tpl_deduce` alongside `tpl_special`, and refute the `const char*` distractor with the source's own "any pointer" wording instead of const-absorption mechanics the student never needs.

    **Verdicts are data, not prose.** The agent returns a `verdicts` array alongside its report, one entry per item, and the flagged set is a *filter over that array* — never something read out of the report's tables. This exists because reading failed: four flagged items were reported as two, from skimming one column of a 22-row table while the totals line two screens below said otherwise. **When a number matters, parse it — do not read it.** An item flagged in the prose but absent from the array is silently kept, so the array is what the loop obeys.

5. **Key-blind review** → `analysis.md`, at high effort. This is the stage worth the most compute. Its report ends with an eight-column table — `Q | Answer | Confidence | AMBIGUOUS | STANDALONE | weak_count | expected_pass | trap_quality` — read by script, so a cell containing prose breaks it. Transcribe the review verbatim; do not summarize it, the per-option paragraphs are the artifact.

6. **Duplication** → `duplication.json`, at high effort, in parallel with the other two. **This agent sees every question AND every key at once** — the one stage in the pipeline with a whole-quiz view. It must, because a collision is usually invisible from the stems: two items can cite different files while one item's key rests on the other item's exact fact. It reports item *pairs* with a confidence and a `same_fact` flag, and where the two are in different tiers, which contains which.

    This is what the old cross-batch selection sheet was for, and it does the job better: a batch reviewer could never see past its own ten items.

7. **Decide the round.** Collect the blocking set: gate failures, `UNSUPPORTED` / `NO SOURCE` verdicts, `platform_dependent` items, untaught terms, reviewer/key disagreements, `AMBIGUOUS` flags, `STANDALONE` no, `example_recall` items, and duplicate pairs above the confidence bar. If it is empty, the loop has converged. Otherwise regenerate **only those items** and start the next round — see **The verification loop** below.

    Report the blocking set in chat every round, and end with the **file manifest** — every file created or modified, by full path, and the words "no files created or modified" when a round produced none.

An item with no source is not automatically wrong, but it is unscoped: nothing guarantees the student was taught it, or taught it in the vocabulary the item uses.

The check that matters is not "is the key right?" but **"can a strong student defend a second option?"** — a different question, and it gets skipped unless asked separately.

### The key-blind rule

**The subagent must see `quiz_blind.md` — `quiz.md` with the `*` markers removed — and nothing else.** Never `quiz.md` itself: it carries the key. Not `key.md`, not the facts ledger, not your reasoning, not which items you already suspect. A reviewer who has seen the key cannot tell you whether the key is findable — it will rationalize toward the answer it was given. If the subagent is contaminated, the review is worthless and must be re-run from a fresh agent.

**Never tell the reviewer the key does not exist.** In round 1 it happens to be true — nothing has reached disk — but from round 2 on the files are there and the claim is a lie the reviewer can discover. Say the key exists, say not to look, and say why. Structural blindness is an unavoidable casualty of iterating; covering it up with a false assertion is not.

Dispatch prompt, in substance:

> Read `<path>/quiz_blind.md` and nothing else. An answer key for this quiz **does** exist on disk, and so does the source material — do not go looking for either. Opening them invalidates this review completely, because the one question worth answering here is whether the key is findable from the item alone, and a reviewer who has seen the key cannot tell you that. If you find yourself wanting to check something, that wanting is the signal the item may be ambiguous: write that down instead. Return your full review as your final message. For **every question**, give: your chosen answer and confidence; then **one paragraph per option** — a–e, including your own choice — stating the strongest case a well-prepared student could make for it and why it is finally right or wrong; the specific misconception each wrong option would catch, or `WEAK` if it would catch nobody; a difficulty estimate; a flag `AMBIGUOUS` if two or more options are genuinely defensible, naming them; and `STANDALONE` no if the answer depends on a fact, scenario or line the item does not show. Do not skip options you consider obviously wrong — say why they are obviously wrong. End with the eight-column summary table, which is read by a script.

## The verification loop

**The quiz is converged on, not selected from.** Round 1 generates exactly the target count and checks it. Every round after that regenerates only the items that failed and re-runs the checks over the whole quiz. The loop ends when a round finds nothing blocking.

This replaces batch-and-cut, and the reason is arithmetic rather than taste. Quiz 1's 40-item pool at 1.4× produced 16 L1 candidates for 14 slots with only 11 clean — **no defect-free selection from that pool existed**, so the process could not have succeeded no matter how carefully the author cut. Regeneration is not subject to that failure: a flagged item comes with a *stated reason*, which is a repair instruction, where a pool offers only alternatives that were never told what was wrong with the one they replace.

### One round

1. **Regenerate only the flagged items** — `regen.js` in this directory, driven the same way as `pipeline.js`:

    ```
    Workflow({ scriptPath: "~/.claude/skills/quiz-cpp/regen.js", args: {...} })
    ```

    One agent per affected tier, **tier-descending like generation**, each told which item numbers it is replacing, the verbatim finding for each, and the facts ledger of the items it is *not* replacing — which it must still avoid. It reads the current `quiz.md` from disk so it can see what the survivors ask. Everything not named is carried forward byte-identically.

    **Give the agent the finding, not a verdict.** "AMBIGUOUS — options b and c are both true of the printed code; write a replacement whose key is the only true statement in its field" repairs; "item 2 failed review" does not. This is the whole reason regeneration beats selecting from a pool.

    When two items are replaced *because they duplicated each other*, tell the higher tier which fact is now spent and unavailable — otherwise both replacements reach for it again and the collision survives the repair.
2. **Splice, then re-check — scoped by what each check actually depends on.** Pass `changedItems` to `pipeline.js`. The three checks are not alike and must not be scoped alike:

    | check | scope on a repair round | why |
    |---|---|---|
    | source check | **changed items only** | item-local: it opens *that item's* cited source. Nothing about item 12 changes item 7's verdict. |
    | key-blind review | **changed items only** | item-local: it answers each item cold from the printed item alone. |
    | duplication | **reads everything, reports pairs with ≥1 changed item** | pairwise — see below. |

    **Never scope the duplication pass to the changed items alone.** It is the one check whose subject is a *relation*, and on Quiz 2 both round-2 replacements collided with items that had **not** changed that round — 8↔22 at 0.65 and 19↔21 at 0.70. A changed-only pass sees neither. Narrowing what it *reports* is safe and strictly good: pairs of two untouched items were judged in an earlier round, and re-scoring them is where the noise came from.

    **Scope what the agents WRITE, never what they READ.** Every check still receives the whole quiz. The reviewer in particular must keep every question in context, because `AMBIGUOUS` is a whole-quiz judgement wearing an item-level label — it asks whether a student could defend a second option, and what a student can defend depends on what else the quiz asks. A replacement is exactly where new cross-item priming enters: rewrite item 5 to be about undefined behaviour, and an untouched item 12 whose throwaway distractor reads "the behaviour is undefined" can become genuinely defensible. Item 12 did not change; the questions around it did.

    **The round's artifacts stay complete: 22 items in `analysis.md`, 22 in `source_check.md`, 22 in `verdicts.json`.** Seed each from the previous round's file and replace only the changed items' sections. What shrinks is generation, not the artifact. **Assert the merged count equals the item count** before computing anything from it — a scoped round returns two entries, and treating that as the whole picture drops twenty items and manufactures a convergence the loop has not earned.

    **Measured stability, Quiz 2, three independent runs over 15 never-changed items:** answer column **0/15** flips, and no unchanged item was ever newly flagged `AMBIGUOUS`. The soft columns are not stable — `expected_pass` drifted on 14/15 (one item ran 0.65 → 0.85 → 0.75), confidence on 2, `trap_quality` on several. So the blocking inputs are safe to carry forward and the advisory ones should be read as estimates, not measurements, whether or not they were re-run.

    Why it matters: output is ~29% of the bill, and on a repair round the checkers' per-option reports over untouched items are most of it. Round 3 of Quiz 2 rewrote 2 items and still paid for a full 22-item review and source check.

    **A replacement routinely collides with a survivor, and this is not a rare case.** On Quiz 2's round 2, both duplicate-driven replacements landed on top of *different* untouched items — at 0.70 and 0.65, higher than the 0.60 and 0.50 collisions they were written to fix. The regenerating agent had been told explicitly which facts those survivors held, and reached for the neighbouring fact anyway. Naming the spent facts helps; it does not substitute for re-checking. This is the single strongest argument for whole-quiz checks and the reason a round is not finished when the regeneration returns.
3. **Snapshot.** Write `rounds/round-K/` with the round's four documents plus `facts.txt`, `verdicts.json`, `duplication.json`, and `replacements.json` recording which items changed and why. Refresh the top-level copies. Never edit an earlier round.

4. **Update `loop_state.json` before deciding anything.** Record the round's results, then evaluate each termination rule *in the file* — converged, no progress, per-item exhaustion, oscillation, budget, cap — with a verdict for each and the resulting decision. Deciding first and writing it down afterwards is how a rule gets skipped: the same reason verdicts are parsed rather than read.

### What blocks, and what does not

| Finding | Blocks? |
|---|---|
| Stem does not compile, and non-compilation is not the key | **yes** |
| `UNSUPPORTED` / `NO SOURCE` | **yes** |
| `platform_dependent` — key rests on a recorded observation | **yes** |
| Untaught term the item depends on | **yes** |
| Not standalone — the reviewer marks `STANDALONE` no, or the source check sets `example_recall` | **yes** |
| Reviewer's answer differs from the key | **yes** |
| `AMBIGUOUS` — two options genuinely defensible | **yes** |
| Duplicate pair with `same_fact: true` at high confidence | **yes**, once — but see the stability rule below |
| `PARTIAL` | **no** — advisory |

**`PARTIAL` is non-blocking, deliberately.** In every observed case the key was sound and only the citation overreached — invisible to a student, and fixed by editing `key.md`, not by regenerating a good item. Regenerating over a citation gap is how the loop destroys its own best work. This is the assumption most worth revisiting: if a `PARTIAL` ever means the *key itself* is unsupported, promote it.

**A cross-tier duplicate replaces the cheaper item.** A three-point trace over several objects swallows a one-point recall item, so the L1 item is the one to rewrite — replacing the L3 item throws away the more expensive artifact to fix a collision the cheap one caused.

### The duplication check is noisy — use the unchanged pairs as a control

**Its confidence has run-to-run variance comparable to its own decision boundary, and you can measure this for free.** Every round re-scores pairs whose items did not change; those pairs are a built-in control group. If an unchanged pair drifts across the `same_fact` line between rounds, the signal is noise at that threshold and must not be treated as blocking.

Measured on Quiz 2: pair (1, 9) scored **0.40 → 0.50 → 0.55** across three rounds with **neither item ever regenerated** — identical input, verdict crossing `same_fact: true` on the third roll. Pair (7, 17) appeared at 0.20 and then vanished, also unchanged. Meanwhile chasing the flagged pairs went 0.60 → 0.70 → 0.60: each repair produced a fresh collision of comparable size, because ~9–15 pairs are re-rolled every round.

The rule that follows:

- **Compare each round's duplication output against the previous round's**, pair by pair, and mark which pairs contain an item that actually changed.
- **A pair flagged in exactly one round, on unchanged items, is noise.** Do not regenerate for it.
- **A pair is worth acting on when it is newly created by a replacement** — a real consequence of this round's edit — or when it holds across rounds.
- **When only noise-grade pairs remain, the loop has converged for practical purposes.** Take the oscillation exit and escalate what is left; do not spend items against a re-rolling signal.

This does not make the duplication pass worthless — it caught the genuine 2↔8 and 19↔21 collisions, and it is still the only stage with a whole-quiz view. It means its *threshold* is soft where the other checks' are hard. The gate, the source verdicts and the reviewer's answer column are deterministic or near-deterministic; this one is a judgement re-made each run.

### The loop runs to termination without asking

**Never stop between rounds to ask whether to run the next one.** The termination rules below are what make that permission unnecessary — a loop with a written stopping condition does not need one. Report each round's findings as they land and then start the next round **in the same turn**; reporting is not pausing.

Stop only on a condition the rules name: converged, no progress, per-item exhaustion, oscillation, budget, or the hard cap of 5. The single question that *is* the author's — and the only one worth interrupting for — is whether the finished quiz ships.

If you catch yourself wanting to ask "shall I run round 2?", the answer is in **Loop termination** below. If a loop ever genuinely lacks a stopping rule, that is a bug in the loop; write the rule rather than substituting a prompt for it.

### The author reviews; the author no longer cuts

The loop hands over a complete quiz, not a sheet. **Present it when it terminates** — whether it ships is the author's call, and nothing downstream may assume it. Report, per item, anything the loop chose not to act on: surviving `PARTIAL`s, duplicate pairs left standing, and any item that escalated after exhausting its attempts. Those are judgement calls being deferred, and they must be visible as such rather than buried in a round folder.

**An item edited after its review is unreviewed.** This is the rule the whole structure protects, and the loop satisfies it by construction: every round re-checks the entire quiz, so a spliced item is always cleared by a review that saw it. A hand edit made *after* the final round is outside that guarantee — it needs another round, not a note.

## Loop termination — cost-shaped, with a hard backstop

The loop stops when it stops *finding* things, not when it hits a count. But a
cost-shaped rule must never be the only exit, because every one of them depends
on a model's output and a model can always produce one more finding.

**The termination guarantee.** The loop counter increments unconditionally at the
top of every iteration and is never reset, decremented, or skipped on any path,
including error paths and retries. The loop condition includes `round < 5`. That
alone bounds the loop at five iterations regardless of what any agent returns.
Every other rule below can only end it *sooner*.

Write it so the bound is visible in one place:

```
for (let round = 1; round <= MAX_ROUNDS; round++) {   // MAX_ROUNDS = 5, constant
    ...                                              // nothing here touches `round`
}
```

Do not express the bound as `while (!converged)` with a counter incremented
inside, and never `continue` past the increment. Those are the two shapes that
turn a capped loop into an unbounded one.

**Early exits, in the order they fire:**

1. **Converged** — no blocking finding in the round's merged results. The normal
   ending.
2. **No progress** — this round's blocking set is a subset of last round's, with
   nothing newly fixed. The loop is re-reporting what it could not repair;
   another round buys nothing.
3. **Per-item exhaustion** — an item has been regenerated twice. It stops being
   regenerated and escalates on its own, while the other items carry on. Track
   this per item, not globally.
4. **Oscillation** — an item alternates between two failure classes (say,
   `AMBIGUOUS` then a duplicate), or fails the same check twice with different
   content, or an unchanged pair crosses the duplication threshold and back. Escalate
   immediately rather than spending the cap on it.
5. **Budget** — a token or wall-clock ceiling, if one was set.

**Round cost is not flat, so a count is a poor budget — but do not overstate the
saving.** There are two shapes of later round and they cost very differently:

- **A checks-only round** — nothing was regenerated, the quiz is re-verified as
  it stands. 3 agents.
- **A repair round** — the normal case, and the expensive one. Regeneration
  runs *and then* all three checks run again. The source check and the blind
  review report only on the changed items but still read the whole quiz; the
  duplication pass reads everything. So **a check's input is priced by the whole
  quiz, whatever number of items changed** — scoping saves output, not reading.

Quiz 2, measured from the per-turn `usage` records in the agent transcripts
(16 subagents, 186 turns total):

| round | agents | wall | output tokens | cumulative context |
|---|---:|---:|---:|---:|
| 1 — generate + check | 6 | 850 s | 89,173 | 3,997,822 |
| 2 — repair (5 items) | 6 | 937 s | 103,455 | 3,191,993 |
| 3 — repair (2 items) | 4 | 686 s | 86,257 | 2,602,549 |

A repair round lands near **80–100% of round 1's wall clock**. What makes a cap
of 5 affordable is that later rounds repair progressively fewer *items* — not
that a later round is individually cheap.

**Three different numbers get called "tokens". Say which one you mean.**
Measured across Quiz 2's 16 agents and 186 turns:

| number | Quiz 2 | what it is |
|---|---:|---|
| output | 278,885 | tokens generated — items, keys, reports |
| peak context, summed per agent | 1,031,467 | distinct material the fleet held |
| total prefill | 9,792,364 | summed over turns; re-sends counted each time |

The **workflow tool's `tokens` field is the middle one** — each agent's
high-water-mark context (`input + cache_creation + cache_read`), summed,
output excluded. Verified to within 6–20 tokens per run against the per-turn
`usage` records in the agent transcripts. It is *not* output and *not* prefill.

**Prefill was 9.5× peak — but do not read that as the cost.** A context is
re-sent in full every turn, so prefill grows with turn count; almost all of it
is cache *reads*, billed at a tenth. Weighting each component by its rate
(cache read ×0.1, cache write ×1.25, output ×5 against base input) gives a very
different ranking:

| | tokens | share of prefill | share of cost |
|---|---:|---:|---:|
| cache write | 2,128,587 | 21.7% | **55.2%** |
| cache read | 7,663,405 | **78.3%** | 15.9% |
| output | 278,885 | — | 28.9% |

Caching cut the input side by **2.9×**, not 10× — the discount only reaches the
portion that was read, and the writes that made those reads possible are the
single largest line.

**So the lever is cache-write volume, not pack size and not turn count.** The
fleet wrote 2.1M against 1.03M of distinct material: every agent whose context
*grows* — a tool call appending file contents, then another — forces a fresh
cache segment. An agent that loads a big prefix once and then reasons over it
is cheap no matter how many turns it takes; an agent that keeps pulling new
material in is not.

Practical consequences: prefer a check that answers from the pack it was given
over one that goes hunting through the repository file by file (the round-3
source check made 21 tool calls, each appending). And do not dismiss output as
negligible because it is 2.85% of prefill — at ×5 it is 29% of the bill, and
the checking agents' long per-option reports are most of it.

**Escalation is an ending, not a failure.** A loop that stops and says "item 14
failed twice, here are both versions and what each costs" has done its job. One
that keeps grinding until something passes has only learned to satisfy the
checker.

## Common Mistakes

| Mistake | Fix |
|---|---|
| Generating before reading the course profile | Profile first; its spec overrides these defaults |
| Giving the review subagent the key, or "just a hint" | Key-blind means blind; re-run from a fresh agent if contaminated |
| Emitting the quiz only in chat | Always write the round's files to the build folder |
| Inventing the folder timestamp | Take it from `date` |
| Editing flagged items without telling the user | Report every disagreement; the author decides what ships |
| Amending an item after the final round and shipping it | The amendment is unreviewed; run another round, do not add a note |
| One agent asked for all 22 items in one pass | One agent per tier, L3 → L2 → L1, each handed the facts ledger |
| Generating a 1.4× pool and cutting it | Retired. Generate exactly N and repair what fails — a pool cannot be told what was wrong |
| Regenerating the whole quiz when four items failed | Regenerate only the flagged items; splice, then re-check all N |
| Scoping the duplication pass to the changed items | It reads everything and reports pairs with ≥1 changed item. Scoping it to the new items misses the collisions replacements actually cause |
| Re-reviewing all 22 items on a repair round | Source check and blind review are item-local — pass `changedItems` and carry the rest forward |
| Using a scoped round's `verdicts` as the whole picture | Merge onto the previous round's before computing the blocking set; assert the merged count equals the item count |
| Writing a scoped round's `analysis.md` with only the changed items in it | Seed from the previous round's file and replace those sections. The artifact is always all N items |
| Scoping what an agent READS rather than what it writes | Every check sees the whole quiz; only the reporting narrows. `AMBIGUOUS` depends on the rest of the quiz |
| Treating `expected_pass` or `trap_quality` as measurements | They drifted on 14/15 unchanged items across three runs. Estimates. Only the answer, `AMBIGUOUS` and `STANDALONE` columns block |
| Regenerating a good item over a `PARTIAL` citation | `PARTIAL` is advisory; fix the citation in `key.md` |
| Replacing the L3 item of a cross-tier duplicate pair | Replace the cheaper item; the trace swallows the recall item, not the reverse |
| Reading the flagged set out of `source_check.md`'s tables | Filter `verdicts.json`. When a number matters, parse it — do not read it |
| Overwriting a round folder | Rounds are the trace; a later round writes a new folder |
| Telling the reviewer "no answer key exists" | True in round 1 only. Say it exists, say not to look, say why |
| Asking for the topic when it was already given | Generate; ask only for genuinely missing inputs |
| Four choices by default | Five, unless specified |
| Marking the key with bold, `(correct)`, or an answer list at the end | Only the `*` prefix, inline |
| `\begin{code}` around plain prose | Code only |
| Question sentence above the code, or code described in prose | Code first, then the question; write declarations as a fragment, not a sentence |
| Answer key positionally biased toward `c)` | Distribute keys across all letters |
| Writing the returned `quiz`/`key` to disk unchecked | Validate first: real documents, right item numbers, exactly one `*` per item, every stem compiles |
| Stripping the `*` from `quiz.md`, or calling it a key leak | `quiz.md` carries the key; the instructor's LaTeX script makes the student and key sheets. Only `quiz_blind.md` is starless |
| Giving the key-blind reviewer `quiz.md` | It holds the `*` key. Pass `quiz_blind.md` (`preAuthoredPaths.blindQuiz` on rounds 2+) |
| Trusting `key.md`'s claim that the stems compile | Extract the code blocks and compile them yourself |
| Resuming a failed run with the prompt unchanged | Cached agents replay the same bad result; edit the prompt to bust the cache |
| A checking agent hunting for a substitute when handed no quiz | Tell both checkers to stop and report, never to go find another target |
| Reporting a failed round without saying no files were written | An empty round folder is invisible; state the manifest, including "none" |
| Asking "shall I run round 2?" | The termination rule is the permission. Report the round, start the next one in the same turn |
| Reporting loop state from memory instead of a file | `loop_state.json` at the build root, updated every round. A resumed session must not have to re-derive the round number or the attempt counts |
| Leaving a mid-flight round folder looking like a failed one | Drop a `STATUS.txt` saying which artifacts are pending and that the round is incomplete, not failed |
| Acting on an agent's flag without checking it | Three of five untaught-term flags on Quiz 2 were false — the checker sees only the *cited* topic, not the corpus. Grep the pack before spending a regeneration |
| Reading `PARTIAL` as "the item is ungrounded" | Ask whether the *premises* are taught. A derived conclusion stated nowhere is what an L2/L3 item is for |
| An L3 item whose key is verbatim in the corpus | That is a recall item at three points. Raise the derivation, don't celebrate the citation |
| Re-running generation on round 2 | Pass `preAuthoredPaths`; rounds 2+ re-check the quiz that already exists |
| Regenerating the item whose key *is* "rejected at compile time" | The gate must exempt items keyed to non-compilation |
| An item answerable only by someone who remembers the demo | Print in the item every fact and line the answer needs; test the rule, not the example |
