# Style: academic

Governs wording only — the format file decides the sections.

## Audience

Readers of a journal article, conference paper, thesis chapter, or technical report: domain researchers and reviewers. They will judge whether the work is sound, whether the description is sufficient to reproduce it, and whether the claims are supported. They are patient with formality and intolerant of unsupported assertion.

## Tone

Formal, measured, impersonal without being stilted. Claims are stated once, precisely, with their support attached. Hedging is used where genuine uncertainty exists and nowhere else — a paper that hedges everything reads as evasive.

Use "we" for authorial choices ("we retain only complete cases"). Avoid "I". Avoid addressing the reader as "you".

## Sentence style

- Complete, well-formed sentences; no fragments outside tables.
- Moderate length, 20–30 words, with subordinate clauses used to attach conditions to claims: "Reliability was computed over the 493 respondents with complete item data, which excludes 47 partial records."
- Past tense for what was done, present tense for what the system does and for general statements.
- Passive voice is permitted where the agent is genuinely irrelevant ("scores were computed per respondent"), but active is preferred when a choice is being described, since a choice has an author.
- Every quantitative claim carries its conditions: sample, tolerance, unit, and where the figure came from.

## Vocabulary level

Standard academic register plus the terminology of the relevant field. Technical software terms are used but introduced, because the reader may be a domain scientist rather than an engineer.

## Jargon policy

Field-standard terminology is expected and should be used precisely — do not soften *listwise deletion* into *dropping incomplete rows* in an academic document. Software-engineering jargon is held to a stricter standard than in `technical` style: introduce it on first use, because a reviewer from the substantive field will not have it.

## Defining terms

Defined at first use, either in an appositive clause or in a definitional sentence of its own. A **Glossary** or **Notation** section is expected when the document uses more than a handful of specialized terms or symbols.

## Paragraph style

Four to eight sentences, developing a single point: claim, support, qualification, implication. Paragraphs connect explicitly — "Because the two datasets share no identifier, …" — so the argument can be followed without the section headings. Lists are used sparingly, chiefly for enumerating conditions, criteria, or steps of a procedure that a reader must reproduce.

## Good phrasing

> Because the three datasets share no respondent identifier and were collected in different years from different populations, we treat them as separate corpora rather than attempting a join. This constrains the analysis to within-dataset statements.

> Coefficient alpha computed over the 493 complete cases was 0.8356, against a published value of 0.836; the standard error of measurement was 2.1020 against a published 2.102. All 26 item means agreed to within 0.005.

> The stronger check is at the level of the individual respondent: all 493 scale scores reproduced exactly. A single published alpha can conceal two compensating item-level errors; 493 individual sums cannot.

> We report this as a limitation rather than a result: the procedure has not been evaluated on a corpus in which the items are ordered differently.

## Bad phrasing

> The system is amazing at handling all kinds of data.

Register and content both fail.

> It seems like the results are probably fine.

Hedging without a stated source of uncertainty.

> We built a pipeline (basically some code that moves data around) and it works great.

Colloquial, and "works" is not a claim a reviewer can evaluate.

> As is well known, reliability is important.

Filler. Either cite it or delete it.
