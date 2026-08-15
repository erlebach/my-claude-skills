---
title: "<Project name> — <occasion and date>"
generator: "write-architecture-report"
cmd: "/write-architecture-report format=seminar-brief style=<resolved> mode=<resolved> sources=<resolved> evidence=<resolved> status_labels=<resolved> evidence_cache=<resolved> source_root=<absolute path>"
created: "<YYYY-MM-DD_HHhMMmEST>"
last_modified: "<same as created>"
source_root: "<absolute path analyzed>"
source_commit: "<short hash, omit the line if not a git repo>"
source_dirty: <true|false from `git status --porcelain`; omit wherever source_commit is omitted>
format: "seminar-brief"
style: "<resolved style>"
mode: "<resolved mode>"
sources: "<resolved sources>"
evidence: "<resolved evidence>"
status_labels: <true|false>
evidence_cache: "<resolved>"
evidence_bundle: "<absolute path to the bundle directory; omit this line under evidence_cache=off>"
evidence_bundle_sha256: "<digest of the bundle MANIFEST.md; omit this line under evidence_cache=off>"
---

# <Project name> — <occasion and date>

<!-- Skeleton for format=seminar-brief. Target one to three pages. Nothing nests more
     than one level. Delete every HTML comment before delivering. -->

**In one line:** <!-- What this project is, in a single sentence containing no
undefined term. It must survive being read alone, while the speaker is talking. -->

## The question

<!-- Two or three sentences: what problem this addresses, and enough context for
     someone who arrived late. -->

## What exists now

<!-- One line per item, each with a status label. -->

- **<Thing>** — Implemented. <!-- one-line qualifier -->
- **<Thing>** — Partial. <!-- what part -->
- **<Thing>** — Planned. <!-- what it waits on -->

<!-- With status_labels=true, define the labels in a single line here:
     Implemented = built and checked; Partial = built, incomplete; Planned = designed,
     not built; Inferred = read from the code, not confirmed by the authors. -->

## How it works

<!-- Five to seven bullets, ordered as the data flows. One idea per bullet. At most one
     level of sub-bullets. -->

-
-
-

<!-- At most one diagram, here. A second competes with the speaker. -->

## Key results

<!-- The two or three numbers or facts that carry the talk. Each with the condition it
     holds under. -->

-
-

## Open questions

<!-- What you want input on. This is the section that makes the meeting worth holding.
     Limitations live here, framed as questions rather than caveats — it gets better
     discussion. Appears before Next steps on purpose. -->

-
-

## Next steps

<!-- Three to five items, each naming what it depends on, so someone in the room can
     offer to unblock one. -->

1.
2.

<!-- Optional: ## Backup detail — material for likely questions, clearly marked as off
     the main line, placed here after Next steps. -->

## Glossary

| Term | Meaning |
|---|---|
| | |
