---
name: write-architecture-report
description: Use when asked to examine an existing repository and write it up in prose — an architecture overview, a progress or status report, a seminar brief, a blog-style explainer, or a paper-style methods section — especially for a reader who understands data and science but not dashboards, ETL, or software architecture jargon.
---

# Write Architecture Report

## Overview

Read a repository, work out what the system is *for* and how it is *put together*, and write that up in prose aimed at a stated audience. The output is a document about a system, not a directory listing and not a code walkthrough.

Three decisions are separate and must not be collapsed:

| Decision | Question it answers | Lives in |
|---|---|---|
| **style** | How is it written — vocabulary, tone, sentence length? | `references/style-*.md` |
| **format** | What sections does it have, in what order? | `references/format-*.md` |
| **template** | What concrete markdown skeleton do I fill in? | `assets/template-*.md` |

A plain-scientist blog post and a technical blog post share a format and differ in style. A technical architecture doc and a technical paper share a style and differ in format. Never assume one implies another.

## When to use

- "Explain what this repo does" / "write an architecture doc"
- Seminar or group-meeting preparation
- Onboarding a new collaborator
- A progress report on work so far
- Drafting a methods or system section for a paper

**Do not use** for API reference, docstrings, README installation instructions, or line-by-line code explanation. Those are documentation of code; this skill writes about a system.

## Options

**A bare invocation prints `help.md` and writes nothing.** If the user supplied no `key=value` options and no bare `run`, do not read the repository, do not resolve options, and do not draft. Read `help.md` from this skill's directory and print its contents verbatim as your reply, then stop. Do not summarize it, extend it, or substitute live values into it — the file is the help text, and keeping it fixed is the whole point, so that what a user sees can be edited in one place and never drifts from run to run. To run with every default, the user passes the single word `run`.

All options are `key=value`, given in the invocation. All have defaults.

| Option | Values | Default |
|---|---|---|
| `mode` | `light`, `guided` | `light` |
| `style` | `plain-scientist`, `technical`, `academic` | `plain-scientist` |
| `format` | `architecture-doc`, `paper`, `blog`, `seminar-brief` | `architecture-doc` |
| `sources` | `inline`, `section-end`, `appendix`, `none` | `section-end` |
| `evidence` | `observed-only`, `observed-plus-inferred` | `observed-only` |
| `status_labels` | `true`, `false` | `true` |
| `source_root` | path | current repository root |
| `output_root` | path | `~/reports/<basename of source_root>/` |
| `evidence_cache` | `use`, `refresh`, `off` | `use` |
| `evidence_root` | path | `~/reports/.evidence/` |
| `filename` | name | `ARCHITECTURE_<format>_<style>_<timestamp>.md` |

What the less obvious ones mean:

