---
name: git
description: Commit the current working-tree changes in logical groups, each with a conventional-commit message composed from the diff. Use when the user types "/git", says "commit my changes", "commit this work", or otherwise wants their uncommitted work committed. NOT for answering general git questions (rebase, history, how-to).
---

# /git — intelligent commit

Commit the working tree in logical groups, each with a conventional-commit
message written from the actual diff, then push the branch to its remote for
safety. Runs in the live session (reads the diff in context). Does not author
JOURNAL entries, does not create branches, does not force-push.

## Arguments

- (none) — group, commit, push, and report.
- `dry-run` — print the proposed groups + messages; commit nothing, push nothing.
- `no-push` (alias `local`) — commit as usual but skip the push step.
- `--help` (alias `help`) — print the **Help output** block below verbatim and
  stop. Run no git commands (works even outside a repo). Do nothing else.

## Procedure

0. **Help short-circuit.** If invoked with `--help` or `help`, print the **Help
   output** block verbatim and stop — run no git commands.

1. **Preflight.** Run `git rev-parse --is-inside-work-tree`. If it fails, tell
   the user this isn't a git repo and stop.

2. **Reuse check** (only if a `/git dry-run` plan from earlier this session is
   in context). Run `git status --porcelain`. If it is identical to what that
   dry-run saw, reuse the plan and skip to step 6. If it differs, say so and
   regenerate (continue to step 3).

3. **Inspect.** Run `git status --porcelain`, `git diff`, `git diff --cached`,
   and note untracked files. Read the diff content — this is how messages and
   groups are decided.

4. **Classify.** Separate real work from scratch/build artifacts and junk —
   generated/build dirs, caches, `*.tmp`, editor swap files, and project-
   specific scratch (e.g. `graphify-out/`, `file_tree*.txt`). Use judgment per
   repo; don't assume those names are scratch everywhere. Never stage artifacts
   unless they are clearly part of the change. Never stage files outside the
   repo root. Exclude secrets/credentials (`.env`, `*.pem`, key files, tokens) —
   flag them, never commit them.

5. **Group.** Partition the real changes into logical commits by relatedness
   (subsystem / feature / type). `JOURNAL.md` goes 
   in a single commit, committed LAST. If nothing real remains after
   classification, report that there is nothing to commit and stop — do not
   create an empty commit.

6. **Commit each group**, in order, JOURNAL, last. For each group:
   - Stage explicitly: `git add <exact pathspecs>`. Never `git add -u` / `git add .`.
   - Compose the message from the diff (see Message rules).
   - `git commit -m "<subject>" [-m "<body>"] -m "<trailer>"`.

7. **Push** (default; skip if invoked with `dry-run` or `no-push`, or if nothing
   was committed). Push the current branch to its remote so the work is backed
   up. Do NOT assume tracking is configured:
   - Current branch: `git rev-parse --abbrev-ref HEAD`.
   - If it already has an upstream (`git rev-parse --abbrev-ref
     --symbolic-full-name @{u}` succeeds), run `git push`.
   - If it has NO upstream, set tracking and push in one step:
     `git push -u <remote> <branch>` — `<remote>` is `origin` when present, else
     the sole entry from `git remote` (if there are multiple remotes and no
     `origin`, stop and ask which to use). This sets tracking on the existing
     branch; it does not create a branch.
   - "Push to the remote branch we are in": push the current branch to the
     same-named branch on the remote (the `-u <remote> <branch>` form above). Only
     target a different remote/branch if the user said so.
   - Never force-push, never create the remote. If there is no remote at all, or
     the push is rejected (e.g. non-fast-forward), report the exact git error and
     stop — the local commits are already safe; suggest the user pull/rebase.

8. **Report.** Print each `<short-sha> — <subject>`, then the push result
   (`<remote>/<branch>` updated to the new tip, or "skipped"/the push error).
   Explicitly list any files left uncommitted (scratch, secrets, out-of-repo).
   Never drop files silently.

## Message rules

- Conventional commit `type(scope): subject` — imperative mood, ≤72-char subject.
- Describe what the diff does, not a filename list. Add a short body only when
  the rationale is not obvious from the subject.
- The JOURNAL commit's subject is the newest `JOURNAL.md` header — the
  first `## ...` line — with the leading `## ` stripped.
- End every commit message with the `Co-Authored-By: Claude …` trailer your
  current session's instructions specify (it names the running model, e.g.
  `Co-Authored-By: Claude Opus 4.8 (1M context) <noreply@anthropic.com>`). If
  your session specifies none, use `Co-Authored-By: Claude <noreply@anthropic.com>`.

## Notes

- Commit on the current branch (matches the user's main-branch workflow); do
  not create branches.
- Push is on by default (for backup/protection), to the current branch's remote.
  Suppress it with `no-push`/`local`. Setting an upstream with `-u` is allowed
  (it tracks the existing branch); creating new branches or remotes is not.

## Help output

When invoked with `--help`/`help`, print this block verbatim and stop:

```
/git — commit the working tree in logical groups, then push for backup.

Usage:
  /git [argument]

Arguments:
  (none)        Group changes, commit each group (conventional-commit message
                from the diff), then push the current branch to its remote.
  dry-run       Show the proposed commit groups + messages only. Commits and
                pushes nothing.
  no-push       Commit as usual but skip the push (alias: local).
  --help        Show this help and stop (alias: help). Runs no git commands.

Behavior:
  - Commits on the CURRENT branch; never creates branches, never force-pushes.
  - JOURNAL.md is committed LAST.
  - Scratch/build artifacts are skipped; secrets (.env, keys, tokens) are never
    committed, only flagged.
  - Push targets the branch you are on. If it has no upstream, tracking is set
    via `git push -u <remote> <branch>` (origin, or the sole remote). No remote
    or a rejected push is reported, not forced.
```
