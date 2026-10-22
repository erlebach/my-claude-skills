#!/usr/bin/env bash
# Re-pull the bundled Classroom 50 documentation from upstream.
#
# The wiki is generated from wiki/ in the main repo (publish-wiki.yaml runs on
# every merge to main), so one shallow clone gets both the wiki text and the
# repo-side material (schemas, READMEs). Discussion threads come from the API.
#
# Usage: scripts/refresh_docs.sh
set -euo pipefail

SKILL_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
REF="$SKILL_DIR/references"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

command -v gh >/dev/null || { echo "need the gh CLI (brew install gh)" >&2; exit 1; }
gh auth status >/dev/null 2>&1 || { echo "run: gh auth login" >&2; exit 1; }

echo "==> cloning foundation50/classroom50"
git clone --depth 1 -q https://github.com/foundation50/classroom50.git "$TMP/repo"

echo "==> refreshing wiki pages"
rm -f "$REF"/wiki/*.md
for f in "$TMP"/repo/wiki/*.md; do
  # Absolutize image links so a cited screenshot is still clickable from here.
  sed 's#](images/#](https://github.com/foundation50/classroom50/blob/main/wiki/images/#g' \
    "$f" > "$REF/wiki/$(basename "$f")"
done

echo "==> refreshing schemas and repo READMEs"
rm -f "$REF"/schemas/*.json
cp "$TMP"/repo/schemas/*.json "$REF/schemas/"
cp "$TMP"/repo/README.md "$REF/repo-README.md"
cp "$TMP"/repo/cli/README.md "$REF/repo-cli-README.md"

echo "==> refreshing discussion threads"
for n in $(ls "$REF/discussions" | sed -n 's/^\([0-9][0-9]*\)-.*/\1/p'); do
  out=$(ls "$REF/discussions/$n"-*.md | head -1)
  python3 "$SKILL_DIR/scripts/fetch_discussion.py" "$n" "$out"
done

SHA=$(git -C "$TMP/repo" rev-parse --short HEAD)
DATE=$(git -C "$TMP/repo" log -1 --format=%cI)
cat > "$REF/SYNC.md" <<EOF
# Documentation sync state

| Field | Value |
| --- | --- |
| Last synced | $(date -u '+%Y-%m-%d %H:%M UTC') |
| Upstream commit | \`$SHA\` |
| Upstream commit date | $DATE |
| Wiki pages | $(ls "$REF"/wiki/*.md | wc -l | tr -d ' ') |
| Discussions captured | $(ls "$REF"/discussions/*.md | wc -l | tr -d ' ') |

Refresh with \`scripts/refresh_docs.sh\`. Classroom 50 shipped in July 2026 and is
under active development, so a sync older than a month or two is worth redoing
before trusting an answer about a recent feature, limitation, or roadmap item.
EOF

echo "==> done"
cat "$REF/SYNC.md"
