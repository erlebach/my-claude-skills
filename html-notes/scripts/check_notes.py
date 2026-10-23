#!/usr/bin/env python3
"""Load an HTML page with the notes layer in headless Chrome and WebKit (Safari's engine)
and report whether the layer started, how many notes loaded, and any page errors.

    check_notes.py page.html

Needs the playwright Python package and its browsers (pip install playwright;
playwright install webkit). Chrome is used through the installed Google Chrome.
"""
import sys
from pathlib import Path

from playwright.sync_api import sync_playwright

JS = """() => ({
  bar: (document.querySelector('.wmn-bar') || {}).innerText || null,
  loaded: window.NOTES ? window.NOTES.notes.length : null,
  withText: window.NOTES ? window.NOTES.notes.filter(n => n.text).length : null,
  highlights: window.NOTES ? window.NOTES.notes.filter(n => n.hl).length : null,
  painted: (window.CSS && CSS.highlights) ? [...CSS.highlights.values()].reduce((s, h) => s + h.size, 0) : null,
  cards: document.querySelectorAll('.wmn-card').length,
  katexErrors: document.querySelectorAll('.katex-error').length,
})"""


def check(pw, name, launch, url):
    browser = launch()
    page = browser.new_page()
    errors = []
    page.on("pageerror", lambda e: errors.append(str(e)))
    page.on("requestfailed", lambda r: errors.append(f"failed to load {r.url}"))
    page.goto(url)
    page.wait_for_timeout(3000)
    r = page.evaluate(JS)
    browser.close()
    bar = (r["bar"] or "NO TOOLBAR").replace("\n", " · ")
    print(f"{name:7} toolbar: {bar} | items in file: {r['loaded']} (with note text: {r['withText']},"
          f" highlights: {r['highlights']}) | cards shown: {r['cards']} | highlights drawn: {r['painted']}"
          f" | KaTeX errors: {r['katexErrors']} | page errors: {errors or 'none'}")
    return r["bar"] is not None and not errors


def main():
    url = Path(sys.argv[1]).resolve().as_uri()
    with sync_playwright() as pw:
        ok = check(pw, "Chrome", lambda: pw.chromium.launch(channel="chrome"), url)
        ok &= check(pw, "WebKit", pw.webkit.launch, url)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
