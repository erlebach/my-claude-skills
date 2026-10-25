# html-notes: usage

html-notes adds a personal notes layer to a standalone HTML page, such as a tutorial, a report or a slide deck. You read the page in a browser and attach notes, highlights and strike-throughs to its text. An AI can then work through the notes you queue for it: fix the text, answer your questions, delete the words you crossed out. You check its work in the page.

## Contents

- [How it works](#how-it-works)
- [Set up a page](#set-up-a-page)
- [Features](#features)
- [Work with an AI](#work-with-an-ai)
- [Scripts](#scripts)
- [Put a page on a web server](#put-a-page-on-a-web-server)
- [Limits](#limits)
- [Suggested features to implement (TODO)](#suggested-features-to-implement-todo)

## How it works

A page with notes uses two files in the same folder:

| File | What it holds |
|---|---|
| `page.html` | The page, plus a copy of the notes code between `<!-- html-notes:…:begin -->` and `<!-- html-notes:…:end -->` markers. |
| `page.notes.js` | Your notes, highlights and strikes, as JSON inside `window.NOTES = …;`. |

The notes file is a `.js` file, not a `.json` file. A page opened from disk (`file://`) can load a script next to it, but it cannot read a data file next to it.

Saving needs Chrome or Edge. These browsers can write to a folder on your computer, after you allow it once. Every change is written to `page.notes.js` at once. Safari and Firefox show the notes, highlights and AI replies, but cannot change them.

Each note stores the text of its paragraph, the text of the two paragraphs next to it, and the headings of its section. When the page is edited or regenerated, a note finds its paragraph again by that text. The AI also gets this text as the setting of the note (see [Conversations](#conversations)). A highlight also stores its exact words and the 32 characters on each side of them.

## Set up a page

1. Run the setup script on the page:

    ```bash
    python3 ~/.claude/skills/html-notes/scripts/add_notes.py page.html
    ```

    The script adds the notes code to the page and creates an empty `page.notes.js`. It never overwrites an existing notes file.

2. Open the page in Chrome.
3. Add a note. The first time, a dialog asks you to choose a folder. Choose the folder that contains the page. Chrome remembers it for every page in that folder.

To set up and test a page in one step, run `check_notes.py` on it instead (see [Scripts](#scripts)).

Run `add_notes.py` again in these cases:

- **The skill was improved.** Each page holds its own copy of the notes code, so a page gets new features only when you run the script on it again.
- **The HTML was regenerated** and the notes code is gone. The notes file is not affected, so your notes come back.

To take the notes code out of a page, run `add_notes.py --remove page.html`. The notes file stays.

## Features

### Notes

Move the pointer over a paragraph, equation, figure or list item. Click the gold **+** at its left. Type the note and press Ctrl+Enter or Cmd+Enter to save it, or Esc to cancel. `$…$` math in a note is rendered if the page uses KaTeX or MathJax.

While you type in a note, the page's own keyboard shortcuts are off. For example, the "o" and arrow keys of a slide deck do not change slides. The shortcuts work again when the note is saved or cancelled.

### Conversations

A note is a conversation. Below the AI's answer, click **Reply to AI** and write your next question or correction. **Reply to AI** appears only when the AI's message is the last one; until the AI answers, use ✎ to change what you wrote. Sending the reply queues the note for the AI. On its next pass, the AI adds its answer as the next turn. The AI answers each note in two layers of context:

1. **The setting:** the headings of the section the note is in, the note's paragraph (with any highlighted or struck words), and the paragraphs before and after it. This works like a system prompt. The AI reads more of the page when it needs to.
2. **The conversation:** every earlier turn, yours and the AI's. Each note keeps its own growing context.

You can change your latest turn with ✎ until the AI has answered it. Earlier turns stay as a record.

You do not need to click **Reviewed** before you reply. Sending a reply clears the note's status, so the note leaves **To review** and joins the AI queue. The AI's earlier answer stays in the conversation, with its status. When the AI answers your reply, the note gets a new status and goes back into **To review**.

### Open and closed notes

Each note has a header row:

| Item | What it does |
|---|---|
| ▾ / ▸ | Closes or opens the note. On a tall note, **Close note** at the bottom does the same, so you need not scroll back up. |
| Status (Fixed, Answered, Declined) | The AI's latest result. Click it to mark the note **Reviewed**; it then shows ✓. |
| 💬 N | On a closed note: the number of exchanges (your question and the AI's answer). Shown only from 2 exchanges, when the bar hides a conversation. |
| 🤖 | Queues the note for the AI, or takes it off the queue. |
| ✎ | Edits your latest turn. |
| 🗑 | Deletes the note (**Remove strike** for a strike). |

A closed note is this one row, with the first words of the note in place of the conversation. The toolbar button **Close all** closes every note on the page; once all are closed, it reads **Open all**.

Some events open or close a note for you:

- Marking a note **Reviewed** closes it.
- A new answer from the AI opens it, so you see the answer.
- A change to the note's paragraph opens it, so you see the change.

The open or closed state is saved in the notes file, so every browser shows the same state.

The Esc key opens or closes the note under the pointer. Esc still closes the highlight popup and cancels typing first. A slider, checkbox or button that has the focus does not block Esc. When the pointer is not over a note, Esc does nothing to the notes, and the page gets the key. The one exception is the bottom of the window, where Esc hides or shows the toolbar (see [Toolbar](#toolbar)).

### Highlights

Select text inside a paragraph. A popup appears with:

- four colours (yellow, green, blue, pink): highlight the text in that colour;
- **Note**: highlight the text and open a note that quotes it;
- **For AI**: highlight the text and queue it for the AI;
- **Strike**: cross the text out (see [Strike-through](#strike-through)).

Click a highlight to open the popup again. There you can change the colour, add or edit the note, queue it, or delete it.

### Strike-through

Select text, then click **Strike**. The words get a red line through them, and the strike is queued for the AI automatically. On its next pass, the AI deletes the words and marks the strike **Fixed**.

To remove a strike, click the struck words, then **Remove strike**. 🗑 on the strike's card does the same. The strike goes at once, and the toolbar shows **Undo** for 10 seconds.

### The AI queue

- Each note card has a 🤖 (**For AI**) button. The highlight popup has a **For AI** button. A queued card has a blue "For AI" tag.
- The toolbar shows `For AI: N`, with **All for AI** to queue every open item and **Clear** to empty the queue.
- When the AI has dealt with an item, the card shows a status and adds the AI's reply as the next turn:
    - **Fixed**: the AI changed the page.
    - **Answered**: your note was a question, and the reply answers it.
    - **Declined**: the AI made no change, and the reply says why.
- **Hide resolved** hides the cards that have a status.
- Click 🤖 on a resolved card to reopen it, or **Reply to AI** to ask a follow-up question.

### Step-through

Use the list and the ◀ ▶ buttons in the toolbar to move from item to item in page order. Each step scrolls to the item and flashes it. The position shows as, for example, `3/12`. The list has three choices:

| Choice | Items it visits |
|---|---|
| All | Every note, highlight and strike. |
| To review | The AI's results (Fixed, Answered, Declined) that you have not yet marked **Reviewed**. |
| Text changed | The notes whose paragraph text changed while the note was neither queued nor resolved. The card shows the change: removed words struck through, new words underlined. While the pointer is over the note or the paragraph, the new words are marked in the page. The comparison is by whole words and is approximate; words inside formulas are not marked in the page. |

Click **Reviewed** on a card to take it off both review lists.

The ← and → keys do the same as ◀ and ▶, so you do not need the toolbar on screen. Each step shows the list and the position at the top of the screen, for example "To review: 3 / 12". The keys do nothing while you type in a note or a text field. They also stay with the page while a slider, or any control inside an interactive widget, has the focus; click elsewhere on the page to get them back.

A page can use the arrow keys itself; a slide deck, for example, uses them to change slides. While the notes use the keys, the page does not get them. Click the **← → notes** switch in the toolbar to give the keys back to the page; it then reads **← → page**. The page remembers the switch.

Interactive widget blocks are never flagged as "Text changed", because their text can change on every load.

### Toolbar

The toolbar sits at the bottom of the window, as wide as the page's text column. When its buttons do not fit on one line, it takes a second line. Empty space at the end of the page keeps the toolbar from covering the page's last lines.

To hide the toolbar, move the pointer to the bottom of the window (over the toolbar) and press Esc. To show it again, press Esc with the pointer near the bottom of the window. The page remembers the choice. From left to right the toolbar shows:

1. the number of notes and highlights;
2. the step-through list, ◀, the position, ▶, the **← → notes** / **← → page** switch, and **Close all** / **Open all**;
3. the AI queue count, **All for AI** and **Clear**;
4. **Hide resolved** (only when a card has a status);
5. **N unattached** (only when some items lost their paragraph);
6. **Hide**, which hides every card and highlight;
7. the sync state.

### Sync

The sync state reads **✓ Synced** when the file on disk matches the page. A red warning says what is wrong. It also says what a click on it will do: choose the folder, let Chrome write the file again, or retry a failed write. Until then, the browser keeps your changes and writes them on the next successful sync.

The page reads the notes file again whenever its tab comes back into view. If the file and the page both changed, they are merged item by item, and the newer version of each item wins. Deleted items stay deleted: the file keeps their ids in a `deleted` list.

### When the page changes

- **A paragraph is edited:** its notes follow it.
- **A paragraph is deleted:** its notes move to the **N unattached** panel. Click **Reattach** on one, then click the paragraph to attach it to.
- **A highlight's words are gone:** the highlight is unattached too, unless the AI resolved it. Fixing a passage is expected to change its words.
- **A paragraph is split in two:** the note stays with the part that shares the most words with the old text.

To move notes to another version of a page (for example a rewrite), copy `a.notes.js` to `b.notes.js` and open `b.html` in Chrome.

## Work with an AI

1. Queue the items you want handled: 🤖 on each card, **For AI** in a highlight's popup, or **All for AI** in the toolbar.
2. Check that the page shows **✓ Synced**, or close the tab.
3. Ask the AI, for example: "Resolve the queued notes on page.html."
4. When the AI is done, reload the page. Choose **To review** in the step-through list and step through the results with → or ▶. For each result, click **Reviewed** to accept it, or **Reply to AI** to correct it or ask a follow-up question.
5. Choose **Text changed** and check any paragraph the AI changed without a queued note.

The AI follows the "Resolving notes" section of `SKILL.md`. In short, it:

- lists the queue with `resolve_notes.py`;
- edits the HTML but never the notes code inside it;
- records each outcome with `resolve_notes.py mark`, and never edits `page.notes.js` by hand;
- reports what it did, note by note.

### Notes that ask for a figure

A note can ask for a new figure, or for a change to an existing one ("Regenerate the panel with a camera"). Interactive illustrations are created with the `/design` command of Claude Code (a command, not a skill). For a static figure, the AI uses the `gpt-image-bridge` skill if Claude Code runs with it. Otherwise, the AI declines the note or offers an SVG figure instead.

1. The AI writes the prompt and saves it as a file next to the other figure prompts.
2. The AI checks each image against the prompt and the page, and draws it again if the image is wrong. It draws at most three times.
3. The AI saves each image as a new file and links the page to that file. It never overwrites or deletes an existing figure. A changed figure gets a new name, for example `-v3`.
4. The AI adds the figure to the page with a caption and alt text, and marks the note `fixed`.

Review the figure on the page as you review other results. To ask for changes, use **Reply to AI**.

## Scripts

All scripts are in `~/.claude/skills/html-notes/scripts/`. They run with plain `python3`. If that Python has no `playwright` package, the scripts that need it start again with `/opt/miniconda3/bin/python`.

| Script | What it does |
|---|---|
| `add_notes.py page.html` | Adds or updates the notes code in the page, and creates an empty notes file if there is none. `--remove` takes the code out. `--banner "<html>"` changes the banner at the top, and `--banner ""` leaves it out. |
| `check_notes.py page.html` | Adds the notes code if the page has none, then loads the page in headless Chrome and WebKit (Safari's engine). It reports the toolbar, the counts of notes, highlights, queued and resolved items, the cards shown, and any page errors. |
| `resolve_notes.py page.html list` | Lists the queued items, each with its paragraph, its words (for a highlight or strike) and the whole conversation. `--all` lists every item. |
| `resolve_notes.py page.html queue all` | Queues every open item. `queue ID …` queues the named items. |
| `resolve_notes.py page.html mark ID STATUS "reply"` | Adds the AI's turn to the conversation and records the outcome. STATUS is `fixed`, `answered` or `declined`. The script sets the timestamps so that the browser does not overwrite the change, and opens the note. |
| `resolve_notes.py page.html delete ID …` | Deletes items and records their ids in `deleted`. Use it only when the reader asks. |
| `test_highlights.py` | Runs the feature tests (51 checks) in headless Chrome on a throwaway page. Run it after changing the notes code. |

## Put a page on a web server

Copy these files to the same folder on the server:

- `page.html`;
- `page.notes.js`, with its name unchanged;
- any folders the page uses for images, for example `assets/`.

On a server, the notes are for reading. Chrome saves notes only to a folder on your own computer. To add notes, work on the local copy, then upload `page.notes.js` again.

If the notes do not appear:

- **No toolbar:** the notes code does not run. A file previewer may show the page without running its scripts, or the server may block inline scripts (a Content-Security-Policy header).
- **The toolbar shows 0 notes:** the notes file did not load. Check its name and folder. Also check that the server does not send `.js` files with the wrong type together with the `X-Content-Type-Options: nosniff` header.
- **The browser console** (Cmd+Option+J in Chrome) names the cause.
- **Old notes after an upload:** force a reload with Cmd+Shift+R.

## Limits

- **What notes attach to:** the blocks `p`, `li`, `dt`, `dd`, `h1`–`h6`, `figure`, `table`, `pre`, `blockquote`, and the classes `.eq`, `.note`, `.diffnote` and `.widget`, inside `<main>` if the page has one. To support other blocks, add them to `BLOCKS` in `assets/notes-layer.html` and run `add_notes.py` on the page again.
- **One block per highlight:** a highlight or strike stays inside one block. A selection that runs into the next block is cut at the end of the first.
- **No partial formulas:** you cannot select part of a formula. A highlight around inline math covers it. To comment on an equation, add a note to it.
- **Hidden blocks:** step-through cannot scroll to a block that the page itself hides, such as a slide that is not showing in a slide deck.
- **Page structure:** the page needs `</head>` and `</body>` tags. HTML fragments are refused.

## Suggested features to implement (TODO)

1. **`check_notes.py` updates old notes code.** Today it adds the code only to a page that has none. It could compare a page's copy with the skill's and replace it when it is older, so that one command always gives a page the current features.
2. **Undo for notes and highlights.** Deleting a strike has Undo and no dialog. Notes and highlights still use a confirmation dialog.
3. **Clear out old deleted ids.** The `deleted` list grows by one id per deletion. Ids older than about 30 days could be dropped, once every tab has synced.
4. **Step-through in slide decks.** Before it scrolls, step-through could show the slide that holds the item. The ← → switch would then not be needed on decks.
5. **Choose the open/close key.** Esc opens and closes notes; a setting could let the reader pick another key.
6. **Export the notes** as a Markdown report: each item with its paragraph, your note and the AI's reply. The notes file already holds this text.
7. **Search and filter:** find notes by text, by highlight colour or by status.
8. **Highlights across blocks.** One selection could make one linked highlight per block, instead of being cut at the first block's end.
9. **Local server mode** (deferred by the author on 2026-10-21): a small local server writes the notes file, so there is no folder dialog and saving also works in Safari and Firefox.
10. **Shared notes** (deferred by the author on 2026-10-21): several readers add notes to the same page.
