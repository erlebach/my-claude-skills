# write-architecture-report

A project-local Claude Code skill for reading a repository and writing about it in prose: architecture overviews, progress reports, seminar briefs, blog-style explainers, and paper-style system sections.

The default reader is a **scientist who understands data and databases but not dashboard, ETL, or software-architecture jargon**. Everything else is configuration.

## What it is for

Use it when someone needs to understand a codebase without reading it — a collaborator joining the project, an audience at a group meeting, a co-author who needs a methods section, or your future self six months from now. It writes about the system as a system: goals first, then the pieces that serve those goals, then how they connect.

It is not for API reference, installation instructions, or code walkthroughs.

## Folder structure

```
.claude/skills/write-architecture-report/
├── SKILL.md                              # entry point: options, boundaries, procedure, quality rules
├── README.md                             # this file
├── help.md                               # printed verbatim on a bare invocation
├── references/
│   ├── style-plain-scientist.md          # HOW to write: non-specialist scientific reader
│   ├── style-technical.md                # HOW to write: technical collaborators
│   ├── style-academic.md                 # HOW to write: formal, paper-like
│   ├── format-architecture-doc.md        # WHAT sections: reference document about a system
│   ├── format-paper.md                   # WHAT sections: paper-style write-up
│   ├── format-blog.md                    # WHAT sections: narrative explainer
│   └── format-seminar-brief.md           # WHAT sections: short talk-support document
└── assets/
    ├── template-architecture-doc.md      # markdown skeleton to fill in
    ├── template-paper.md
    ├── template-blog.md
    └── template-seminar-brief.md
```

Every referenced file is one level below `SKILL.md`. `SKILL.md` names each file explicitly at the point where it should be loaded, so nothing is loaded speculatively.

Generated output and cached reading live outside the analyzed repository, in one tree:

```
~/reports/
├── .evidence/                            # cached READING — never conclusions
│   └── <repo name>/                      # one live bundle per repo, not one per commit
│       ├── MANIFEST.md                   # what was read, at which digest, and why
│       ├── COMMANDS.md                   # commands, exit codes, verbatim output
│       └── <flattened copies of the files read>
└── <repo name>/                          # the reports themselves — output_root
    └── ARCHITECTURE_<format>_<style>_<timestamp>.md
```

**The commit is recorded inside `MANIFEST.md`, not in the path.** A commit-keyed directory fragments the cache without buying provenance: a new commit resolves to a directory that does not exist, so the bundle rebuilds whole even when every file in it is unchanged — committing one irrelevant file discards everything, while leaving that file untracked costs nothing. It also implies a precision a hash does not have, since one commit covers every dirty worktree sitting at it. The per-file digests are the validity check; the commit and the dirty flag are provenance, and both live in the manifest header where a reader sees them together.

`.evidence/` is a **sibling** of the report directories, not a child of one. That placement is deliberate: `output_root` is `~/reports/<repo name>/`, which the skill may never read from, and putting the cache beside it rather than inside it means that rule needs no exception. The leading dot also keeps `ls ~/reports` showing only report directories, and keeps an `ARCHITECTURE_*` glob from matching a cached copy of a repository's own `ARCHITECTURE.md`.

## Style vs format vs template

These are three independent choices, and confusing them is the most common way to get a document that reads wrong.

- **Style** is *how the sentences sound*: vocabulary, tone, sentence length, how much jargon is allowed, whether terms must be defined. A style file never says what sections to write.
- **Format** is *what the document contains and in what order*: required sections, optional sections, what the opening must accomplish, how limitations and next steps appear. A format file never says how to phrase anything.
- **Template** is *the concrete markdown skeleton* for one format: the actual headings, with a line or two of guidance under each. One template per format.

So `style=technical format=blog` is a narrative explainer written for engineers, and `style=plain-scientist format=paper` is a paper-shaped document a non-specialist can read. Both are sensible. The style files and format files are deliberately orthogonal.

## Options

| Option | Values | Default |
|---|---|---|
| `mode` | `light`, `guided` | `light` |
| `style` | `plain-scientist`, `technical`, `academic` | `plain-scientist` |
| `format` | `architecture-doc`, `paper`, `blog`, `seminar-brief` | `architecture-doc` |
| `sources` | `inline`, `section-end`, `appendix`, `none` | `section-end` |
| `evidence` | `observed-only`, `observed-plus-inferred` | `observed-only` |
| `status_labels` | `true`, `false` | `true` |
| `source_root` | path to read from | current repository root |
| `output_root` | path to write to | `~/reports/<name of source_root>/` |
| `evidence_cache` | `use`, `refresh`, `off` | `use` |
| `evidence_root` | where bundles live | `~/reports/.evidence/` |
| `filename` | output file name | `ARCHITECTURE_<format>_<style>_<timestamp>.md` |

