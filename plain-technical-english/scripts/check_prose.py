#!/usr/bin/env python3
"""Check Markdown prose against the plain-technical-english rules.

Reads one or more Markdown files and prints one line per finding:

    FILE:LINE: CODE message

Codes:
    WRAP      a text line continues the paragraph or list item on the line above (hard wrap)
    LISTGAP   a list starts with no blank line before it
    INDENT    a list marker is indented by a number of spaces that is not a multiple of 4
    LONG      a sentence is longer than the limit (20 words in a list item, 25 elsewhere)
    PARA      a paragraph has more than 6 sentences
    INTENS    an intensifier that adds no information (exactly, genuinely, very, ...)
    PASSIVE   a possible passive verb ("is run", "were made"); a hint, not a rule
    REQWORD   with --spec: lowercase must/should/may, which reads as an unclear requirement

Skipped: YAML front matter, fenced code, tables, headings, HTML comments, and block quotes
(quotations and example texts stay as written). Use --quotes to check block quotes too.

Exit status: 1 if any Markdown fault (WRAP, LISTGAP, INDENT) is found, else 0. Prose findings
are prompts to look again and do not change the exit status.
"""
import argparse
import re
import sys

LIST_RE = re.compile(r"^( *)([-*+]|\d+\.) ")
INTENSIFIERS = ["exactly", "genuinely", "precisely", "really", "very", "simply", "just",
                "clearly", "obviously", "basically"]
INTENS_RE = re.compile(r"\b(" + "|".join(INTENSIFIERS) + r")\b", re.I)
PASSIVE_RE = re.compile(r"\b(is|are|was|were|be|been|being)\s+(\w+ed|built|made|done|run|given|shown|written|taken|kept|found|seen)\b", re.I)
REQ_RE = re.compile(r"\b(must|should|may)\b")
SENT_SPLIT_RE = re.compile(r"(?<=[.!?])[\"')\]*]*\s+(?=[A-Z`*\"(\[0-9])")


def plain_text(s):
    """Return the line with code spans and link targets removed, so they do not count as words."""
    s = re.sub(r"`[^`]*`", "CODE", s)
    s = re.sub(r"\]\([^)]*\)", "]", s)
    s = re.sub(r"\{\{<[^>]*>\}\}", "X", s)
    return s


def sentences(text):
    """Split a paragraph into sentences (approximate)."""
    return [x for x in SENT_SPLIT_RE.split(text.strip()) if x.strip()]


def check(path, spec, quotes):
    """Check one file and return a list of (line number, code, message) findings."""
    lines = open(path, encoding="utf-8").read().split("\n")
    out = []
    fence = comment = False
    start = 0
    if lines and lines[0] == "---":
        for j in range(1, len(lines)):
            if lines[j] == "---":
                start = j + 1
                break
    prev = None      # kind of the previous line: 'text', 'item', 'blank', or None for anything else
    in_list = False
    para = []        # (line number, text) of the current paragraph or list item
    is_item = False

    def flush():
        if not para:
            return
        n0 = para[0][0]
        text = plain_text(" ".join(t for _, t in para))
        sents = sentences(text)
        limit = 20 if is_item else 25
        for s in sents:
            words = len(s.split())
            if words > limit:
                out.append((n0, "LONG", f"{words} words (limit {limit}): {s[:60]}..."))
        if not is_item and len(sents) > 6:
            out.append((n0, "PARA", f"{len(sents)} sentences in one paragraph (limit 6)"))
        for m in INTENS_RE.finditer(text):
            out.append((n0, "INTENS", f"'{m.group(1)}'"))
        for m in PASSIVE_RE.finditer(text):
            out.append((n0, "PASSIVE", f"possible passive: '{m.group(0)}'"))
        if spec:
            for m in REQ_RE.finditer(text):
                out.append((n0, "REQWORD", f"lowercase '{m.group(1)}': use MUST/SHOULD/MAY or plain wording"))
        para.clear()

    for i in range(start, len(lines)):
        n = i + 1
        raw = lines[i]
        if comment or raw.lstrip().startswith("<!--"):
            comment = "-->" not in raw
            flush(); prev = None
            continue
        quoted = raw.startswith(">")
        if quoted and not quotes:
            flush(); prev = None; in_list = False
            continue
        line = re.sub(r"^> ?", "", raw) if quoted else raw
        if re.match(r"^ *```", line):
            fence = not fence
            flush(); prev = None
            continue
        if fence:
            continue
        s = line.strip()
        if s == "":
            flush(); prev = "blank"
            continue
        if s.startswith(("#", "|", "<")) or re.fullmatch(r"-{3,}|\*{3,}", s):
            flush(); prev = None; in_list = False
            continue
        m = LIST_RE.match(line)
        if m:
            flush()
            ind = len(m.group(1))
            if ind % 4:
                out.append((n, "INDENT", f"list marker at {ind} spaces (use a multiple of 4)"))
            if not in_list and prev not in ("blank", None):
                out.append((n, "LISTGAP", "no blank line before this list"))
            in_list = True
            is_item = True
            para.append((n, line[m.end():]))
            prev = "item"
            continue
        if prev in ("text", "item"):
            out.append((n, "WRAP", "line continues the text above; join it into one line"))
            para.append((n, s))
            continue
        flush()
        if not line.startswith(" "):
            in_list = False
        is_item = False
        para.append((n, s))
        prev = "text"
    flush()
    return sorted(out)


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("files", nargs="+", help="Markdown files to check")
    ap.add_argument("--spec", action="store_true", help="the file is a specification or rubric: flag lowercase must/should/may")
    ap.add_argument("--quotes", action="store_true", help="also check text inside block quotes")
    args = ap.parse_args()
    fault = False
    for f in args.files:
        for n, code, msg in check(f, args.spec, args.quotes):
            print(f"{f}:{n}: {code} {msg}")
            fault |= code in ("WRAP", "LISTGAP", "INDENT")
    sys.exit(1 if fault else 0)


if __name__ == "__main__":
    main()
