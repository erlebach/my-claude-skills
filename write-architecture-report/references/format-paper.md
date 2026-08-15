# Format: paper

Governs structure only — the style file decides the wording. Template: `assets/template-paper.md`.

## Purpose

A paper-shaped account of the system: the problem, what was built, how it was verified, and what it does and does not establish. Suitable as a draft methods or system section, a technical report, or a thesis chapter. It is written to be evaluated, so every claim carries its support.

## When to use

- Drafting a methods, system, or data-processing section for a manuscript
- A standalone technical report for a funder or collaborator
- Any document that will be read by someone deciding whether the work is sound

Use `architecture-doc` instead if the reader needs to maintain the code. Use `seminar-brief` if it will be spoken rather than read.

## Required sections, in order

1. **Title and abstract** — abstract in 150–250 words: problem, what was built, how it was checked, what was found, one limitation.
2. **Introduction** — the problem, why it is hard, what exists already, and what this work contributes. Ends with an explicit contribution list.
3. **Background** — only what the reader needs to follow the rest: domain concepts, prior systems, terminology.
4. **Materials and data** — the corpus, its provenance, its size, its known defects, and the access conditions.
5. **System description** — the design and its components, at the level of detail a reader would need to build an equivalent. Organized by function.
6. **Procedure** — what the system does to the data, step by step, including every decision that could change a result (exclusions, tolerances, orderings, defaults).
7. **Verification** — how correctness was established: tests, reference values reproduced, invariants checked, and what each check would have caught. State what has *not* been verified.
8. **Results** — what the system produces, with numbers.
9. **Discussion** — what the results support, what they do not, and what surprised you.
10. **Limitations** — a section of its own, not a paragraph inside Discussion.
11. **Future work** — with dependencies stated.
12. **Availability** — where the code and data live, licences, and how to reproduce.
13. **Glossary or Notation** — when the document uses specialized terms or symbols.
14. **References** — cited works, and the source appendix if `sources=appendix`.

## Optional sections

- **Related work** — as its own section when the comparison is substantive; otherwise fold into Introduction.
- **Threats to validity** — where the work makes empirical claims.
- **Appendices** — schemas, parameter tables, full result listings.

## Ordering rules

Problem before solution, solution before evidence, evidence before interpretation. Verification always precedes Results, so the reader knows how much to trust the numbers before seeing them. Limitations always follow Discussion and precede Future work, so that each proposed next step is read in light of a stated gap.

## What the introduction must do

Establish the problem in terms a domain reader recognizes, before any implementation detail. Say why the obvious approach is insufficient. Close with a numbered or bulleted statement of contributions, each of which must be supported by a later section — a contribution with no corresponding evidence is a defect.

## What the ending must do

Future work closes the body. It states what is not yet done and what each item depends on. It must not restate the contributions; the abstract and introduction already did that. Availability and references follow as apparatus.

## Status, limitations, next steps

A paper distinguishes what was built and verified from what was designed but not built. With `status_labels=true`, apply the labels inside the System description and summarize them in one table; do not scatter them through Results, where they would blur the line between a finding and a plan.

Limitations get their own section, and each entry names the condition under which the conclusion would fail. Under `evidence=observed-only`, no capability may be reported unless it was observed in the source; a design that exists only as intention belongs in Future work, not System description.
