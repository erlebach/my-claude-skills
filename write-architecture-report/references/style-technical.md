# Style: technical

Governs wording only — the format file decides the sections.

## Audience

Technical collaborators: engineers, data engineers, and computational scientists who will read or extend the code. They know what a schema, a pipeline, a lockfile, a fixture, and a CI run are. They are reading to make a decision — whether to adopt it, extend it, or debug it — so precision beats accessibility.

## Tone

Direct and unsentimental. State mechanisms and trade-offs. Say what was rejected and why; a technical reader trusts a document more when it shows the alternatives it considered. No teaching voice, no marketing.

## Sentence style

- Short and declarative. 10–20 words is normal. Fragments are acceptable in tables and lists.
- Active voice, named actor, present tense for behaviour: "`doctor` validates the manifest and exits non-zero on any unknown key."
- Name things exactly as the code names them, in backticks. Never paraphrase an identifier.
- Quantify: counts, sizes, exit codes, tolerances, complexity. "214,663 bytes across 625 rows" beats "much smaller".

## Vocabulary level

Full software vocabulary. Standard terms — idempotent, listwise deletion, denormalized, fixture, invariant, backpressure — are used without gloss.

## Jargon policy

Unrestricted for standard terms. The one rule: **project-invented vocabulary must be defined.** If the codebase coins a word, define it once and then use it consistently. Do not invent new names in the document for things the code already names.

## Defining terms

Only project-specific terms and non-obvious domain terms. A short **Glossary** is still expected if the document coins or relies on more than two project-specific terms, and it is required if the readership crosses a domain boundary (engineers reading about psychometrics, statisticians reading about build systems).

## Paragraph style

Short — two to four sentences. Lead with the claim, follow with the mechanism. Heavy use of tables, lists, and code blocks: a technical reader scans first and reads second, so structure carries most of the load. Prose is reserved for rationale, trade-offs, and anything a table would flatten.

## Good phrasing

> `build` is idempotent: it writes 5 of 5 tables from an empty state and 0 of 5 on rerun, keyed on a content hash of the manifest plus the inputs.

> Reconciliation defaults to disclosed. An entry only fails a run when it declares `enforce: true`, and even then a `published_only` row cannot fail, because a statistic the authors published and this pipeline cannot compute is the normal state of a newly added dataset.

> JSONC was rejected for the machine-read artefacts: three internal `json.loads` call sites would break, and comment stripping corrupts `source` fields holding `file://` URLs. Documentation went into `description` and `$comment` instead.

> Known gap: the reconciliation report does not distinguish a tolerance set too loosely from a genuine match. There is no test for that.

## Bad phrasing

> The build is highly optimized and very fast.

No number, no baseline, no conditions.

> We use a clean, modern architecture with best practices throughout.

Zero information. Name the pattern and the constraint it satisfies.

> The configuration file (a file containing configuration) tells the program what to do.

Over-explaining for this audience; wastes the reader's attention on something they already know.

> Things mostly work, though there might be some issues in certain cases.

Vague hedging. Either name the failure mode or say the case is untested.
