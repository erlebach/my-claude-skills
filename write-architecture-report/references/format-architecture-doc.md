# Format: architecture-doc

Governs structure only — the style file decides the wording. Template: `assets/template-architecture-doc.md`.

## Purpose

A standing reference describing what a system is for and how it is put together. Written to be re-read and to survive changes to the code. Its job is to let someone reason about the system — predict where a change belongs, understand why a piece exists — without reading the source.

## When to use

- Onboarding a collaborator
- Recording the shape of a system while it is fresh
- The default when no format is requested
- Any request phrased as "explain how this works" or "document the architecture"

Choose a different format if the reader will consume it once and discard it (`seminar-brief`), if it must persuade or narrate (`blog`), or if it must satisfy reviewers (`paper`).

## Required sections, in order

1. **Purpose and scope** — what problem the system solves, for whom, and what it explicitly does not do.
2. **Overview** — the whole system in one paragraph plus, if useful, one diagram or ordered list of stages. A reader who stops here should be able to describe the system in a sentence.
3. **Inputs** — what goes in: data, configuration, external services. Where each comes from and what is assumed true about it.
4. **Components** — the parts, one subsection each: what it is responsible for, what it consumes, what it produces, and the one design decision that most shaped it. Group by responsibility, never by directory.
5. **Data and control flow** — how a single unit of work travels end to end. Concrete, following one example through.
6. **Outputs and artifacts** — what the system produces, in what form, and who or what reads it next.
7. **Key design decisions** — each as decision, alternatives considered, reason chosen, consequence accepted. This is the section that ages best; it is worth the space.
8. **Status** — what is implemented, partial, planned, or inferred.
9. **Limitations and known gaps** — honest, specific, including anything untested.
10. **Next steps** — what would come next and what it depends on.
11. **Glossary** — every technical term the audience is not assumed to know.

## Optional sections

- **How to run it** — commands and their preconditions, if a reader is likely to try.
- **Testing and verification** — what is checked and how, if the system's correctness claims depend on it.
- **Repository map** — a short table of top-level locations. Only include it *after* the component sections, and only as an index. It is never a substitute for describing the system.
- **Sources appendix** — required when `sources=appendix`.

## Ordering rules

Goals before mechanism, mechanism before code locations. Components come before flow because flow references them by name. Decisions come after components, since a decision is only meaningful once the pieces it constrains are known. Status, limitations, and next steps close the document as a group, so a reader looking for "where does this stand" finds them together. The glossary is always last.

## What the introduction must do

Name the problem before naming any technology. State what the system is for, who needs it, and what a successful outcome looks like. If the reader stops after the first paragraph, they should know what the project does and why it exists — not what language it is written in.

## What the ending must do

Leave the reader with a clear account of standing: what works, what is not built, what is unknown. It must not end on a summary of how good the system is. The last substantive statement should be about the future or the gaps, not the achievements.

## Status, limitations, next steps

When `status_labels=true`, each component subsection carries a label — **Implemented**, **Partial**, **Planned**, **Inferred** — and the labels are defined the first time one appears. The **Status** section then collects them into one view so the reader does not have to reconstruct it.

Limitations are specific and falsifiable: "untested against a corpus with more than three datasets" rather than "may have scaling limits". Next steps state their dependency: what must be true before each becomes possible.

Under `evidence=observed-only`, no component may be described as Planned unless the plan itself is written down somewhere in the source; otherwise it is not observed and does not belong in the document.
