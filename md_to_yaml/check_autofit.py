#!/usr/bin/env python3
"""Per-slide autofit report for compiled decks — the build-time check autofitAll()
cannot do itself, because fit is decided by the browser's layout.

    python3 check_autofit.py deck.html [more.html ...]

Needs the `playwright` package with Chromium installed (`playwright install chromium`).
Columns: content = zoom applied to .slide-content-area (1.000 = untouched),
title = rendered title size in canvas px, FLOOR = content did not fit even at the
floor (split the slide), bounds = elements crossing the slide edge.
Exit status 1 if any slide hit the floor.
"""
import sys
from playwright.sync_api import sync_playwright

JS = r"""
() => {
  const rep = window.__mdToYamlAutofitReport();
  const bad = window.__mdToYamlAuditBounds();
  const slides = Array.from(document.querySelectorAll('#deck-app-root [role="group"]'));
  return slides.map((s, i) => {
    const t = s.querySelector('h2, h1'), hd = s.querySelector('.slide-heading-stack');
    const z = parseFloat(s.style.zoom || '1') * (hd ? parseFloat(hd.style.zoom || '1') : 1);
    return { slide: i + 1,
             layout: (s.className.match(/slide-([a-z0-9-]+)/) || [, '?'])[1],
             content: rep[i].content, floor: rep[i].floor, over: rep[i].over,
             title: t ? parseFloat(getComputedStyle(t).fontSize) * z : null,
             bounds: bad.filter(b => b.slide === i + 1).length };
  });
}
"""

def main(paths):
    floored = 0
    with sync_playwright() as p:
        browser = p.chromium.launch()
        page = browser.new_page(viewport={'width': 1280, 'height': 720})
        for path in paths:
            page.goto('file://' + path)
            page.wait_for_timeout(600)
            print(f"\n== {path}")
            print(f"{'sl':>3} {'layout':<12} {'content':>7} {'title':>6} {'bounds':>6}")
            for r in page.evaluate(JS):
                flag = f"  FLOOR (+{r['over']}%)" if r['floor'] else ''
                title = f"{r['title']:.0f}" if r['title'] is not None else '-'
                print(f"{r['slide']:>3} {r['layout']:<12} {r['content']:>7.3f} {title:>6} {r['bounds']:>6}{flag}")
                floored += r['floor']
        browser.close()
    return 1 if floored else 0

if __name__ == '__main__':
    sys.exit(main([p if p.startswith('/') else __import__('os').path.abspath(p) for p in sys.argv[1:]]))