A **bare invocation prints `help.md` verbatim and writes nothing.** To actually run with every default, pass the single word `run`.

The help text lives in its own file so that what a user sees is fixed and editable in one place, rather than re-composed on each run. It is deliberately generic — it shows the *shape* of the output path rather than a resolved absolute path and a live timestamp, because a constant file cannot carry values that change per repository and per minute. If you later want several levels of detail, add `help-<level>.md` beside it and route on an argument; the current single file is the short version.

- `mode=light` suits a strong model: read style + format, then write. `mode=guided` walks the format's sections one at a time and runs the quality list explicitly — more structure, more turns.
- `sources` controls where evidence appears: next to each claim (`inline`), in a short list closing each section (`section-end`), in one table at the end (`appendix`), or nowhere (`none`, for a standalone document).
- `evidence=observed-only` permits only what is visible in the source. `observed-plus-inferred` permits inference, marked as inference in the sentence making it.
- `status_labels=true` tags every component **Implemented / Partial / Planned / Inferred**.
- `evidence_cache` controls reuse of the reading, never of the writing: `use` revalidates and reuses a bundle, `refresh` rebuilds one, `off` reads the repository directly and caches nothing.
- `filename` encodes the format, the style, and a generation timestamp — `ARCHITECTURE_architecture-doc_plain-scientist_2026-08-01_10h19mEST.md`. A name you supply is decorated the same way, keeping your stem.

## Collecting reports later

Every report is self-describing, in two places that serve different purposes.

The **filename** carries format, style, and generation time, so a directory of reports can be sorted and filtered without opening anything: `ls ~/reports/*/ARCHITECTURE_blog_*` finds every blog-style explainer you have ever generated, across every repository.

The **frontmatter** carries the full set of resolved options plus `cmd`, `created`, `last_modified`, `source_root`, `source_commit`, and `source_dirty`. Every string value is double-quoted as a blanket rule — only the two booleans, `status_labels` and `source_dirty`, are bare — because quoting just the values that look risky means judging each one, and the judgement fails exactly where it matters.

`cmd` is the invocation that regenerates the document, with every option written out explicitly so it survives a change of defaults. Paste it to produce a fresh report from the same choices. It deliberately omits `filename`, which needs a new timestamp — pasting a recorded filename would collide with the file it came from. Every option appears even when left at its default, so two reports are always comparable field by field. `source_commit` is the short hash of the analyzed repository at generation time, which is what makes an old report interpretable rather than merely dated — you can check out that commit and see roughly what the document was describing. `source_dirty` says whether uncommitted changes were present, and it is there because the hash alone would otherwise be read as pinning the tree when it does not. When it is `true`, the commit locates the report and `evidence_bundle_sha256` is what actually identifies the evidence.

`last_modified` is seeded equal to `created` and is meant to be updated by hand if you edit a report afterwards. Nothing enforces it. Since the skill never overwrites, any file where the two differ has been touched by a person, which is the signal the field exists to carry.

`output_root` is deliberately not recorded: it describes where the file happens to sit, not what the document is, and it would go stale the moment you moved the file.

## Input and output boundaries

`source_root` is read-only input. `output_root` is write-only output, and by default it sits **outside** the analyzed repository, under `~/reports/<repo name>/`. That default is deliberate: a report written into the repository becomes input to the next run, appears in `git status`, and tends to get committed as though it were source.

The skill will not read, cite, or be influenced by anything already sitting in `output_root` — so you can generate five different reports from the same repository without report number four contaminating report number five. It also **never overwrites**: the timestamp makes collisions rare, and if a name is somehow taken it appends `-2`, `-3`, and tells you which it used. Nothing you have already generated can be destroyed by running it again.

If you deliberately point `output_root` inside `source_root`, you get one warning that future runs will see the report, and then it proceeds.

A third location, `evidence_root`, is read *and* written: it holds the cached reading described in the next section. It sits beside the report directories rather than inside one, precisely so that the "never read from `output_root`" rule stays absolute.

The skill's own files always stay in the current repository's `.claude/skills/`, regardless of where `output_root` points.

## The evidence bundle

Reading a repository well is expensive, and almost none of that expense depends on the format. The same thirty-odd files are read whether the output is a blog post or a paper; what changes is the writing. So the reading is cached and the writing never is.

What gets cached is not only the bytes but the **selection** — which files matter, and which slices of the large ones. Deciding that a thousand-line module is worth reading in two specific ranges is most of what the exploration phase produces, and it is the part a second run should not have to re-derive. `MANIFEST.md` records that judgement one row per file, with the real source path, a sha256, the line ranges read, and a one-line note on why the file was included.