- **`mode=light`** — read the style and format files, then write. Use judgment; skip the checklists. Best default for strong models, sparse prompting, or cases where the user wants less scaffolding. **`mode=guided`** — additionally work through the format file's section list one at a time, drafting each against its stated purpose before moving on, and run the Quality Assurance list explicitly at the end. Best default when the user wants a more deterministic structure, tighter evidence discipline, or more conservative drafting. Guided produces more predictable structure and costs more turns.  
- **`sources`** — where the evidence for a claim appears. `inline` puts a file path or path:line next to the claim; `section-end` collects them under a short "Where this comes from" list closing each section; `appendix` maps every section to its sources in one table at the end; `none` produces a standalone document with no file references, for readers who will never see the repository.
- **`evidence=observed-only`** — state only what is present in the source and can be pointed at. **`observed-plus-inferred`** — inference is allowed but must be marked as inference in the sentence that makes it ("the naming suggests…", "this appears to be intended for…"). Never silently blend the two.
- **`status_labels=true`** — every component gets one of **Implemented**, **Partial**, **Planned**, or **Inferred**, and the document says what those labels mean the first time one is used. Use these meanings unless the user explicitly asks for a different scheme: **Implemented** = present in the repository and described by code, configuration, tests, or other direct evidence; **Partial** = present but incomplete, provisional, or only partly wired together; **Planned** = described in specs, notes, or comments but not yet implemented; **Inferred** = not explicitly stated, but a cautious conclusion drawn from naming, structure, or surrounding evidence.
- **`evidence_cache=use`** — reuse the evidence bundle for this `source_root` if one exists and revalidates, and build it if it does not. **`refresh`** — discard any existing bundle and read the repository afresh. **`off`** — read the repository directly and write no bundle, which is the pre-cache behaviour. See the **Evidence bundle** section for what is cached and what is deliberately not. Reach for `refresh` when you suspect a bundle was hand-edited, and for `off` when a single run must be provably independent of anything on disk but the repository itself.
- **`evidence_root`** — where bundles live, one subdirectory per analyzed repository. The default sits beside the per-repository report directories rather than inside one, so that the rule forbidding reads from `output_root` needs no exception carved into it.
- **`filename`** — the default is `ARCHITECTURE_<format>_<style>_<timestamp>.md`, so a default run produces `ARCHITECTURE_architecture-doc_plain-scientist_2026-08-01_10h19mEST.md`. The name encodes the choices that determine what the document *is*, so a directory of reports can be sorted, filtered, and counted without opening any of them. `ARCHITECTURE` stays constant even for `format=paper`, where it reads oddly, because a single `ARCHITECTURE_*` glob then finds everything this skill has ever produced.
- **The timestamp** is the moment the report is generated, formatted `YYYY-MM-DD_HHhMMmEST` — 24-hour, literal `EST` label, no seconds. Generation time is the right stamp because the report describes the repository as it stood when it was read; a report written an hour later against new commits is a different document, and the two must not collide. Read the clock from the system (`date "+%Y-%m-%d_%Hh%Mm"`) and append the literal `EST`; the label is a fixed naming convention, not a computed time zone, so do not substitute `EDT` or anything else.
- **A supplied `filename` is decorated the same way.** Keep the user's stem, insert format, style, and timestamp before the extension, and skip any part the name already carries: `EXPLAINER.md` with `format=blog style=technical` becomes `EXPLAINER_blog_technical_2026-08-01_10h19mEST.md`.

## Frontmatter

**Every generated report opens with a YAML frontmatter block.** It records what the document is and how it was made, so a directory of reports can later be collected, categorized, and audited by machine rather than by reading prose. Emit it verbatim in this field order, before the `# Title` line, with no blank line above it:

```yaml
---
title: "<the report's H1, without the leading #>"
generator: "write-architecture-report"
cmd: "/write-architecture-report format=architecture-doc style=plain-scientist mode=light sources=section-end evidence=observed-only status_labels=true evidence_cache=use source_root=/absolute/path/to/analyzed/repo"
created: "2026-08-01_10h19mEST"
last_modified: "2026-08-01_10h19mEST"
source_root: "/absolute/path/to/analyzed/repo"
source_commit: "0c26a22"
source_dirty: false
format: "architecture-doc"
style: "plain-scientist"
mode: "light"
sources: "section-end"
evidence: "observed-only"
status_labels: true
evidence_cache: "use"
evidence_bundle: "/Users/you/reports/.evidence/my-repo/"
evidence_bundle_sha256: "9f2c1a…"
---
```

Rules for the fields:

