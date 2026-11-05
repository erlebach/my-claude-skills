#!/usr/bin/env python3
"""Add (or update, or remove) a personal notes layer in a standalone HTML file.

    add_notes.py page.html            # add the layer, or replace an older copy of it
    add_notes.py page.html --remove   # take the layer out again (the notes file is kept)
    add_notes.py page.html --banner "Notes: Chrome only"
    add_notes.py --all FOLDER           # update every page in FOLDER and below that has the layer
    add_notes.py --all FOLDER --check   # only list the out-of-date pages

The layer consists of three marked blocks: in <head>, a key guard and a <script> tag that
loads <stem>.notes.js; a banner at the top of <body>, and the notes code before </body>.
Re-running replaces the marked blocks, so it is safe after the HTML is regenerated.
The notes file is created empty if missing and never overwritten.
"""
import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import quote

ASSET = Path(__file__).resolve().parent.parent / "assets" / "notes-layer.html"
DEFAULT_BANNER = ("<strong>Add notes via Chrome only!</strong> Hover over a paragraph and click "
                  "<b>+</b>. Safari and Firefox show the notes but cannot save them.")
PARTS = ("head", "banner", "layer")


def mark(part, body):
    return f"<!-- html-notes:{part}:begin -->\n{body}\n<!-- html-notes:{part}:end -->\n"


def strip(html):
    for part in PARTS:
        html = re.sub(rf"<!-- html-notes:{part}:begin -->.*?<!-- html-notes:{part}:end -->\n?",
                      "", html, flags=re.S)
    return html


def render(html, page, banner):
    """The page's HTML with the current notes layer. banner None keeps the page's banner (a new page gets the default)."""
    notes = page.with_name(page.stem + ".notes.js")
    had = "<!-- html-notes:" in html
    if banner is None:
        m = re.search(r'<!-- html-notes:banner:begin -->\n<div class="wmn-banner">(.*?)</div>\n<!-- html-notes:banner:end -->', html, flags=re.S)
        banner = m.group(1) if m else ("" if had else DEFAULT_BANNER)
    html = strip(html)
    if not had and 'class="wmn-banner"' in html:
        sys.exit(f"{page}: has an unmarked notes layer from before this script; remove it by hand first.")
    # a notes file is linked only here: a hand-written or copied tag would make two pages share one notes file
    html, stray = re.subn(r'<script\b[^>]*\bsrc="[^"]*\.notes\.js"[^>]*>\s*</script>\n?', "", html, flags=re.I)
    if stray:
        print(f"{page}: {stray} hand-written notes script tag(s), dropped from the updated page")
    head_end = re.search(r"</head>", html, flags=re.I)
    body_ends = list(re.finditer(r"</body>", html, flags=re.I))
    if not head_end or not body_ends:
        sys.exit(f"{page}: no </head> or </body> tag; is this a complete HTML document?")
    layer = (ASSET.read_text(encoding="utf-8")
             .replace("__NOTES_FILE__", notes.name)
             .replace("__HTML_FILE__", page.name))
    # the key guard is registered here, before the page's own scripts, so it sees every key first
    guard = ("<script>['keydown','keypress','keyup'].forEach(function(t){window.addEventListener(t,"
             "function(e){if(window.wmnGuard)window.wmnGuard(e);},true);});</script>")
    head = guard + f'\n<script src="{quote(notes.name)}"></script>'
    i = head_end.start()
    html = html[:i] + mark("head", head) + html[i:]
    if banner:
        m = re.search(r"<body[^>]*>\n?", html, flags=re.I)
        html = html[:m.end()] + mark("banner", f'<div class="wmn-banner">{banner}</div>') + html[m.end():]
    i = list(re.finditer(r"</body>", html, flags=re.I))[-1].start()
    return html[:i] + mark("layer", layer.rstrip("\n")) + html[i:]


def ensure_notes(page):
    notes = page.with_name(page.stem + ".notes.js")
    if notes.exists():
        return f"kept existing {notes}"
    notes.write_text(f"// Personal notes for {page.name}. Written by the page; edit with care.\n"
                     + 'window.NOTES = ' + json.dumps({"version": 1, "updated": "", "notes": []}) + ";\n", encoding="utf-8")
    return f"created empty {notes}"


def update_all(folder, check):
    """Every page under folder that already has the layer gets the current code. Other pages, and bak and backup folders, are left alone."""
    counts = {"current": 0, "stale": 0}
    for page in sorted(folder.rglob("*.html")):
        if any(p == "bak" or p.startswith((".", "backup")) or p == "node_modules" for p in page.relative_to(folder).parts[:-1]):
            continue
        try:
            html = page.read_text(encoding="utf-8")
        except (UnicodeDecodeError, OSError):
            continue
        if "<!-- html-notes:" not in html:
            continue
        new = render(html, page, None)
        if new == html:
            counts["current"] += 1
            continue
        counts["stale"] += 1
        print(f"{'out of date' if check else 'updated'}: {page}")
        if not check:
            page.write_text(new, encoding="utf-8")
            msg = ensure_notes(page)
            if msg.startswith("created"):
                print(f"  {msg}")
    verb = "out of date" if check else "updated"
    print(f"{counts['stale']} {verb}, {counts['current']} current, under {folder}")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path, nargs="?")
    ap.add_argument("--remove", action="store_true", help="remove the notes layer")
    ap.add_argument("--banner", default=None, help="banner HTML ('' for no banner); default: keep the page's banner")
    ap.add_argument("--all", type=Path, metavar="FOLDER", help="update every page in FOLDER (and below) that already has the layer")
    ap.add_argument("--check", action="store_true", help="with --all: only list the out-of-date pages")
    a = ap.parse_args()
    if a.all:
        return update_all(a.all, a.check)
    if not a.html:
        ap.error("give a page, or --all FOLDER")

    page = a.html
    html = page.read_text(encoding="utf-8")
    had = "<!-- html-notes:" in html
    if a.remove:
        page.write_text(strip(html), encoding="utf-8")
        print(f"notes layer removed from {page}")
        return
    new = render(html, page, a.banner)
    if new == html:
        print(f"notes layer already current in {page}")
    else:
        page.write_text(new, encoding="utf-8")
        print(f"notes layer {'updated in' if had else 'added to'} {page}")
    print(ensure_notes(page))


if __name__ == "__main__":
    main()
