# Meaning check — prompt for the verifier subagent

Use this prompt for verification check 3. Fill in the two paths. Run it in a fresh subagent that has not seen the rewrite being written: a writer who checks their own rewrite reads what they meant to write, not what they wrote.

Model: for an explanation or a guide, one run with `haiku` (Haiku 5.5). For a specification, rubric or policy, two runs in parallel with this same prompt, one with `haiku` and one with `sonnet` at `effort: low`; merge the two sets of findings.

---

You compare a source document with a rewrite of it. The rewrite changed the wording to plain technical English. It must not change the meaning. Your job is to find every place where the meaning changed. You do not judge the style, and you do not edit any file.

- Source: `<SOURCE PATH>`
- Rewrite: `<REWRITE PATH>`

Read both files in full. Then work through the source from top to bottom, one section at a time. For each section, list every item of these kinds:

- an instruction (something the reader must do);
- a requirement or rule, with its level: required, recommended, allowed, forbidden;
- a condition (when, if, unless, only, except) and the thing it controls;
- a fact, number, count, limit, date or name;
- a reason given for a rule.

For each item, find the matching text in the rewrite and decide:

- **KEPT** — the rewrite says the same thing.
- **MISSING** — the rewrite does not say it.
- **CHANGED** — the rewrite says something different. This includes:
    - a different number, scope or object ("each file" became "the file");
    - a condition dropped, weakened, widened, or moved so it no longer controls the same thing;
    - a requirement level changed in either direction ("should" became MUST, "must" became "can");
    - a cause or reason changed or dropped;
    - an exception lost.

Then read the rewrite once more and list anything it says that is not in the source:

- **ADDED** — a new instruction, requirement, fact or claim.

Do not report KEPT items. Do not report changes of wording that keep the meaning, such as a long sentence split into two, a list made from a sentence, or "check" replaced by "examine". Do not report code blocks, links or numbers that are byte-identical; a script already checks those. Do not report an added `draft: true` in the front matter; it is added on purpose so the rewrite does not publish.

In a specification, the rewrite adds MUST, MUST NOT, SHOULD and MAY on purpose. When the source already states a rule — as a fact ("Every regression test passes on `tests_before`") or as a plain instruction ("Leave `starter/` as it is") — and the rewrite writes the same rule with MUST or MUST NOT, do not report it as a finding. List it once, at the end, under "Requirement words added", with one line per item. Do not report the short paragraph that defines MUST, MUST NOT, SHOULD and MAY; the rewrite adds it on purpose. Report it as CHANGED only when the strength differs: a recommendation became MUST, a rule became SHOULD, MAY or "can", or a rule became a description.

The requirement words can also appear as a shortcode, `{{< req must >}}`, `{{< req "must not" >}}`, `{{< req should >}}`, `{{< req may >}}`. Read each one as the capital word it names.

<!-- For a rubric, replace the paragraph above with this one: the skill removes the requirement words from rubrics. -->
In a rubric, the rewrite removes MUST, MUST NOT and MAY on purpose. It says once, near the top, that every condition on the page is required, and writes each condition as a statement of what the grader checks ("`X` MUST be Y" becomes "`X` is Y"). A MUST that became such a statement or an imperative is not a finding: list it at the end, under "Requirement words removed". Report CHANGED only when the strength differs: a required condition now reads as optional, as a recommendation, or as something that may or may not happen; or an allowed option now reads as required or forbidden.

Write your answer in this format and nothing else:

```
VERDICT: <PASS if no MISSING, CHANGED or ADDED items; else FAIL>

## Findings

1. CHANGED — <section heading>
   Source: "<exact quote from the source>"
   Rewrite: "<exact quote from the rewrite>"
   Difference: <one sentence: what the reader would now understand differently>

2. MISSING — <section heading>
   Source: "<exact quote>"
   Rewrite: (none)
   Difference: <one sentence>

## Requirement words added (no change of meaning)

- "<source quote>" → "<rewrite quote>"
```

Quote both texts exactly, so the finding can be checked with a text search. If you are not sure whether an item changed, report it and write "UNSURE" at the start of the Difference line. A false alarm costs the author one look; a missed change can reach students.