- **Double-quote every string value, without exception.** `status_labels` and `source_dirty` are booleans and stay bare; everything else is quoted even when it plainly needs no quoting. Quoting only the values that look dangerous means judging each one, and the judgement is wrong exactly when it matters: a title containing `: `, a path containing `#`, a value starting with `*` or `[`. A blanket rule is checkable by eye and cannot be misapplied. An unquoted title like `IDEAL Dashboard: architecture` makes the block unparseable and silently destroys the machine-readability the block exists for.
- **`cmd` is the invocation that reproduces this document**, written so it can be pasted straight back into the terminal. Give every option explicitly at its resolved value, including ones left at their defaults, so the command still means the same thing if a default changes later. Include `source_root`. Omit `filename`, which must be free to take a fresh timestamp — pasting a recorded filename would collide with the very file it came from — and omit `output_root`, for the reason below.
- **Every option goes in, resolved** — including the ones left at their defaults. A field that is absent because it was not overridden makes two reports incomparable; the point of the block is that every report answers the same questions.
- **`created`** is the generation timestamp, in the same `YYYY-MM-DD_HHhMMmEST` form the filename uses, and it never changes.
- **`last_modified`** is seeded equal to `created` and is meant to be updated by whoever edits the file afterwards. Nothing enforces this. Since the skill never overwrites a file, a run always writes the two fields equal — a later divergence means a human edited the report, which is exactly the signal the field exists to carry.
- **`source_root`** is the absolute path that was analyzed, and **`source_commit`** is the short commit hash of `source_root` at generation time when it is a git repository, obtained with `git -C <source_root> rev-parse --short HEAD`. Omit `source_commit` entirely if there is no repository or the command fails; do not write a placeholder. Together these say *what* was described and *at which moment*, which is what makes an old report interpretable instead of merely dated.
- **`source_dirty`** is whether `git -C <source_root> status --porcelain` produced any output at generation time, and it is a bare boolean like `status_labels`. Omit it wherever `source_commit` is omitted. It exists because a commit hash alone does not identify what was read: uncommitted work is routine, and a reader seeing only a hash will reasonably assume it pins the tree. When this is `true`, the commit locates the report in history but does not determine its evidence — `evidence_bundle_sha256` is what does that, and it is the field to compare when two reports must be shown to rest on the same reading.
- **`evidence_bundle`** is the absolute path of the bundle directory the report was drafted from, and **`evidence_bundle_sha256`** is the digest of that bundle's `MANIFEST.md` at the moment drafting began. Together they pin the exact evidence set, so two reports carrying the same digest were demonstrably written from the same reading of the same tree — which is what makes a style-versus-style comparison a comparison of the writing rather than of what happened to be read. Omit both lines entirely under `evidence_cache=off`; do not write a placeholder.
- **`evidence_cache` is recorded but `evidence_root` is not.** The first says how the evidence was obtained, which a later reader needs in order to interpret `evidence_bundle_sha256`. The second says where bundles happen to live, which is machine-local and goes stale the moment they are moved — the same reasoning that keeps `output_root` out.
- **`output_root` is deliberately absent.** It says where the file happens to sit, not anything about the document, and it goes stale the moment the file is moved.

## Input and output boundaries

Three locations, with different permissions.

**Source root** — `source_root`, defaulting to the current repository root. This is the *only* place facts about the system come from. Analysis, evidence, quotations, and citations all originate here, whether read directly or through a bundle copied from here.

**Output root** — `output_root`, defaulting to `~/reports/<basename of source_root>/`. Write-only, and deliberately **outside** the analyzed repository: a report written into the repository becomes input to the next run, shows up in `git status`, and invites being committed as though it were source. Defaulting outside keeps the corpus clean without the user having to think about it. Write the document to `output_root/filename`.

**Evidence root** — `evidence_root`, defaulting to `~/reports/.evidence/`. Read *and* write, holding one bundle directory per analyzed repository. It sits beside the per-repository report directories, never inside one, which is what lets rule 4 stand unamended: `output_root` is `~/reports/<basename>/`, and `~/reports/.evidence/` is not inside it. The leading dot keeps `ls ~/reports` showing only report directories and keeps an `ARCHITECTURE_*` glob from ever matching a cached copy of a repository's own `ARCHITECTURE.md`.

Rules:

1. Read and analyze only from `source_root`, whether directly or through a revalidated evidence bundle copied from it. No other location is a source of facts about the system.
2. Write the generated document to `output_root/filename`. Create `output_root` if it does not exist, including parent directories.
3. **Never overwrite an existing file.** Test whether the resolved path already exists — with a shell test (`ls`, `test -e`), never by reading it, since reading it would violate rule 4. If it exists, append `-2` to the stem, then `-3`, and so on until the name is free. Say which name was used when reporting back. Because nothing this skill writes ever lands on an existing file, the Write tool's read-before-overwrite requirement never arises; if you find yourself about to read the output file to satisfy that requirement, the filename logic above was skipped.
4. **Do not scan, read, summarize, cite, or infer anything from files already in `output_root`.** A previously generated report there is not evidence. Nothing in `output_root` may influence the content of the new report unless the user explicitly says to include it as an input document.
5. Treat `output_root` as an experiment destination — the user may generate several different reports from the same source corpus, and each must be written independently of the others.
6. If the resolved output path is inside `source_root` — which now happens only when the user asks for it explicitly — warn once: the report will be visible to future runs that analyze this repository, and they should confirm that is intended or choose an `output_root` outside it. Then proceed.
7. When analyzing `source_root`, skip generated reports (files matching the report filenames this skill produces, and any `ARCHITECTURE.md`-style summary at the root) unless the user explicitly names them as input documents.
8. The skill's own files always live in the **current repository's** `.claude/skills/write-architecture-report/`, even when `output_root` points elsewhere. Only generated reports go to `output_root`.
9. **The evidence bundle is read as evidence and never analyzed as part of the system.** It is a copy of `source_root`, not a component of it: nothing in it may be cited as a module, a decision, a limitation, or a gap, and the bundle directory must never appear in a repository map. The asymmetry is the whole point — rule 4 forbids reading `output_root` at all, whereas the bundle exists to be read.
10. **Assert that the resolved bundle path is not inside the resolved `output_root`.** With both at their defaults it cannot be, but a user who sets `output_root=~/reports` would otherwise place the cache inside the one directory the skill must not read from. Refuse and say so rather than proceeding: a rule with one silent exception is a rule nobody can rely on.
11. **Only raw excerpts enter a bundle.** File paths, digests, line ranges, verbatim content, command invocations and their verbatim output, and a one-line factual note on why each file was included. Never a summary, a conclusion, a status label, a draft sentence, or any prose about the system. A bundle that carries interpretation is a back-channel for one run's thinking into the next, which is the failure the Context independence section exists to prevent.

