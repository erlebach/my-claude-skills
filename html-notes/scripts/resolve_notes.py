#!/usr/bin/env python3
"""Work through a page's notes as an AI: list the ones the reader queued "For AI", and record what
was done with each. Change the notes file only through this script: the page merges the file with
the browser's copy by note id and timestamp, and this script sets both correctly.

    resolve_notes.py page.html list               # the queued notes and strikes, each with its passage
    resolve_notes.py page.html list --all         # every note and highlight
    resolve_notes.py page.html queue all          # queue every open note (the reader said "all")
    resolve_notes.py page.html queue ID [ID ...]
    resolve_notes.py page.html mark ID fixed|answered|declined "what was changed, or the answer"   # adds the AI's turn
    resolve_notes.py page.html delete ID [ID ...] # only when the reader asks for it

page.html may also be the notes file itself (page.notes.js).
"""
import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

STATUSES = ("fixed", "answered", "declined")


def now():
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def notes_path(arg):
    p = Path(arg).resolve()
    return p if p.name.endswith(".notes.js") else p.with_name(p.stem + ".notes.js")


def load(path):
    if not path.exists():
        sys.exit(f"{path}: no notes file; the page has no notes yet")
    t = path.read_text(encoding="utf-8")
    i, j = t.find("{"), t.rfind("}")
    data = json.loads(t[i:j + 1]) if i >= 0 else {"version": 1, "updated": "", "notes": []}
    head = t.split("\n", 1)[0] if t.startswith("//") else f"// Personal notes for {path.name[:-9]}.html. Written by the page; edit with care."
    return data, head


def save(path, data, head):
    data["updated"] = now()
    path.write_text(head + "\nwindow.NOTES = " + json.dumps(data, indent=1, ensure_ascii=False) + ";\n", encoding="utf-8")


def find(data, nid):
    for n in data["notes"]:
        if n["id"] == nid:
            return n
    sys.exit(f"no note with id {nid}")


def turns(n):
    """The conversation, oldest first: the note, then the replies. Older notes keep AI replies in history."""
    t = [{"who": "me", "text": n["text"], "at": n.get("created")}] if n.get("text") else []
    if "thread" in n:
        return t + n["thread"]
    for h in n.get("history", []) + [n]:
        if h.get("resolution"):
            t.append({"who": "ai", "text": h["resolution"], "status": h.get("status"), "at": h.get("resolved")})
    return t


def show(n):
    kind = "strike" if n.get("strike") else ("highlight + note" if n.get("text") else "highlight") if n.get("hl") else "note"
    state = "FOR AI" if n.get("ai") else (n.get("status") or "open").upper()
    print(f"== {n['id']}  [{kind}, {state}]  near #{n.get('anchor') or '?'}")
    # the setting of the conversation, like a system prompt: where the note sits in the page
    print("   context (the setting for the whole conversation):")
    if n.get("sec"):
        print("     section: " + " > ".join(n["sec"]))
    if n.get("prev"):
        print(f"     before:  {n['prev']}")
    print(f"     PASSAGE: {n.get('txt') or n.get('fp', '')}")
    if n.get("strike"):
        print(f"     DELETE these words: \"{n['hl']['quote']}\"")
    elif n.get("hl"):
        print(f"     highlighted words: \"{n['hl']['quote']}\"")
    if n.get("next"):
        print(f"     after:   {n['next']}")
    T = turns(n)
    if T:
        print("   conversation, oldest first (answer the reader's last turn, in the light of the whole conversation):")
        for x in T:
            who = "reader" if x["who"] == "me" else f"AI ({x.get('status') or 'reply'})"
            print(f"     {who}: " + x["text"].replace("\n", "\n       "))
    print()


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("page")
    sub = ap.add_subparsers(dest="cmd", required=True)
    sub.add_parser("list").add_argument("--all", action="store_true")
    sub.add_parser("queue").add_argument("ids", nargs="+")
    m = sub.add_parser("mark")
    m.add_argument("id")
    m.add_argument("status", choices=STATUSES)
    m.add_argument("resolution")
    sub.add_parser("delete").add_argument("ids", nargs="+")
    a = ap.parse_args()

    path = notes_path(a.page)
    data, head = load(path)
    if a.cmd == "list":
        items = data["notes"] if a.all else [n for n in data["notes"] if n.get("ai")]
        print(f"{len(items)} {'items' if a.all else 'items queued for AI'} in {path.name}\n")
        for n in items:
            show(n)
        if not items and not a.all:
            print("Nothing is queued. The reader queues notes with the 'For AI' button, or say 'queue all'.")
        return
    t = now()
    if a.cmd == "queue":
        items = [n for n in data["notes"] if not n.get("ai") and not n.get("status")] if a.ids == ["all"] else [find(data, i) for i in a.ids]
        for n in items:
            n["ai"] = True
            n.pop("status", None)
            n.pop("reviewed", None)
            n["updated"] = t
        print(f"queued {len(items)}")
    elif a.cmd == "mark":
        n = find(data, a.id)
        if "thread" not in n:
            n["thread"] = turns(n)[1 if n.get("text") else 0:]
            n.pop("history", None)
        n["thread"].append({"who": "ai", "text": a.resolution.strip(), "status": a.status, "at": t})
        # a new answer reopens the note, so the reader sees it
        for k in ("ai", "was", "reviewed", "collapsed"):
            n.pop(k, None)
        n.update(status=a.status, resolution=a.resolution.strip(), resolved=t, updated=t)
        print(f"{a.id}: {a.status}")
    elif a.cmd == "delete":
        for i in a.ids:
            data["notes"].remove(find(data, i))
            data.setdefault("deleted", []).append(i)
        print(f"deleted {len(a.ids)}")
    save(path, data, head)


if __name__ == "__main__":
    main()
