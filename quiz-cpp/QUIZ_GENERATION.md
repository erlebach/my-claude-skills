# How a quiz gets generated

Plain-language description of what happens when you ask for a quiz, what each file is for, and where you as the author fit in. This is documentation for you, not instructions for the agent — the agent's instructions are in `SKILL.md` and `Cpp.md`.

## The short version

You ask for a quiz. The agent you are talking to reads the course material, then hands it to a writer, which produces the questions and the answer key together. A second agent checks that every question really came from something you assigned. A third agent, which is never shown the answers, sits the quiz cold and writes up every option of every question. You get four files and a report of everywhere they disagreed.

All three run on Opus 5. The two writing-and-checking stages run at medium effort; the cold review runs at high effort, because arguing the strongest case for an answer you believe is wrong is the hardest thing anyone in this process is asked to do.

The point of the whole arrangement is a single question that is easy to skip and expensive to skip: **can a well-prepared student defend an answer other than the one you intended?**

## The four files

Everything from one run lands in one folder, named for the quiz and the moment it was made. Each quiz in the course has a folder of its own, and a run folder sits inside it:

```
quizzes/quiz-1/
    quiz_1_2026-07-26_14h14mEST/    one run
        quiz.md          what the students see
        key.md           what you see
        source_check.md  whether each question came from something you assigned
        analysis.md      what the cold reviewer thought
    quiz_1_2026-07-26_17h21mEST/    another run
    final_analysis_.../             the paper you actually give out
```

A run is a batch of candidate questions, not the quiz. The quiz gets assembled from the runs in `final_analysis_`, which is where you come in — see below.

**`quiz.md`** is the student paper. Questions numbered, options lettered, point value printed on each question, no answers anywhere in the file. This is what goes to LaTeX and onto paper.

**`key.md`** is yours. It opens with a table — one row per question giving its difficulty tier, its point value, which module it belongs to, **where the material came from**, whether it is an agentic item, and the correct answer. Below the table is a paragraph per question explaining why the key is the key and what misconception each wrong option is meant to catch.

The *source* column is the one that earns its place. It has to be specific enough that you can reopen it — a demo page and the section within it, a slide number, a named example. If a question was invented rather than drawn from assigned material, the column says `none`, and that gets reported to you rather than quietly passing. An unsourced question is not necessarily a bad question, but nothing guarantees your students were taught it, or taught it in the words the question uses.

**`source_check.md`** answers one question per item: does the thing it says it came from actually say that? A separate agent opens every source cited in `key.md` and reports whether it exists, whether the cited section really supports the question, and — the part that pays for itself — **any term the question leans on that the source never introduces**. That is how you find a question testing vocabulary your course has not yet taught. Nothing else in the process can see it: the cold reviewer knows C++ and will happily answer a question about material your students have never met.

**`analysis.md`** is the cold review. For every question it records the reviewer's own answer and confidence, then a paragraph for *each* option — including the right one — laying out the strongest case a good student could make for choosing it, and why it finally holds or fails. It flags any option that would catch nobody, and it flags any question where two options are genuinely defensible.

## Who writes what, and why it matters

**`quiz.md` and `key.md` are written together, by one agent, in one pass.** Never by two agents, never in two sittings. The failure this avoids is mundane and common: a question's wording changes and the key still describes the old wording. One author, one pass, no drift. The agent you are talking to does the reading, hands the material over, and copies both files back unedited — it does not rewrite them, because rewriting one without the other is precisely the drift being guarded against.

**`analysis.md` comes from a different agent that has never seen the key.** This is the part that cannot be shortcut. An agent that knows the intended answer will find reasons for it — that is what reasoning does — and will tell you the key is fine no matter what. Only a reviewer working blind can tell you whether the intended answer is the one a prepared student actually reaches.

So the two files are produced by two independent agents, and deliberately so. `key.md` is not delegated at all; it is written by the agent you are talking to, because it must stay welded to `quiz.md`.

**`source_check.md` comes from a third agent**, which reads the key and the sources together. It necessarily sees the answers, which is exactly why it can never also be the cold reviewer — those are always two separate dispatches. It runs first, so a question with no source behind it is known before the blind review is spent on it.

Neither reviewing agent can write files — a platform rule requires them to hand their findings back as text. The agent you are talking to transcribes each one into its file, unedited.

## Why a quiz takes several runs, and where you choose

One writer asked for twenty-two questions drifts. It repeats itself, it leans on whichever demo it warmed up on, and the last questions get less care than the first. So a full quiz is written in batches of about ten, each a complete run — written, source-checked, cold-reviewed — and each blind to the others. Questions are numbered straight through, so question 23 is question 23 from the moment it is written until it reaches the paper.

That deliberately produces **more questions than the quiz needs**, about half again as many. The surplus is the point: a question with a defect gets dropped rather than patched, and you get a real choice rather than a fait accompli.

Then you get a **selection sheet** — every candidate in one table, by difficulty tier, each row saying what the question asks, which demo it came from, whether it is agentic, and what any reviewer flagged about it. Underneath: which questions overlap each other, which demos are over- or under-represented, and which questions have defects to fix or avoid.

The comparisons on that sheet are ones **no reviewer in any run could have made**, because each run's reviewer saw only its own ten questions. Two questions testing the same principle from opposite sides, written a day apart by different agents, look fine individually and redundant side by side.

**You make the cuts.** Not the writer, not a reviewer, not the agent you are talking to. If a tier ends up short — you reject four of the six hardest questions and only two survive — you say so, and another batch of that tier alone gets written and added to the sheet.

Once you have your set, it is renumbered, the answer letters are rebalanced, and the whole assembled paper goes through **one more cold review** as a single quiz. That last pass matters for a specific reason: any question you or the agent edited after its original review is, strictly, unreviewed. The final pass is what clears it.

## What comes back to you

A list of disagreements, not a corrected quiz:

- every question where the cold reviewer chose a different answer than the key
- every question it marked ambiguous, and the argument for the second answer
- every option it judged dead — one nobody would plausibly pick, which quietly turns a five-choice question into a four- or three-choice one
- every question with no source behind it

Nothing is fixed automatically. The disagreements *are* the product, and which ones are real defects is a judgment about your students and your course that the agent is not positioned to make. You say what to change; then it changes it.

## What this is worth, honestly

The cold reviewer agreeing with the key on every question does not prove the quiz is good. It proves that one competent reader, on one pass, found nothing — which is worth having and is not the same thing. The mechanism earns its keep on the questions where it *disagrees*, and on a clean run you have not seen it work.

The three agents run as an orchestrated pipeline rather than one at a time, which buys two things: the effort levels above are actually enforced, and nothing is written to disk until all three have finished — so when the cold reviewer works, the answer key does not yet exist anywhere it could reach. The cost is that the sequence runs start to finish without stopping to think. If the second question is nonsense, the pipeline still spends a full high-effort review on it, and you find out at the end rather than in the middle.

It also cannot check what it was never given. If the agent writes questions from module summaries instead of the demo pages themselves, the review will still come back clean, because the reviewer knows C++ and will not notice that a question tests something your course never taught. That is what the source column exists to catch, and it is the reason step one of the process is *read the actual material*.

## Where the settings live

- `SKILL.md` — the format, the item-writing craft, and the pipeline. Shared across courses.
- `Cpp.md` — ISC5305's numbers: 22 items, the L1/L2/L3 mix and weights, the scope rule, the agentic fraction, where the folders go. One file per course.
