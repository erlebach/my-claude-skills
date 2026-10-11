# Writing prompts the image model cannot misread

The wrapper sends your prompt to the image model word for word (it checks this, see `SKILL.md`). Nothing
between you and the image model edits it any more. So the prompt must already say everything the
picture is allowed to contain. This file says how, with fixes that worked on real figures.

## Why prompts need this

The image model draws something in **every** region of the picture. Where the prompt names a box but
not its contents, the model fills it with plausible content of its own: code, error messages, version
numbers, axis ticks, quoted replies, a company logo. It also cannot count reliably, and it does not know
which side of a conversation a speech bubble belongs to.

Until 2026-10-10 the Codex agent in front of the image model was `gpt-6-astra`, which silently rewrote
every prompt before passing it on (230 of 231 calls). Its edits were mostly tightening:

| What Astra added | Calls (of 231) |
|---|---:|
| an exact panel count ("exactly 3 panels" for our "2 to 4 panels") | ~170 |
| "No additional code." / "No extra text." after a box | ~30 |
| "Caption exactly:", "Label exactly:", "Title exactly:" before quoted text | ~25 |
| "Render all quoted text verbatim without quotation marks." | 5 |
| a fixed size, "1536x1024" | 5 |

The agent now copies the prompt unchanged, so that tightening is the prompt writer's job. It was still not
enough under Astra: images made through it also needed redraws for invented text and a correct design
drawn in red.

## Rules

1. **Give every region its exact text, or say it has none.** A box, card, window, terminal, chat
   bubble or diff the prompt mentions gets either a quoted string or "plain grey bars, no text", or
   "NO text inside".