With every root left at its default, the report lands outside the analyzed repository, the bundle lands outside `output_root`, and neither rule 6's warning nor rule 10's refusal fires.

## Evidence bundle

Reading a repository well is expensive, and almost none of that expense is format-specific. The same thirty-odd files are read whether the output is a blog post or a paper; what changes is the writing. The bundle caches the *reading* — and, more valuably, the *selection*: which files matter, and which slices of the large ones. It never caches the writing.

### Layout

One directory per analyzed repository, and one only:

```
~/reports/.evidence/<basename of source_root>/
  MANIFEST.md          # what was read, from where, at which digest, and why
  COMMANDS.md          # commands run, their exit codes, and their verbatim output
  src_ideal_pipeline.py    # verbatim copies, path-flattened
  README.md
  ...
```

Copies are path-flattened (`/` to `_`) so the directory stays one level deep and every file is readable by name; `MANIFEST.md` carries the real path, which is what citations use.

**The commit is recorded in `MANIFEST.md`, never in the path.** Putting it in the path looks like provenance and is actually fragmentation: a new commit resolves to a directory that does not exist, so the bundle is rebuilt whole even when every file in it is byte-identical — committing one irrelevant file discards the entire cache, while leaving that same file untracked costs nothing. It also promises a precision it cannot deliver, since a commit hash does not distinguish the dirty worktrees that sit at it. The per-file digests are the validity check and need no help from the path; the commit and the dirty flag are provenance, and provenance belongs in the manifest where a reader can see both.

One live bundle per repository therefore accumulates across commits rather than forking at each one. The cost accepted is that an old bundle cannot be reconstructed after the tree moves on — but nothing reads an old bundle, and each report already pins its own evidence set through `evidence_bundle_sha256`. A repository with no git history needs no special case at all.

**A directory of copies rather than one concatenated file.** A single bundle for a repository of this size runs to thousands of lines, past the point where a file is read whole, so it would have to be sliced by offset — which means carrying a map of where each file begins, which is a filesystem rewritten inside a text file. Ordinary per-file copies are read the way any source file is read, and the map that matters is `MANIFEST.md`.

**Copies rather than pointers.** Pointers back into `source_root` would be lighter and would still record the selection, but they leave the bundle non-hermetic. Copies mean a drafting subagent can be given the bundle directory and no access to `source_root` at all, at which point "nothing came from anywhere else" is a property of what it could reach rather than a promise about what it chose.

### `MANIFEST.md`

A header naming what was read and when, then one row per file:

```markdown
# Evidence bundle — IDEAL-dashboard

built: "2026-08-01_12h19mEST"
source_root: "/Users/erlebach/src/2026/IDEAL-dashboard"
source_commit: "0c26a22"
worktree_dirty: true

| source path | sha256 | lines | slice | copied as | why included |
|---|---|---|---|---|---|
| src/ideal/pipeline.py | 3f9a… | 581 | whole | src_ideal_pipeline.py | orchestration, receipts, report writer |
| src/ideal/contract.py | 8c11… | 1004 | 1-140, 700-1004 | src_ideal_contract.py | validation entry points and disclosures |
```

