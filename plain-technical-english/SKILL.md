---
name: plain-technical-english
description: Write or rewrite technical text in plain technical English — plain language as the base (ISO 24495-1, Google developer style), the useful ASD-STE100 structure rules (one instruction per sentence, numbered steps, active voice, short sentences), and RFC 2119 MUST/SHOULD/MAY for requirements, without the STE fixed dictionary. Use this skill whenever the user asks to make text clearer, simpler, plainer or more precise; to rewrite a page, homework, rubric, guide, README, handoff or procedure "in plain English", "in STE", "in Simplified Technical English" or "for non-native readers"; to write instructions, specifications or grading rules students or users must follow; or mentions ASD-STE100, controlled language, plain language or readability — even if they do not name this skill. Not for auditing prose without editing it (that is the plain-language audit skill).
---

# Plain technical English

A writing standard for technical and teaching text. It combines three sources and takes from each only what helps a reader who works alone, possibly in a second language, and must act on the text:

| Source | What this skill takes | What it leaves |
|---|---|---|
| Plain language (ISO 24495-1:2023; US Federal Plain Language Guidelines; Google developer documentation style guide) | The base: the reader can find what they need, understand it, and use it. Address the reader as "you". Main point first. | Nothing; this is the frame. |
| ASD-STE100 (Simplified Technical English) | Structure rules: one instruction per sentence, numbered steps, imperative, active voice, sentence and paragraph length limits, articles kept, one word for one meaning. | The fixed ~900-word dictionary, the ban on *-ing* forms, and anything that removes a precise term. |
| RFC 2119 / RFC 8174 | must, must not, should, should not, may for requirements, with fixed meanings, marked in small capitals (or capitals outside Hugo). | Use outside specifications, homework pages and policies, and in rubrics. |

Why not full STE: its dictionary was built for aircraft maintenance. It has no words for many ideas in software and teaching (*scope creep*, *trade-off*, *grounding*), and forcing them into approved words loses precision. In one test, "however the block is left" became "all the ways that the program can go out of the block", which no longer clearly includes an early `return` or an exception. Precision wins over vocabulary rules.

## Precedence

1. The user's explicit request in this conversation.
2. The project's own writing rules (for example a "Write plainly" section or a rejected-words table in the project `CLAUDE.md`). Apply them on top of this skill; where they conflict, they win.
3. This skill.

Global memory rules also apply, in particular `~/.claude/memory/feedback/plain-language.md` and `~/.claude/memory/feedback/markdown-formatting.md`.

## The rules

### Words

- Use the plain word. Cut showy words rather than replacing one with three ordinary ones. Plain text is usually shorter.
- Keep the exact technical term when precision needs it. On first use, if the reader may not know it, give the plain phrase and the term together: "the entries live elsewhere in memory (on the heap)".
- One word for one meaning, through the whole document. If a step says "examine", do not switch to "check", "review" and "inspect" for the same act. If the project already uses a word for an idea (for example "distinguishing test"), use that word.
- No intensifiers that add emphasis but no information: *exactly, genuinely, precisely, really, very, simply, just, clearly, obviously, basically*.
- No metaphor the reader has to decode. Say the thing.
- Keep the articles (*the*, *a*). Dropped articles make text read like notes and harder to translate.

### Sentences

- Active voice. Name who does the action: "the grader runs the tests", not "the tests are run".
- One instruction per sentence. "Build the program. Run it with `-O2`." — not "Build and run the program with `-O2`, then compare."
- Instructions in the imperative: "Commit the file", not "You will want to commit the file".
- Length targets, from STE: at most about 20 words in an instruction, about 25 in a description. These are targets. Split a sentence that runs over, unless splitting would separate a condition from what it controls.
- Conditions first: "If the test fails, examine the diff." The reader then knows when the instruction applies before reading it.
- State facts, not impressions. Give the number, the file, the command, the measured result. Vague pointers ("as stated above", "the convention") must point at something real: name it.

### Paragraphs and structure

- At most about 6 sentences per paragraph. Start with the point.
- Steps that occur in a set order → a numbered list. Items with no order → a bulleted list. A sentence that packs four parallel items → a vertical list.
- Headings that say what the section contains or asks: "Run the benchmark", not "Benchmarking considerations".
- Tables for comparisons and look-ups. Keep cells short; put any claim that needs explanation in the text.

### Requirements (specifications, homework, rubrics, policies)

- Use the requirement words must, must not, should, should not and may with the RFC 2119 meanings:
    - **must / must not**: required; failing it fails the requirement.
    - **should / should not**: recommended; there can be a valid reason to do otherwise, and the writer says what it costs.
    - **may**: allowed, not required.
