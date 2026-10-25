---
name: html-notes
description: Add a personal, interactive notes layer to a standalone HTML file (a tutorial, report, explainer or Claude-generated page) so the reader can attach their own notes to paragraphs, equations and figures in the browser. Notes are saved to a sidecar <name>.notes.js next to the HTML, survive regeneration of the HTML, and show read-only in Safari/Firefox. Use this whenever the user wants to annotate, comment on, add margin notes or personal notes to, or "write in" an HTML page they read locally — or wants to restore/update notes after an HTML file was regenerated, or wants an AI to work through (fix, answer) the notes on a page — even if they don't say "skill" or "notes layer".
---

# html-notes

Adds a self-contained notes layer to a local HTML page. In Chrome or Edge, the reader hovers over a block, clicks the gold **+**, and types a note (`$…$` math works if the page uses KaTeX or MathJax). Notes are written straight to `<stem>.notes.js` next to the HTML through Chrome's File System Access API. Other browsers load the same file and show the notes read-only. That is why the notes file is a `.js` and not a `.json`: browsers refuse to `fetch` a sibling file from a `file://` page, but every browser will load it through a `<script>` tag.

## Add or update the layer

```bash
python3 ~/.claude/skills/html-notes/scripts/add_notes.py path/to/page.html
```

- Inserts three marked blocks (`<!-- html-notes:…:begin/end -->`): a `<script src="page.notes.js">` tag before `</head>`, a banner ("Add notes via Chrome only!") after `<body>`, and the notes code before `</body>`.
- Creates an empty `page.notes.js` if there is none. It never overwrites an existing notes file, because that file holds the user's notes.
- Re-running replaces the marked blocks. That makes it the right step both after the HTML was regenerated (the layer is gone, the notes file is not) and after this skill's layer code was improved.
- `--remove` takes the layer out and keeps the notes file. `--banner "<html>"` changes the banner text, and `--banner ""` omits it.

If the script reports an *unmarked* notes layer (one added by hand before this skill existed), delete the old blocks first: the `<script src="….notes.js">` tag, the `<div class="wmn-banner">`, and the `<style>`/`<script>` pair whose classes start with `wmn-`. Then re-run.

## Verify

```bash
/opt/miniconda3/bin/python ~/.claude/skills/html-notes/scripts/check_notes.py path/to/page.html
```

