# Format: blog

Governs structure only — the style file decides the wording. Template: `assets/template-blog.md`.

## Purpose

A narrative explanation of the system for a reader who has no obligation to finish it. It carries the reader from a problem they can recognize to an understanding of how the system addresses it. Structure is subordinate to momentum: sections exist to keep the thread, not to catalogue the system.

## When to use

- Explaining the project to a general or cross-disciplinary audience
- A lab website post, a newsletter, a long email to collaborators
- Any request phrased as "explain this in plain terms" or "at the level of a blog post"

Do not use it when completeness matters — a blog post is allowed to omit whole components if they do not serve the story. Use `architecture-doc` for that.

## Required sections, in order

1. **Title** — concrete and specific. It names the problem or the surprise, not the technology.
2. **The problem** — open with a situation the reader recognizes. No preamble about the project; the first sentence is already about the problem. No headings needed before this.
3. **Why it is harder than it looks** — the complication that rules out the obvious approach. This is what makes the rest worth reading.
4. **The approach** — the central idea in plain terms, before any detail. One idea, stated once, clearly.
5. **How it works** — two to four subsections following the flow of the data or the work. Each subsection earns its place by answering a question the previous one raised.
6. **What it produces** — concrete output, ideally with a real example.
7. **Where it stands** — what works, what does not, said plainly.
8. **What is next**
9. **Glossary** — required if any technical term appears, placed at the end so it never interrupts the narrative.

## Optional sections

- **A worked example** — one concrete case followed end to end. The single most effective optional section; include it if a real example exists.
- **What surprised us** — a finding or a wrong assumption. Cheap to write, and it is often what the reader remembers.
- **Sources** — placement follows the `sources` option; `sources=none` is common for this format and is a reasonable default choice for a public post.

## Ordering rules

Problem, complication, idea, mechanism, result, standing. Never open with architecture. Never open with a definition. Each section should raise the question the next section answers; if two adjacent sections could be swapped without loss, one of them is not doing any work and should be merged or cut.

Depth increases monotonically — the reader should never have to go back up a level of abstraction.

## What the introduction must do

Earn the second paragraph. Start with a concrete situation, not with "This post describes…". By the end of the opening the reader must know what problem is being solved and why they should care; they must *not* need to know any technology yet.

## What the ending must do

Land, not trail off. Close on where the work stands and what comes next, in a few sentences of prose rather than a bulleted list. No summary of what the post said, no thanks-for-reading, and no claim about how good the system is.

## Status, limitations, next steps

Honesty in narrative form. "Where it stands" says plainly what is built and what is not; with `status_labels=true`, keep the labels out of the prose sections and collect them in a short list under that heading, since labels interrupt a narrative badly.

Limitations belong in the same section, stated as sentences rather than a bulleted catalogue: a blog reader accepts one or two honest caveats and skips a list of ten. Choose the ones that would actually change how a reader interprets the results.
