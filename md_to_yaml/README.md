# md_to_yaml skill (bundled compiler)

This directory contains:

- **`SKILL.md`** — agent instructions for generating YAML slide decks and compiling HTML.
- **`compiler/`** and **`schema/`** — copied from the `md_to_yaml` project (YAML → HTML pipeline). Re-copy those trees when updating the compiler.
- **`requirements.txt`** — Python dependencies for the compiler.
- **`compile.sh`** — runs `python3 -m compiler` with `PYTHONPATH` set to this folder.
- **`layout_rules_llm.md`**, **`equations.md`**, **`creating_good_presentations.md`** — authoring guides.

## Quick compile

```bash
cd /path/to/md_to_yaml   # this skill folder
pip install -r requirements.txt
./compile.sh /path/to/deck.yaml /path/to/out.html --embed-images
```

