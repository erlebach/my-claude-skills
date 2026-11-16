#!/usr/bin/env python3
"""Search and read the Cloudflare developer docs (developers.cloudflare.com) as Markdown.

The site publishes machine-readable indexes: /llms.txt lists every product, /<product>/llms.txt
lists that product's pages, and /api/llms.txt lists the REST API reference. Every page is
available as Markdown at <page>/index.md. This script fetches those, caches them for a day,
and strips the page chrome so only the content is printed.

    cfdocs.py products [WORD ...]          products whose name/summary match (all words), with their slug
    cfdocs.py index PRODUCT [WORD ...]     pages of one product (e.g. workers, d1, pages), filtered
    cfdocs.py search WORD [WORD ...]       search the page titles/summaries of the common deploy products
        [--in workers,pages,d1]            ... or of the products given
    cfdocs.py api WORD [WORD ...]          REST API reference entries (resources and methods), filtered
    cfdocs.py page URL_OR_PATH [--grep RE] [--max N]
                                           one page as Markdown; a path like /workers/static-assets/ works.
                                           --grep prints only sections whose heading or text matches.
    cfdocs.py refresh                      empty the cache

Matching is case-insensitive; every WORD must occur in the entry. Standard library only.
"""

from __future__ import annotations

import os
import re
import sys
import time
import urllib.request
from pathlib import Path

BASE = "https://developers.cloudflare.com"
CACHE = Path(os.environ.get("CFDOCS_CACHE", Path.home() / ".cache" / "cfdocs"))
TTL = 24 * 3600
# The products most deployment questions touch; `search` scans these unless --in is given.
DEPLOY = ["workers", "pages", "d1", "cloudflare-one", "fundamentals", "dns", "ssl", "r2", "kv", "rules", "cache", "turnstile"]


