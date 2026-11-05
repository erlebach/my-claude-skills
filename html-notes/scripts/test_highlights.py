#!/usr/bin/env python3
"""Exercise highlights in headless Chrome on a throwaway page: a repeated phrase is matched by its
surroundings, a highlight whose words are gone is unattached, a new highlight is made from a selection,
a highlight gets a note, both survive a reload, a click on a highlight deletes it, and typing in a note box
does not trigger the page's own keyboard shortcuts, and the AI queue round-trips through resolve_notes.py.

    /opt/miniconda3/bin/python test_highlights.py
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:                      # run with a python that lacks playwright: retry with the one that has it
    import os
    PY = "/opt/miniconda3/bin/python"
    if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY):
        os.execv(PY, [PY, *sys.argv])
    sys.exit("check_notes.py needs the playwright package: pip install playwright")

PARAS = ["The world model predicts the next latent state from the current one.",
         "Then a cat sat. Then a dog sat. Then a cat sat again on the mat.",
         "This paragraph has <em>emphasised words</em> inside it."]
PAGE = ('<!doctype html><html><head><meta charset="utf-8"><title>t</title></head><body><main>\n<h2 id="s1">Section</h2>\n'
        + "\n".join(f"<p>{p}</p>" for p in PARAS) + "\n</main>\n"
        # keyboard shortcuts like a slide deck's: "o" opens an overview, Space turns the slide
        "<script>window.addEventListener('keydown', () => { window.keysSeen = (window.keysSeen || 0) + 1; }, true);</script>\n"
        "<script>document.addEventListener('keydown', e => { if (e.target.tagName === 'INPUT') return;"
        " if (e.key === 'o') document.body.classList.toggle('ov'); if (e.key === ' ') e.preventDefault();"
        " if (e.key === 'ArrowRight') document.body.dataset.slides = +(document.body.dataset.slides || 0) + 1; });</script>\n"
        '<p><input type="range" id="rg" min="0" max="10" value="5" aria-label="test slider"></p>\n'
        "</body></html>\n")


def item(i, para, quote, pre, suf, at, color, text=""):
    fp = re.sub(r"[\s$]+", "", re.sub(r"<[^>]+>", "", para))[:120]
    return {"id": i, "tag": "P", "fp": fp, "anchor": "s1", "k": 0, "text": text, "created": "2026-01-01T00:00:00.000Z",
            "updated": "2026-01-01T00:00:00.000Z", "hl": {"quote": quote, "pre": pre, "suf": suf, "at": at, "color": color}}


NOTES = {"version": 1, "updated": "2026-01-01T00:00:00.000Z", "notes": [
    item("h1", PARAS[1], "a cat sat", "Then a dog sat. Then ", " again on the mat.", 36, "g"),
    item("h2", PARAS[2], "words that are gone", "", "", 0, "y", "orphan me")]}

SELECT = """([i, a, b]) => { const p = document.querySelectorAll('main p')[i], s = p.textContent;
  const w = document.createTreeWalker(p, NodeFilter.SHOW_TEXT), pts = []; let n, o = 0;
  while ((n = w.nextNode())) { pts.push([n, o]); o += n.data.length; }
  const at = k => { for (let j = pts.length - 1; j >= 0; j--) if (pts[j][1] <= k) return [pts[j][0], k - pts[j][1]]; };
  const r = document.createRange(), x = s.indexOf(a), y = s.indexOf(b) + b.length;
  r.setStart(...at(x)); r.setEnd(...at(y)); getSelection().removeAllRanges(); getSelection().addRange(r);
  p.dispatchEvent(new MouseEvent('mouseup', {bubbles: true})); }"""
HL = "k => [...(CSS.highlights.get('wmn-' + k) || [])].map(r => [r.toString(), r.startOffset])"


def main():
    d = Path(tempfile.mkdtemp())
    (d / "t.html").write_text(PAGE)
    (d / "t.notes.js").write_text("window.NOTES = " + json.dumps(NOTES) + ";\n")
    subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(d / "t.html")], check=True)
    fails = []

    def ok(cond, what):
        print(("ok   " if cond else "FAIL ") + what)
        if not cond:
            fails.append(what)

    with sync_playwright() as pw:
        page = pw.chromium.launch(channel="chrome").new_page()
        errors = []
        page.on("pageerror", lambda e: errors.append(str(e)))
        dialogs = []
        page.on("dialog", lambda dlg: (dialogs.append(dlg.message), dlg.accept()))
        page.goto((d / "t.html").as_uri())
        page.wait_for_timeout(500)
        nuke = "() => document.querySelectorAll('.wmn-dialog').forEach(e => e.remove())"

        ok(page.evaluate(HL, "g") == [["a cat sat", 37]], "repeated phrase drawn at its second copy")
        ok("1 unattached" in page.inner_text(".wmn-bar"), "highlight with missing words is unattached")

        page.evaluate(SELECT, [0, "next", "state"])
        page.wait_for_timeout(100)
        ok(page.is_visible(".wmn-pop"), "selection opens the popup")
        page.click(".wmn-pop .wmn-sw >> nth=2")
        page.evaluate(nuke)
        ok(page.evaluate(HL, "b") == [["next latent state", 29]], "new blue highlight drawn")

        page.evaluate(SELECT, [2, "has", "inside"])
        page.wait_for_timeout(100)
        page.click(".wmn-pop >> text=Note")
        page.evaluate(nuke)
        page.type(".wmn-card textarea", "my note on o")
        ok(page.input_value(".wmn-card textarea") == "my note on o"
           and not page.evaluate("document.body.classList.contains('ov')"), "typing a note does not trigger page shortcuts")
        page.click(".wmn-card >> text=Save note")
        page.keyboard.press("o")
        ok(page.evaluate("document.body.classList.contains('ov')"), "page shortcuts work again once the note is saved")
        page.keyboard.press("o")
        ok(page.inner_text(".wmn-card .wmn-quote") == "“has emphasised words inside”", "highlight across <em> with a note card")

        page.reload()
        page.wait_for_timeout(500)
        ok(page.evaluate(HL, "b") == [["next latent state", 29]], "blue highlight survives reload")
        ok(len(page.evaluate(HL, "y")) == 1 and "Highlights: 4" in page.inner_text(".wmn-bar"), "noted highlight survives reload")

        box = page.evaluate("() => { const r = [...CSS.highlights.get('wmn-b')][0].getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }")
        page.mouse.click(*box)
        page.wait_for_timeout(100)
        page.click(".wmn-pop >> text=Delete")
        ok(page.evaluate(HL, "b") == [], "click on a highlight, then Delete, removes it")

        # the AI queue: queue the note, let resolve_notes.py answer it, see the answer in the page
        res = [sys.executable, str(Path(__file__).with_name("resolve_notes.py")), str(d / "t.html")]
        page.evaluate(nuke)
        page.click(".wmn-card [aria-label='For AI']")
        page.evaluate(nuke)
        ok(page.is_visible(".wmn-card.wmn-queued .wmn-tag.ai") and "For AI: 1" in page.inner_text(".wmn-bar"), "For AI queues a note")
        data = page.evaluate("() => wmnNotes()")          # what the page would have written to disk
        (d / "t.notes.js").write_text("// Personal notes for t.html.\nwindow.NOTES = " + json.dumps(data) + ";\n")
        nid = next(n["id"] for n in data["notes"] if n.get("ai"))
        out = subprocess.run(res + ["list"], capture_output=True, text=True).stdout
        ok(nid in out and "my note on o" in out and "PASSAGE: This paragraph has emphasised words inside it." in out
           and "section: Section" in out and "before:  Then a cat sat." in out,
           "resolve_notes.py lists the queued note with its context: section, paragraphs before and after, passage")
        subprocess.run(res + ["mark", nid, "answered", "Yes, it does."], check=True)
        page.reload()
        page.wait_for_timeout(500)
        ok(page.inner_text(".wmn-card .wmn-tag") == "Answered" and "AI (answered): Yes, it does." in page.inner_text(".wmn-card .wmn-reply")
           and "For AI: 0" in page.inner_text(".wmn-bar"), "the answer shows on the card after reload")
        page.click(".wmn-bar >> text=Hide resolved (1)")
        ok(not page.is_visible(".wmn-card.wmn-done"), "Hide resolved hides it")
        page.click(".wmn-bar >> text=Show resolved (1)")
        page.click(".wmn-bar >> text=All for AI")
        page.evaluate(nuke)
        ok("For AI: 2" in page.inner_text(".wmn-bar"), "All for AI queues every open item")
        page.click(".wmn-bar >> text=Clear")
        ok("For AI: 0" in page.inner_text(".wmn-bar"), "Clear empties the queue")
        data = page.evaluate("() => wmnNotes()")
        (d / "t.notes.js").write_text("// Personal notes for t.html.\nwindow.NOTES = " + json.dumps(data) + ";\n")
        subprocess.run(res + ["mark", "h2", "fixed", "Removed the words."], check=True)
        page.reload()
        page.wait_for_timeout(500)
        ok("unattached" not in page.inner_text(".wmn-bar") and page.is_visible(".wmn-card[data-id=h2]"),
           "a fixed highlight whose words changed stays under its paragraph")

        # strike: cross out a word; the AI deletes it and marks it fixed
        page.evaluate(SELECT, [0, "latent", "latent"])
        page.wait_for_timeout(100)
        page.click(".wmn-pop >> text=Strike")
        page.evaluate(nuke)
        ok(page.evaluate(HL, "strike") == [["latent", 34]], "Strike crosses out the words")
        data = page.evaluate("() => wmnNotes()")
        (d / "t.notes.js").write_text("// Personal notes for t.html.\nwindow.NOTES = " + json.dumps(data) + ";\n")
        sid = next(n["id"] for n in data["notes"] if n.get("strike"))
        out = subprocess.run(res + ["list"], capture_output=True, text=True).stdout
        ok('DELETE these words: "latent"' in out, "resolve_notes.py lists the strike as words to delete")
        html = (d / "t.html").read_text()
        (d / "t.html").write_text(html.replace("next latent state", "next state")
                                  .replace("again on the mat.", "again on the mat. Then it slept."))
        subprocess.run(res + ["mark", sid, "fixed", "Deleted."], check=True)
        page.reload()
        page.wait_for_timeout(500)
        ok(page.evaluate(HL, "strike") == [] and page.is_visible(f".wmn-card[data-id={sid}] .wmn-tag.fixed"),
           "after the AI deletes the words, the strike shows as Fixed")

        # step-through: three lists; a paragraph edited without a resolved note counts as "Text changed"
        opts = "() => [...document.querySelectorAll('.wmn-bar select option')].map(o => o.textContent)"
        ok(page.evaluate(opts) == ["All (4)", "For AI (0)", "To review (3)", "Text changed (1)"], f"step-through counts {page.evaluate(opts)}")
        page.select_option(".wmn-bar select", "review")
        page.click(".wmn-bar >> text=▶")
        ok("1/3" in page.inner_text(".wmn-bar") and page.evaluate("(document.querySelector('.wmn-flash') || {dataset: {}}).dataset.id") == sid,
           "▶ goes to the first item to review, in page order, and flashes it")
        page.click(f".wmn-card[data-id={sid}] >> text=Reviewed")
        page.evaluate(nuke)
        ok("To review (2)" in page.evaluate(opts), "Reviewed takes an AI result off the review list")
        page.select_option(".wmn-bar select", "changed")
        page.click(".wmn-bar >> text=▶")
        ok(page.is_visible(".wmn-card[data-id=h1] .wmn-tag.was") and page.inner_text(".wmn-card[data-id=h1] .wmn-old ins") == "Then it slept.",
           "a note whose paragraph changed shows the change: new words marked in the note")
        DIFF = "() => [...(CSS.highlights.get('wmn-diff') || [])].map(r => r.toString())"
        page.evaluate(nuke)
        page.hover(".wmn-card[data-id=h1] .wmn-old")
        on_card = page.evaluate(DIFF)
        page.mouse.move(1, 1)
        off = page.evaluate(DIFF)
        page.hover("main p >> nth=1")
        on_para = page.evaluate(DIFF)
        ok(on_card == ["Then it slept."] and off == [] and on_para == ["Then it slept."],
           f"hovering the note or the paragraph marks the new words in the page {on_card} {off} {on_para}")
        page.click(".wmn-card[data-id=h1] >> text=Reviewed")
        page.evaluate(nuke)
        ok("Text changed (0)" in page.evaluate(opts), "Reviewed clears Text changed")

        # removing a strike: click the struck words, then Remove strike; only its id stays, in "deleted"
        page.evaluate(SELECT, [1, "dog", "dog"])
        page.wait_for_timeout(100)
        page.click(".wmn-pop >> text=Strike")
        page.evaluate(nuke)
        box = page.evaluate("() => { const r = [...CSS.highlights.get('wmn-strike')][0].getBoundingClientRect(); return [r.x + r.width / 2, r.y + r.height / 2]; }")
        page.mouse.click(*box)
        page.wait_for_timeout(100)
        before = len(dialogs)
        page.click(".wmn-pop >> text=Remove strike")
        page.evaluate(nuke)
        left = page.evaluate("() => wmnNotes().notes.filter(n => n.strike && !n.status).length")
        ok(page.evaluate(HL, "strike") == [] and left == 0 and len(dialogs) == before
           and "dog" not in page.evaluate("() => wmnNotes().notes.map(n => n.hl ? n.hl.quote : '')"),
           "Remove strike removes it at once, without a dialog, and its words leave the data")
        page.click(".wmn-bar >> text=Undo")
        page.evaluate(nuke)
        back = page.evaluate("() => { const d = wmnNotes(), n = d.notes.find(n => n.strike && !n.status); return n ? [n.ai, d.deleted.includes(n.id)] : null; }")
        ok(page.evaluate(HL, "strike") == [["dog", 23]] and back == [True, False], f"Undo brings the strike back, still queued for the AI {back}")

        # arrow keys: → steps through the list without the toolbar; the switch gives the arrows back to the page
        page.select_option(".wmn-bar select", "all")
        n_all = len(page.evaluate("() => wmnNotes().notes"))
        page.keyboard.press("ArrowRight")
        page.keyboard.press("ArrowRight")
        ok(page.inner_text(".wmn-toast").startswith("All: 2 / ") and page.evaluate("document.body.dataset.slides") is None,
           f"→ steps through the notes, shows the position, and the page does not see the key ({page.inner_text('.wmn-toast')})")
        page.keyboard.press("ArrowLeft")
        ok(page.inner_text(".wmn-toast").startswith("All: 1 / "), "← steps back")
        page.click(".wmn-bar >> text=← → notes")
        page.keyboard.press("ArrowRight")
        ok(page.evaluate("document.body.dataset.slides") == "1" and page.inner_text(".wmn-toast").startswith("All: 1 / "),
           "with the switch on page, the arrows go to the page")
        page.click(".wmn-bar >> text=← → page")

        # conversation: a reply queues the note; the AI's answer is the next turn; Reviewed closes the note into one bar
        card = f".wmn-card[data-id={nid}]"
        page.click(f"{card} >> text=Reply to AI")
        page.fill(f"{card} textarea", "Why?")
        page.click(f"{card} >> text=Send")
        page.evaluate(nuke)
        ok(page.is_visible(f"{card} .wmn-tag.ai") and "You: Why?" in page.inner_text(card), "a reply is added to the note and queues it")
        ok(page.locator(f"{card} .wmn-meta >> text=Reply to AI").count() == 0 and page.locator(f"{card} [aria-label='Edit']").count() == 1,
           "while the reader has the last word there is no Reply, only ✎")
        data = page.evaluate("() => wmnNotes()")
        (d / "t.notes.js").write_text("// Personal notes for t.html.\nwindow.NOTES = " + json.dumps(data) + ";\n")
        out = subprocess.run(res + ["list"], capture_output=True, text=True).stdout
        ok("reader: my note on o" in out and "AI (answered): Yes, it does." in out and "reader: Why?" in out,
           "resolve_notes.py lists the whole conversation")
        subprocess.run(res + ["mark", nid, "answered", "Because the target changes."], check=True)
        page.reload()
        page.wait_for_timeout(500)
        ok(page.locator(f"{card} .wmn-reply").count() == 2 and "💬" not in page.inner_text(card)
           and "Because the target changes." in page.inner_text(card), "the AI's answer is the next turn; an open note shows no count")
        page.click(f"{card} >> text=Reviewed")
        page.evaluate(nuke)
        ok(page.is_visible(f"{card}.wmn-closed") and "Answered ✓" in page.inner_text(card) and "my note on o" in page.inner_text(card)
           and page.locator(f"{card} .wmn-reply").count() == 0 and page.get_attribute(f"{card} .wmn-count", "title") == "2 exchanges"
           and page.inner_text(f"{card} .wmn-count") == "💬2", "Reviewed closes the note into one bar: status, first words, 2 exchanges, icons")
        data = page.evaluate("() => wmnNotes()")
        (d / "t.notes.js").write_text("// Personal notes for t.html.\nwindow.NOTES = " + json.dumps(data) + ";\n")
        page.reload()
        page.wait_for_timeout(500)
        ok(page.is_visible(f"{card}.wmn-closed"), "the closed state is saved in the notes file")
        page.click(f"{card} [aria-label='Open note']")
        page.evaluate(nuke)
        ok(not page.is_visible(f"{card}.wmn-closed") and page.locator(f"{card} .wmn-reply").count() == 2, "▸ opens the note again")
        page.wait_for_timeout(100)
        ok(page.locator(f"{card} .wmn-meta >> text=Close note").count() == 0, "a short note has no Close note button at the bottom")
        page.click(f"{card} [aria-label='Close note']")
        ok(page.is_visible(f"{card}.wmn-closed"), "▾ closes it")
        page.click(f"{card} [aria-label='Open note']")
        page.click(f"{card} >> text=Reply to AI")
        page.fill(f"{card} textarea", "\n".join(f"line {i}" for i in range(20)))
        page.click(f"{card} >> text=Send")
        page.evaluate(nuke)
        page.wait_for_timeout(100)
        page.click(f"{card} .wmn-meta >> text=Close note")
        ok(page.is_visible(f"{card}.wmn-closed"), "a tall note has Close note at the bottom too, and it closes the note")

        # Open all / Close all
        page.click(".wmn-bar >> text=Close all")
        page.evaluate(nuke)
        n_open = page.locator("main .wmn-card:not(.wmn-closed)").count()
        ok(n_open == 0 and page.locator("main .wmn-card").count() > 0 and page.is_visible(".wmn-bar >> text=Open all"), "Close all closes every note")
        page.click(".wmn-bar >> text=Open all")
        page.evaluate(nuke)
        ok(page.locator("main .wmn-card.wmn-closed").count() == 0 and page.is_visible(".wmn-bar >> text=Close all"), "Open all opens every note")

        # Esc: opens or closes the note under the pointer, and nothing else
        page.hover(f"{card} .wmn-head")
        page.keyboard.press("Escape")
        page.evaluate(nuke)
        closed1 = page.is_visible(f"{card}.wmn-closed")
        page.keyboard.press("Escape")
        page.evaluate(nuke)
        ok(closed1 and not page.is_visible(f"{card}.wmn-closed"), "Esc closes and opens the note under the pointer")
        page.mouse.move(1, 1)
        page.keyboard.press("ArrowRight")
        before = page.locator("main .wmn-card.wmn-closed").count()
        page.keyboard.press("Escape")
        page.evaluate(nuke)
        ok(page.locator("main .wmn-card.wmn-closed").count() == before, "Esc does nothing when no note is under the pointer, even after stepping")

        # the bar: as wide as the text column; Esc near the bottom hides and shows it
        geo = page.evaluate("""() => { const b = document.querySelector('.wmn-bar').getBoundingClientRect(), p = document.querySelector('main p').getBoundingClientRect();
                                       return [Math.round(b.left - p.left), Math.round(b.width - p.width)]; }""")
        ok(geo == [0, 0], f"the bar has the left edge and width of the text column {geo}")
        h = page.evaluate("innerHeight")
        page.mouse.move(300, h - 5)
        page.keyboard.press("Escape")
        hidden = not page.is_visible(".wmn-bar")
        page.keyboard.press("Escape")
        ok(hidden and page.is_visible(".wmn-bar"), "Esc near the bottom hides the bar, and again shows it")
        page.mouse.move(300, h // 3)
        page.keyboard.press("Escape")
        ok(page.is_visible(".wmn-bar"), "Esc away from the bottom and from any note leaves the bar alone")
        # a focused slider (common in widgets) must not block Esc, but keeps its arrow keys
        page.focus("#rg")
        page.mouse.move(300, h - 5)
        page.keyboard.press("Escape")
        hidden = not page.is_visible(".wmn-bar")
        page.keyboard.press("Escape")
        ok(hidden and page.is_visible(".wmn-bar"), "Esc near the bottom works while a slider has the focus")
        page.keyboard.press("ArrowRight")
        ok(page.input_value("#rg") == "6", "with a slider focused, → moves the slider, not the notes")
        page.evaluate("document.activeElement.blur()")

        # in a note, no key acts outside it, not even a page handler that listens early; the mouse still works
        state = "() => [window.keysSeen || 0, document.body.classList.contains('ov'), document.body.dataset.slides, scrollY]"
        page.click(f"{card} [aria-label='Edit']")
        page.evaluate(nuke)
        s0 = page.evaluate(state)
        page.keyboard.type("o ")
        page.keyboard.press("ArrowRight")
        ok(page.evaluate(state) == s0 and "o " in page.input_value(f"{card} textarea"), "while typing in a note, no key reaches an early page handler")
        page.mouse.click(300, 300)
        page.evaluate(nuke)
        s0 = page.evaluate(state)
        pos0 = page.inner_text(".wmn-toast")
        for key in ("o", "ArrowRight", "Space", "PageDown"):
            page.keyboard.press(key)
        page.wait_for_timeout(100)
        ok(page.evaluate(state) == s0 and page.inner_text(".wmn-toast") == pos0, "after a mouse click outside the open note, keys still do nothing out there")
        page.click(".wmn-bar >> text=▶")
        ok(page.inner_text(".wmn-toast") != pos0 or page.locator(".wmn-flash").count() > 0, "the mouse still works while the note is open")
        page.click(f"{card} textarea")
        page.keyboard.press("Escape")
        ok(page.locator(".wmn-card textarea").count() == 0, "Esc still cancels inside the note")
        page.click(f"{card} [aria-label='Edit']")
        page.evaluate(nuke)
        page.keyboard.type(" more")
        page.keyboard.press("Control+Enter")
        page.evaluate(nuke)
        ok(page.locator(".wmn-card textarea").count() == 0 and "more" in page.inner_text(card), "Ctrl+Enter still saves inside the note")
        page.mouse.click(300, 300)
        s0 = page.evaluate(state)
        page.keyboard.press("o")
        ok(page.evaluate(state)[:2] == [s0[0] + 1, not s0[1]], "page shortcuts work again once the note is closed")

        # Cmd/Ctrl+Enter from outside the note; Shift also queues; on the note under the pointer it toggles For AI
        page.click(f"{card} [aria-label='Edit']")
        page.evaluate(nuke)
        page.keyboard.type(" outside")
        page.mouse.click(300, 300)
        page.keyboard.press("Control+Enter")
        page.evaluate(nuke)
        ok(page.locator(".wmn-card textarea").count() == 0 and "outside" in page.inner_text(card), "Ctrl+Enter saves even with the focus outside the note")
        page.mouse.move(1, 1)
        page.hover("main p >> nth=0")
        page.click(".wmn-add")
        page.evaluate(nuke)
        page.keyboard.type("queue me")
        page.keyboard.press("Control+Shift+Enter")
        page.evaluate(nuke)
        q = page.evaluate("() => { const n = wmnNotes().notes.find(n => n.text === 'queue me'); return n && [n.id, !!n.ai]; }")
        ok(q and q[1], "Ctrl+Shift+Enter saves and queues the note for the AI")
        page.hover(f".wmn-card[data-id={q[0]}] .wmn-text")
        page.keyboard.press("Control+Shift+Enter")
        page.evaluate(nuke)
        ok(not page.evaluate("id => !!wmnNotes().notes.find(n => n.id === id).ai", q[0]), "Ctrl+Shift+Enter toggles For AI on the note under the pointer")

        # the dialog: three visible buttons; Later and No differ
        toggle = f".wmn-card[data-id={q[0]}] [aria-label='For AI']"
        def flip():
            page.click(toggle)
            page.wait_for_timeout(200)       # the dialog comes after the folder lookup
        flip()
        vis = page.evaluate("""() => [...document.querySelectorAll('.wmn-dialog button')].map(b => [b.textContent, getComputedStyle(b).color !== getComputedStyle(b).backgroundColor])""")
        ok(vis == [["Yes, choose folder", True], ["Later", True], ["No", True]], f"the dialog shows Yes, Later and No, all readable {vis}")
        page.click(".wmn-dialog button >> text=Later")
        ok(page.locator(".wmn-dialog").count() == 0, "Later closes the dialog")
        flip()
        ok(page.locator(".wmn-dialog").count() == 0, "Later: no more asking on this visit")
        page.reload()
        page.wait_for_timeout(500)
        flip()
        ok(page.locator(".wmn-dialog").count() == 1, "Later: asks again when the page is opened again")
        page.click(".wmn-dialog button >> text=/^No$/")
        ok(page.locator(".wmn-dialog").count() == 0, "No closes the dialog")
        page.reload()
        page.wait_for_timeout(500)
        flip()
        ok(page.locator(".wmn-dialog").count() == 0 and "Not synced" in page.inner_text(".wmn-bar"), "No: never asks again; the toolbar warning stays")

        # notes off: N over a note turns off everything the layer adds; elsewhere the key is not ours; it survives a reload
        seen = "() => ['.wmn-bar', '.wmn-banner', '.wmn-card'].map(s => [...document.querySelectorAll(s)].filter(e => e.getClientRects().length).length)"
        page.evaluate(nuke)
        page.click("main p >> nth=0")
        ok(page.evaluate(seen)[0] == 1 and page.evaluate(seen)[2] > 0, "notes on: toolbar and cards show")
        page.mouse.move(1, 1)
        k0 = page.evaluate("window.keysSeen || 0")
        page.keyboard.press("n")
        off1 = page.evaluate(seen)
        page.keyboard.press("n")
        ok(off1 == [0, 0, 0] and page.evaluate(seen)[0] == 1 and page.evaluate("window.keysSeen || 0") == k0, "N turns all notes off and on from anywhere, and the page does not see the key")
        page.hover(f"{card} .wmn-head")
        page.keyboard.press("n")
        ok(page.evaluate(seen) == [0, 0, 0] and page.evaluate("[...CSS.highlights.values()].reduce((s, h) => s + h.size, 0)") == 0,
           "N over a note too: toolbar, banner, cards and highlights are gone")
        page.hover("main p >> nth=1")
        add_shown = page.is_visible(".wmn-add")
        page.evaluate(SELECT, [0, "world", "world"])
        page.wait_for_timeout(100)
        ok(not add_shown and not page.is_visible(".wmn-pop"), "notes off: no + button and no selection popup")
        page.evaluate("getSelection().removeAllRanges()")
        s0 = page.evaluate("() => +(document.body.dataset.slides || 0)")
        page.keyboard.press("ArrowRight")
        ok(page.evaluate("() => +(document.body.dataset.slides || 0)") == s0 + 1, "notes off: the arrow keys go to the page")
        page.reload()
        page.wait_for_timeout(500)
        ok(page.evaluate(seen) == [0, 0, 0], "notes off is remembered after a reload")
        page.mouse.move(5, page.evaluate("innerHeight") - 5)
        page.click(".wmn-on")
        page.evaluate(nuke)
        ok(page.evaluate(seen)[0] == 1 and page.evaluate(seen)[2] > 0, "the corner button turns notes back on")
        page.click(".wmn-bar >> text=Notes off")
        ok(page.evaluate(seen) == [0, 0, 0], "the toolbar button turns notes off")
        page.mouse.move(5, page.evaluate("innerHeight") - 5)
        page.click(".wmn-on")
        page.evaluate(nuke)
        page.mouse.move(1, 1)
        page.hover("main p >> nth=1")
        page.click(".wmn-add")
        page.evaluate(nuke)
        page.hover(".wmn-card textarea")                # pointer over the note too: the box still wins
        page.keyboard.type("nhNH")
        ok(page.input_value(".wmn-card textarea") == "nhNH" and page.evaluate(seen)[0] == 1
           and page.evaluate("getComputedStyle(document.querySelector('.wmn-card textarea')).visibility") == "visible",
           "typing in a note's text box, N and H are just letters, even with the pointer over the note")
        page.mouse.click(300, 300)
        page.hover(".wmn-card textarea")
        page.keyboard.press("n")
        ok(page.locator(".wmn-card textarea").is_visible() and "Save or cancel" in page.inner_text(".wmn-toast"), "with a note open, N refuses and says why")
        page.click(".wmn-card >> text=Cancel")

        # out-of-date pages: --all finds and updates them; other pages, bak folders and notes files are left alone
        add = [sys.executable, str(Path(__file__).with_name("add_notes.py"))]
        f = d / "tree"
        (f / "sub").mkdir(parents=True)
        (f / "bak").mkdir()
        page_src = '<!doctype html><html><head><title>x</title></head><body><main><p>Text.</p></main></body></html>'
        for rel in ("a.html", "sub/b.html", "bak/c.html"):
            (f / rel).write_text(page_src)
            subprocess.run(add + [str(f / rel), "--banner", "My banner"], check=True, capture_output=True)
        (f / "plain.html").write_text(page_src)
        (f / "a.notes.js").write_text('window.NOTES = {"version":1,"updated":"x","notes":[]};\n')
        for rel in ("a.html", "sub/b.html", "bak/c.html"):
            (f / rel).write_text((f / rel).read_text().replace("const canSave", "const OLD=1, canSave"))
        old = (f / "a.html").read_text()
        out = subprocess.run(add + ["--all", str(f), "--check"], capture_output=True, text=True).stdout
        ok("2 out of date, 0 current" in out and (f / "a.html").read_text() == old, f"--all --check lists the out-of-date pages and changes nothing: {out.splitlines()[-1]}")
        out = subprocess.run(add + ["--all", str(f)], capture_output=True, text=True).stdout
        ok("2 updated, 0 current" in out and "OLD=1" not in (f / "a.html").read_text() and "OLD=1" not in (f / "sub/b.html").read_text(), "--all updates them")
        ok("OLD=1" in (f / "bak/c.html").read_text() and "html-notes" not in (f / "plain.html").read_text(), "--all leaves bak folders and pages without notes alone")
        ok('"updated":"x"' in (f / "a.notes.js").read_text() and "My banner" in (f / "a.html").read_text(), "--all keeps the notes file and the page's banner")
        out = subprocess.run(add + ["--all", str(f), "--check"], capture_output=True, text=True).stdout
        ok("0 out of date, 2 current" in out, "after --all, all pages are current")
        m0 = (f / "a.html").stat().st_mtime_ns
        out = subprocess.run(add + [str(f / "a.html")], capture_output=True, text=True).stdout
        ok("already current" in out and (f / "a.html").stat().st_mtime_ns == m0, "a current page is not rewritten")

        # a deck: later content painted over the note, and a box that clips it; Save must still take the click
        (d / "deck.html").write_text("""<!doctype html><html><head><meta charset="utf-8"><title>d</title><style>html,body{overflow:hidden;height:100%;margin:0}
