#!/usr/bin/env python3
"""Add (or update, or remove) a personal notes layer in a standalone HTML file.

    add_notes.py page.html            # add the layer, or replace an older copy of it
    add_notes.py page.html --remove   # take the layer out again (the notes file is kept)
    add_notes.py page.html --banner "Notes: Chrome only"

The layer consists of three marked blocks: a <script> tag in <head> that loads
<stem>.notes.js, a banner at the top of <body>, and the notes code before </body>.
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


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("html", type=Path)
    ap.add_argument("--remove", action="store_true", help="remove the notes layer")
    ap.add_argument("--banner", default=DEFAULT_BANNER, help="banner HTML ('' for no banner)")
    a = ap.parse_args()

    page = a.html
    html = page.read_text(encoding="utf-8")
    notes = page.with_name(page.stem + ".notes.js")
    had = "<!-- html-notes:" in html
    html = strip(html)
    if not had and 'class="wmn-banner"' in html:
        sys.exit(f"{page}: has an unmarked notes layer from before this script; remove it by hand first.")

    if not a.remove:
        head_end = re.search(r"</head>", html, flags=re.I)
        body_ends = list(re.finditer(r"</body>", html, flags=re.I))
        if not head_end or not body_ends:
            sys.exit(f"{page}: no </head> or </body> tag; is this a complete HTML document?")
        layer = (ASSET.read_text(encoding="utf-8")
                 .replace("__NOTES_FILE__", notes.name)
                 .replace("__HTML_FILE__", page.name))
        head = f'<script src="{quote(notes.name)}"></script>'
        i = head_end.start()
        html = html[:i] + mark("head", head) + html[i:]
        if a.banner:
            m = re.search(r"<body[^>]*>\n?", html, flags=re.I)
            html = html[:m.end()] + mark("banner", f'<div class="wmn-banner">{a.banner}</div>') + html[m.end():]
        i = list(re.finditer(r"</body>", html, flags=re.I))[-1].start()
        html = html[:i] + mark("layer", layer.rstrip("\n")) + html[i:]

    page.write_text(html, encoding="utf-8")
    action = "removed from" if a.remove else ("updated in" if had else "added to")
    print(f"notes layer {action} {page}")
    if not a.remove and not notes.exists():
        notes.write_text(f"// Personal notes for {page.name}. Written by the page; edit with care.\n"
                         f"window.NOTES = {json.dumps({'version': 1, 'updated': '', 'notes': []})};\n",
                         encoding="utf-8")
        print(f"created empty {notes}")
    elif notes.exists():
        print(f"kept existing {notes}")


if __name__ == "__main__":
    main()
