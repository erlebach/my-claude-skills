---
title: "<Concrete title naming the problem or the surprise — not the technology>"
generator: "write-architecture-report"
cmd: "/write-architecture-report format=blog style=<resolved> mode=<resolved> sources=<resolved> evidence=<resolved> status_labels=<resolved> evidence_cache=<resolved> source_root=<absolute path>"
created: "<YYYY-MM-DD_HHhMMmEST>"
last_modified: "<same as created>"
source_root: "<absolute path analyzed>"
source_commit: "<short hash, omit the line if not a git repo>"
source_dirty: <true|false from `git status --porcelain`; omit wherever source_commit is omitted>
format: "blog"
style: "<resolved style>"
mode: "<resolved mode>"
sources: "<resolved sources>"
evidence: "<resolved evidence>"
status_labels: <true|false>
evidence_cache: "<resolved>"
evidence_bundle: "<absolute path to the bundle directory; omit this line under evidence_cache=off>"
evidence_bundle_sha256: "<digest of the bundle MANIFEST.md; omit this line under evidence_cache=off>"
---

# <Concrete title naming the problem or the surprise — not the technology>

<!-- Skeleton for format=blog. Headings here are the spine, not a checklist; merge or
     rename them to keep the thread moving. Delete every HTML comment before
     delivering. -->

<!-- Opening: two or three paragraphs, no heading. Start with a situation the reader
     recognizes. First sentence is about the problem, never about the post. By the end
     of this the reader knows what problem is being solved and why it matters — and
     still has not been told any technology. -->

## Why this is harder than it looks

<!-- The complication that rules out the obvious approach. This is what makes the rest
     worth reading; if you cannot name a complication, reconsider the piece. -->

## The idea

<!-- The central approach in plain terms, before any detail. One idea, stated once. -->

## How it works

<!-- Two to four subsections following the flow of the data or the work. Each one
     answers a question the previous section raised. Depth increases monotonically —
     never send the reader back up a level. -->

### <First step, named for what it does>

### <Second step>

## What it produces

<!-- Concrete output. A real example beats a description. -->

## Where it stands

<!-- Plainly: what works, what does not. With status_labels=true, keep labels out of
     the prose above and collect them in a short list here. Fold in the one or two
     limitations that would actually change how a reader reads the results. -->

## What is next

<!-- A few sentences of prose, not a bulleted list. Land it; do not trail off. No
     summary of the post, no thanks for reading, no claims about how good the system
     is. -->

## Glossary

<!-- At the end so it never interrupts the narrative. Required if any technical term
     appears. -->

| Term | Meaning |
|---|---|
| | |

<!-- Optional, when available:
     ## A worked example   — one concrete case followed end to end; the highest-value
                             optional section in this format
     ## What surprised us  — a wrong assumption or an unexpected finding
     ## Sources            — placement per the sources option; sources=none is common
                             and reasonable for a public post -->