The `slice` column is the expensive judgement, not the bytes. Deciding that a thousand-line module is worth reading in two specific ranges is most of what the exploration phase produces, and it is exactly what a second run should not have to re-derive.

### Validity

The list of per-file digests *is* the validity check. On `evidence_cache=use`, re-hash every file the manifest names and compare. Rewrite the entries that differ, drop the entries whose source file is gone, and leave the rest untouched. Re-hashing thirty files is cheap next to reading them.

Digests catch changed files but cannot catch *added* ones, and a bundle that silently caps coverage is worse than no bundle. So when `source_commit` differs from the manifest's, or when the worktree is dirty, additionally re-scout cheaply — list the tree, compare against the manifest's paths, and read anything new that the report would plausibly need. A bundle is a floor, never a ceiling. Both halves of that condition are reachable, which is the point of keeping the commit out of the path: a bundle built at one commit is revalidated and extended at the next, rather than abandoned for a fresh directory. Update the manifest header to the commit and dirty state this run observed once the re-scout is done.

**Extend rather than obey.** If the current `format` or `style` needs a file the bundle does not have — a `paper` about statistical method wants readers a `seminar-brief` never touched — read it from `source_root`, add it to the bundle, and rehash. The bundle then converges on the union across formats instead of being frozen at whatever the first invocation happened to want.

### Command output is a separate class

`COMMANDS.md` holds each command, its exit code, its verbatim output, and the `source_commit` plus dirty-state it was run at. It is cached under the same validity key, and two rules govern reuse. **Timings are never reused** — a duration describes one execution, not a tree, so a cited wall-clock number must come from a run made during this invocation or be omitted. And **a cached result may never be reported as fresh**: the reading log distinguishes what was run now from what was read from the bundle and when. Under `evidence_cache=refresh`, and whenever the validity check fails, re-run rather than reuse.

### The hazard

A stale or hand-edited bundle produces a report describing a repository state that never existed, and it will read as authoritative. Three defenses, none optional. Revalidate by digest on every run and rebuild what fails rather than warning and proceeding. Record `evidence_bundle_sha256` in the frontmatter so a reader can tell which snapshot a document describes. And when the validity check fails in a way that cannot be repaired file by file — a manifest that will not parse, copies that do not match their recorded digests — discard the bundle directory and rebuild it whole, rather than salvaging part of something whose integrity is in question.

## Context independence

**A report must be derivable from the invocation alone.** The same options against the same commit must produce the same document in a fresh session as after an hour of unrelated conversation. Every assertion traces to a file read, or a command run, during *this* invocation.

Re-read from disk on every run, without exception:

- The style file, the format file, and the template — even if this session wrote them, edited them, or printed them minutes ago. A copy in the conversation is not a copy on disk; the file may have been edited since, by the user or by a linter.
- Every source file the report relies on, either from `source_root` or from a **revalidated evidence bundle**.

**A revalidated bundle counts as a read from disk, and a stale one does not.** The bundle is a byte copy of `source_root` whose every entry has been re-hashed against the file it came from during this invocation, so reading it is a disk read of verified content rather than a recollection. That is a stronger position than reading the repository directly, not a weaker one: two reports carrying the same `evidence_bundle_sha256` were provably written from the same evidence, which is what makes them comparable. The strength rests entirely on the revalidation, so a bundle that fails its digest check is not evidence until it is rebuilt.

Never treat any of the following as evidence, because none of them was read from `source_root` by this run:

- **Conversation history.** Earlier turns, previous answers, facts established in discussion.
- **Hook-injected content.** `JOURNAL.md` excerpts, `SNAPSHOT.md` dumps, session-start context, or memory blocks pasted in by the harness. When one of those files is a legitimate source — and both of those are — open it from `source_root` and cite it. Do not quote the injected copy: it is routinely truncated, summarized, or elided, and it reflects the moment the hook fired rather than the moment you read it.
- **Recalled memory** of any kind, including `<MEM>` blocks.
- **A previously generated report**, whether it sits in `output_root`, in `source_root`, or only in this conversation's history. Rule 4 forbids reading one; having *written* one earlier in the session does not make its wording or its conclusions available.

