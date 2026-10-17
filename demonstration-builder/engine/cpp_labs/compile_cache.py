"""Remember what g++ already told us, so an unchanged program is not rebuilt.

Every page bakes real compiler and program output, and a page is always built
whole: change one word of prose and every program on that page is compiled and
run again. That is slow (a full 37-page build takes about two minutes) and, more
importantly, it is not repeatable -- the programs print memory addresses, and
the operating system puts them somewhere different on every run. Two builds of
identical source therefore produce different pages, which is what made comparing
a fresh build against the published one such a chore.

This module keys a compile+run result on everything that can change its output:
the exact source text handed to the compiler, the flags, the language standard,
and the compiler's own version banner. Anything else being equal, the recorded
answer is reused and the page comes out byte-for-byte identical to last time.

Three results are never recorded: a run that hit the clock, a compile that hit
the clock, and a sanitizer report that stops before its SUMMARY line. All three
are accidents of how busy the machine was, and freezing one would make a page
permanently wrong (see test_timeout_never_baked.py and
test_partial_report_never_baked.py).

Off switches:
    CPP_LABS_CACHE=off      ignore and do not write the cache (always compile)
    rm -rf .compile_cache   start again from nothing
"""

from __future__ import annotations

import hashlib
import json
import os
import subprocess
from pathlib import Path
from typing import Any

from .compiler_runner import RunResult

CACHE_DIR = Path(__file__).resolve().parents[1] / ".compile_cache"

_FIELDS = ("stdout", "stderr", "exit_code", "memory_bytes", "status",
           "command", "compiler_stderr", "ptrdata")

_compiler_id: str | None = None


def enabled() -> bool:
    return os.environ.get("CPP_LABS_CACHE", "").lower() not in ("off", "0", "no")


def _compiler_version() -> str:
    """The compiler's version banner, so an upgrade invalidates every entry."""
    global _compiler_id
    if _compiler_id is None:
        try:
            out = subprocess.run(["g++", "--version"], capture_output=True,
                                 text=True, timeout=10).stdout
        except (OSError, subprocess.SubprocessError):
            out = "unknown"
        _compiler_id = out.strip().splitlines()[0] if out.strip() else "unknown"
    return _compiler_id


def key(source: str, extra_flags: list[str] | None, std: str) -> str:
    h = hashlib.sha256()
    for part in (source, "\0".join(extra_flags or []), std, _compiler_version()):
        h.update(part.encode("utf-8"))
        h.update(b"\0")
    return h.hexdigest()


def truncated_sanitizer_report(result: RunResult) -> bool:
    """True if an AddressSanitizer report began but never reached its SUMMARY.

    ASan closes every report with a ``SUMMARY: AddressSanitizer:`` line. A report
    without one was cut short, and baking it leaves the page showing part of an
    exhibit that still reads like a whole one: `array_pointer` shipped with 2 of
    its 7 report lines missing on 2026-08-27, and every test still passed,
    because they check that a report is present rather than that it is complete.

    Only AddressSanitizer is checked. UndefinedBehaviorSanitizer does not always
    print a SUMMARY when it is allowed to recover, so requiring one there would
    fail builds that are fine.
    """
    text = f"{result.stderr}\n{result.stdout}"
    return ("ERROR: AddressSanitizer" in text
            and "SUMMARY: AddressSanitizer" not in text)


def lookup(source: str, extra_flags: list[str] | None, std: str) -> RunResult | None:
    if not enabled():
        return None
    path = CACHE_DIR / f"{key(source, extra_flags, std)}.json"
    try:
        stored: dict[str, Any] = json.loads(path.read_text())
    except (OSError, ValueError):
        return None
    if set(stored) != set(_FIELDS):        # written by an older layout; ignore
        return None
    return RunResult(**stored)


def store(source: str, extra_flags: list[str] | None, std: str,
          result: RunResult) -> None:
    """Record *result*, unless it is an accident of machine load."""
    if not enabled():
        return
    if result.status in ("execution-timeout", "cancelled"):
        return
    if result.compiler_stderr.strip() == "Compilation timed out.":
        return
    if truncated_sanitizer_report(result):
        return
    path = CACHE_DIR / f"{key(source, extra_flags, std)}.json"
    tmp = path.with_suffix(".json.tmp")
    try:
        CACHE_DIR.mkdir(exist_ok=True)
        tmp.write_text(json.dumps({f: getattr(result, f) for f in _FIELDS}))
        tmp.replace(path)                  # atomic: never a half-written entry
    except (OSError, TypeError):
        pass                               # a cache that cannot be written is not an error