.s{position:absolute;inset:0;overflow:hidden}dl{position:absolute;left:40px;top:40px;display:grid;grid-template-columns:auto 1fr;margin:0}
h2{position:absolute;left:0;right:0;top:110px;height:300px;margin:0;font-size:80px}.b{position:absolute;left:600px;top:40px;width:200px;height:30px;overflow:hidden}.b p{margin:0}</style></head>
<body><main><div class="s"><dl><dt>Wanted item</dt><dd>one thing here</dd></dl><h2>A big heading over the note</h2><div class="b"><p>Clipped text</p></div></div></main></body></html>""")
        subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(d / "deck.html")], check=True)
        deck = page.context.browser.new_page()
        deck.goto((d / "deck.html").as_uri())
        deck.wait_for_timeout(300)
        where_ = """() => ['dd', 'h2'].map(s => { const r = document.querySelector(s).getBoundingClientRect(); return [r.left, r.top]; })"""
        before = deck.evaluate(where_)
        for sel, word in (("dt", "covered"), (".b p", "clipped")):
            deck.hover(sel)
            deck.click(".wmn-add")
            deck.evaluate(nuke)
            deck.keyboard.type(word)
            deck.click(".wmn-card >> text=Save note", timeout=3000)
            deck.evaluate(nuke)
            ok(deck.evaluate("w => wmnNotes().notes.some(n => n.text === w)", word), f"a {word} note can be saved with the mouse")
        deck.wait_for_timeout(100)
        ok(deck.evaluate(where_) == before, "on a deck, saved notes do not move the slide's content")
        boxes = deck.evaluate("""() => [...document.querySelectorAll('.wmn-layer .wmn-card')].map(c => { const r = c.getBoundingClientRect(), t = c.querySelector('.wmn-text');
            const hit = document.elementFromPoint(r.left + 40, r.top + 10); return [Math.round(r.width) > 0, r.bottom <= innerHeight, c.contains(hit), t.textContent]; })""")
        ok(len(boxes) == 2 and all(b[0] and b[1] and b[2] for b in boxes), f"on a deck, saved notes float on top, even from a box that clips them {boxes}")
        away = "() => [...document.querySelectorAll('.wmn-layer .wmn-card')].filter(c => c.getClientRects().length).length"
        deck.evaluate("() => { document.querySelector('.s').style.visibility = 'hidden'; }")
        deck.wait_for_timeout(100)
        n_hidden = deck.evaluate(away)
        deck.evaluate("() => { document.querySelector('.s').style.visibility = ''; }")
        deck.wait_for_timeout(100)
        n_back = deck.evaluate(away)
        ok(n_hidden == 0 and n_back == 2, f"notes show only while their slide does {n_hidden} {n_back}")
        deck.evaluate("() => { const o = document.createElement('div'); o.id = 'over'; o.style = 'position:fixed;inset:0;background:#000;z-index:30'; document.body.append(o); }")
        deck.wait_for_timeout(100)
        n_over = deck.evaluate(away)
        deck.evaluate("() => document.getElementById('over').remove()")
        ok(n_over == 0, "notes hide behind the deck's own overlay, such as its slide overview")
        # slide a floating note out of the way; its position is remembered; a double click puts it back
        box = "id => { const r = document.querySelector(`.wmn-card[data-id=${id}]`).getBoundingClientRect(); return [Math.round(r.left), Math.round(r.top), r.width, r.height]; }"
        nid2 = deck.evaluate("() => wmnNotes().notes.find(n => n.text === 'covered').id")
        deck.wait_for_timeout(150)
        before2 = deck.evaluate(where_)
        home = deck.evaluate(box, nid2)
        head = lambda r: (r[0] + r[2] / 2, r[1] + 12)
        def drag(r, dx, dy, at=None):
            deck.evaluate(nuke)              # the folder dialog comes a moment after a change, and would cover the note
            x, y = at or head(r)
            deck.mouse.move(x, y)
            deck.mouse.down()
            deck.mouse.move(x + dx / 2, y + dy / 2)
            deck.mouse.move(x + dx, y + dy)
            deck.mouse.up()
            deck.wait_for_timeout(100)
            deck.evaluate(nuke)
        drag(home, 200, 250)
        moved = deck.evaluate(box, nid2)
        ok(abs(moved[0] - home[0] - 200) <= 2 and abs(moved[1] - home[1] - 250) <= 2, f"dragging a note moves it {home} -> {moved}")
        ok(deck.evaluate(where_) == before2, "dragging a note does not move the slide's content")
        ok(deck.evaluate("id => !!wmnNotes().notes.find(n => n.id === id).pos", nid2), "the position is recorded with the note")
        deck.reload()
        deck.wait_for_timeout(300)
        ok(deck.evaluate(box, nid2)[:2] == moved[:2], "the position survives a reload")
        deck.click(f".wmn-card[data-id={nid2}] [aria-label='Close note']")
        deck.evaluate(nuke)
        deck.wait_for_timeout(150)
        closed = deck.evaluate(box, nid2)
        drag(closed, 40, 30, (closed[0] + closed[2] / 2, closed[1] + closed[3] / 2))
        ok(deck.locator(f".wmn-card[data-id={nid2}].wmn-closed").count() == 1 and deck.evaluate(box, nid2)[:2] != closed[:2],
           "a closed note drags too, and the drag does not open it")
        deck.click(f".wmn-card[data-id={nid2}] [aria-label='Open note']")
        deck.evaluate(nuke)
        deck.wait_for_timeout(150)
        now_at = deck.evaluate(box, nid2)
        t = deck.evaluate("id => { const r = document.querySelector(`.wmn-card[data-id=${id}] .wmn-text`).getBoundingClientRect(); return [r.left + 5, r.top + 8]; }", nid2)
        drag(now_at, 60, 0, tuple(t))
        ok(deck.evaluate(box, nid2)[:2] == now_at[:2], "dragging across a note's text selects it and does not move the note")
        deck.evaluate("getSelection().removeAllRanges()")
        deck.click(f".wmn-card[data-id={nid2}] [aria-label='Edit']")
        deck.evaluate(nuke)
        deck.wait_for_timeout(150)
        ed = deck.evaluate(box, nid2)
        drag(ed, -30, 20, (ed[0] + 9, ed[1] + ed[3] / 2))
        ok(deck.evaluate(box, nid2)[:2] != ed[:2] and deck.evaluate("document.activeElement.tagName") == "TEXTAREA", "an open text box drags by its margin and keeps the focus")
        deck.keyboard.press("Escape")
        deck.evaluate(nuke)
        deck.wait_for_timeout(100)
        r3 = deck.evaluate(box, nid2)
        deck.dblclick(f".wmn-card[data-id={nid2}] .wmn-head", position={"x": r3[2] / 2, "y": 10})
        deck.wait_for_timeout(100)
        deck.evaluate(nuke)
        ok(deck.evaluate("id => !wmnNotes().notes.find(n => n.id === id).pos", nid2) and deck.evaluate(box, nid2)[:2] != r3[:2],
           "a double click on the header row puts the note back in its default place")
        # the selected note: an orange + at its paragraph; Alt+H hides the note to see under it, and shows it again
        mark = "() => { const m = document.querySelector('.wmn-mark'); if (!m || !m.getClientRects().length) return null; const r = m.getBoundingClientRect(); return [r.left, r.top, getComputedStyle(m).backgroundColor]; }"
        card2 = f".wmn-card[data-id={nid2}]"
        deck.mouse.move(1, 1)
        deck.wait_for_timeout(150)
        ok(deck.evaluate(mark) is None, "no orange + while no note is selected")
        deck.hover(f"{card2} .wmn-text")
        deck.wait_for_timeout(150)
        m1 = deck.evaluate(mark)
        dt = deck.evaluate("() => { const r = document.querySelector('dt').getBoundingClientRect(); return [r.left, r.top]; }")
        ok(m1 and m1[2] == "rgb(232, 89, 12)" and m1[0] < dt[0] and abs(m1[1] - dt[1]) < 2, f"a selected note marks its paragraph with an orange + {m1} {dt}")
        deck.keyboard.press("h")
        deck.wait_for_timeout(100)
        hidden = deck.evaluate("s => getComputedStyle(document.querySelector(s)).visibility", card2)
        marked = deck.evaluate(mark) is not None
        deck.mouse.move(1, 1)
        deck.keyboard.press("h")
        deck.wait_for_timeout(100)
        ok(hidden == "hidden" and marked and deck.evaluate("s => getComputedStyle(document.querySelector(s)).visibility", card2) == "visible",
           "H over a note hides it and keeps the orange +; H again, from anywhere, shows it")
        deck.evaluate("() => { window.pageKeys = 0; window.addEventListener('keydown', () => window.pageKeys++); }")
        deck.keyboard.press("h")
        deck.wait_for_timeout(50)
        ok(deck.evaluate("s => getComputedStyle(document.querySelector(s)).visibility", card2) == "visible" and deck.evaluate("window.pageKeys") == 1,
           "H with the pointer off any note is not ours; the page gets it")
        deck.hover(f"{card2} .wmn-text")
        deck.keyboard.press("h")
        deck.wait_for_timeout(100)
        was = deck.evaluate("s => getComputedStyle(document.querySelector(s)).visibility", card2)
        listed = deck.evaluate("() => document.querySelector('.wmn-bar select option').textContent")
        deck.keyboard.press("ArrowDown")
        deck.wait_for_timeout(100)
        ok(was == "hidden" and listed == "All (2)" and deck.evaluate("s => getComputedStyle(document.querySelector(s)).visibility", card2) == "visible",
           "a note hidden with H stays in the step-through list, and stepping shows it again")
        deck.keyboard.press("ArrowDown")
        deck.wait_for_timeout(150)
        ok(deck.evaluate(mark) is not None, "stepping to a note selects it")
        # printing: notes stay out of the printed deck
        deck.emulate_media(media="print")
        pr = deck.evaluate("() => ['.wmn-layer', '.wmn-mark'].map(s => getComputedStyle(document.querySelector(s)).display)")
        deck.emulate_media(media="screen")
        ok(pr == ["none", "none"], f"floating notes and the orange + are not printed {pr}")
        # a small element over the centre of a paragraph must not hide its note; a full overlay must
        deck.evaluate("""() => { const r = document.querySelector('dd').getBoundingClientRect(), o = document.createElement('div'); o.id = 'tiny';
            o.style = `position:fixed;left:${r.left + r.width / 2 - 3}px;top:${r.top + r.height / 2 - 3}px;width:6px;height:6px;z-index:30`; document.body.append(o); }""")
        deck.hover(f"{card2} .wmn-text")
        deck.wait_for_timeout(100)
        n_tiny = deck.evaluate(away)
        deck.evaluate("() => document.getElementById('tiny').remove()")
        ok(n_tiny == 2, f"a small element over a paragraph's centre leaves its note showing {n_tiny}")
        # slides: ← → always move the slides; ↑ ↓ step through the notes and bring up the right slide
        (d / "two.html").write_text("""<!doctype html><html><head><meta charset="utf-8"><title>two</title><style>html,body{overflow:hidden;height:100%;margin:0}
