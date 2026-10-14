#!/usr/bin/env python3
"""Locate the version-matched Streamlit docs bundled inside the project's own
Streamlit install.

Streamlit >= 1.57 ships an agent-facing documentation tree at
``<streamlit_pkg>/.agents/skills/developing-with-streamlit/``. Because it lives
inside the installed package, it always describes the exact version the project
runs -- which is the whole point: it cannot drift the way a model's training
data or a hand-copied cheat sheet does.

This script finds that tree using the *project's* interpreter, not whatever
Python happens to be on PATH. Those are frequently different, and using the
wrong one silently yields the wrong version's docs.

Usage:
    python find_bundled_docs.py [--project-dir PATH]

Exit codes:
    0  success; prints "<version>\t<abs path to SKILL.md>" on stdout
    1  Streamlit found but older than 1.57 (no bundled docs) -- prints version
    2  no interpreter with Streamlit installed was found
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path

# Order matters: project-local virtualenvs win over any ambient interpreter,
# because an activated-but-unrelated env is a common way to read the wrong docs.
CANDIDATE_RELATIVE_PYTHONS = (
    ".venv/bin/python",
    ".venv/Scripts/python.exe",
    "venv/bin/python",
    "venv/Scripts/python.exe",
    "env/bin/python",
    "../.venv/bin/python",
)

PROBE = (
    "import json,streamlit,pathlib;"
    "p=pathlib.Path(streamlit.__file__).parent/'.agents/skills/developing-with-streamlit/SKILL.md';"
    "print(json.dumps({'version':streamlit.__version__,'skill':str(p),'exists':p.is_file()}))"
)


def probe(python: str) -> dict | None:
    """Ask one interpreter where its Streamlit docs live. None if unusable."""
    try:
        out = subprocess.run(
            [python, "-c", PROBE],
            capture_output=True,
            text=True,
            timeout=30,
            check=False,
        )
    except (OSError, subprocess.SubprocessError):
        return None
    if out.returncode != 0:
        return None
    try:
        return json.loads(out.stdout.strip().splitlines()[-1])
    except (ValueError, IndexError):
        return None


def candidates(project_dir: Path) -> list[str]:
    found = [
        str(project_dir / rel)
        for rel in CANDIDATE_RELATIVE_PYTHONS
        if (project_dir / rel).is_file()
    ]
    # `uv run` resolves the project env even when no .venv directory is present.
    found.append("uv run --no-sync python")
    found.append(sys.executable)
    found.append("python3")
    return found


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--project-dir", default=".")
    args = ap.parse_args()
    project_dir = Path(args.project_dir).resolve()

    stale_version = None
    for cand in candidates(project_dir):
        parts = cand.split()
        info = probe(parts[0]) if len(parts) == 1 else None
        if info is None and len(parts) > 1:
            # Re-probe multi-word launchers such as `uv run --no-sync python`.
            try:
                out = subprocess.run(
                    [*parts, "-c", PROBE],
                    capture_output=True, text=True, timeout=60,
                    cwd=project_dir, check=False,
                )
                info = json.loads(out.stdout.strip().splitlines()[-1]) if out.returncode == 0 else None
            except (OSError, subprocess.SubprocessError, ValueError, IndexError):
                info = None
        if info is None:
            continue
        if info["exists"]:
            print(f"{info['version']}\t{info['skill']}")
            return 0
        stale_version = info["version"]

    if stale_version:
        print(
            f"ERROR: Streamlit {stale_version} is installed but predates bundled docs "
            "(added in 1.57). Either upgrade (`uv add -U streamlit`) or rely on "
            "references/ in this skill plus https://docs.streamlit.io .",
            file=sys.stderr,
        )
        return 1

    print(
        "ERROR: No interpreter with Streamlit installed was found under "
        f"{project_dir}. If this is not a Streamlit project, stop and say so.",
        file=sys.stderr,
    )
    return 2


if __name__ == "__main__":
    sys.exit(main())
