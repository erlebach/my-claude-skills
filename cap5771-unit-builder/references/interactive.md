# Interactives

Make one interactive for each objective that is hard to learn from static text and figures. The author asks for one with `/design <text>`. `/design` is a Claude Code command, not a skill. In this project it means: write a standalone HTML file. Do not make a claude.ai Design canvas. When the text after `/design` is a correction or a comment, act on it and make no canvas.

## Models

- CAP5771: `course_site/static/interactives/preprocess.html` ("What does each preprocessing step do?"): two datasets, ten steps, each in stages. Start from a copy of it. Its data block is written by a build script from the numbers script; every Predict answer has a `check()` that recomputes it, and `__verify()` runs them all.
- CAP5771: `course_site/static/interactives/nearest.html` ("Which customer is nearest?"), the first one, without stages.
- ISC5305: `~/src/2026/isc5305_f2026/cpp_demos/course_site/static/interactives/adaptive_quad.html`.
- CAP5771 Module 4: each page is built from a template in `build/module-04/` (`kmeans_steps.template.html`, `cluster_quality.template.html`). The two unit 2 pages share one frame, `u2_frame.html`, with a page script each (`linkage_tree.page.js`, `dbscan_steps.page.js`). The frame has optional hooks, `pageKey` and `pageControls`, so one page can add a key and a button (the Eps circles of `dbscan_steps`, key C) without changing the other. Fix the template or the frame and rerun the build script; never edit the generated page.

## Rules

| Rule | Detail |
|---|---|
| One file | All CSS, script and data inside. No fonts, libraries or network requests. |
| Location | `course_site/static/interactives/<name>.html` |
| 16:9 stage | `.stage` sized in units of `--u: min(1vw, 1.7778vh)`. Controls in a side column; figures on a board. |
| Narrow screens | `@media (max-aspect-ratio: 4/3), (max-width: 700px)`: a stacked page that scrolls. |
| Modes | Explore (a few set-up cases), Predict (at least 20 questions: the reader commits, then sees the answer), Flash cards (the whole bank of at least 30 cards, shuffled). |
| Stages | Break each multi-step algorithm into stages, as the ISC5305 pages `assembly.html`, `csr_build.html` and `newton.html` do. A step bar shows "Step t of n" and a caption with the stage's numbers. Keys: → or N next stage, ← or Shift+N back, Space play, Shift+Space restart (Home is kept as a silent alias; the Restart button shows Shift+Space). The Shift+Space test must come before the plain Space test in the key handler. In Predict and Flash cards, N goes to the next question or card and Shift+N back (test `e.shiftKey`, not the capital letter, so that Caps Lock does not reverse N). Model: `preprocess.html`. |
| Predict questions stand alone | Each question restates its setting. A **Given** box under the text, built by the page from its own data, holds every value needed to answer. After an answer, **Derivation** (key `D`) opens numbered steps with every intermediate number. Each question has `given()` and `derive()`; `__verify()` checks that every derivation ends at the stored answer. No question depends on the answer to another (`preprocess` Q7 depended on Q6 and was rewritten). Keep the Given box short: in `prune_tree` Q4, a long box pushed the choices out of view in the 16:9 layout (open). Model: `build/module-04/kmeans_steps.template.html`. |
| Links to the notes | Link to the most specific heading, not to the top of the notes. The build script inserts the id → title map at `/*__HEADINGS__*/` with `build/notes_headings.py` (`headings_js("module-NN/<unit>")`), which repeats Hugo's id rule. `build/check_notes_anchors.py` compares the maps with a check build; run it after any change to a notes heading. |
| Help | A "What this page shows" `<dialog>`; `?` opens it. |
| The data | The page stands on its own: a "The data" `<dialog id="data">`, opened by a link beside "What this page shows" and by key `T`, lists every dataset the page uses, each as a table with a short description (attributes, units, class, training/test split). Small sets in full (C1–C24, XOR); large sets (the card payments, simulated points) as a summary (counts, class balance, ranges) with a sample of rows. Each dataset links to the notes heading that defines it (the running-example section and its subsections), through the heading map; never to a later section that only uses it (author, 2026-11-14: XOR linked to "The perceptron on XOR" instead of "The running example › XOR"). Each Explore step's notes line shows two links: "Course notes: <topic heading> · Data: <definition heading>" (one link when both are the same heading). Keep one map, dataset → notes id, so that the step line and the dialog agree. Built from the same data block the page computes with, never typed. Decided 2026-11-14; model: `knn_bayes.html`. |
| Keys | As in `nearest.html`: E, P, F (modes), N (next), ← → , 1–4 (answers), ?. |
| Data | The unit's running example, with values from the numbers script. The unit's vocabulary headwords. |
| Plots | Axis labels, a grid, hover values. Give each axis its own range when the units differ. |

## Magnifier

The lens is the ISC5305 file `interactives/lens.js`, with two larger lens sizes added (125 % and 150 %, 2026-11-14); otherwise unchanged. Install it, or update it, from the workspace folder:

```bash
python3 interactives/add_lens.py <name>
```

It writes the script between `<!-- LENS BEGIN -->` and `<!-- LENS END -->`. Do not edit that block. Rerun the script after a change to `lens.js`, for all pages. The lens adds its own line to the help dialog; `+` opens it, R makes it larger and Shift+R smaller (both wrap). ISC5305's copy does not have the two larger sizes or Shift+R.

## List entry

Add the page to `course_site/data/interactives.yaml`, under its module group. The build fails on a file that is not listed.

```yaml
    - name: <name>
      unit: <unit-slug>          # the rail page lists it under Course materials
      title: "<a question, as in 'Which customer is nearest?'>"
      lesson: <n>
      text: >-
        One or two sentences on what the reader can change and see.
```

List a page before it is written with `planned: true`; remove that line when the file exists. Optionally link it from a rail panel with `try_it`, and from text with `{{< interactive "name" >}}text{{< /interactive >}}`.

## Test

1. Copy the file into an empty folder in the scratchpad and serve it there (`python3 -m http.server 8765`). This proves that it needs nothing else.
2. Open it at 1600 × 900 and at 390 px wide.
3. Check that nothing overflows the stage, that each mode works, that each key works, and that `+` opens the magnifier.
4. For every Predict question, compare its answer with the page's own computation, including ties (two objects at the same distance are a tie, and the answer must say so). Run every option combination through every stage in the page (call each `draw` from the console) and check for errors and for "NaN" in the output. Run `__verify()`. On `preprocess.html` this covered 89 combinations and 649 stages.
5. After you change the file, reload it with a new query string (`?r=2`): going to a new `#` address does not reload the page.
6. Check the browser console: no errors, no network requests other than the page.
