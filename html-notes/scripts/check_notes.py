#!/usr/bin/env python3
"""Load an HTML page with the notes layer in headless Chrome and WebKit (Safari's engine)
and report whether the layer started, how many notes loaded, and any page errors.
A page without the layer gets it first (add_notes.py), so this works on any page.

    check_notes.py page.html

Needs the playwright Python package and its browsers (pip install playwright;
playwright install webkit). Chrome is used through the installed Google Chrome.
"""
import subprocess
import sys
from pathlib import Path

try:
    from playwright.sync_api import sync_playwright
except ImportError:                      # run with a python that lacks playwright: retry with the one that has it
    import os
    PY = "/opt/miniconda3/bin/python"
    if os.path.exists(PY) and os.path.realpath(sys.executable) != os.path.realpath(PY):
        os.execv(PY, [PY, *sys.argv])
    sys.exit("check_notes.py needs the playwright package: pip install playwright")

JS = """() => ({
  bar: (document.querySelector('.wmn-bar') || {}).innerText || null,
  loaded: window.NOTES ? window.NOTES.notes.length : null,
  withText: window.NOTES ? window.NOTES.notes.filter(n => n.text).length : null,
  highlights: window.NOTES ? window.NOTES.notes.filter(n => n.hl).length : null,
  queued: window.NOTES ? window.NOTES.notes.filter(n => n.ai).length : null,
  resolved: window.NOTES ? window.NOTES.notes.filter(n => n.status).length : null,
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
          f" highlights: {r['highlights']}, for AI: {r['queued']}, resolved: {r['resolved']}) | cards shown: {r['cards']} | highlights drawn: {r['painted']}"
          f" | KaTeX errors: {r['katexErrors']} | page errors: {errors or 'none'}")
    return r["bar"] is not None and not errors


def main():
    page = Path(sys.argv[1]).resolve()
    if "<!-- html-notes:" not in page.read_text(encoding="utf-8", errors="replace"):
        print(f"{page.name} has no notes layer: adding it with add_notes.py", flush=True)
        r = subprocess.run([sys.executable, str(Path(__file__).with_name("add_notes.py")), str(page)])
        if r.returncode:
            sys.exit(r.returncode)
    url = page.as_uri()
    with sync_playwright() as pw:
        ok = check(pw, "Chrome", lambda: pw.chromium.launch(channel="chrome"), url)
        ok &= check(pw, "WebKit", pw.webkit.launch, url)
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