section{position:absolute;inset:0;display:none;padding:40px}section.on{display:block}</style></head><body><main><section class="on"><p>Slide one text here.</p></section>
<section><p>Slide two text here.</p></section><section><p>Slide three text here.</p></section></main>
<script>let i = 0; const S = document.querySelectorAll('section'); document.addEventListener('keydown', e => { const d = e.key === 'ArrowRight' ? 1 : e.key === 'ArrowLeft' ? -1 : 0;
if (!d) return; S[i].classList.remove('on'); i = Math.max(0, Math.min(2, i + d)); S[i].classList.add('on'); window.moves = (window.moves || 0) + 1; });</script></body></html>""")
        subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(d / "two.html")], check=True)
        two = page.context.browser.new_page()
        two.goto((d / "two.html").as_uri())
        two.wait_for_timeout(300)
        at = "() => [...document.querySelectorAll('section')].findIndex(s => s.classList.contains('on'))"
        def note2(word):
            two.hover("section.on p")
            two.click(".wmn-add")
            two.evaluate(nuke)
            two.keyboard.type(word)
            two.keyboard.press("Control+Enter")
            two.wait_for_timeout(250)
            two.evaluate(nuke)
        note2("first")
        two.mouse.click(600, 500)
        two.keyboard.press("ArrowRight")
        ok(two.evaluate(at) == 1, "on a deck, → moves to the next slide")
        two.keyboard.press("ArrowRight")
        note2("third")
        two.mouse.click(600, 500)
        ok(two.evaluate(at) == 2 and not two.is_visible(".wmn-bar >> text=← →"), "on a deck there is no ← → switch")
        two.keyboard.press("ArrowDown")
        two.wait_for_timeout(100)
        ok(two.evaluate(at) == 0 and "All: 1 / 2" in two.inner_text(".wmn-toast"), f"↓ goes to the first note and brings up its slide {two.evaluate(at)}")
        two.keyboard.press("ArrowDown")
        two.wait_for_timeout(100)
        ok(two.evaluate(at) == 2 and "All: 2 / 2" in two.inner_text(".wmn-toast"), "↓ goes on to the next note, on its slide")
        two.keyboard.press("ArrowUp")
        two.wait_for_timeout(100)
        ok(two.evaluate(at) == 0, "↑ goes back")
        two.evaluate(nuke)
        two.click(".wmn-layer [aria-label='Edit']")
        two.evaluate(nuke)
        two.keyboard.press("ArrowLeft")
        two.keyboard.type("x")
        v0 = two.input_value(".wmn-card textarea")
        two.keyboard.press("ArrowLeft")
        ok(two.evaluate(at) == 0 and v0 == "firsxt", f"in a note's text box, ← only moves the cursor {v0}")
        two.keyboard.press("ArrowDown")
        ok(two.locator(".wmn-card textarea").count() == 1 and "Save or cancel" not in two.inner_text(".wmn-toast"), "in mid-text, ↓ only moves the cursor")
        two.keyboard.press("End")
        two.keyboard.press("ArrowDown")
        two.wait_for_timeout(100)
        ok(two.evaluate(at) == 0 and "Save or cancel" in two.inner_text(".wmn-toast"), "with text open, ↓ at the end of the text will not leave the slide, and says why")
        two.keyboard.press("Escape")
        two.evaluate("""() => { const o = document.createElement('div'); o.id = 'panel'; o.style = 'position:fixed;right:0;top:0;width:200px;height:200px;overflow:auto;z-index:20';
            o.innerHTML = '<div style="height:2000px">speaker notes</div>'; document.body.append(o); }""")
        two.hover("#panel")
        toast3 = two.inner_text(".wmn-toast")
        two.keyboard.press("ArrowDown")
        two.wait_for_timeout(100)
        ok(two.inner_text(".wmn-toast") == toast3, "with the pointer over a scrolling panel, ↑ ↓ are left to the panel")
        two.mouse.move(600, 500)
        two.keyboard.press("ArrowDown")
        two.wait_for_timeout(100)
        ok(two.inner_text(".wmn-toast") != toast3 or two.locator(".wmn-flash").count() > 0, "away from the panel, ↓ steps through the notes again")
        two.close()

        # a notes file belongs to one page: a copied page is read-only; add_notes.py gives it its own file and removes foreign links
        (d / "copy.html").write_text((d / "two.html").read_text())
        cp = page.context.browser.new_page()
        cp.goto((d / "copy.html").as_uri())
        cp.wait_for_timeout(300)
        ok("no notes file of its own" in cp.inner_text(".wmn-bar") and cp.locator(".wmn-add").count() == 0, "a copied page warns and cannot write the other page's notes file")
        cp.close()
        (d / "hand.html").write_text('<!doctype html><html><head><title>h</title><script src="two.notes.js"></script></head><body><main><p>Hand.</p></main></body></html>')
        for name in ("copy", "hand"):
            subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(d / f"{name}.html")], check=True, capture_output=True)
            text = (d / f"{name}.html").read_text()
            ok("two.notes.js" not in text and f"{name}.notes.js" in text and (d / f"{name}.notes.js").exists(), f"add_notes.py gives {name}.html its own notes file")
        fine = page.context.browser.new_page()
        fine.goto((d / "copy.html").as_uri())
        fine.wait_for_timeout(300)
        ok("no notes file of its own" not in fine.inner_text(".wmn-bar"), "after add_notes.py the page can save")
        fine.close()

        (d / "doc.html").write_text("<!doctype html><html><head><meta charset=utf-8><title>l</title></head><body><main><dl><dt>Term</dt><dd>Meaning</dd></dl>"
                                    + "<p>Filler text.</p>" * 200 + "</main></body></html>")
        subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(d / "doc.html")], check=True)
        doc = page.context.browser.new_page()
        doc.goto((d / "doc.html").as_uri())
        doc.wait_for_timeout(300)
        doc.hover("dt")
        doc.click(".wmn-add")
        doc.evaluate(nuke)
        doc.keyboard.type("flow")
        doc.click(".wmn-card >> text=Save note")
        ok(doc.evaluate("() => { const c = document.querySelector('dl .wmn-card'); return !!c && c.previousElementSibling.tagName === 'DD'; }")
           and doc.locator(".wmn-layer").count() == 0, "on a scrolling page, a note stays in the text flow, and a note on a <dt> follows its <dd>")
        doc.close()
        deck.close()
        ok(not errors, f"no page errors {errors}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