2. **Fix the panel count.** Write "EXACTLY three panels", not "2 to 4".
3. **Count with labels, not with drawings.** Number the items ("five segments with the digits 1–5 under
   them") or state the count as text ("EXACTLY ten EMPTY boxes, the first three blue"). Never rely on the
   model counting unlabelled dots or points.
4. **Give charts in units, not ratios.** "A linear axis with NO numbers; the h bar 4 units tall, the h/2
   bar exactly 1 unit tall". Name the axis direction and which value goes at which end.
5. **Name the speaker.** A prompt comes from a person icon, a reply from a robot icon. A statement about
   the page or a rule is plain text with no speaker.
6. **Say which colour means what, and when it does not.** "neither red nor green: neither reply is marked
   right or wrong"; "gates 1–3 all the same neutral grey".
7. **No characters where they would make a claim.** A robot next to "the author's code" says a model wrote
   it. Write "NO person, robot or character in this panel" when that matters.
8. **State the layout.** "Panels 1 and 2 side by side on top, panel 3 full width below", with the
   panel count. Left open, the layout changes from draw to draw and long rows get squeezed.
9. **Give every panel its colour and its mark, and draw the recommended practice green.** For each
   panel say blue/orange/green/red and check mark, warning sign or none. A panel that shows what to do
   is green with a check, even when it also lists the wrong ways: on 2026-10-10 a figure titled
   "A null pointer argument: write nullptr" came out under a red header because the prompt gave
   that panel no colour.
10. **Give neutral panels distinct neutral colours.** Two panels that are neither the trap nor the
    recommended practice, but show different ideas, get different neutral colours (blue, purple, teal),
    never orange, red or green. One colour for both merges them for the reader.
11. **State what each arrow means and which way it points.** "ONE arrow pointing DOWN from the pointer
    to its array (the pointer refers to the array)". Left open, arrows come out pointing whichever way
    fits the layout.
12. **Quote a label and say where it sits.** "The words "Fortran routine" are written INSIDE that box".
    "A box labelled X (no other text)" can come out as an empty box.
13. **End every prompt with the STRICT line** (below).

### The STRICT line

Append to the end of every prompt:

> STRICT: draw ONLY the text and code quoted above. Do not add any other words, code, declarations, file
> names, version numbers, quoted replies, error messages, terminal output, axis numbers or captions. A
> box, card or window the prompt gives no text for stays empty or holds a simple wordless icon. No brand
> logos of any company or product; draw a model or AI assistant as a plain robot icon. A prompt comes from
> a person icon (the user); a reply comes from a robot icon; a statement about the page or a rule is plain
> text with no speaker.

It stops most invention but not all. Measured on one batch: 3 of 7 first drafts usable without it, 17 of 28
with it. Fixing the specific panel (examples below) took every one of 15 redraws to a usable image. It can
also remove too much: a box whose wording was described rather than quoted comes out empty. **Quote
anything you want drawn.**

## Fixes that worked (2026-10-10, agentic Use Cases figures)

Each row: what the prompt said, what the image showed, the rewrite that produced a correct redraw.

| Prompt said | Image showed | Rewrite that worked |
|---|---|---|
| `a terminal window icon` | `$ ./a.out` printing `0.3`: an invented command and output | `a small terminal window icon with NO text, no command and no output inside it` |
| `with "std::setprecision(17)" it shows "0.30000000000000004"` | `0.3000000000000004`: one zero missing | `… "0.30000000000000004" (that is 0, a point, 3, then fifteen zeros, then 4: nineteen characters in all)` |
| `the h/2 bar is a quarter of the h bar, labelled "falls by about 4"` | a log axis where the bars fell ~15×, under "about 4" | `a plain LINEAR vertical axis labelled "error", with NO numbers, ticks or log scale … the h bar is 4 units tall and the h/2 bar exactly 1 unit tall` |
| `a code card "first order"` | invented code `u[i] = u[i-1] + h*f(u[i-1]);` | `a card labelled "code" containing only the words "first order" (NO code, no formula, no symbols)` |
| `a small header-file card labelled "the real header declares only summarize"` | an invented `scicomp.hpp` declaring `void summarize();`, and an invented compiler error | `a header-file card whose ONLY text is the file name "scicomp/stats.hpp" and the label …; draw NO code inside the card` plus `the compiler box shows exactly this one error line and nothing else: "error: no member named 'stats' in namespace 'scicomp'"` |
| `a curve over EXACTLY 5 intervals (an odd number)` | 5 dots, i.e. 4 intervals, labelled "5"; and 6 dots (5 intervals) under "even" | `a horizontal bar divided into EXACTLY five equal segments, with the digits 1, 2, 3, 4, 5 written under the five segments`; panel 1 `text only: NO curves, dots, bars or other drawings` |
| `a reply box with a routine and a "main" that "verifies" it` | an invented `int add(int a, int b)` with a `main` of checks | `two blocks of plain grey bars with NO readable code: the top block labelled "routine", the bottom block labelled "main: verifies it on a few inputs", ending in one readable line, "it works"` |
| `a result drawn as a row of digit boxes` | the digits `1234567890` | `a row of EXACTLY ten EMPTY digit boxes with NO digits or characters written in them, the first three blue and the other seven orange` |
| `Row A …: values near "1e6", correct code, verdict "fails"` | the labels "correct code" / "wrong code" dropped, an invented `std::abs(a - b) < 1e-9` added | `three text cells, "values near 1e6", "correct code", and the verdict "fails"` … `NO code in either row` |
| `a log-scale axis with EXACTLY two marked points: "masses near 1e30 kg" and "lengths near 1e-10 m"` | 1e30 on the left of an axis increasing to the right | `values increasing from left to right, with NO tick numbers … "lengths near 1e-10 m" near the LEFT end and "masses near 1e30 kg" near the RIGHT end` |
| `two reply boxes …, with the differing part of each outlined` | invented `auto x = 0.0f;` in red against `0.0;` in green | `each holding only plain grey bars (NO code, no text); one bar in each box differs and is outlined in the SAME neutral blue in both boxes (neither red nor green: neither reply is marked right or wrong)` |
| `two prompt boxes in one chat column` | the user's prompts drawn in the robot's speech bubbles | `two prompt boxes sent by a PERSON icon (the user, not a robot)`; the page's own observation `a plain text note, NOT a speech bubble and with NO person or robot` |
| `the three models stop at different gates, not in order of size` | large at gate 1, medium at 2, small at 3: reverse size order, so the stops still followed size | `"medium" is stopped at gate 1, "large" is stopped at gate 2, "small" gets furthest and is stopped at gate 3` |
| `A box "the author's code with a planted error" climbs past gates 1 to 3` | a robot beside the box, and gate 3 drawn red ("the tests failed") | `Gates 1, 2 and 3 are all the same neutral light grey (NOT red, orange or blue) … NO person, robot or character anywhere in panel 3: the author wrote this code, not a model.` |
| (no rule about logos) | the OpenAI logo drawn as "the model" | the STRICT line's `No brand logos …; draw a model or AI assistant as a plain robot icon` |

## Checking still comes last

A tight prompt reduces faults; it does not end them. Read every image against its prompt and the page,
count what has to be counted (crop and measure if needed), and redraw or caption it yourself, at most
three draws per figure, as `SKILL.md` ("Verify and iterate") says.