- **How to mark them** (author's choice, 2026-10-14; full capitals were too loud, italics read as emphasis, underline reads as a link):
    - **On a Hugo site with a `req` shortcode** (the ISC5305 `course_site` has one): small capitals, through the shortcode: `{{< req must >}}`, `{{< req "must not" >}}`, `{{< req should >}}`, `{{< req "should not" >}}`, `{{< req may >}}`. The shortcode accepts only these five words. Do not mix it with capital MUST in the same file.
    - **Anywhere else** (plain Markdown, a README, a commit message): capitals, MUST / SHOULD / MAY.
- Define them once, near the top of the document, in one short sentence or a small table. Say how they look: "the words in small capitals have fixed meanings".
- Do not use the plain lowercase words *must*, *should* or *may* for anything else in that document. Lowercase "should" in a specification makes a reader ask whether it is required. Use "can", "is expected to" or a plain statement of fact instead.
- **Where to use them:** a specification, a homework page, a policy: the pages where a reader chooses what to do and must tell required from recommended from optional.
- **A rubric does not use them.** In a rubric, almost every condition is required, and the heading ("Required for full marks:") already says so. Marking each one (60 times in the HW4 rubric) is noise. Write each condition as a statement of what the grader checks: "`refactor.diff` is the output of `diff -ru before after`". Near the top, say once that every condition on the page is required. If a rubric item is optional, say so in words ("you can use `valgrind` instead").
- In an explanation or a guide, *must*, *should* and *may* are ordinary words: keep them, unmarked. Do not replace "your answer should say it" with "your answer says it"; that turns an instruction into a description.
- Each requirement is one sentence that a reader can test: what is required, of what, and how it is checked. "`refactor.diff` {{< req must >}} be the output of `diff -ru before after`" — not "the diff should be a proper one".

### What never changes in a rewrite

- Code, commands, file names, paths, identifiers, numbers, units, points, dates, links, shortcodes and front matter.
- Quotations, and example texts shown to readers as models. Above all, a deliberately wrong example stays wrong; rewriting it in plain style would remove the fault it exists to show. If the user wants model texts rewritten too, they will ask.
- The meaning. If a rule here would change what the text says, keep the original wording and report it.

## Markdown output

These are global rules, repeated here because rewrites break them most often:

- One paragraph = one line. One list item = one line. Do not hard-wrap; the page or container width controls line breaks. Block-quote paragraphs (`> …`) too.
- A blank line before every list. A list and its sublists count as one block.
- List markers at multiples of 4 spaces (0, 4, 8). Nested level n is indented 4·n spaces.
- Never let a wrap put `17.` or `- ` at the start of a line; Markdown reads it as a list.

When you give this work to a subagent, copy these Markdown rules into its prompt word for word, and do not mention "continuation lines".

## Workflow for a rewrite

1. Read the whole source. Note its audience (students alone at night? engineers? graders?) and its kind of text: procedure, specification, rubric, explanation, reference.
2. Write to a new file unless the user asked to edit in place. Never overwrite an existing file without being asked.
3. Rewrite section by section. Apply the rules above. Keep every item from the "never changes" list.
4. Run the verification phase below.
5. In the reply, report the verification results, the passages where the rewrite lost or changed meaning, and the terms you kept because no plain word fits. That list is for the user's decision. Do not fix meaning findings silently; a finding can also be a false alarm.

## Verification phase

Run it after every rewrite of an existing text. For new text with no source, run only check 2.

The scripts are in `~/.claude/skills/plain-technical-english/scripts/` (below, `$PTE` stands for that folder).

1. **Preservation (script, always).** It compares the source and the rewrite, and fails if a code block is missing or changed, or if any of these is missing: an inline code span, a link target, a shortcode, a number with its unit, a block quote, a front-matter value. White space is ignored, so joined lines are not a change. Fix every finding, or tell the user why the source item was dropped on purpose.

    ```bash
    python3 $PTE/verify_preservation.py SOURCE.md REWRITE.md
    ```

2. **Format (script, always).** Fix every Markdown fault (`WRAP`, `LISTGAP`, `INDENT`). Treat the prose findings (`LONG`, `PARA`, `INTENS`, `PASSIVE`, `REQWORD`) as prompts to look again, not as orders: a 27-word sentence that cannot be split without losing its condition stays.

    ```bash
    python3 $PTE/check_prose.py REWRITE.md          # explanation, guide
    python3 $PTE/check_prose.py --spec REWRITE.md   # specification, rubric
    ```

3. **Meaning (subagent, on by default, can be turned off).** A fresh subagent compares the two texts item by item and reports what is missing, changed or added, with exact quotes from both. Its prompt is in `references/meaning-check.md`; fill in the two paths and pass it to the Agent tool. It must be a new agent, not the one that wrote the rewrite.
    - **Model, for an explanation or a guide:** one check with `haiku` (Haiku 5.5).
    - **Model, for a specification, rubric or policy:** two checks in parallel, one with `haiku` and one with `sonnet` at `effort: low`. Merge their findings and remove duplicates. In a test on the HW4 pages (2026-10-13), each model found about half of the real changes that the other missed, and neither found them all.
    - **Another model:** use it when the user asks for it.
    - **Turn it off** when the user says so ("no meaning check", "skip check 3", "scripts only"), and for short text such as a reply, a commit message or a paragraph under about 150 words. Say in the reply that check 3 did not run.
    - **Many files:** run one subagent per file, in parallel.
    - **Before you report a finding,** search for its two quotes in the files. Drop a finding whose quotes are not there, and say how many you dropped.
    - **For a MISSING finding,** there is no rewrite quote to search for. Search the rewrite for a short, distinctive phrase from the source quote (for example "Only taught gates are graded"). If the phrase is there, the finding is a false alarm: drop it and count it.

## Example

Before:

> Make sure to run the benchmark a few times with optimizations on and report the median, since the first run is usually slower, and the numbers should include the conditions.

After (specification):

> 1. Build `bench.cpp` with `-O2`.
> 2. Run `./bench_O2` five times.
> 3. Report the median time, not the first run. The first run is usually the slowest.
> 4. Each time you report MUST state its units, the optimization level, the number of runs and the size N.

What changed: one instruction per step; "a few" became a number; "should include" became a testable MUST; the reason stays, in its own sentence.
