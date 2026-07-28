# File caching for quiz generation

> **OBSOLETE — 2026-07-26. Do not implement.**
>
> This design solves the cost of *re-distilling* the corpus with a language model. That cost no longer exists: pack building moved to `cpp_labs/make_source_pack.py`, a deterministic script that rebuilds all 57 topics in under a second for zero tokens. There is nothing left to cache and no staleness to detect — every run rebuilds from source.
>
> Kept for the reasoning below, not as a plan.

Design note. **Not implemented yet** — this records the design so it is not lost.

## The problem

Authoring a quiz means reading the assigned demonstrations. For Quiz 1 (Modules 1–3) that is ten demos, 126 YAML files, ~280 KB, roughly **70,000 tokens** — paid again on every run, whether you ask for 7 items or 40.

The first fix was a **source pack**: distil the YAML once into one file of ~12–17k tokens and read that instead. It works, but its staleness check is all-or-nothing — edit one topic and the entire pack rebuilds, re-distilling 126 files to capture one change.

## The fix: hash each file, cache each topic

Cache at the level of the **individual topic**, keyed by the SHA-256 of its source file. A run then re-distils only what actually changed, and the pack becomes a concatenation of cached pieces rather than a thing that is built.

```
cpp_demos/quizzes/source_packs/
    index.json                        the hash index
    sections/
        array_pointer/
            off_the_end.md            one distilled topic
            arr_decays.md
            ...
        class_structure/
            cls_copy_ctor.md
            ...
    modules_1-3_<timestamp>.md        assembled pack (a view, not the cache)
```

`index.json`, one entry per source file:

```json
{
  "format_version": 3,
  "files": {
    "cpp_labs/array_pointer/topics/off_the_end.topic.yaml": {
      "sha256": "9f2c…",
      "section": "sections/array_pointer/off_the_end.md",
      "demo": "array_pointer",
      "topic_id": "off_the_end",
      "distilled_at": "2026-07-26_18h02mEST"
    }
  }
}
```

## The run

1. **Hash.** `shasum -a 256` every `*.topic.yaml` and `*.demo.yaml` under the demos this quiz covers.
2. **Diff against the index.** A file is *dirty* if its hash differs, or it has no entry at all. A file in the index that no longer exists on disk is *deleted*.
3. **Re-distil only the dirty ones** — one agent per dirty topic, all in parallel. Unchanged topics cost nothing: no agent, no tokens, no time.
4. **Update** the changed section files, write the new hashes, drop the sections of deleted files.
5. **Assemble** the pack by concatenating the section files for the covered demos. This is plain file I/O — no agents, no model calls.

Edit one topic and the next run spends one agent instead of ten. Change nothing and it spends none, and the pack assembles in under a second.

## Why SHA-256 rather than timestamps

Modification times lie in both directions. `git checkout` and `git stash` rewrite them on files whose contents never changed, forcing needless rebuilds; copying or restoring a file can carry an *older* mtime forward, so a real edit goes unnoticed. A content hash answers the only question that matters — *is this file different?* — and answers it the same way on every machine. Hashing 126 small files takes milliseconds.

## Two ways this can quietly go wrong

**The extraction rules are part of the cache key.** A section is a function of two things: the source file *and* the prompt that distilled it. Improve the extraction rules in `sourcepack.js` and every cached section is stale, though not one source file changed. That is what `format_version` is for: bump it whenever the extraction prompt changes, and treat a version mismatch as "everything is dirty." Forgetting this means improvements silently never reach the packs.

**Deletions are as important as edits.** A topic removed from a demo must have its section dropped from the index, or the pack keeps teaching material the course no longer assigns — and a quiz item sourced from it will look perfectly grounded. Step 2 must scan for index entries with no file on disk, not only for files whose hash moved.

## What this does not change

The pack remains a **reading convenience, never an authority**. Sections stay verbatim — `explanation` text and ✅/❌ code copied word for word, engine plumbing dropped — because a paraphrase would recreate the failure the whole arrangement exists to prevent: writing quiz items from a description instead of the material. Items still cite the original `.topic.yaml` path, and the source-check agent still opens those originals, so a cached section is never verified against itself.

## Cost, for the decision

| | Agents | Tokens |
|---|---:|---:|
| No cache (read every YAML) | 0 extra, but every run reads 126 files | ~70k per run |
| Pack, whole-file staleness | 10 on any change | ~15k per run |
| Hash index, per-topic | 1 per *changed topic* | ~15k per run |

The first build costs the same either way. The difference shows up on the second and every one after it — which is where all the actual work happens, since one quiz gets regenerated and re-reviewed several times before it goes on paper.
