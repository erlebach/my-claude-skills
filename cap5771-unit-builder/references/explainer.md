# Visual explainer

Make it with the `visual-explainer` skill, from the course notes and the existing slides. Put it in `course_site/static/explainers/<unit-slug>.html` and set `materials.explainer` in `unit.yaml` to the file name.

## The pattern the author approved

The author rejected a first version that covered the book section by section ("every last detail"). The approved version is an illustrated post, in the style of Jay Alammar, built on one question.

| Property | Approved pilot: "Who is like C1?" |
|---|---|
| Built on | one question about the running example |
| Sections | 9, numbered; each answers one step of the question |
| Figures | one per section, one colour key for all figures |
| Length | about 2,100 words, 10–12 minutes |
| Detail | stays in the notes; the explainer leaves out what is not needed for the question |
| Title | the question, then "– CAP5771" |

Models:

- `course_site/static/explainers/data-types-quality-similarity.html` (approved pattern).
- `~/world_models/visual_explainers/world-models-comprehensive-survey-nguyen-illustrated-fable51.html` (the author's model of the style).

`…-long.html` is the rejected long version, kept on purpose. Do not copy its structure.

## Rules

- One attribution line under the lead, and no other source line (class `attrib`): the same text as at the top of the notes, with the title in `<em>`.
- Section tags link to the sections of the course notes, never to textbook sections.
- Same running example, same vocabulary headwords, same numbers (from the script) as the notes. If the unit has two datasets, the explainer's question decides which one it uses; ask the author before using both.
- Every new number in the explainer goes into the numbers script, and into the notes after the author approves it.
- One HTML file with no network requests (decided 2026-11-16): no Google Fonts, no CDN. Without internet, a font link made Chrome slow and stopped Safari from showing the page. The font stacks fall back to local fonts (Georgia, Helvetica, Menlo).
- The "notes:" tag beside each heading opens the course notes in a new tab (`target="_blank" rel="noopener"`).
- Every reference to another section of the page ("Section 06") is a link to that section's anchor (`#s6`).
- The color key carries `data-note-block`, so that the html-notes layer can attach a note to it.
- Run the source check on it (`verification.md` §3) and the browser checks at desktop and 390 px.
- Multiple explainers per unit are allowed, for example one per lesson, each on its own question (unit 2 has two: "What does one big customer do to the data?" and "How much of the weather data can we throw away?"). List all of them in `unit.yaml`.
- When an explainer has many data figures, build it with a script from the data of the notes (unit 2: `build_explainers.py`), so every number and coordinate comes from one place. Fix the script, never the HTML.
- Take a full-page screenshot and look at every figure: labels that overlap, values cut at the edge, points outside a panel. On unit 2, four figures had such faults that the build could not catch.
- Section tags must wrap on a phone (`@media (max-width: 600px)`), or a long tag makes the page scroll sideways.
- Number cards: group by attribute, with a label, and compare like with like.
- Never argue from one random draw (one sample, one random dataset). Show the spread over all draws, or build data with the exact property shown.

## Interactive figures (author, 2026-11-14)

An explainer does not have to be static. The goal is student understanding, and sometimes a student understands only by changing a figure and seeing what follows. Up to Module 5, every explainer was static; from now on, decide for each figure.

**Make a figure interactive when the change is the lesson.** Good cases:

| Case | Example |
|---|---|
| A parameter whose effect is the point | k in k-NN: C22's class changes as k grows; C in the soft-margin SVM; the threshold of a fraud model; the fuzzifier p |
| An algorithm that runs in steps | AdaBoost round by round; EM iterations; the perceptron's updates; SOM training |
| One object's computation, chosen by the reader | point at a customer to see its distances, votes, weights or responsibilities |
| Two states to compare | with and without C10; scaled and unscaled; one tree and 100 bagged trees |

Keep a figure static when nothing changes in it that the reader must see change: a table of data, a fixed diagram of a network, a definition.

**Restraint (author, 2026-11-14):** enhance the figures the explainer already has; do not copy the interactive's controls into it. Too much information is as bad as too little. The aim is to engage the student. The explainer stays linear, read from top to bottom like a normal document: no tabs, no modes, no panels that replace the text.

**Rules for an interactive figure:**

- The page is still an illustrated post on one question. The prose leads; each interactive figure serves the step of the argument in its section.
- The default state is a correct static figure: it reads correctly with no interaction, in a screenshot and when printed. The prose states what that default state shows.
- One or two controls per figure, native and keyboard-operable (`<input type="range">`, buttons, `<select>`), with a visible label and the current value. Pointing (hover) may add detail, but nothing is reachable only by hover: a click or a key gives it too.
- A live readout shows the numbers that change, next to the figure, with `aria-live="polite"`.
- The caption says what to try and what to notice, with the numbers: "Move k from 1 to 7. C22 changes to 'yes' at k = 4."
- No autoplay. Step-through figures have Back and Next buttons; a Play button is optional, and respects `prefers-reduced-motion`.
- The data comes from the numbers script, embedded as JSON by the build script. The page may compute only what is cheap and deterministic (a vote, a distance, a threshold count). Every number that the page shows at any control setting must equal the script's value: the build script writes the expected values, and the page has a `__verify()` that compares them, as in the interactives. It sets every control through its range and returns `{checked: N, bad: [...]}`, with `bad` empty when all pass. The expected values come from the numbers script (through its JSON), never from a computation in the build script: a check of the build script against itself proves nothing (Module 5 unit 2, 2026-11-14). Extend the unit's `check_displayed_*.py` to cover the default text.
- Draw from data with SVG, not from embedded images or many precomputed snapshots. The Module 5 unit 4 explainers reached 450 KB from snapshots; aim for under 200 KB.
- Do not copy the unit's interactive: no Predict mode, no flash cards, no stage panel. An explainer figure shows one idea; link to the interactive for full exploration.
- Self-contained: inline script, no libraries, no fonts from the network.
- **Test:** open the page at 1600 × 900 and at 390 px. Operate every control through its whole range; check the console for errors; take screenshots of the default state and of one changed state of every interactive figure; run `__verify()`. The page must not scroll sideways at any setting.
