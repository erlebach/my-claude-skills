#!/usr/bin/env python3
"""Render a GitHub discussion thread to Markdown.

Used by refresh_docs.sh to keep references/discussions/ in sync. Discussion
threads are where maintainers answer questions the wiki does not cover yet, so
they are worth capturing verbatim rather than summarized.

Usage: fetch_discussion.py <number> <output.md>   (requires an authenticated `gh`)
"""
import json
import subprocess
import sys

OWNER, REPO = "foundation50", "classroom50"

QUERY = """
query($owner:String!,$repo:String!,$num:Int!){
  repository(owner:$owner,name:$repo){
    discussion(number:$num){
      number title url createdAt category{name}
      author{login} body
      comments(first:100){nodes{
        author{login} createdAt body isAnswer
        replies(first:100){nodes{author{login} createdAt body}}
      }}
    }
  }
}
"""


def main() -> int:
    num, out = int(sys.argv[1]), sys.argv[2]
    raw = subprocess.run(
        ["gh", "api", "graphql", "-f", f"query={QUERY}",
         "-F", f"owner={OWNER}", "-F", f"repo={REPO}", "-F", f"num={num}"],
        capture_output=True, text=True, check=True,
    ).stdout
    d = json.loads(raw)["data"]["repository"]["discussion"]

    def who(node):
        return (node.get("author") or {}).get("login") or "ghost"

    lines = [
        f"# Discussion #{d['number']}: {d['title']}",
        "",
        f"Source: {d['url']}",
        f"Category: {d['category']['name']} · Opened by @{who(d)} on {d['createdAt'][:10]}",
        "",
        "> Verbatim capture of the thread. Comments are from the public; replies from",
        "> maintainers (@rongxin-liu, @dmalan, @brianyu28) carry the most authority.",
        "",
        "## Announcement (original post)",
        "",
        d["body"].strip(),
        "",
    ]
    for i, c in enumerate(d["comments"]["nodes"], 1):
        first = c["body"].strip().splitlines()[0][:70] if c["body"].strip() else ""
        lines += [
            "---", "",
            f"## Thread {i} — @{who(c)} ({c['createdAt'][:10]}){' [ANSWER]' if c.get('isAnswer') else ''}",
            "", f"<!-- {first} -->", "",
            c["body"].strip(), "",
        ]
        for r in c["replies"]["nodes"]:
            lines += [f"**Reply — @{who(r)} ({r['createdAt'][:10]}):**", "", r["body"].strip(), ""]

    with open(out, "w") as fh:
        fh.write("\n".join(lines).rstrip() + "\n")
    print(f"wrote {out} ({len(d['comments']['nodes'])} threads)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
