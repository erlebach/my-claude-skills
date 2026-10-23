#!/usr/bin/env python3
"""Exercise highlights in headless Chrome on a throwaway page: a repeated phrase is matched by its
surroundings, a highlight whose words are gone is unattached, a new highlight is made from a selection,
a highlight gets a note, both survive a reload, and a click on a highlight deletes it.

    /opt/miniconda3/bin/python test_highlights.py
"""
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

from playwright.sync_api import sync_playwright

PARAS = ["The world model predicts the next latent state from the current one.",
         "Then a cat sat. Then a dog sat. Then a cat sat again on the mat.",
         "This paragraph has <em>emphasised words</em> inside it."]
PAGE = ('<!doctype html><html><head><meta charset="utf-8"><title>t</title></head><body><main>\n<h2 id="s1">Section</h2>\n'
        + "\n".join(f"<p>{p}</p>" for p in PARAS) + "\n</main></body></html>\n")


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
        page.on("dialog", lambda dlg: dlg.accept())
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
        page.fill(".wmn-card textarea", "my note")
        page.click(".wmn-card >> text=Save note")
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
        ok(not errors, f"no page errors {errors}")
    sys.exit(1 if fails else 0)


if __name__ == "__main__":
    main()