def fetch(url: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    key = CACHE / re.sub(r"[^A-Za-z0-9._-]+", "_", url.removeprefix(BASE))[:200]
    if key.exists() and time.time() - key.stat().st_mtime < TTL:
        return key.read_text()
    req = urllib.request.Request(url, headers={"Accept": "text/markdown, text/plain", "User-Agent": "cfdocs-skill/1"})
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            text = r.read().decode("utf-8", "replace")
    except Exception as e:  # noqa: BLE001 - report any network/HTTP failure the same way
        if key.exists():
            print(f"[cfdocs: {url} failed ({e}); using cached copy]", file=sys.stderr)
            return key.read_text()
        sys.exit(f"cfdocs: cannot fetch {url}: {e}")
    key.write_text(text)
    return text


def md_url(u: str) -> str:
    """Any docs URL or path -> its Markdown URL."""
    u = u.strip()
    if u.startswith("http"):
        u = re.sub(r"^https?://developers\.cloudflare\.com", "", u)
    if not u.startswith("/"):
        u = "/" + u
    u, _, frag = u.partition("#")
    if u.endswith(("llms.txt", ".md")):
        return BASE + u
    return BASE + u.rstrip("/") + "/index.md"


def entries(text: str):
    """Markdown list links: (title, url, summary). Relative URLs are made absolute."""
    for m in re.finditer(r"^\s*- \[([^\]]+)\]\(([^)]+)\)(?::\s*(.*))?$", text, re.M):
        title, url, summ = m.group(1), m.group(2), (m.group(3) or "").strip()
        yield title, (BASE + url if url.startswith("/") else url), summ


def product_entries(product: str, depth: int = 2):
    """A product's pages, following the nested llms.txt indexes some products use (Cloudflare One's
    access-controls/llms.txt, for one); the index links themselves are listed too."""
    url = f"{BASE}/{product.strip('/')}/llms.txt"
    seen = set()

    def walk(u, d):
        if u in seen:
            return
        seen.add(u)
        for t, link, s in entries(fetch(u)):
            yield t, link, s
            if link.endswith("/llms.txt") and link.startswith(f"{BASE}/{product.strip('/').split('/')[0]}/") and d > 0:
                yield from walk(link, d - 1)

    yield from walk(url, depth)


def matches(words, *fields) -> bool:
    hay = " ".join(fields).lower()
    return all(w.lower() in hay for w in words)


def show(rows, limit=60):
    rows = list(rows)
    for t, u, s in rows[:limit]:
        print(f"- {t}\n  {u}" + (f"\n  {s}" if s else ""))
    if len(rows) > limit:
        print(f"... {len(rows) - limit} more; add words to narrow it")
    if not rows:
        print("(no match; try fewer or other words)")


def cmd_products(words):
    rows = []
    for t, u, s in entries(fetch(BASE + "/llms.txt")):
        slug = u.removeprefix(BASE + "/").removesuffix("/llms.txt")
        if matches(words, t, s, slug):
            rows.append((f"{t}  [{slug}]", u, s))
    show(rows, 200)


def cmd_index(product, words):
    rows = entries(fetch(BASE + "/api/llms.txt")) if product == "api" else product_entries(product)
    show([e for e in rows if matches(words, e[0], e[1], e[2])], 80)


def cmd_search(words, products):
    rows = []
    for p in products:
        for t, u, s in product_entries(p):
            if matches(words, t, u, s):
                rows.append((f"[{p}] {t}", u, s))
    show(rows, 60)


def api_methods(resource_url: str):
    """The methods listed on an API resource page: (title, 'VERB /path', url)."""
    md = fetch(resource_url)
    for m in re.finditer(r"^#{4,6} \[([^\]]+)\]\(([^)]+)\)\s*\n\s*\n?\s*(GET|POST|PUT|PATCH|DELETE)\s*(/\S+)", md, re.M):
        yield m.group(1), f"{m.group(3)} {m.group(4).replace(chr(92), '')}", m.group(2)


def cmd_api(words):
    """Resources whose path matches the leading words; their methods filtered by the remaining words.
    api/llms.txt lists resources only, so methods come from each resource's own page."""
    res = api_resources()
    for k in range(len(words), 0, -1):
        hit = [r for r in res if matches(words[:k], r[0], r[1])]
        if hit:
            break
    else:
        print("(no API resource matches; try the product name, e.g. 'd1', 'workers scripts', 'pages projects', 'zero_trust access')")
        return
    rest = words[k:]
    if len(hit) > 12 and not rest:
        show(hit, 40)
        print("(many resources; add words to see their methods)")
        return
    shown, seen = 0, set()
    for name, url, _ in hit[:12]:
        ms = [m for m in api_methods(url) if matches(rest, m[0], m[1]) and m[2] not in seen]
        seen.update(m[2] for m in ms)
        if not ms and rest:
            continue
        print(f"## {name}  ({url.removesuffix('index.md')})")
        for t, vp, u in ms:
            print(f"- {t}: {vp}\n  {u}")
        shown += 1
    if not shown:
        print(f"(resources match {' '.join(words[:k])!r} but no method matches {' '.join(rest)!r})")
        show(hit, 20)
    print("\nA method page: cfdocs.py page <its URL>   (add --grep 'Body|Parameters' to skip the response models)")


def api_resources():
    # api/llms.txt nests resources; carry the parent headings so "d1 database" matches "D1 > Database".
    rows, ctx = [], []
    for line in fetch(BASE + "/api/llms.txt").splitlines():
        h = re.match(r"^#{3,}\s*\[([^\]]+)\]\(([^)]+)\)", line)
        e = re.match(r"^(\s*)- \[([^\]]+)\]\(([^)]+)\)(?::\s*(.*))?", line)
        if h:
            ctx = [h.group(1)]
            rows.append((h.group(1), BASE + h.group(2), ""))
            continue
        if e:
            depth = len(e.group(1)) // 2 + 1
            ctx = ctx[:depth] + [e.group(2)]
            rows.append((" > ".join(ctx), BASE + e.group(3) if e.group(3).startswith("/") else e.group(3), e.group(4) or ""))
    return rows


CHROME = [
    r"^\[Skip to content\]\(#[^)]*\)\s*$",
    r"^> (Documentation Index|Fetch the complete documentation index|Use this file to discover).*$",
    r"^(Copy Markdown|Copy page)\s*$",
    r"^Open in \*\*Claude\*\*.*$",
    r"^\*\*Copy Markdown\*\*.*$",
    r"^\[Link to this property\]\(.*\)\s*$",
    r"^(Was this helpful\?|YesNo)\s*$",
]


def clean(md: str) -> str:
    md = re.sub(r"\A---\n.*?\n---\n", "", md, flags=re.S)
    md = re.split(r"(?m)^## On this page\s*$", md)[0]  # the footer: page outline, logo, JSON-LD  # front matter (title/description kept below in the H1)
    lines = [l for l in md.splitlines() if not any(re.match(p, l) for p in CHROME)]
    md = "\n".join(lines)
    md = re.sub(r'<a href="[^"]*">Link to this property</a>', "", md)  # API reference anchors
    md = re.sub(r"</?(details|summary)>", "", md)
    md = re.sub(r"Last updated ([^|]+)\|.*", r"(Last updated \1)", md)
    md = re.sub(r"\n{3,}", "\n\n", md)
    return md.strip() + "\n"


def cmd_page(target, grep=None, maxchars=40000):
    url = md_url(target)
    md = clean(fetch(url))
    if grep:
        rx = re.compile(grep, re.I)
        parts = re.split(r"(?m)^(?=#{1,6} )", md)
        keep = [p for p in parts if rx.search(p)]
        md = "\n".join(keep) if keep else f"(no section matches /{grep}/; showing the start)\n\n" + md[:4000]
    print(f"Source: {url.removesuffix('index.md')}\n")
    if len(md) > maxchars:
        print(md[:maxchars] + f"\n\n[... truncated at {maxchars:,} of {len(md):,} characters; use --grep or --max]")
    else:
        print(md)


def main(argv):
    if not argv or argv[0] in ("-h", "--help"):
        print(__doc__)
        return
    cmd, rest = argv[0], argv[1:]
    if cmd == "products":
        cmd_products(rest)
    elif cmd == "index" and rest:
        cmd_index(rest[0], rest[1:])
    elif cmd == "search" and rest:
        prods = DEPLOY
        if "--in" in rest:
            i = rest.index("--in")
            prods, rest = rest[i + 1].split(","), rest[:i] + rest[i + 2:]
        cmd_search(rest, prods)
    elif cmd == "api" and rest:
        cmd_api(rest)
    elif cmd == "page" and rest:
        grep = maxc = None
        if "--grep" in rest:
            i = rest.index("--grep"); grep = rest[i + 1]; rest = rest[:i] + rest[i + 2:]
        if "--max" in rest:
            i = rest.index("--max"); maxc = int(rest[i + 1]); rest = rest[:i] + rest[i + 2:]
        cmd_page(rest[0], grep, maxc or 40000)
    elif cmd == "refresh":
        for f in CACHE.glob("*"):
            f.unlink()
        print(f"emptied {CACHE}")
    else:
        print(__doc__)
        sys.exit(2)


if __name__ == "__main__":
    main(sys.argv[1:])