What never gets cached: summaries, conclusions, status labels, draft prose, and previously generated reports. A bundle carrying interpretation would be a back-channel for one run's thinking into the next, which is the exact thing the context-independence rules exist to stop. Only raw excerpts and factual inclusion notes may be written into one.

**Validity is checked, not assumed.** The list of per-file digests *is* the check: every run re-hashes the files the manifest names, rewrites what changed, and drops what is gone. Because digests catch changed files but not added ones, a run whose commit differs from the manifest's — or whose worktree is dirty — also re-scouts the tree for anything new. A bundle is a floor, never a ceiling: if the current format needs a file the bundle lacks, that file is read from the repository and added, so the bundle converges on the union across formats.

**Command output is a separate class.** `COMMANDS.md` holds each command, its exit code, its verbatim output, and the tree state it was run at. Durations are never reused, since a wall-clock figure describes one execution rather than a state of the tree, and a cached result is never reported as fresh — the reading log distinguishes what was run now from what was read from the bundle and when.

The saving is mostly latency rather than tokens. A drafting run still reads the same content; what disappears is the serial exploration that found it — the tree walks, the searches, the files opened and discarded. On a small repository that is a modest win. On a large one, where deciding what to read *is* the problem, it is most of the cost.

Two practical consequences. `rm -rf ~/reports/.evidence/<repo name>` is the clean-room reset for checking that a report is genuinely re-derivable. And the bundle makes the strongest isolation cheap: a drafting subagent can be handed the bundle directory and no repository access at all, so its evidence is bounded by what it can reach rather than by what it was told to ignore.

## Context independence

A report must be derivable from its invocation alone — the same options against the same commit should give the same document in a fresh session as in a long one. `SKILL.md` therefore requires that the style file, format file, and template be re-read from disk on every run, that every cited fact come from a file opened or a command run during that run, and that hook-injected file excerpts, memory blocks, conversation history, and previously generated reports be excluded as evidence. Each run reports a log of what it read, so the claim is auditable rather than asserted.

A revalidated bundle counts as a read from disk; a stale one does not. The bundle is a byte copy whose every entry was re-hashed against its source during the run, so reading it is a verified disk read rather than a recollection — and two reports carrying the same `evidence_bundle_sha256` were provably written from the same evidence, which is what makes a style-versus-style comparison a comparison of the writing.

This is discipline, not a proof. A model that already carries context cannot demonstrate it ignored it. The structural guarantee is a fresh process: dispatch the drafting to a subagent that receives the resolved options and nothing else. The bundle makes that practical, since the subagent can be handed a bundle path in place of a repository. Use it when a report will be audited, published, or compared against another run.

## Example invocations

Print the options and their resolved defaults, and write nothing:

```
/write-architecture-report
```

Run with every default — plain-scientist architecture doc, section-end sources, written to `~/reports/<repo name>/ARCHITECTURE_architecture-doc_plain-scientist_<timestamp>.md`:

```
/write-architecture-report run
```

A blog-style explainer of this repository for a non-specialist, no file references at all:

```
/write-architecture-report format=blog style=plain-scientist sources=none filename=EXPLAINER.md
```

A ten-minute group-meeting brief, written to a chosen directory:

```
/write-architecture-report format=seminar-brief output_root=~/reports/ideal filename=SEMINAR.md
```

Analyze one repository, write into another:

```
/write-architecture-report source_root=~/src/2026/IDEAL-dashboard output_root=~/writing/ideal-notes filename=architecture-draft.md
```

A methods-section draft for co-authors, formal, with a source appendix and inference allowed:

```
/write-architecture-report format=paper style=academic sources=appendix evidence=observed-plus-inferred output_root=~/papers/ideal
```

A precise internal document for engineers, with inline path citations and step-by-step drafting:

```
/write-architecture-report style=technical sources=inline mode=guided
```

Several experiments from one corpus, each isolated from the others — the second and third reuse the first run's reading, so only the writing is redone:

```
/write-architecture-report source_root=. output_root=~/reports/exp1 format=blog filename=v1.md
/write-architecture-report source_root=. output_root=~/reports/exp2 format=seminar-brief filename=v2.md
```

Re-read the repository from scratch, ignoring any cached bundle — use after hand-editing a bundle, or when you want the reading itself re-derived:

```
/write-architecture-report evidence_cache=refresh
```

Use no cache at all, so the run depends on nothing on disk but the repository and the skill:

```
/write-architecture-report evidence_cache=off
```

## Maintaining the skill

Add a style by writing `references/style-<name>.md` covering the same headings as the existing style files, then adding the name to the options table in `SKILL.md` and to the routing list in the Procedure section. Add a format by writing both `references/format-<name>.md` and `assets/template-<name>.md`, then registering it in the same two places. Formats and styles stay independent — a new style should need no template, and a new format should need no style.
