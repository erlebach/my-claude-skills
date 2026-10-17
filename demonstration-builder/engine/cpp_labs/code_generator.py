"""Code Generation Module for the C++ Pointer Lab.

Defines the data structures for topic templates and UI controls, and the
:func:`generate_source` function that substitutes control values into a C++
template and injects the memory-dump instrumentation harness.

Placeholder syntax
------------------
Templates use ``<<name>>`` double-angle-bracket placeholders (e.g.
``<<type>>``, ``<<value>>``) rather than ``str.format`` braces.  This avoids
all brace-escaping conflicts with C++ code, which is full of ``{`` and ``}``.

A special placeholder ``<<HARNESS>>`` marks where the memory-dump
instrumentation block is inserted.  The harness references the topic's
``target_var`` (the variable being initialized) and prints its raw bytes to
stdout in a parseable ``MEMBYTES:`` line.
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field


# ---------------------------------------------------------------------------
# Data structures
# ---------------------------------------------------------------------------


@dataclass
class ControlDef:
    """Definition of a single UI control and its template mapping."""

    id: str
    label: str
    kind: str
    options: list[str] = field(default_factory=list)
    default: str | bool = ""
    placeholder: str = ""
    value_map: dict[str, str] | None = None


@dataclass
class CaseDef:
    """A build-time sub-case shown within one variant panel.

    Each case is compiled independently; ``subs`` fills extra template
    placeholders (e.g. ``<<op>>``) to vary one operation while the
    variant's control state (e.g. the declaration) stays fixed.
    """

    label: str
    subs: dict[str, str] = field(default_factory=dict)


@dataclass
class TopicTemplate:
    """A single lab topic: its template, controls, and metadata."""

    id: str
    name: str
    template: str
    controls: list[ControlDef]
    explanation: str
    group: str
    target_var: str = "x"
    sanitize: bool = False
    has_ptrdata: bool = True
    # byte_grid decode mode for this topic's raw-byte dump. "" keeps the default
    # per-byte char row; "int32" replaces it with a grouped (4-byte) row of
    # decoded little-endian ints — legible for numeric arrays, where the char
    # row is noise. See components.byte_grid.
    byte_decode: str = ""
    # Human label for the byte_grid caption — "Raw bytes of <byte_label>". Empty
    # falls back to target_var (the dumped variable's name). Set it to disambiguate
    # scope when the bare name is not enough, e.g. "arr (the int* parameter of show)".
    byte_label: str = ""
    doc_url: str = ""
    # Scaffolding lines: substrings identifying source lines that are the page's
    # instrumentation rather than the lesson (a shadow-stack recorder, a marker
    # printf). Any source line containing one is rendered dimmed. The code is
    # still emitted verbatim and stays copy-pasteable -- only its colour changes.
    scaffold_lines: list[str] = field(default_factory=list)
    cases: list[CaseDef] | None = None
    extra_compile_flags: list[str] = field(default_factory=list)
    # Directory to run the compiler from. Only needed by a topic whose verbatim
    # code uses an angle include (<a/b.hpp> does not search the source's own
    # directory), so the header must be reached with -I. from here. Keeping the
    # flag relative keeps the build command shown on the page retypeable.
    compile_cwd: str = ""
    standards: list[int] = field(default_factory=list)
    # Output-flag tabs: each entry is {"label": str, "flags": list[str]}. The
    # engine fans out one tab per entry, compiling the SAME source with that
    # entry's flags (e.g. -O0 vs -O2). Mirrors ``standards``/``__std__``.
    flag_variants: list[dict] = field(default_factory=list)
    # Per-tab compile flags: {dropdown option label: [flags]}. Only the tab with
    # that label compiles with them (e.g. one AddressSanitizer tab among plain
    # ones). Unlike ``sanitize``, which applies to every tab of the topic.
    option_flags: dict = field(default_factory=dict)
    # Performance chart spec: keyed by chart id; each entry has mode, match,
    # y/x axis specs. Populated and validated by topic_yaml._validate_perf_chart.
    perf_chart: dict = field(default_factory=dict)
    # Multi-file project: {"dir": str, "tabs": [{"label", "target", "files"}]}.
    # ``dir`` is relative to cpp_labs/. Each tab is one make target; ``files``
    # are the files shown in that tab, in order. None for a single-file topic.
    project: dict | None = None


# ---------------------------------------------------------------------------
# Harness construction
# ---------------------------------------------------------------------------

_HARNESS_TEMPLATE = """\
    // --- instrumentation (not part of the lesson) ---
    {{
        unsigned char* p = reinterpret_cast<unsigned char*>(&{var});
        std::cout << "MEMBYTES:";
        for (size_t i = 0; i < sizeof({var}); ++i) {{
            printf(" %02x", p[i]);
        }}
        std::cout << std::endl;
    }}
    // --- end instrumentation ---"""


