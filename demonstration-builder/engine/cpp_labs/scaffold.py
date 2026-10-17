"""Which source lines are the page's instrumentation rather than the lesson.

One implementation, because the engine renders code by two different paths: the
plain panel (``yaml_engine.render_page._pre``) and the hover-linked panels
(``components.code_line_link`` / ``console_line_link``). Both dim with the same
``code-scaffold`` class, whose strength is the ``--code-dim`` CSS token.
"""
from __future__ import annotations

from collections.abc import Sequence

# Free for every demo, because these are ENGINE PROTOCOL rather than anything an
# author wrote as a lesson: the three data markers the build scrapes out of
# stdout to drive its diagrams (and then strips from the console), and the
# byte-dump harness code_generator injects, which fences itself with comments.
DEFAULT_MARKERS = ("PTRDATA:", "MEMBYTES:", "GAUGE:")
FENCE = ("--- instrumentation (not part of the lesson) ---",
         "--- end instrumentation ---")


def flag_lines(lines: Sequence[str],
               markers: Sequence[str] = ()) -> list[tuple[str, bool]]:
    """Pair each source line with whether it is instrumentation.

    A marker matches a line, but instrumentation comes in *blocks*: marking only
    matching lines left a dimmed ``frame_enter(...)`` signature followed by a
    bright ``printf("enter %s\\n", fn);``. The match therefore extends, by shape
    rather than by parsing C++:

    * an explicit ``FENCE`` region dims wholesale (the injected byte harness);
    * a matched line that OPENS a block dims to the brace that closes it (the
      first line at or left of the opener's indent starting ``}``);
    * a matched line that is an unfinished statement dims to its ``;`` -- and if
      that turns out to be a wrapped *signature*, the ``{`` arriving a line later
      promotes it to a block, or its closing brace would stay bright;
    * a matched ``//`` comment dims the rest of its comment run, since the marker
      lands on whichever line happens to hold the word.
    """
    all_markers = tuple(markers) + DEFAULT_MARKERS
    flags: list[tuple[str, bool]] = []
    in_fence = False
    carry_indent = None
    carry_stmt = False
    carry_stmt_indent = 0
    carry_comment = False
    for line in lines:
        stripped = line.strip()
        indent = len(line) - len(line.lstrip())
        dim = any(m in line for m in all_markers)
        if in_fence:
            flags.append((line, True))
            if FENCE[1] in line:
                in_fence = False
            continue
        if FENCE[0] in line:
            in_fence = True
            flags.append((line, True))
            continue
        if carry_indent is not None:
            dim = True
            if stripped.startswith("}") and indent <= carry_indent:
                carry_indent = None
        elif carry_stmt:
            dim = True
            if stripped.endswith("{"):
                carry_stmt = False
                carry_indent = carry_stmt_indent
            elif stripped.endswith(";"):
                carry_stmt = False
        elif carry_comment and stripped.startswith("//"):
            dim = True
        elif dim:
            carry_comment = stripped.startswith("//")
            if carry_comment:
                pass
            elif stripped.endswith("{"):
                carry_indent = indent
            elif stripped and not stripped.endswith((";", "}")):
                carry_stmt = True
                carry_stmt_indent = indent
        if not stripped.startswith("//"):
            carry_comment = False
        flags.append((line, dim))
    return flags


def has_scaffold(text: str, markers: Sequence[str] = ()) -> bool:
    """True when *text* carries anything worth dimming."""
    return (any(m in text for m in tuple(markers) + DEFAULT_MARKERS)
            or FENCE[0] in text)
