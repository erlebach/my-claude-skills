# write-architecture-report

Reads a repository and writes it up in prose. Nothing was written — this is the help.

## Options

| Option | Values | Default |
|---|---|---|
| `mode` | `light`, `guided` | `light` |
| `style` | `plain-scientist`, `technical`, `academic` | `plain-scientist` |
| `format` | `architecture-doc`, `paper`, `blog`, `seminar-brief` | `architecture-doc` |
| `sources` | `inline`, `section-end`, `appendix`, `none` | `section-end` |
| `evidence` | `observed-only`, `observed-plus-inferred` | `observed-only` |
| `status_labels` | `true`, `false` | `true` |
| `source_root` | path | the current repository root |
| `output_root` | path | `~/reports/<name of source_root>/` |
| `evidence_cache` | `use`, `refresh`, `off` | `use` |
| `evidence_root` | path | `~/reports/.evidence/` |
| `filename` | name | `ARCHITECTURE_<format>_<style>_<timestamp>.md` |

A default run writes one file, to a path of this shape:

```
~/reports/<repo name>/ARCHITECTURE_architecture-doc_plain-scientist_<YYYY-MM-DD_HHhMMmEST>.md
```

The output directory is created if it does not exist. Nothing is ever overwritten — if the name is already taken, `-2` is appended, then `-3`.

## Examples

```
/write-architecture-report run
/write-architecture-report format=blog sources=none
/write-architecture-report format=seminar-brief style=technical
/write-architecture-report format=paper style=academic sources=appendix mode=guided
/write-architecture-report source_root=~/src/other-repo output_root=~/writing/notes
```

## Three things worth knowing before you pick

**Style and format are independent.** Style is how sentences sound; format is what sections exist. `style=plain-scientist format=paper` is a paper-shaped document a non-specialist can read, and `style=technical format=blog` is a narrative explainer for engineers. Both are sensible combinations.

**`mode=guided` costs more turns.** It walks the format's section list one at a time and runs the quality checklist explicitly. `light` uses judgment instead and is the right default for most runs.

**The timestamp is generation time**, so two runs an hour apart against different commits produce two files rather than a collision. Each file opens with a frontmatter block recording every resolved option plus `source_commit` and `source_dirty`, which together make an old report interpretable later — the hash alone would not, since uncommitted work is routine.

**Reading is cached; writing never is.** The first run over a repository saves what it read — file copies, digests, and which slices of the large files mattered — under `~/reports/.evidence/<repo name>/`, one live bundle per repository rather than one per commit. Later runs re-hash those files, reuse what still matches, pick up anything newly added, and skip the exploration. Committing does not discard the cache. Conclusions, drafts, and previous reports are never cached and never reused. Pass `evidence_cache=refresh` to re-read from scratch, or `evidence_cache=off` to use no cache at all.

Pass `run` to proceed with every default.
