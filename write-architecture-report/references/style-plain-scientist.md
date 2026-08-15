# Style: plain-scientist

The default style. Governs wording only — the format file decides the sections.

## Audience

A working scientist. They are comfortable with data, tables, statistics, file formats, and the idea of a database. They are not software architects: terms like *ETL*, *pipeline*, *schema migration*, *idempotent*, *manifest*, *dependency injection*, *CI*, and *dashboard framework* are not part of their vocabulary and must be earned before use.

Assume high intelligence and low patience for jargon. They will not ask you what a word means; they will skim past the sentence and lose the thread.

## Tone

Explanatory and matter-of-fact, the way a careful colleague explains their setup at a whiteboard. Confident about what is true, plain about what is not yet done. No salesmanship, no apology, no excitement about the tooling.

## Sentence style

- One idea per sentence. Aim for 15–25 words; let a few run longer for rhythm, but never stack three clauses.
- Active voice with a named actor: "the build step writes five tables", not "five tables are written".
- Concrete subjects. Prefer the name of the thing that acts over an abstraction: "the manifest lists which columns to keep" beats "configuration governs column selection".
- Say the thing, then qualify it. Not: "Subject to the availability of complete cases, the reliability statistic is computed." Rather: "The reliability statistic is computed from the 493 respondents who answered every item."

## Vocabulary level

Ordinary English plus the reader's own scientific vocabulary. *Sample*, *variance*, *missing data*, *spreadsheet*, *column*, *record* need no gloss. Anything from software engineering does.

Substitute where a plain word exists:

| Instead of | Write |
|---|---|
| ingest | read in |
| persist / materialize | save, write |
| orchestrate | run in order, coordinate |
| downstream consumer | whatever reads it next — name it |
| surface (verb) | show, report |
| leverage | use |
| idempotent | running it twice changes nothing |
| schema | the set of columns and their types |

## Jargon policy

Allowed, but only after it is defined, and only when it earns its keep — that is, when you will use the word more than twice or when the reader will meet it in the code. A term used once should be replaced by its definition instead of introduced.

## Defining terms

Mandatory at first use, in the same sentence, using an em dash or parenthesis. Do not defer to the glossary; the glossary is for looking back, not for first contact.

> The results are assembled by an ETL pipeline — code that reads the raw files, reshapes them, and writes clean tables.

A **Glossary** section is required whenever more than two technical terms appear.

## Paragraph style

Three to six sentences, one point each. Open with the point and use the rest to support it, so a skimming reader gets the argument from first sentences alone. Break the paragraph when the subject changes.

Reasoning goes in prose. Lists are for things that genuinely come in parts — steps, inputs, options, failure cases. A bulleted argument reads as a list of assertions with the connective tissue removed.

## Good phrasing

> The project answers one question: given several survey datasets that were never designed to be combined, what can be said about each of them without pretending they join?

> Each dataset is described by a manifest — a small configuration file listing the raw files, the columns to keep, and the checks to run. Nothing about a specific dataset appears in the code itself.

> Two of the three datasets contain no scale items, so the reliability statistics simply do not apply. The build records that as a note rather than an error.

> This is implemented and tested. The user interface that would display these tables is planned but not written.

## Bad phrasing

> A robust, extensible ingestion layer facilitates seamless onboarding of heterogeneous data sources.

Hype, no content, and three undefined terms.

> Manifests are leveraged to parameterize dataset-specific transformations, thereby decoupling the core library from corpus specifics.

Every noun is abstract. Say what a manifest is and what stays out of the code.

> The system handles all edge cases and is fully automated.

Two unverifiable claims. Name the cases handled and say which steps a person still triggers.

> Data is ingested, normalized, and persisted downstream.

Passive, undefined, and it never says what actually ends up where.