Verification claims are held to the same standard. A test count, a commit hash, a build result, or a byte size must come from a command run during this invocation, or from `COMMANDS.md` in a bundle that revalidated — in which case the reading log says so and gives the time it was run. Citing a number seen earlier *in the conversation* remains the failure this section prevents, because the tree may have changed since it was seen and nothing re-checked it. Durations are never reused from a bundle, since a wall-clock figure describes one execution rather than a state of the tree.

**What this cannot guarantee.** A model already carrying context cannot prove it ignored that context. This section reduces the problem to re-derivation discipline; it does not eliminate it. The only structural guarantee is a fresh process — dispatching the draft to a subagent that receives the resolved options and nothing else. The bundle makes that dispatch practical: the subagent can be handed a bundle path instead of a repository, at which point its evidence is bounded by what it can reach rather than by what it was told to ignore. Prefer that whenever the report will be audited, published, or compared against another run.

## Procedure

0. **Bare invocation?** If the user gave no options and no `run`, print the contents of `help.md` verbatim and stop here. Do not read the repository and do not continue to step 1.
1. **Resolve options.** Fill in defaults, reading the clock once — the same stamp serves the filename, `created`, and `last_modified`. Read `source_commit` while you are at it, and note whether the worktree is dirty (`git -C <source_root> status --porcelain`), since the bundle's validity depends on both. Build the filename from format, style, and stamp. Check the boundary rules above: create `output_root`, pick a non-colliding name per rule 3, issue the rule-6 warning if it applies, and refuse per rule 10 if the bundle path would land inside `output_root`.
2. **Load the style file** for the chosen `style`:
   - `plain-scientist` → `references/style-plain-scientist.md`
   - `technical` → `references/style-technical.md`
   - `academic` → `references/style-academic.md`
3. **Load the format file** for the chosen `format`:
   - `architecture-doc` → `references/format-architecture-doc.md`
   - `paper` → `references/format-paper.md`
   - `blog` → `references/format-blog.md`
   - `seminar-brief` → `references/format-seminar-brief.md`

All style and format files are one level deep under `references/` and are loaded only when their option is selected. Do not recurse through additional reference layers. **Open both files from disk on this run**, even if their contents already appear earlier in the conversation, and treat what you read as the controlling guidance for wording and structure.

4. **Build or revalidate the evidence bundle**, unless `evidence_cache=off`. Resolve the bundle path to `evidence_root/<basename of source_root>/`. If it exists and `evidence_cache=use`, read `MANIFEST.md`, re-hash every file it names, rewrite the entries that changed, drop the entries whose source is gone, and re-scout for added files when the commit differs from the manifest's or the worktree is dirty. If it does not exist, or `evidence_cache=refresh`, or the manifest will not parse, build it whole from step 5's reading. Either way, `MANIFEST.md` and `COMMANDS.md` end the step describing exactly what this run has verified; take the digest of `MANIFEST.md` for the frontmatter.
5. **Understand the system before writing about it.** Start from goals: what problem does this repository solve, for whom, and what does a successful run of it produce? Then find the pieces that serve those goals and how data or control moves between them. Read entry points, configuration, and the top of the main modules; read tests to learn intended behaviour; read a project journal, snapshot, or changelog if one exists, for decisions and their reasons — **opening each from the revalidated bundle or from `source_root`, never relying on a session-start injection of the same file**. Anything the bundle lacks and this format needs is read from `source_root` and added to the bundle. Re-run any command whose output you intend to cite, unless a revalidated `COMMANDS.md` already holds it and the reading log will say when it was run; durations are always re-measured or omitted. Do not enumerate directories.
6. **Load the matching template from disk** when you begin drafting — again, not from a copy in the conversation:
   - `architecture-doc` → `assets/template-architecture-doc.md`
   - `paper` → `assets/template-paper.md`
   - `blog` → `assets/template-blog.md`
   - `seminar-brief` → `assets/template-seminar-brief.md`

   The template is a skeleton, not a form. Drop a heading whose section genuinely does not apply, and say why in one line if its absence is surprising.
