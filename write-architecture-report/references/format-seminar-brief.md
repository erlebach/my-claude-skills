# Format: seminar-brief

Governs structure only — the style file decides the wording. Template: `assets/template-seminar-brief.md`.

## Purpose

A short document supporting a spoken presentation: a group meeting, a lab seminar, a project update, a ten-minute talk. It is written to be *spoken from* and *handed out*, so it must be scannable at a glance and complete enough to stand alone afterwards. Length target: one to three pages.

## When to use

- Preparing to present the project to colleagues
- A status update that will be talked through rather than read silently
- Any request mentioning a talk, a meeting, a seminar, or a set number of minutes

Use `blog` if it will be read rather than spoken. Use `architecture-doc` if the reader needs it as a standing reference.

## Required sections, in order

1. **One-line summary** — what the project is, in a single sentence, at the very top.
2. **The question** — what problem this addresses, in two or three sentences.
3. **What exists now** — the current state as a short list, each item one line, each with a status label.
4. **How it works** — the system in five to seven bullets, ordered as the data flows. One idea per bullet, no sub-bullets deeper than one level.
5. **Key results or evidence** — the two or three numbers or facts that carry the talk. Each stated with its condition.
6. **Open questions** — what you want the audience's input on. This is the section that makes a seminar useful; do not omit it.
7. **Next steps** — three to five items, each with its dependency.
8. **Glossary** — a compact term/definition table, present whenever any technical term appears.

## Optional sections

- **One diagram** — at most one, placed after "How it works". A talk supports one picture; a second competes with the speaker.
- **Backup detail** — material to answer likely questions, clearly marked as not part of the main line. Always last, after Next steps and before the glossary.
- **Sources** — under `sources=appendix`, a compact table at the end; `sources=none` and `sources=section-end` are the natural choices for this format.

## Ordering rules

Summary first, always — the reader may look at this document for ten seconds while the speaker is talking. Status before mechanism, because an audience's first question is "how far along is this". Open questions must appear before Next steps: the audience should see what is uncertain before they see the plan, or they will treat the plan as settled.

Nothing is nested more than one level deep. Nothing requires reading in order except the first two sections.

## What the introduction must do

The one-line summary must survive being read alone. It names the problem and the approach, and it contains no undefined term. The question section then gives just enough context for someone who arrived late.

## What the ending must do

End on next steps, stated as commitments with dependencies, so that the audience knows what happens after the meeting and what could block it. No summary and no restatement of the one-liner.

## Status, limitations, next steps

Status is load-bearing in this format and appears early, as labels on the "What exists now" list: **Implemented**, **Partial**, **Planned**, **Inferred**, defined in a single line beneath the list when `status_labels=true`.

Limitations are folded into Open questions rather than given a section of their own — in a seminar, a limitation is an invitation for input, and framing it that way gets better discussion than a defensive caveat list. Each next step names what it depends on, so the audience can offer to unblock one.
