# Verification

Run these checks on every unit, and on every later change to its text. Run them before you ask the author to review. Report each result, and name each check you did not run.

## Contents

1. Read the sources
2. Compute every number
3. Source check (subagent prompt), and 3b. Gap check (subagent prompt)
4. Confirm each finding
5. Site checks
6. Browser checks
7. Report to the author

## 1. Read the sources

```bash
S=<scratchpad>/sources; mkdir -p $S
pdftotext -layout course_materials/module-NN_*/textbook/<file>.pdf $S/textbook.txt
pdftotext -layout course_materials/module-NN_*/slides/<file>.pdf  $S/deck.txt
```

Read the textbook body for every part the notes cover, not only the headings. Record which parts come from the deck, the textbook, your own knowledge, or text invented for the course.

## 2. Compute every number

One script in the workspace (`build/module-NN/unit_numbers.py`, in git) holds the running example and prints every value used in the notes, the panels, the explainer and the interactive: distances, coefficients, means, standard deviations, date differences. Copy values from its output. Round in one place, in the script. Keep every script in `build/module-NN/`, never only in the scratchpad: the scratchpad is lost when the session ends.

## 3. Source check (subagent prompt)

Dispatch a fresh agent with `model: sonnet`. It must not be the agent that wrote the text. Fill in the brackets:

```text
Check course text against a textbook. You did not write the text.

Files to check:
- <unit>/notes.md
- <unit>/vocabulary.yaml
- <unit>/section-*.yaml   (list each path)
- <explainer path, if checked now>

Sources (extracted with pdftotext -layout):
- textbook: <path>
- deck: <path>

Written from memory, not from the sources (look hardest here): <list>.
The running example (<describe>) is invented; do not check it against the book.

Check:
1. every statement that is not about the invented running example;
2. every textbook section number that the text cites;
3. every vocabulary definition, against the textbook's definition.

For each finding give: the verdict, the exact quote from the course file with its line
number, and the exact quote from the source with its line number. Verdicts:
- CONTRADICTED: the textbook says otherwise.
- WRONG-SECTION: the section number is wrong.
- NOT-IN-TEXTBOOK: the provided pages do not contain the statement. Say whether you
  believe the statement is true.
- DIFFERS: the same idea with a different name, formula or wording, which a student
  who compares the two would notice.

Note: pdftotext keeps the ligatures U+FB01 (fi) and U+FB02 (fl) as single characters.
End with the count of statements checked and the number supported.
```

## 3b. Gap check (subagent prompt)

A source check finds statements that are wrong; it does not find ideas that are missing. Students do not use the textbook, so a missing idea is a gap in the course. After the notes pass the source check, dispatch one fresh agent per unit (`model: sonnet`, in parallel when there are two units). On the pilot this found 5 major, 14 medium and 17 minor gaps; on unit 2, 0 major, 3 medium and 14 minor.

```text
Gap analysis: find meaningful textbook material that is missing from a set of course notes.
Read only; do not edit any file.
Students do NOT use the textbook; the course notes replace it.
Unit: <module, unit, textbook sections>.
Textbook text (pdftotext -layout): <split files>; <full chapter, for the chapter introduction
and to check that the split files are complete>. Ignore other sections, bibliographic notes
and exercises. Read the body text, not only headings.
Course material: <unit>/notes.md, vocabulary.yaml, section-*.yaml, unit.yaml.
For each piece of textbook material (concept, definition, method, formula, property, worked
example, caveat) decide whether the notes cover it. Report only what is missing or partly
covered: the textbook section, line numbers and a short quote; what the notes have instead
(quote, line) or "absent"; importance MAJOR (core idea, or one that later modules rely on),
MEDIUM (a careful course would include it), MINOR (a detail); and where it would go.
Also report textbook examples or figures that teach a MAJOR idea the notes state without
an example, and whether the split files and the full chapter differ.
End with counts per importance, and each subsection marked covered / partly / not covered.
```

Then:

1. Confirm each major finding: grep the textbook for its quote and the notes for the idea.
2. Give the author the major gaps and a recommended set of medium ones, with one recommendation. Add only what the author approves.
3. Write the additions with numbers from the script, in the sections the agent named. Add new terms to the vocabulary.
4. Run the source check again on the new passages only. List them in the prompt by heading, and give the arithmetic to recompute.

## 3c. Second source check (explainer, interactive, slides, quiz)

The notes pass the source check before the other parts are made. The other parts restate the notes and add their own text: captions, Predict questions, flash cards, slide bullets, quiz answers. Check them too. In Module 4 (2026-11-14), one fresh `sonnet` agent per unit checked about 190–215 items each. It found 0 contradictions, but it found an overstated K-means++ claim (C10's chance is 0.156, not "little"), two numbers off by 0.001, a quiz question that depended on the answer to another question, and several terms that were not the vocabulary headwords.

Give the agent the same verdicts as in §3, plus:

- each number against the unit's numbers-script output (`build/module-NN/unitN_out.txt`);
- each term against `vocabulary.yaml`: only headwords;
- each Predict and quiz question: can it be answered on its own, from its own text?

## 4. Confirm each finding

1. Search both files for both quotes. Drop a finding whose quote is not there.
2. If a quote is not found, search again with the white space joined, and with part of the word that avoids "fi" and "fl" (search "speci", not "specific").
3. Fix each confirmed finding. Then read the text around the fix: a fix can make a nearby sentence false.
4. Keep a statement that is correct but not in the textbook. List it in the report.
5. After a fix, rerun the source check on the changed text.
6. When the notes deliberately differ from the textbook (a printing defect), keep the notes' form, add the defect to `textbook-defects.md`, and list it in the report.

## 5. Site checks

```bash
cd course_site
hugo --noBuildLock -d scratch/checkbuild          # no error, no warning
hugo --noBuildLock -d scratch/checkbuild --clock 2027-05-01T12:00:00-04:00   # with future homework
```

- Do not run a plain `hugo` beside the author's preview.
- A new build check is verified only after it has failed once: break the data, build, see the error, restore the file, build clean.
- Run the prose check on each new or changed text file and fix every `WRAP`, `LISTGAP` and `INDENT` finding:

  ```bash
  python3 ~/.claude/skills/plain-technical-english/scripts/check_prose.py <file>
  ```

## 6. Browser checks

Use `playwright-cli`. Serve the site on a port other than 1313:

```bash
cd course_site && hugo server -p 1314 --noBuildLock -d scratch/serve > scratch/server1314.log 2>&1 &
```

For each changed page, at desktop width and at 390 px:

- the formulas render, and no KaTeX error (red text) shows;
- the page does not scroll sideways (`document.documentElement.scrollWidth <= innerWidth`);
- on the rail page, each button shows its panel, and the Course materials links resolve.

For an interactive, also serve it from an empty folder (see `interactive.md`). Stop the server afterwards.

Safari and dark mode were never checked on the pilot. Say so in the report if they are still not checked.

## 7. Report to the author

- what was made, with paths;
- the source of each part (deck, textbook, own knowledge, invented);
- the source check: statements checked, number supported, each finding and what was done;
- the statements kept that are not in the textbook;
- the build, the failed-once checks, the browser checks, the prose check;
- the checks not run;
- open questions, each with a recommendation first and its reason.