If the page has no notes layer yet, the script first adds it (it runs `add_notes.py`), so this one command also prepares a new page. It then loads the page in headless Chrome and WebKit (Safari's engine). For each browser, it prints the toolbar text, the number of notes in the file, the number of note cards shown, and any page errors. A healthy result shows a toolbar in both browsers, no errors, and the same number of cards as notes (minus any reported as unattached). The script needs the `playwright` Python package, which is installed in `/opt/miniconda3`. The folder picker cannot be driven headlessly, so ask the user to add one note in Chrome and confirm the indicator reads ✓ Synced.

## What to tell the user

- **Highlights:** in Chrome, select text inside a paragraph. A popup offers four colours and **Note**. A colour highlights the text; **Note** highlights it and opens a note card that quotes it. Clicking a highlight reopens the popup to change the colour, edit the note, or **Delete**. Highlights are saved in the same notes file (an item with an `hl` field), sync and merge like notes, and show read-only in Safari 17.2+ and Firefox 140+. **Hide** hides highlights too.
- **Conversations and closing notes:** a note is a conversation. **Reply to AI** (shown only when the AI's message is the last one) adds a turn and queues the note for the AI, whose answer becomes the next turn. Each card has a header row: ▾/▸ to close or open it (on a tall note also **Close note** at the bottom), the status (click it to mark Reviewed), 💬 the number of exchanges (closed notes with 2 or more only), and the icons 🤖 For AI, ✎ edit your latest turn, 🗑 delete. A closed note is that row alone, with the note's first words. Reviewed closes a note; a new AI answer opens it. The open/closed state is saved in the notes file. The toolbar's **Close all** / **Open all** acts on every note. Esc opens or closes the note under the pointer; near the bottom of the window it hides or shows the toolbar; otherwise the page gets the key. The toolbar is as wide as the page's text column (measured from its paragraphs) and wraps to a second line if needed.
- **Asking an AI to act on notes:** each card has a **For AI** button (also in a highlight's popup); the toolbar shows the count and has **All for AI** and **Clear**. The AI records each outcome, and the card then shows a badge (**Fixed**, **Answered**, **Declined**) with the AI's reply. **Hide resolved** hides those cards. Clicking **For AI** on a resolved note reopens it.
- **Crossing out text:** select text and click **Strike**. The words are drawn crossed out and queued for the AI, which deletes them on its next pass and marks the strike Fixed. Click struck text, then **Remove strike**: it goes at once, without a dialog, and the toolbar offers **Undo** for 10 seconds.
- **Stepping through:** the toolbar's list and ◀ ▶ buttons move from item to item in page order and flash each one. **All** visits every note, highlight and strike. **To review** visits the AI's results (Fixed, Answered, Declined) that the reader has not yet marked **Reviewed**. **Text changed** visits the notes whose paragraph text changed while the note was neither queued nor resolved; the card shows the change word by word (removed words struck, new words underlined), hovering the note or the paragraph marks the new words in the page, and **Reviewed** clears it. Interactive widget blocks are never flagged, because their text can change on every load. The ← → keys step too, and a position label appears at the top of the screen, so the toolbar need not be visible. While the notes use the arrows, the page does not get them; the toolbar switch **← → notes / page** gives them back to a page that needs them (a slide deck), and is remembered per page.
- **Saving is automatic.** There is no Save button. Every change is written to the notes file at once, and the toolbar shows **✓ Synced**.
- **One-time setup per folder:** the first time a note is added on a page whose folder is not yet connected, a dialog asks to "Choose folder". Pick the folder that contains the HTML file. The page checks this and warns if the folder is wrong. Chrome remembers the folder for every page in it. If Chrome asks for permission, "Allow on every visit" stops it asking again after a restart.
- **Out of sync:** the toolbar indicator turns red and says what is wrong and what a click on it will do: choose the folder, let Chrome write the file again, or retry a failed write. Until then, changes are kept in the browser's localStorage and are written on the next successful sync.
- **Several tabs or edits by hand:** the page re-reads the notes file whenever the tab regains focus. If the file and the page both changed, they are merged by note id. The newer version of a note wins, and deleted notes stay deleted, because deletions are recorded in the file.
- **When text changes:** a note stays with its block when the block is edited, and becomes unattached only when the block is deleted. Each note stores the block's text (up to 2,000 characters) and its two neighbours' text (600 each). On load, an exact match on the first 120 characters comes first. If that fails, the note goes to the most similar block between its old neighbours. If those neighbours are now adjacent, the block was deleted, and the note appears under **"N unattached"**; **Reattach** moves it to a block the user clicks. If the neighbours changed too, the note goes to the most similar block on the page, if any is similar enough. Notes that move are written back automatically. A paragraph split in two keeps its note on the part that shares the most words with the old text.
- **The notes file doubles as a record:** because each note stores its paragraph's text, `<stem>.notes.js` can be read on its own, with each note next to the passage it is about.
- **Moving notes to another version of a page** (for example a rewrite): copy `a.notes.js` to `b.notes.js` and open `b.html` in Chrome. The notes follow their edited paragraphs and are written back with the new text.
- **Safari and Firefox:** these show the notes read-only. If Safari shows an older set of notes, it is using a cached copy of the notes file: reload with Cmd+Option+R.

## Resolving notes (when you are the AI asked to act on them)

The reader queues notes with **For AI**. Work only on those, unless the reader says "all notes": then queue them all first with `queue all`.

1. Ask the reader to check the page shows **✓ Synced** in Chrome (or close the tab), so the notes file holds their latest notes.
2. List the queue. Each entry shows the note id, the passage (the block's text, with math as TeX), any highlighted words, and the note:
   ```bash
   python3 ~/.claude/skills/html-notes/scripts/resolve_notes.py page.html list
   ```
3. For each note, start from its **context** block: the section headings, the paragraph before, the passage (with any highlighted or struck words) and the paragraph after. Treat it as the setting of the conversation, like a system prompt: the reader is asking about this passage, in this place of the page. If it is not enough, read the HTML around the passage. Then read the whole conversation and answer the reader's last turn in its light: earlier turns are context too, and the reader may be correcting your last answer. Find the passage in the HTML and decide. A request for a change: edit the HTML, then mark it `fixed`. A question: answer it, and mark it `answered`. If the question shows the text is unclear, also fix the text and mark it `fixed` with the answer in the reply. No change needed, or you need more from the reader: mark it `declined` with the reason.
   ```bash
   python3 ~/.claude/skills/html-notes/scripts/resolve_notes.py page.html mark <id> fixed "Reworded: ... -> ..."
   ```
   A **strike** (listed as `DELETE these words`) asks you to delete exactly those words. Repair the sentence around them only as much as grammar needs (a doubled space, a dangling comma or article). Mark it `fixed` with a short reply ("Deleted." or what you also repaired). If deleting them would make the text wrong, mark it `declined` and say why.
   The reply shows on the card as plain text (`$…$` math renders; Markdown does not). Keep it to one to three sentences; say what changed, or give the answer.
4. Run `check_notes.py` on the page and report what you did to the reader, note by note.

Rules:
- Change the notes file only with `resolve_notes.py`. Never edit `<stem>.notes.js` by hand: the page merges it with the browser's copy by note id and timestamp, and the script sets both. It also keeps earlier replies in a `history` list.
- Never edit the HTML between `<!-- html-notes:…:begin -->` and `<!-- html-notes:…:end -->`. That is the notes layer. If you regenerate the whole HTML file, re-run `add_notes.py` afterwards.
- Do not delete notes unless the reader asks; then use `resolve_notes.py page.html delete <id>`, which records the deletion so the browser does not bring the note back.
- Do not change paragraphs that carry no queued note unless a fix requires it: the reader is shown such changes under **Text changed** for review. Mention every such change in your report.
- After a fix the note follows its rewritten paragraph. A resolved highlight whose words changed stays under its paragraph instead of becoming unattached.

## Limits worth knowing

- Notes attach to these blocks: `p, li, dt, dd, h1–h6, figure, table, pre, blockquote`, and the classes `.eq, .note, .diffnote, .widget`. They are searched inside `<main>` if the page has one, otherwise inside `<body>`. To support a page with other block wrappers, extend `BLOCKS` in `assets/notes-layer.html` and re-run the script on the page.
- Two blocks with identical leading text are told apart by the nearest preceding `id` and their order on the page.
- Step-through scrolls to an item's card or block. A block that the page itself hides (for example a slide that is not on screen in a slide deck) cannot be scrolled to.
- A highlight stays inside one block: a selection that runs into the next block is cut at the end of the first. Text inside KaTeX/MathJax formulas cannot be selected for a highlight (a highlight around inline math still covers it); put a note on the equation instead. A highlight follows its block like a note, and becomes unattached when its exact words are no longer in the block. Reattaching it to a block without those words turns it into a note that quotes them.
- `scripts/test_highlights.py` runs the highlight flows in headless Chrome on a throwaway page. Run it after changing the layer.
- The page needs `</head>` and `</body>` tags. HTML fragments are refused.
