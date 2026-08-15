---
title: "<System name> — architecture"
generator: "write-architecture-report"
cmd: "/write-architecture-report format=architecture-doc style=<resolved> mode=<resolved> sources=<resolved> evidence=<resolved> status_labels=<resolved> evidence_cache=<resolved> source_root=<absolute path>"
created: "<YYYY-MM-DD_HHhMMmEST>"
last_modified: "<same as created>"
source_root: "<absolute path analyzed>"
source_commit: "<short hash, omit the line if not a git repo>"
source_dirty: <true|false from `git status --porcelain`; omit wherever source_commit is omitted>
format: "architecture-doc"
style: "<resolved style>"
mode: "<resolved mode>"
sources: "<resolved sources>"
evidence: "<resolved evidence>"
status_labels: <true|false>
evidence_cache: "<resolved>"
evidence_bundle: "<absolute path to the bundle directory; omit this line under evidence_cache=off>"
evidence_bundle_sha256: "<digest of the bundle MANIFEST.md; omit this line under evidence_cache=off>"
---

# <System name>: architecture

<!-- Skeleton for format=architecture-doc. Delete a heading whose section genuinely
     does not apply; if its absence would surprise a reader, replace it with one line
     saying why. Delete every HTML comment before delivering. -->

## Purpose and scope

<!-- What problem this system solves, for whom, and what it deliberately does not do.
     No technology named in the first paragraph. If the reader stops here, they should
     be able to say what the project is for. -->

## Overview

<!-- The whole system in one paragraph, then optionally an ordered list of stages or a
     single diagram. Name the pieces you will describe later, in the order you will
     describe them. -->

## Inputs

<!-- What goes in: data, configuration, external services. For each: where it comes
     from, what form it takes, and what is assumed true about it. State assumptions
     explicitly — they are usually the first thing to break. -->

## Components

<!-- One subsection per component, grouped by responsibility and never by directory. -->

### <Component name> — <Implemented | Partial | Planned | Inferred>

<!-- Responsible for what. Consumes what. Produces what. The one design decision that
     most shaped it. Define the labels above where the first one appears, if
     status_labels=true. -->

### <Component name> — <status>

## Data and control flow

<!-- Follow one unit of work end to end, by name: this file, through this step, into
     this table, read by this thing. Concrete beats general. Refer to components by the
     names used above. -->

## Outputs and artifacts

<!-- What the system produces, in what form, where it lands, and what reads it next. -->

## Key design decisions

### <Decision, stated as a choice>

<!-- Alternatives considered. Why this one. What was accepted as a cost. This section
     ages better than any other; give it real space. -->

## Status

<!-- One view of where everything stands. A short table of component → label →
     one-line qualifier is usually the clearest form. -->

## Limitations and known gaps

<!-- Specific and falsifiable. Include what is untested, not only what is broken. -->

## Next steps

<!-- Each item with the thing it depends on. -->

## Glossary

<!-- Every technical term the audience is not assumed to know, defined in one sentence
     each. Required whenever such terms appear. -->

| Term | Meaning |
|---|---|
| | |

<!-- Optional sections, when they earn their place:
     ## How to run it        — commands and preconditions
     ## Testing and verification — what is checked, and what each check would catch
     ## Repository map       — a short index table, AFTER the components, never instead
     ## Sources              — required as an appendix when sources=appendix -->
