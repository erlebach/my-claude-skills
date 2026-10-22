---
name: classroom50
description: Authoritative offline copy of the Classroom 50 documentation (the Fifty Foundation's open-source GitHub Classroom alternative at classroom50.org) — the full wiki, JSON schemas, and maintainer answers from the discussion forum — for answering questions about it accurately and with citations. Use this skill whenever the user mentions Classroom 50, classroom50.org, `gh teacher`, `gh student`, or asks about setting up a classroom/roster/assignment, autograding student code with GitHub Actions, `autograder.py` or `tests.json`, assignment templates, service tokens, collecting scores, group assignments, or migrating from GitHub Classroom — even if they don't name the tool, and even when the question sounds simple enough to answer from memory. Classroom 50 is NOT GitHub Classroom and behaves differently in ways that make remembered answers wrong.
---

# Classroom 50 documentation

This skill carries a synced copy of everything Classroom 50 publishes: all 26 wiki
pages, the config JSON schemas, the repo READMEs, and the launch discussion thread
where maintainers answer questions the wiki doesn't cover. The point is to answer
from the actual documentation instead of from recall.

**Why this matters more than usual here.** Classroom 50 launched in July 2026, so
little about it is in any model's training data — but *GitHub Classroom*, a
different product with much of the same vocabulary, is. The two diverge on
architecture, permissions, and lifecycle. Answering "classroom", "roster",
"assignment", or "accept" from general knowledge produces confident, plausible,
wrong answers. Read the page.

## How to answer a question

1. **Route to a page** using the table below. If the routing isn't obvious, read
   `references/INDEX.md` (a section-level map of all 26 pages), or grep the corpus:
   `grep -ril "service token" references/`.
2. **Read the actual page** — the whole relevant section, not just the grep hit.
   These pages are dense and often qualify a rule two paragraphs later ("but not
   for group assignments", "unless the org is Enterprise").
3. **Answer, then cite** the wiki page and heading as a link, so the user can
   verify and go deeper:
   `[Which commits grade](https://github.com/foundation50/classroom50/wiki/Autograding-Basics#which-commits-grade)`.
   Anchors are the heading, lowercased, spaces to hyphens.
4. **Separate what's documented from what you're inferring.** If the docs answer
   it, say so. If you're reasoning from the architecture to a case the docs don't
   address, label it as inference. If nothing covers it, say that plainly and
   point to [Discussions](https://github.com/foundation50/classroom50/discussions)
   or [Issues](https://github.com/foundation50/classroom50/issues) — a clean "the
   docs don't say" is far more useful than a fabricated answer, because the user
   is going to act on it in a live course.

Answer at the length the question deserves. A "what's the repo naming scheme"
question wants one line and a link; "how do I set up autograding for a C++
assignment" wants the recipe walked through.

## Where things are

| The question is about | Read |
| --- | --- |
| What it is, why no server, why state looks stale, why students are admins | `wiki/How-Classroom-50-Works.md` |
| Org plan, GitHub Education, Team vs Enterprise, campus networks | `wiki/Prerequisites-and-GitHub-Education.md` |
| Fastest path from empty org to a graded assignment | `wiki/Quickstart.md` |
| Doing anything in the web app at classroom50.org | `wiki/Web-Teacher-Guide.md` |
| Doing anything from the terminal, teacher side | `wiki/CLI-Teacher-Guide.md` |
| Exact `gh teacher` command, flag, or subcommand | `wiki/gh-teacher.md` |
| Exact `gh student` command or flag | `wiki/gh-student.md` |
| Installing / updating / verifying the CLI extensions | `wiki/Installation.md` |
| TAs, co-teachers, the four roles, what staff can see | `wiki/Staff-TAs-and-Multiple-Teachers.md` |
| Due dates, closing, staging, end of term, reuse next term, org reset | `wiki/Course-Lifecycle-and-End-of-Term.md` |
| How grading works, which commits grade, reading results, feedback PRs | `wiki/Autograding-Basics.md` |
| Language-specific setup (Python, Java, C#, C/C++, Rust, own CI) | `wiki/Autograder-Recipes.md` |
| Writing `autograder.py`, the `result.json` contract, `runtime`, `allowed_files` | `wiki/Advanced-Autograding.md` |
| Actions minutes, what grading costs, spending caps, turning grading off | `wiki/Managing-Actions-Cost.md` |
| Template repos, starter code, structure, template gotchas | `wiki/Assignment-Templates.md` |
| Permissions, scopes, allowed domains, scaffolded workflows, secrets, REST calls | `wiki/GitHub-Integration.md` |
| What a student sees and does (web / CLI) | `wiki/Web-Student-Guide.md`, `wiki/CLI-Student-Guide.md` |
| A specific error message or something not working | `wiki/Troubleshooting.md` |
| "Can it do X?" / "Why can't it do X?" / roadmap | `wiki/Known-Limitations.md`, then `wiki/FAQ.md` |
| Terminology, repo naming scheme, GitHub Classroom equivalents | `wiki/Glossary.md` |
| Shape of a config file the tools read or write | `schemas/*.json` |
| Localization, OAuth-scope objections, training recordings, ISP blocking, reported bugs | `discussions/46-introducing-classroom-50.md` |
| Source layout, what lives in `cli/` / `web/` / `templates/` | `repo-README.md`, `repo-cli-README.md` |

Both guides for a given task (web and CLI) describe the same underlying
operations, so when the user hasn't said which they're using, either answer both
briefly or ask — the CLI guide is usually more precise about flags and edge cases,
the web guide about what's on screen.

## Facts worth holding while you read

These come up in most questions and explain behavior that otherwise reads as a
bug. They are summaries — cite the page, not this list.

- **GitHub is the backend.** There is no Classroom 50 server or database. The web
  app is a static GitHub Pages site; the CLI runs locally. Classrooms, rosters,
  assignments, and scores live in a private `classroom50` repo in the teacher's
  org, plus org/team membership and permissions. Almost every surprising behavior
  follows from this.
- **Nothing happens while you're signed out.** Interactive work runs as the
  signed-in teacher; background work (score collection, regrading) runs as GitHub
  Actions and only after a **service token** is provisioned. There are no
  webhooks and no notifications.
- **Views are as-of-read.** The web app reads GitHub on page load (org list cached
  10 min); CLI reads report the moment they run; scores refresh only when
  collection runs. "Stale" usually means "not re-read yet," not broken.
- **Students are admins of their own assignment repos** — a deliberate consequence
  of the permission model, not a misconfiguration.
- **Repos are named `<classroom>-<assignment>-<username>`**, and
  `<classroom>-<assignment>-group-<n>` for groups. The 100-char GitHub cap gives
  the classroom and assignment slugs a shared budget.
- **Enroll, unenroll, and remove are three different things.** Unenrolling a
  student does not delete their repository.
- **Group assignments are GitHub Teams**, with a teacher-committed snapshot in
  `teams.json`.
- **Email invites can't be resolved to accounts** — GitHub's API offers no
  email→user lookup, so invited-by-email students sit as pending roster rows until
  they accept and a sync fills in the account.
- **Students can't see scores in the app.** Results are published as a Release on
  the student's repo; cross-origin reads of Release assets are blocked. Send
  students to Releases or the feedback PR.
- **It's GPLv3, at github.com/foundation50/classroom50**, web app at
  classroom50.org, backed by the Fifty Foundation. Localization shipped after
  launch (Spanish among others).

## Keeping this current

`references/SYNC.md` records when the bundle was last pulled and from which
upstream commit. Classroom 50 is under active development, so for a question about
a recent feature, a limitation the user hopes has been lifted, or anything
roadmap-shaped, check that date. If it's stale — or the answer matters enough to
be sure — run `scripts/refresh_docs.sh` (needs `git` and an authenticated `gh`; it
re-pulls the wiki, schemas, READMEs, and every captured discussion, then rewrites
`SYNC.md`). Mention that you refreshed, so the user knows the answer is current.

To capture another discussion thread permanently:
`python3 scripts/fetch_discussion.py <number> references/discussions/<number>-<slug>.md`
— it'll then be kept current by every subsequent refresh.
