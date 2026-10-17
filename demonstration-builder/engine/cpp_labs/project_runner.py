"""Build and run one target of a multi-file demo project with make.

A v2 demo example is a project folder (headers, .cpp files, a Makefile), not one
generated source. This module copies the folder's source files to a temporary
directory, runs ``make <target>`` there, runs ``./<target>``, and returns the
same RunResult that compiler_runner returns for a single file. Building in a
copy keeps built programs out of the repository and out of the cache key.

The result is cached through compile_cache. The key is the name and text of
every source file in the folder, the target, and the g++ version, so a change
to any header rebuilds every tab of that project.
"""

from __future__ import annotations

import re
import shutil
import subprocess
import tempfile
from pathlib import Path

from cpp_labs import compile_cache
from cpp_labs.compiler_runner import RunResult

LABS_DIR = Path(__file__).resolve().parent
# The files that are part of a project's source. Anything else in the folder
# (a built program, a .gitignore, an editor backup) is ignored.
SOURCE_RE = re.compile(r"^(Makefile|.+\.(cpp|hpp|h|md|txt))$")

BUILD_TIMEOUT = 120.0   # seconds; make may compile several files
RUN_TIMEOUT = 10.0      # seconds; a demo program finishes in well under one


def read_project(rel: str) -> dict[str, str]:
    """``{file name: text}`` for every source file in the folder, sorted by name.

    *rel* is relative to cpp_labs/; an absolute path is used as it is.
    """
    folder = LABS_DIR / rel
    return {p.name: p.read_text(encoding="utf-8")
            for p in sorted(folder.iterdir())
            if p.is_file() and SOURCE_RE.match(p.name)}


def key_text(files: dict[str, str]) -> str:
    """One string that changes when any file's name or text changes."""
    return "".join(f"{name}\0{text}\0" for name, text in files.items())


def _strip(text: str, build_dir: str) -> str:
    return text.replace(build_dir + "/", "")


def _build_and_run(files: dict[str, str], target: str) -> RunResult:
    tmp = tempfile.mkdtemp(prefix="cpp_proj_")
    cmd = f"make {target}"
    try:
        for name, text in files.items():
            Path(tmp, name).write_text(text, encoding="utf-8")
        try:
            # stderr into stdout: the reader sees make's lines and the
            # compiler's messages in the order they were printed.
            build = subprocess.run(["make", target], cwd=tmp, text=True,
                                   stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                   timeout=BUILD_TIMEOUT)
        except subprocess.TimeoutExpired:
            return RunResult("", "", None, "n/a", "compile-failed", cmd,
                             "Compilation timed out.")
        if build.returncode != 0:
            return RunResult("", "", build.returncode, "n/a", "compile-failed", cmd,
                             _strip(build.stdout, tmp))
        try:
            run = subprocess.run([f"./{target}"], cwd=tmp, text=True,
                                 capture_output=True, timeout=RUN_TIMEOUT)
        except subprocess.TimeoutExpired as exc:
            out = exc.stdout or ""
            if isinstance(out, bytes):
                out = out.decode("utf-8", errors="replace")
            return RunResult(_strip(out, tmp), "", None, "n/a", "execution-timeout",
                             cmd, "")
        status = "success" if run.returncode == 0 else "execution-error"
        return RunResult(_strip(run.stdout, tmp), _strip(run.stderr, tmp),
                         run.returncode, "n/a", status, cmd, "")
    finally:
        shutil.rmtree(tmp, ignore_errors=True)


def make_and_run(rel: str, target: str) -> RunResult:
    """Build *target* of the project at *rel* with make, run it, and cache the result."""
    files = read_project(rel)
    source = key_text(files)
    flags = [f"__make__={target}"]
    result = compile_cache.lookup(source, flags, "make")
    if result is None:
        result = _build_and_run(files, target)
        compile_cache.store(source, flags, "make", result)
    return result
