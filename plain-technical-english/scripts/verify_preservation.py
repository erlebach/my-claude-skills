#!/usr/bin/env python3
"""Check that a rewrite of a Markdown file keeps everything that must not change.

Usage:
    verify_preservation.py SOURCE.md REWRITE.md [--allow-key KEY ...]

Compares the two files and prints one line per finding:

    CODE detail

Codes:
    CODEBLOCK   a fenced code block of the source is missing or changed in the rewrite
    INLINE      an inline code span of the source is missing in the rewrite
    LINK        a link target or URL of the source is missing in the rewrite
    SHORTCODE   a Hugo shortcode occurs a different number of times
    NUMBER      a number of the source (with its unit) is missing in the rewrite
    QUOTE       a block-quote paragraph of the source is missing or changed
    FRONTMATTER a front-matter key is missing or has a different value
    COMMENT     an HTML comment of the source is missing (a warning only)

Text is compared after collapsing white space, so joining wrapped lines is not a change.
Block-quote markers (`> `) and the indent of a fence nested under a list item are removed
before code blocks and quotes are compared.

Exit status: 1 if any finding other than COMMENT, else 0.
"""
import argparse
import re
import sys
from collections import Counter

FENCE_RE = re.compile(r"^ *```")
NUM_RE = re.compile(r"(?<![\w.\-])\d+(?:[.,]\d+)?(?:\s?(?:%|ms|µs|us|ns|s|KB|MB|GB|×|x))?(?![\w])")


def norm(s):
    """Collapse all white space to single spaces."""
    return " ".join(s.split())


def split_front_matter(text):
    """Return (front-matter dict, body lines). Only simple 'key: value' lines are read."""
    lines = text.split("\n")
    fm = {}
    if lines and lines[0] == "---":
        for j in range(1, len(lines)):
            if lines[j] == "---":
                key = None
                for ln in lines[1:j]:
                    m = re.match(r"^([A-Za-z_][\w-]*):\s?(.*)$", ln)
                    if m:
                        key = m.group(1)
                        fm[key] = m.group(2).strip()
                    elif key:
                        fm[key] += " " + ln.strip()
                return fm, lines[j + 1:]
    return fm, lines


def parse(text):
    """Split a Markdown file into the parts that a rewrite must keep."""
    fm, lines = split_front_matter(text)
    blocks, prose, quotes, comments = [], [], [], []
    cur_block = None
    fence_indent = 0
    cur_quote = []
    in_comment = False
    comment_buf = []
    for raw in lines:
        quoted = raw.startswith(">")
        line = re.sub(r"^> ?", "", raw) if quoted else raw
        if in_comment or (cur_block is None and raw.lstrip().startswith("<!--")):
            comment_buf.append(raw)
            in_comment = "-->" not in raw
            if not in_comment:
                comments.append(norm(" ".join(comment_buf)))
                comment_buf = []
            continue
        if FENCE_RE.match(line):
            if cur_block is None:
                cur_block = []
                fence_indent = len(line) - len(line.lstrip(" "))
            else:
                blocks.append("\n".join(x.rstrip() for x in cur_block))
                cur_block = None
            continue
        if cur_block is not None:
            # a block nested under a list item is indented; compare it without that indent
            cut = min(fence_indent, len(line) - len(line.lstrip(" ")))
            cur_block.append(line[cut:])
            continue
        if quoted:
            if line.strip():
                cur_quote.append(line)
            elif cur_quote:
                quotes.append(norm(" ".join(cur_quote)))
                cur_quote = []
            continue
        if cur_quote:
            quotes.append(norm(" ".join(cur_quote)))
            cur_quote = []
        prose.append(line)
    if cur_quote:
        quotes.append(norm(" ".join(cur_quote)))
    return fm, blocks, "\n".join(prose), quotes, comments


def inline_spans(text):
    """Return the set of inline code spans."""
    return {norm(m) for m in re.findall(r"`([^`\n]+)`", text)}


def links(text):
    """Return the set of link targets and bare URLs."""
    found = set(re.findall(r"\]\(([^)\s]+)", text))
    found |= set(re.findall(r"https?://[^\s)>\]]+", text))
    return found


def shortcodes(text):
    """Return a count of each Hugo shortcode."""
    return Counter(norm(m) for m in re.findall(r"\{\{[<%].*?[>%]\}\}", text))


def numbers(text):
    """Return the set of numbers in prose, without code spans and list-item numbers."""
    t = re.sub(r"`[^`\n]*`", " ", text)
    t = re.sub(r"\]\([^)]*\)", "]", t)
    t = re.sub(r"\{\{[<%].*?[>%]\}\}", " ", t)
    t = re.sub(r"(?m)^\s*\d+\.\s", " ", t)
    return {norm(m) for m in NUM_RE.findall(t)}


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("source")
    ap.add_argument("rewrite")
    ap.add_argument("--allow-key", action="append", default=["draft"],
                    help="front-matter key the rewrite may add or change (default: draft)")
    args = ap.parse_args()
    s_fm, s_blocks, s_prose, s_quotes, s_comments = parse(open(args.source, encoding="utf-8").read())
    r_fm, r_blocks, r_prose, r_quotes, r_comments = parse(open(args.rewrite, encoding="utf-8").read())
    findings = []

    missing_blocks = Counter(s_blocks) - Counter(r_blocks)
    for b, k in missing_blocks.items():
        first = next((ln for ln in b.split("\n") if ln.strip()), "(empty block)")
        findings.append(("CODEBLOCK", f"{k}x missing or changed, starts: {first.strip()[:70]}"))

    s_all = s_prose + "\n" + "\n".join(s_quotes)
    r_all = r_prose + "\n" + "\n".join(r_quotes)
    for x in sorted(inline_spans(s_all) - inline_spans(r_all)):
        findings.append(("INLINE", f"`{x}`"))
    for x in sorted(links(s_all) - links(r_all)):
        findings.append(("LINK", x))
    sc_s, sc_r = shortcodes(s_all), shortcodes(r_all)
    for x in sorted(set(sc_s) | set(sc_r)):
        if sc_s[x] != sc_r[x]:
            findings.append(("SHORTCODE", f"{x}: source {sc_s[x]}, rewrite {sc_r[x]}"))
    for x in sorted(numbers(s_prose) - numbers(r_all)):
        findings.append(("NUMBER", x))
    missing_quotes = Counter(s_quotes) - Counter(r_quotes)
    for q, k in missing_quotes.items():
        findings.append(("QUOTE", f"missing or changed: {q[:80]}"))
    for key, val in s_fm.items():
        if key in args.allow_key:
            continue
        if key not in r_fm:
            findings.append(("FRONTMATTER", f"key '{key}' missing"))
        elif norm(r_fm[key]) != norm(val):
            findings.append(("FRONTMATTER", f"key '{key}' changed"))
    for c in s_comments:
        if c not in r_comments:
            findings.append(("COMMENT", f"missing: {c[:80]}"))

    for code, detail in findings:
        print(f"{code} {detail}")
    if not findings:
        print("OK: code blocks, inline code, links, shortcodes, numbers, quotes and front matter preserved")
    sys.exit(1 if any(c != "COMMENT" for c, _ in findings) else 0)


if __name__ == "__main__":
    main()
