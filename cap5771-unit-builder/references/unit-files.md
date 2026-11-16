# Unit folder files

A unit is the folder `course_site/content/modules/module-NN/<unit-slug>/`. The slug is the unit's `unit:` text in kebab case, for example `data-preprocessing`. Model: `module-02/data-types-quality-similarity/`.

The rail layout (`layouts/modules/rail.html`) fails the build when a file or a field below is missing, or when a section's `notes` id is not a heading id in `notes.md`.

## Contents

1. `_index.md`
2. `unit.yaml`
3. `vocabulary.yaml`
4. `section-NN-<name>.yaml`
5. `notes.md`
6. YAML and math
7. Module page

## 1. `_index.md`

Front matter only. Use `weight` for the unit's order in the module.

```yaml
---
title: "Data preprocessing"
weight: 2
layout: rail
build:
  publishResources: false   # the YAML files are sources of this page, not downloads
math: true
description: "Module 2, unit 2: <one sentence, the same as notes.md>."
---

<!-- The rail page is built from the files in this folder, not from this body:
     unit.yaml (goal, takeaway, objectives), vocabulary.yaml, section-NN-*.yaml
     (one panel each, in file-name order) and notes.md (the course notes). -->
```

## 2. `unit.yaml`

Write it first. The author approves it before any other part is written.

```yaml
goal: "<one sentence: what a student can do after the unit>"
takeaway: "<two sentences at most: the one idea to remember, with a concrete case>"
objectives:
  - "<a verb a student can be tested on: classify, compute, state, choose, recognize> ..."
materials:
  explainer: ""   # a file name in static/explainers/; or, for two or more, a list:
                  #   - file: "name.html"
                  #     title: "The explainer's question"
  slides: ""      # an address
  practice: ""    # a page path
```

- Each objective uses one verb that a quiz can test. "Understand" is not testable.
- Objectives decide what goes in the notes. Material outside them goes in "Take it further".
- An empty `materials` value shows a "planned" marker. A `practice` path that does not exist fails the build.
- `materials` feeds two pages: the Course materials panel of the rail page, and the site's Materials page (`content/materials/`, shortcode `materials-table`, added 2026-11-14), which has one row per unit. A new unit appears there with no other edit. The build fails when an `explainer` file is not in `static/explainers/`. Do not keep a second list of the materials anywhere.

## 3. `vocabulary.yaml`

```yaml
terms:
  - term: "data object"
    meaning: "One thing that a dataset describes, such as one customer. A data object is one row of a data table."
    also: ["record", "data point", "instance", "sample"]
```

- The headword is the most common term in the field. `also` lists the synonyms (optional).
- Check each `meaning` against the textbook definition.
- Use the headword, and only the headword, in every later part of the unit: notes, panels, explainer, interactive, slides.
- Give an example from the running example where you can.

## 4. `section-NN-<name>.yaml`

One file per rail panel, in file-name order. Use two digits: `section-01-…`. The first panel is the running example; the last is "Take it further".

```yaml
title: "Distance between data objects"
notes: "distance-between-data-objects"   # the id of a heading in notes.md
example: |
  <a worked example on the running data: a table, a formula, computed values>
key_idea: |
  <two to four short sentences: the rule the example shows>
try_it:                                   # optional
  - interactive: nearest                  # a name in data/interactives.yaml
    text: "Change the unit of income and see which customer is nearest."
```

- Hugo makes heading ids from the text: lower case, spaces become `-`. `## Distance between data objects` gives `distance-between-data-objects`.
- Every number in `example` comes from the script in the scratchpad.
- Each panel matches one `## ` section of `notes.md`, with the same running example as that section.

## 5. `notes.md`

```markdown
---
title: "Course notes: <unit title in lower case>"
weight: 1
math: true
description: "<the same sentence as _index.md>"
---

*Module N, Lessons a and b · {{< lesson module-0N a date >}} and {{< lesson module-0N b date >}}*

Source: P.-N. Tan, M. Steinbach, A. Karpatne and V. Kumar, *Introduction to Data Mining*, 2nd edition, Pearson, 2019, and the authors' lecture slides. The examples are invented for this course.

The goal, objectives and vocabulary of this unit are on the [unit page]({{< ref "/modules/module-0N/<unit-slug>" >}}).

<Which lesson covers which sections. Students do not use the textbook, so do not send them to it.>

## The running example
## <one ## section per main idea>
### Check yourself
## Questions people ask
## Take it further
```

- **Running example.** Ideally, one small invented dataset, used in every section, panel, figure and interactive. Pick it so that each idea of the unit shows on it (the pilot: eight grocery customers, one attribute of each type, units that differ by 1,000×). Use a second dataset only if one example cannot show all the required ideas of the unit (Module 2 unit 2: grocery purchase records, and weather-station readings for the time series and the strongly related attributes). Then:
    - each section uses one dataset, chosen by what it shows best, and says which;
    - the first section introduces every dataset in full;
    - the author approves the split of the sections between the datasets.

  A label (C1, P06, station A) means the same object in every unit of the course. A hypothetical object for one sentence (an outlier, a duplicate) gets no label: "another customer", "a second row for C2".

  Mark invented text with `{{< fake >}}` where a reader could take it for real data.
- **Check yourself.** At the end of each main section: two or three questions, the answers in a collapsed block:

  ```markdown
  ### Check yourself

  1. Question one?
  2. Question two?

  {{< answer >}}

  1. Answer one.
  2. Answer two.

  {{< /answer >}}
  ```

  Keep the blank line after the opening shortcode and before the closing one.
- **Questions people ask.** Questions that students ask, each answered in the notes.
- **Take it further.** Topics outside the objectives. Where an item names a place to read more, it is a source that students can reach and that is accessible: never a textbook section, never a Kumar deck (not ADA compliant). Say that none is needed for the homework or quizzes.
- **Length.** The pilot notes are about 7,000 words, 11 sections. Dates come from shortcodes, never typed.

## 6. YAML and math

- Text in YAML is Markdown.
- In a block scalar (`|`): write math as `\(…\)`, display math as `$$…$$`.
- In a string in double quotes: write `\\(…\\)`.
- A single `$` is text, not math, so a dollar amount such as `$28,000` is safe.

## 7. Module page

In `content/modules/module-NN/_index.md`, under the unit's `## ` heading, add the links line:

```markdown
**Unit page:** [<title>]({{< ref "/modules/module-NN/<unit-slug>" >}}) · **Course notes:** [course notes]({{< ref "/modules/module-NN/<unit-slug>/notes" >}})
```

Remove the module's `{{< planned … >}}` line only when every unit of the module has its parts.

Each module also has a practice quiz on the whole module, `content/modules/module-NN/practice.md` (weight 90, `math: true`, solutions included, "practice, not graded"). Model: `module-04/practice.md` (14 questions). It replaces the module page's "planned" line for the quiz, and the Materials page links it under the module heading.
