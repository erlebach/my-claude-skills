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
        ok(page.evaluate(opts) == ["All (4)", "To review (3)", "Text changed (1)"], f"step-through counts {page.evaluate(opts)}")
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
        ok(not errors, f"no page errors {errors}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
