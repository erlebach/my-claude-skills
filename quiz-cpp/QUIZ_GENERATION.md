# How a quiz gets generated

Plain-language description of what happens when you ask for a quiz, what each file is for, and where you as the author fit in. This is documentation for you, not instructions for the agent — the agent's instructions are in `SKILL.md` and `Cpp.md`.

## The short version

You ask for a quiz. The agent you are talking to reads the course material, then hands it to three writers in turn — hardest questions first, easiest last, each told what the ones before it already used up. Three checkers then go over the finished quiz at once: one asks whether every question really came from something you assigned, one sits the quiz cold having never seen the answers, and one looks for two questions testing the same fact. Whatever they flag gets rewritten, and the checks run again. When a pass finds nothing, you get the quiz.

Everyone runs on Opus 5. Writing and source-checking run at medium effort; the cold review and the duplicate hunt run at high effort, because arguing the strongest case for an answer you believe is wrong — and spotting one fact wearing two disguises — are the hardest things anyone in this process is asked to do.

The point of the whole arrangement is a single question that is easy to skip and expensive to skip: **can a well-prepared student defend an answer other than the one you intended?**

## The files

Everything lands in one folder, named for the moment the build started. Each quiz in the course has a folder of its own:

```
quizzes/quiz-1/
    build_2026-07-28_21h20mEST/
        quiz.md          the quiz, key marked with *    ← the current version
        quiz_blind.md    the same without the *, for the cold reviewer only
        loop_state.json  which pass it is on, what each pass found, and why it stopped
        key.md           what you see                   ← the current version
        source_check.md  whether each question came from something you assigned
        analysis.md      what the cold reviewer thought
        rounds/
            round-1/     everything above, exactly as it stood when round 1 ended
            round-2/     ditto, plus a note of which questions were rewritten and why
```

The files at the top are the quiz. The `rounds/` folders are the history — frozen the moment each pass ends, never edited afterwards, so you can always see what a question looked like before it was rewritten and what was wrong with it.

**`quiz.md`** is the quiz. Questions numbered, options lettered, point value printed on each question, and a `*` before the correct choice of each question. The instructor's script turns it into formatted LaTeX — the student sheets without the `*`, the key sheets with it. (`quiz_blind.md`, the same text without the `*`, exists only so the key-blind reviewer cannot see the answers.)

**`key.md`** is yours. It opens with a table — one row per question giving its difficulty tier, its point value, which module it belongs to, **where the material came from**, whether it is an agentic item, and the correct answer. Below the table is a paragraph per question explaining why the key is the key and what misconception each wrong option is meant to catch.

The *source* column is the one that earns its place. It has to be specific enough that you can reopen it — a demo page and the section within it, a slide number, a named example. If a question was invented rather than drawn from assigned material, the column says `none`, and that gets reported to you rather than quietly passing. An unsourced question is not necessarily a bad question, but nothing guarantees your students were taught it, or taught it in the words the question uses.

**`source_check.md`** answers one question per item: does the thing it says it came from actually say that? A separate agent opens every source cited in `key.md` and reports whether it exists, whether the cited section really supports the question, and — the part that pays for itself — **any term the question leans on that the source never introduces**. That is how you find a question testing vocabulary your course has not yet taught. Nothing else in the process can see it: the cold reviewer knows C++ and will happily answer a question about material your students have never met.

**`analysis.md`** is the cold review. For every question it records the reviewer's own answer and confidence, then a paragraph for *each* option — including the right one — laying out the strongest case a good student could make for choosing it, and why it finally holds or fails. It flags any option that would catch nobody, and it flags any question where two options are genuinely defensible.

## Who writes what, and why it matters

**A question and its key are written together, by one agent, in one pass.** Each tier's writer produces its own questions and its own key entries in a single sitting — never two agents, never two sittings. The failure this avoids is mundane and common: a question's wording changes and the key still describes the old wording. The agent you are talking to does the reading, hands the material over, and copies both files back unedited — it does not rewrite them, because rewriting one without the other is precisely the drift being guarded against.

**`analysis.md` comes from a different agent that has never seen the key.** This is the part that cannot be shortcut. An agent that knows the intended answer will find reasons for it — that is what reasoning does — and will tell you the key is fine no matter what. Only a reviewer working blind can tell you whether the intended answer is the one a prepared student actually reaches.

So the two files are produced by two independent agents, and deliberately so.

**`source_check.md` comes from a third agent**, which reads the key and the sources together. It necessarily sees the answers, which is exactly why it can never also be the cold reviewer — those are always two separate dispatches.

**A fourth agent hunts for duplicates**, and it is the only one shown every question and every answer at once. It has to be: two questions can cite different files and still turn on one fact, and that is invisible from the questions alone. This is the comparison that used to require assembling a sheet across separate batches, and it does the job better than the sheet did.

