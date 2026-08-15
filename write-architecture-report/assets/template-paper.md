---
title: "<Specific title naming the problem and the approach>"
generator: "write-architecture-report"
cmd: "/write-architecture-report format=paper style=<resolved> mode=<resolved> sources=<resolved> evidence=<resolved> status_labels=<resolved> evidence_cache=<resolved> source_root=<absolute path>"
created: "<YYYY-MM-DD_HHhMMmEST>"
last_modified: "<same as created>"
source_root: "<absolute path analyzed>"
source_commit: "<short hash, omit the line if not a git repo>"
source_dirty: <true|false from `git status --porcelain`; omit wherever source_commit is omitted>
format: "paper"
style: "<resolved style>"
mode: "<resolved mode>"
sources: "<resolved sources>"
evidence: "<resolved evidence>"
status_labels: <true|false>
evidence_cache: "<resolved>"
evidence_bundle: "<absolute path to the bundle directory; omit this line under evidence_cache=off>"
evidence_bundle_sha256: "<digest of the bundle MANIFEST.md; omit this line under evidence_cache=off>"
---

# <Specific title naming the problem and the approach>

<!-- Skeleton for format=paper. Delete every HTML comment before delivering. -->

## Abstract

<!-- 150–250 words: the problem, what was built, how it was checked, what was found,
     and one limitation. Written last. No citations, no undefined abbreviations. -->

## 1. Introduction

<!-- The problem in terms a domain reader recognizes. Why the obvious approach is
     insufficient. What already exists. Close with an explicit contribution list —
     every item must be supported by a later section. -->

**Contributions.**

1. <!-- claim → supported in section N -->
2.

## 2. Background

<!-- Only what is needed to follow the rest: domain concepts, prior systems,
     terminology. Not a literature review unless Related work is folded in here. -->

## 3. Materials and data

<!-- The corpus: provenance, size, collection conditions, known defects, access terms.
     Say what the data cannot support as well as what it can. -->

## 4. System description

<!-- Design and components at the level of detail needed to build an equivalent.
     Organized by function. With status_labels=true, label each component and collect
     the labels in one table at the end of this section. -->

### 4.1 <Component or subsystem>

## 5. Procedure

<!-- What the system does to the data, step by step. Every decision that could change a
     result belongs here: exclusions, tolerances, orderings, defaults, tie-breaking. -->

## 6. Verification

<!-- How correctness was established: tests, reference values reproduced, invariants
     checked. For each check, what it would have caught. Then state plainly what has
     NOT been verified. This section precedes Results on purpose. -->

## 7. Results

<!-- What the system produces, with numbers, units, and the conditions each was
     measured under. -->

## 8. Discussion

<!-- What the results support, what they do not, and what was unexpected. -->

## 9. Limitations

<!-- Its own section. Each entry names the condition under which a conclusion above
     would fail. -->

## 10. Future work

<!-- Each item with its dependency. Do not restate the contributions here. -->

## Availability

<!-- Where code and data live, licences, and what is needed to reproduce the results. -->

## Glossary / Notation

| Term or symbol | Meaning |
|---|---|
| | |

## References

<!-- Cited works. Under sources=appendix, the section-to-source mapping table goes here
     as well, separate from the bibliography. -->