def _build_harness(target_var: str) -> str:
    """Return the instrumentation block that dumps ``target_var``'s bytes."""
    return _HARNESS_TEMPLATE.format(var=target_var)


# ---------------------------------------------------------------------------
# Value resolution
# ---------------------------------------------------------------------------


def _resolve_control_value(ctrl: ControlDef, raw: str | bool) -> str:
    if ctrl.value_map is not None:
        if isinstance(raw, bool):
            key = "true" if raw else "false"
        else:
            key = str(raw)
        return ctrl.value_map.get(key, str(raw))
    return str(raw)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def generate_source(
    topic: TopicTemplate,
    control_state: dict,
    extra_subs: dict[str, str] | None = None,
) -> str:
    """Generate the full C++ source for *topic* given *control_state*.

    *extra_subs* (used for per-case sub-case rendering) are applied on top
    of the control-resolved substitutions, filling placeholders such as
    ``<<op>>`` that no control owns.
    """
    subs: dict[str, str] = {}
    for ctrl in topic.controls:
        raw = control_state.get(ctrl.id, ctrl.default)
        subs[ctrl.placeholder] = _resolve_control_value(ctrl, raw)

    if extra_subs:
        subs.update(extra_subs)

    subs["<<HARNESS>>"] = _build_harness(topic.target_var)

    result = topic.template
    for _ in range(8):
        previous = result
        for placeholder, value in subs.items():
            result = _substitute(result, placeholder, value)
        if result == previous:
            break
    return result


# A placeholder alone on its line, with only whitespace before it. The captured
# whitespace is the indentation the substituted block has to adopt.
def _own_line(placeholder: str) -> re.Pattern:
    return re.compile(rf"^([ \t]*){re.escape(placeholder)}[ \t]*$", re.M)


def _substitute(text: str, placeholder: str, value: str) -> str:
    """Fill one ``<<placeholder>>``, re-indenting a multi-line value to match it.

    A plain ``str.replace`` indents only the value's FIRST line — the template's
    own leading whitespace sits in front of it, and every later line lands at
    column zero. On a class member that means a method printed flush against the
    left margin, inside the class body, which reads as a syntax error the reader
    then has to talk themselves out of. (The compiler never minded; C++ ignores
    the whitespace. The reader is the one being misled.)

    So: when the placeholder is alone on its line, every line of the value takes
    that line's indentation. Blank lines stay empty rather than becoming trailing
    whitespace. A placeholder used mid-line has no indentation to inherit and is
    substituted verbatim, as before.
    """
    pat = _own_line(placeholder)
    if not pat.search(text):
        return text.replace(placeholder, value)

    def _fill(m: re.Match) -> str:
        pad = m.group(1)
        return "\n".join(pad + ln if ln.strip() else "" for ln in value.split("\n"))

    # A function replacement is used deliberately: re.sub does not expand escape
    # sequences in what a function returns, so a value containing "\n" (as C++
    # string literals here routinely do) survives verbatim.
    return pat.sub(_fill, text)