Before any of them run, one wholly mechanical check goes first — every question's code is pulled out and compiled. It takes about a second and it is the only check in the process that cannot be mistaken.

Neither reviewing agent can write files — a platform rule requires them to hand their findings back as text. The agent you are talking to transcribes each one into its file, unedited.

## Hardest first, and why

One writer asked for twenty-two questions drifts — it repeats itself, leans on whichever demo it warmed up on, and gives the last questions less care than the first. So the writing is split three ways, one writer per difficulty tier, and **the hard ones are written first**.

That order is not arbitrary, and it is the single decision the whole process rests on. A three-point question is a trace through several steps, and the facts it uses are a *superset* of the facts several one-point questions would use. Write the small questions first and the big ones have nothing left to build from — they end up restating, in three points, something the quiz already asks in one. Written hardest-first, each writer hands the next one a list of the facts it has spent, with instructions to avoid them and any narrower version of them.

## The loop, and where you choose

The first pass writes exactly twenty-two questions. There is no surplus and nothing gets cut.

That is a change from how this used to work. The old process wrote about half again as many questions and had you cut the pool down — and on Quiz 1 it turned out there was **no good quiz inside the pool at all**: of the sixteen easy questions written for fourteen slots, only eleven were clean. No amount of careful choosing gets you a defect-free quiz out of that. Rewriting works where choosing does not, for a simple reason: a flagged question comes with a *reason it was flagged*, which is an instruction to the writer. A pool of alternatives was never told what was wrong with the one it is replacing.

So instead: the checkers flag what they find, **only the flagged questions are rewritten**, and the checks run again. Every checker still reads the whole quiz, but the source check and the cold review report only on the rewritten questions; the duplicate hunt reports any pair that involves one — because a replacement can collide with a question that was fine a moment ago. That repeats until a pass turns up nothing, and it is capped at five passes regardless. Quiz 1 converged on the second.

One flag is deliberately *not* acted on. When a source check says the question is right but its citation reaches a little too far, the citation gets fixed in `key.md` and the question is left alone — it is invisible to a student, and rewriting a good question over a footnote is how a process like this destroys its own best work.

**You review; you no longer cut.** What comes back is a finished quiz, not a worksheet, and whether it ships is your call. Anything the loop chose not to act on is reported to you by question number rather than buried — the citations it left, any two questions it thought overlapped but kept, and any question it gave up on after two rewrites.

## What comes back to you

A finished quiz, plus an account of what each pass found and what it did about it. Every round reports:

- every question where the cold reviewer chose a different answer than the key
- every question it marked ambiguous, and the argument for the second answer
- every option it judged dead — one nobody would plausibly pick, which quietly turns a five-choice question into a four- or three-choice one
- every question with no source behind it, or leaning on a word the course never taught
- every question a student could answer only by remembering a particular course example rather than by knowing C++ — each question must stand on its own
- every question whose answer would change on a different compiler or machine
- every pair of questions found to test the same fact

Those are what get rewritten in the next pass, and you see them as they are found rather than at the end. What survives to the last pass — the citations left alone, the overlaps kept, anything given up on — is reported to you by question number, because those are judgement calls being handed to you, not problems that were solved.

Which of them are real defects for *your* students remains yours to decide. You say what to change; then it changes it.

## What this is worth, honestly

The cold reviewer agreeing with the key on every question does not prove the quiz is good. It proves that one competent reader, on one pass, found nothing — which is worth having and is not the same thing. The mechanism earns its keep on the questions where it *disagrees*, and on a clean run you have not seen it work.

The agents run as an orchestrated pipeline rather than one at a time, which enforces the effort levels above. On the first pass it buys one thing more: nothing is written to disk until every agent has finished, so when the cold reviewer works, the answer key does not yet exist anywhere it could reach. That guarantee is spent from the second pass onward — rewriting needs the files on disk, and the reviewer could find the key if it went looking. It is told the key exists, told not to look, and told why, which is weaker than the first pass and is stated rather than glossed.

The cost of the arrangement is that each pass runs start to finish without stopping to think. If the second question is nonsense, that pass still spends a full high-effort review on it, and you find out when the pass ends rather than in the middle.

It also cannot check what it was never given. If the agent writes questions from module summaries instead of the demo pages themselves, the review will still come back clean, because the reviewer knows C++ and will not notice that a question tests something your course never taught. That is what the source column exists to catch, and it is the reason step one of the process is *read the actual material*.

## Where the settings live

- `SKILL.md` — the format, the item-writing craft, and the pipeline. Shared across courses.
- `Cpp.md` — ISC5305's numbers: 22 items, the L1/L2/L3 mix and weights, the scope rule, the agentic fraction, where the folders go. One file per course.
