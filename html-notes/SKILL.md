---
name: html-notes
description: Add a personal, interactive notes layer to a standalone HTML file (a tutorial, report, explainer or Claude-generated page) so the reader can attach their own notes to paragraphs, equations and figures in the browser. Notes are saved to a sidecar <name>.notes.js next to the HTML, survive regeneration of the HTML, and show read-only in Safari/Firefox. Use this whenever the user wants to annotate, comment on, add margin notes or personal notes to, or "write in" an HTML page they read locally — or wants to restore/update notes after an HTML file was regenerated — even if they don't say "skill" or "notes layer".
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

The script loads the page in headless Chrome and WebKit (Safari's engine). For each browser, it prints the toolbar text, the number of notes in the file, the number of note cards shown, and any page errors. A healthy result shows a toolbar in both browsers, no errors, and the same number of cards as notes (minus any reported as unattached). The script needs the `playwright` Python package, which is installed in `/opt/miniconda3`. The folder picker cannot be driven headlessly, so ask the user to add one note in Chrome and confirm the indicator reads ✓ Synced.

## What to tell the user

- **Highlights:** in Chrome, select text inside a paragraph. A popup offers four colours and **Note**. A colour highlights the text; **Note** highlights it and opens a note card that quotes it. Clicking a highlight reopens the popup to change the colour, edit the note, or **Delete**. Highlights are saved in the same notes file (an item with an `hl` field), sync and merge like notes, and show read-only in Safari 17.2+ and Firefox 140+. **Hide** hides highlights too.
- **Saving is automatic.** There is no Save button. Every change is written to the notes file at once, and the toolbar shows **✓ Synced**.
- **One-time setup per folder:** the first time a note is added on a page whose folder is not yet connected, a dialog asks to "Choose folder". Pick the folder that contains the HTML file. The page checks this and warns if the folder is wrong. Chrome remembers the folder for every page in it. If Chrome asks for permission, "Allow on every visit" stops it asking again after a restart.
- **Out of sync:** the toolbar indicator turns red and says what is wrong and what a click on it will do: choose the folder, let Chrome write the file again, or retry a failed write. Until then, changes are kept in the browser's localStorage and are written on the next successful sync.
- **Several tabs or edits by hand:** the page re-reads the notes file whenever the tab regains focus. If the file and the page both changed, they are merged by note id. The newer version of a note wins, and deleted notes stay deleted, because deletions are recorded in the file.
- **When text changes:** a note stays with its block when the block is edited, and becomes unattached only when the block is deleted. Each note stores the block's text (up to 2,000 characters) and its two neighbours' text (600 each). On load, an exact match on the first 120 characters comes first. If that fails, the note goes to the most similar block between its old neighbours. If those neighbours are now adjacent, the block was deleted, and the note appears under **"N unattached"**; **Reattach** moves it to a block the user clicks. If the neighbours changed too, the note goes to the most similar block on the page, if any is similar enough. Notes that move are written back automatically. A paragraph split in two keeps its note on the part that shares the most words with the old text.
- **The notes file doubles as a record:** because each note stores its paragraph's text, `<stem>.notes.js` can be read on its own, with each note next to the passage it is about.
- **Moving notes to another version of a page** (for example a rewrite): copy `a.notes.js` to `b.notes.js` and open `b.html` in Chrome. The notes follow their edited paragraphs and are written back with the new text.
- **Safari and Firefox:** these show the notes read-only. If Safari shows an older set of notes, it is using a cached copy of the notes file: reload with Cmd+Option+R.

## Limits worth knowing

- Notes attach to these blocks: `p, li, dt, dd, h1–h6, figure, table, pre, blockquote`, and the classes `.eq, .note, .diffnote, .widget`. They are searched inside `<main>` if the page has one, otherwise inside `<body>`. To support a page with other block wrappers, extend `BLOCKS` in `assets/notes-layer.html` and re-run the script on the page.
- Two blocks with identical leading text are told apart by the nearest preceding `id` and their order on the page.
- A highlight stays inside one block: a selection that runs into the next block is cut at the end of the first. Text inside KaTeX/MathJax formulas cannot be selected for a highlight (a highlight around inline math still covers it); put a note on the equation instead. A highlight follows its block like a note, and becomes unattached when its exact words are no longer in the block. Reattaching it to a block without those words turns it into a note that quotes them.
- `scripts/test_highlights.py` runs the highlight flows in headless Chrome on a throwaway page. Run it after changing the layer.
- The page needs `</head>` and `</body>` tags. HTML fragments are refused.