7. **Draft** into the path resolved in step 1, opening with the frontmatter block specified above, then obeying the style file for wording, the format file for structure, and `sources` / `evidence` / `status_labels` for attribution and hedging. Cite the real `source_root` paths recorded in `MANIFEST.md`, never the flattened copy names — the bundle is how the file was read, not where it lives.
8. **Run the Quality Assurance list below.** In `mode=guided`, run it item by item and fix as you go. In `mode=light`, run it as a final read-through.
9. **Report back**: the full path written — including the timestamp, and the `-2` suffix if rule 3 added one — the resolved options, and anything you could not determine from the source. Include a **reading log** that separates three things: what was read or run **during this invocation**, what came from a **revalidated bundle** (with the bundle path, its digest, and when its entries were built), and what the bundle **gained** this run. That separation is the evidence for the Context independence rule; a log that blends cached and fresh readings claims a freshness the run does not have. If anything in the draft came from outside all three, say so explicitly and name it; an undisclosed dependency on session context is worse than a disclosed one. **End the reply with the `cmd` line in a fenced code block**, so the user can copy it without hunting through prose. It is the last thing in the turn, every time.

## Quality Assurance

Run this before declaring the document finished.

**Language**

- Plain words over impressive ones. *Bad:* "The orchestration layer facilitates the materialization of downstream artifacts." *Good:* "This step writes the tables that the rest of the pipeline reads."
- Define every technical term at first use, in the sentence that uses it. *Good:* "an ETL pipeline — code that extracts data from files, reshapes it, and loads it into tables."
- Ban hype: **robust, seamless, cutting-edge, powerful, leverage, blazing-fast, state-of-the-art, effortless, enterprise-grade**. Use one only if you immediately justify it with a measurement. *Bad:* "a robust validation layer." *Good:* "validation that fails the build on any of 12 specific error conditions, listed below."
- Sentences direct and moderately short. One idea per sentence. Prefer active voice and a named actor: "the loader writes…" over "it is written by…".
- Paragraphs hold one point, typically three to six sentences. If a paragraph turns a corner, start a new one.
- Use a list when something has parts, steps, or options. Use prose when something has a reason. Do not put reasoning in bullets.

**Accuracy**

- Every claim about behaviour is traceable to something in `source_root`. If you could not check it, do not assert it.
- Separate **implemented**, **planned**, and **inferred** in the text, not only in a label. Never write "the system does X" about code that does not exist yet.
- No overclaiming: no "fully automated" for a step with a manual trigger, no "handles all cases" without seeing the cases, no performance claim without a number and the conditions it was measured under.
- Numbers carry units and provenance. "523 tests pass" is a claim; say where you saw it.
- Under `evidence=observed-only`, cut any sentence you cannot point at. Under `observed-plus-inferred`, every inference is marked as one in its own sentence.

**Attribution and completeness**

- The frontmatter block is present, is the first thing in the file, and carries every resolved option plus `cmd`, `created`, `last_modified`, `source_root`, and — where the source is a git repository — `source_commit` and `source_dirty` together, never one without the other. Its `format` and `style` values match those encoded in the filename. `evidence_bundle` and `evidence_bundle_sha256` are present unless `evidence_cache=off`, in which case both are absent rather than empty.
- Every string value in the block is double-quoted; only `status_labels` and `source_dirty` are bare. Confirm the block parses — feed it to a YAML parser rather than eyeballing it.
- Source attribution matches the requested `sources` mode exactly — no inline paths in `sources=none`, no missing appendix table in `sources=appendix`.
- A **Glossary** exists whenever the document uses technical terms, and it defines every term the target audience is not assumed to know. In `plain-scientist` this is mandatory.
- Nothing in the document came from `output_root`.
- Every claim traces to a file opened or a command run **during this invocation, or to a bundle entry re-hashed during it**, and the style file, format file and template were read from disk on this run. Nothing rests on conversation history, a hook-injected excerpt of a file, a memory block, or a report generated earlier in the session. Any exception is disclosed in the report-back by name.
- **Every bundle entry the report leans on was revalidated this run**, and the entries that failed were rebuilt rather than warned about. No cited duration came from a cache.
- **Nothing interpretive was written into the bundle** — no summary, conclusion, status label, or draft prose. Re-read what this run added to `MANIFEST.md` and the copies, and confirm they are raw excerpts and factual inclusion notes only.
- **Citations name real `source_root` paths**, not the flattened copy names inside the bundle, and no bundle path appears in a repository map or component list.
- If `status_labels=true`, every component has a label and the labels are explained on first use.
- The opening tells the reader what the system is for before it tells them how it is built. If a reader stops after the first paragraph, they should still know what the project does.
