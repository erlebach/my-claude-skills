"""Build orchestrator for the C++ Pointer Lab static HTML output.

Entry point: ``python -m cpp_labs.build_html``

For each lab (pointers_refs, smart_ptrs) and each topic in that lab:
  1. Expand variants from the topic's categorical controls.
  2. For each variant: generate source → compile+run → parse output.
  3. Render a fragment via :func:`html_renderer.render_fragment`.
  4. Write ``dist/topics/<topic_id>.html`` (one fragment, standalone).
  5. Write ``dist/lab_<lab>.html`` (all fragments for the lab, combined).

Only categorical (dropdown) controls produce variants; free-text controls are
dropped (their default is baked in).  Topics with no categorical controls
yield a single variant.
"""

from __future__ import annotations

import re
import shutil
import sys
from pathlib import Path
from typing import Any

from .code_generator import ControlDef, TopicTemplate, generate_source
from .compiler_runner import (
    compile_and_run, parse_gauge_all, parse_membytes, parse_perf_chart,
    parse_ptrdata_all, PerfChartError)
from .html_renderer import assemble_page, render_fragment, svg_renderer


# ---------------------------------------------------------------------------
# Console scrubbing
# ---------------------------------------------------------------------------

# The instrumented programs print ``MEMBYTES:`` / ``PTRDATA:`` / ``GAUGE:`` marker
# lines so the engine can parse them (see parse_membytes / parse_ptrdata_all /
# parse_gauge_all) and build the memory / stack-frame diagram or step-gauge. Those
# lines — and the raw addresses they carry — are backstage data for the diagram,
# not part of the program's real output, so they must be stripped from the stdout
# shown to the student.
_MARKER_LINE_RE = re.compile(
    r"^[ \t]*(?:MEMBYTES|PTRDATA|GAUGE):.*(?:\r?\n|$)", re.MULTILINE)


def _display_stdout(stdout: str) -> str:
    """Return program stdout with the diagram-feed marker lines removed."""
    return _MARKER_LINE_RE.sub("", stdout)


# A source line the author brackets with /*[hl]*/ … /*[/hl]*/ to echo beside the
# byte grid, so a "Raw bytes of arr" dump names the exact line it came from. The
# markers are valid C block comments; we lift the text between them and strip them
# from the source that is compiled and shown, leaving neither a marker nor a box.
_HL_LINE_RE = re.compile(r"/\*\[hl\]\*/(.*?)/\*\[/hl\]\*/", re.S)


def _extract_hl_line(source: str) -> tuple[str, str]:
    """Return ``(marked_line, source_without_markers)`` — empty line if unmarked."""
    m = _HL_LINE_RE.search(source)
    line = m.group(1).strip() if m else ""
    clean = source.replace("/*[hl]*/", "").replace("/*[/hl]*/", "")
    return line, clean


def _extract_gauge_lines(source: str) -> list[str]:
    """Bind each ``GAUGE:`` print statement in the source to a marked code line.

    Walks the source top-to-bottom: a ``/*[hl]*/ … /*[/hl]*/`` marked line becomes
    "pending"; the next ``GAUGE:``-printing ``cout`` consumes it. Returns one entry
    per GAUGE print, in source order — the marked line's text, or ``""`` when no
    marker preceded that print (e.g. a step caused by an implicit scope-exit /
    destructor). Index-aligned with :func:`parse_gauge_all` for straight-line code,
    so each gauge step can name the exact line that moved the count. The lifted
    text is verbatim from the real code, so it can't drift (same guarantee as
    :func:`_extract_hl_line`)."""
    lines_out: list[str] = []
    pending = ""
    for line in source.splitlines():
        m = _HL_LINE_RE.search(line)
        if m:
            pending = m.group(1).strip()
        if '"GAUGE:' in line:          # the cout that emits a GAUGE: marker
            lines_out.append(pending)
            pending = ""
    return lines_out


# console_line_link (item 22): a traced ``cout`` line the author brackets with
# /*[hl]*/ … /*[/hl]*/ so its REAL output lines can be hover-linked back to it.
# Same marker as the byte-grid / step_gauge, but here EVERY marked line is a link
# target (not one pending slot), so we collect them all in source order.
# First double-quoted, escape-aware string literal. (Raw strings R"(...)" are
# not handled — not used in these traces.)
_LINK_PREFIX_RE = re.compile(r'"((?:[^"\\]|\\.)*)"')


def _norm(s: str) -> str:
    """Whitespace-normalized form, so indentation never breaks line matching."""
    return " ".join(s.split())


def _extract_link_lines(source: str) -> list[tuple[str, str, str]]:
    """Return ``[(verbatim_line, output_prefix, output_suffix), …]`` per ``/*[hl]*/`` line.

    ``verbatim_line`` is the marked line with its markers removed (so it matches
    the displayed, stripped source); ``output_prefix`` is the FIRST string literal
    in the marked region (the text its ``cout`` prints first). ``output_suffix`` is
    the LAST literal when a value is interpolated in the MIDDLE
    (``"Buffer " << id << " born"`` → prefix ``"Buffer "``, suffix ``" born"``) — it
    disambiguates two lines that share a prefix but differ in their tail (`born` vs
    `freed`); it is empty when the value prints at the end (only the prefix binds).
    All lifted verbatim from the compiled source, so none can drift."""
    out: list[tuple[str, str, str]] = []
    for line in source.splitlines():
        m = _HL_LINE_RE.search(line)
        if not m:
            continue
        clean = line.replace("/*[hl]*/", "").replace("/*[/hl]*/", "")
        lits = _LINK_PREFIX_RE.findall(m.group(1))
        prefix = lits[0] if lits else ""
        # A suffix exists only when a value sits BETWEEN two literals (>= 2
        # literals); a single-literal print has no trailing static text to bind.
        suffix = lits[-1] if len(lits) >= 2 else ""
        # A static message often IS the whole literal ending in an escaped
        # newline (`"Buffer freed\n"`); the real stdout line has that newline
        # consumed, so strip a trailing ``\n`` escape to let static-message
        # lines bind like interpolated ones (`"find_max = " << v`).
        if prefix.endswith("\\n"):
            prefix = prefix[:-2]
        if suffix.endswith("\\n"):
            suffix = suffix[:-2]
        # A whitespace-only literal (e.g. the `" "` separator in a value-printing
        # `for (x : lst) cout << " " << x` loop, or a trailing `"\n"`) is not a
        # meaningful constraint — treat it as empty. An empty prefix makes the
        # line prefix-less so it JOINS the group of the `cout` label above it.
        if not prefix.strip():
            prefix = ""
        if not suffix.strip():
            suffix = ""
        out.append((clean, prefix, suffix))
    return out


_INT_RE = re.compile(r"-?\d+")


def _value_keys(text: str, prefix: str = "") -> list[str]:
    """The distinct value keys ``v<N>`` for one console line, in first-seen order.

    Integers are taken from the line's DATA only: the bound output-prefix (a
    static label that may carry incidental integers — a range bound ``[2, 1)``,
    an argument ``insert(it, 99)``, a ``size = 3``) is stripped first, so only
    the printed values key to diagram boxes. A multi-value dump line keys to ALL
    its boxes; a single-value line to one. (Reverses the earlier MVP rule that a
    multi-int line linked code<->console only, never to a box.)"""
    data = text[len(prefix):] if prefix and text.startswith(prefix) else text
    # A pure static message ("pushed 5\n", "Buffer 1 born") IS its literal, so the
    # value lives IN the prefix — nothing follows it. Fall back to the whole line
    # so that value still keys. (Label+data lines like "after insert(...): 5 2 9"
    # keep only the data, dropping incidental label integers.)
    if not data.strip():
        data = text
    out: list[str] = []
    for n in _INT_RE.findall(data):
        k = f"v{n}"
        if k not in out:
            out.append(k)
    return out


def _bind_console_link(
    clean_source: str, stdout: str, link_lines: list[tuple[str, str, str]],
) -> tuple[list[tuple[str, str | None]], list[tuple[str, str | None]]]:
    """Build the (source, console) keyed line-lists for ``console_line_link``.

    Marked source lines are grouped by output line: a line WITH a string-literal
    prefix owns a new group (key ``"l<i>"``); a marked line with NO prefix (a
    value-printing ``for`` loop, which shares the physical output line of the
    ``cout`` label just above it) JOINS the current group, taking the same key.
    So one output line links to every code line that printed it. Every real stdout
    line is bound to the group whose prefix it STARTS with AND whose suffix it ENDS
    with — the suffix disambiguates a value printed mid-line (``Buffer 1 born`` vs
    ``Buffer 1 freed``, both prefix ``"Buffer "``). Most specific (longest
    prefix+suffix) wins. Lines with no match carry ``None``; ``([], [])`` when
    nothing is marked.

    Marked source lines are matched to the displayed source by their (whitespace-
    normalized) text, so the marked ``cout`` lines must be textually distinct
    (true for real traces, where each print differs)."""
    if not link_lines:
        return [], []
    # Assign each marked line its group key: a prefixed line (or the first line)
    # starts a group named for its own index; a prefix-less line joins the current.
    group_of: list[str] = []
    cur = "l0"
    for i, (_text, p, _s) in enumerate(link_lines):
        if p or not group_of:
            cur = f"l{i}"
        group_of.append(cur)
    key_of = {_norm(text): group_of[i] for i, (text, _p, _s) in enumerate(link_lines)}
    link_source = [(ln, key_of.get(_norm(ln))) for ln in clean_source.splitlines()]
    binders = sorted(
        ((p, s, group_of[i]) for i, (_t, p, s) in enumerate(link_lines) if p),
        key=lambda psk: len(psk[0]) + len(psk[1]), reverse=True,
    )
    link_console: list[tuple[str, str | None]] = []
    for ln in stdout.splitlines():
        key = next((k for p, s, k in binders
                    if ln.startswith(p) and (not s or ln.endswith(s))), None)
        link_console.append((ln, key))
    return link_source, link_console



def _gauge_steps_with_code(stdout: str, gauge_lines: list[str]) -> list[dict]:
    """Parse the GAUGE: steps from ``stdout`` and attach each step's marked code
    line (by index). Steps with no marked line carry no ``code`` key."""
    steps = parse_gauge_all(stdout)
    for step, code in zip(steps, gauge_lines):
        if code:
            step["code"] = code
    return steps


def _perf_charts_from_stdout(topic, display_stdout: str) -> dict:
    """Build {chart_id: {"spec": spec, "points": [...]}} from DISPLAYED stdout.

    Each bar gets a stable ``cll`` key (pc-<chart>-<i>) so bar<->console hover
    reuses the existing tri-link handler. Single-stdout charts only; charts with
    from:flag_variants are aggregated later (see Task 7) and skipped here.
    """
    out: dict = {}
    for chart_id, spec in getattr(topic, "perf_chart", {}).items():
        if spec.get("from"):   # cross-variant chart, aggregated in _attach_flag_variant_charts
            continue
        points = parse_perf_chart(display_stdout, spec)
        for i, pt in enumerate(points):
            pt["cll"] = f"pc-{chart_id}-{i}"
        out[chart_id] = {"spec": spec, "points": points}
    return out


def _aggregate_flag_variant_charts(spec: dict, tabs: list) -> dict:
    """tabs: [(label, display_stdout), ...] -> {"spec": spec, "points": [...]}.

    One bar per tab: y from the regex's `y` group. The bar label is the i-th
    entry of an optional ``labels:`` list on the spec (short chart labels), else
    the variant/tab title — the verbose tab titles overlap under narrow bars, so
    authors supply short labels here. Raises PerfChartError if a tab's stdout
    does not match (loud failure, consistent with single-stdout parse_perf_chart).
    """
    override = spec.get("labels") or []
    points = []
    for i, (label, stdout) in enumerate(tabs):
        m = re.search(spec["match"], stdout, re.MULTILINE)
        if not m:
            raise PerfChartError(
                f"perf_chart cross-variant: {spec['match']!r} matched nothing "
                f"in tab {label!r}")
        try:
            y = float(m.group("y"))
        except (IndexError, ValueError) as exc:
            raise PerfChartError(
                f"perf_chart cross-variant: non-numeric y in tab {label!r}: "
                f"{m.group(0)!r}") from exc
        bar_label = override[i] if i < len(override) else label
        points.append({"label": bar_label, "y": y, "raw": m.group(0),
                       "cll": f"pc-fv-{i}"})
    return {"spec": spec, "points": points}


def _attach_flag_variant_charts(topic, variants: list) -> None:
    """Build each cross-variant (from:) perf_chart across all (non-failed) tabs and
    attach it to EVERY variant so the comparison shows in each tab's diagram
    column. Mutates the variant dicts in place.
    """
    fv_charts = {cid: spec
                 for cid, spec in getattr(topic, "perf_chart", {}).items()
                 if spec.get("from")}
    if not fv_charts:
        return
    tabs = [(v.get("label", ""), v.get("stdout", ""))
            for v in variants if not v.get("failed")]
    if not tabs:
        return
    for cid, spec in fv_charts.items():
        chart = _aggregate_flag_variant_charts(spec, tabs)
        for v in variants:
            v.setdefault("perf_chart", {})[cid] = chart


# ---------------------------------------------------------------------------
# Variant expansion
# ---------------------------------------------------------------------------


def expand_variants(topic: TopicTemplate) -> list[dict[str, str]]:
    """Return a list of control-state dicts, one per categorical variant.

    Categorical controls are those with ``kind == "dropdown"``.  For every
    combination of dropdown options (there is at most one dropdown per topic
    in the current set), one dict is produced.  Free-text controls always use
    their default value.  If no dropdown control exists, one dict (all
    defaults) is returned.
    """
    # Seed all controls with their defaults
    base: dict[str, str | bool] = {}
    dropdowns: list[ControlDef] = []
    for ctrl in topic.controls:
        if ctrl.kind == "dropdown":
            dropdowns.append(ctrl)
        else:
            # Free-text / checkbox — bake in the default. Preserve the
            # default's type (notably bool for checkboxes) so the resolver
            # keys on "true"/"false", not the stringified bare "False".
            base[ctrl.id] = ctrl.default

    # A standards topic (validated to have no dropdowns) fans out on the C++
    # standard instead: one variant per standard, carrying a synthetic
    # ``__std__`` key that _compile_one turns into the -std flag and
    # capture_variant turns into the "C++NN" tab label.
    if getattr(topic, "standards", None):
        return [{**base, "__std__": str(n)} for n in topic.standards]

    # A flag-variant topic (validated to have no dropdowns) fans out on its
    # compile-flag sets: one variant per set, carrying a synthetic ``__opt__``
    # index that _compile_one turns into extra flags and capture_variant turns
    # into the flag-set's tab label. Same source across every tab.
    if getattr(topic, "flag_variants", None):
        return [{**base, "__opt__": str(i)} for i in range(len(topic.flag_variants))]

    if not dropdowns:
        return [dict(base)]

    # Enumerate combinations (currently only one dropdown per topic)
    # If multiple dropdowns existed we'd take the Cartesian product, but the
    # current topic set has at most one, so a simple loop suffices.
    results = []
    for combo in _cartesian(dropdowns):
        state = dict(base)
        state.update(combo)
        results.append(state)
    return results


def _cartesian(dropdowns: list[ControlDef]) -> list[dict[str, str]]:
    """Return the Cartesian product of dropdown option lists as dicts."""
    if not dropdowns:
        return [{}]
    ctrl = dropdowns[0]
    rest = _cartesian(dropdowns[1:])
    result = []
    for option in ctrl.options:
        for suffix in rest:
            d = {ctrl.id: option}
            d.update(suffix)
            result.append(d)
    return result


# ---------------------------------------------------------------------------
# Per-variant capture
# ---------------------------------------------------------------------------


def capture_variant(topic: TopicTemplate, control_state: dict[str, str]) -> dict[str, Any]:
    """Compile and run one variant; return a render-data dict.

    Keys:
      label      — human-readable label from the control options
      source     — generated C++ source
      svg        — inline SVG string
      stdout     — program stdout (or "" on compile failure)
      membytes   — parsed MEMBYTES hex string (or "n/a")
      failed     — True if compilation failed
      stderr     — compiler stderr (non-empty when failed)
    """
    # Build a human-readable label from the categorical control values
    label_parts = []
    for ctrl in topic.controls:
        if ctrl.kind == "dropdown":
            label_parts.append(control_state.get(ctrl.id, ctrl.default))
    label = " / ".join(str(p) for p in label_parts) if label_parts else ""
    if "__std__" in control_state:
        label = f"C++{control_state['__std__']}"
    if "__opt__" in control_state:
        label = topic.flag_variants[int(control_state["__opt__"])]["label"]

    # Multi-case topics: compile one independent sub-case per CaseDef and
    # bundle them under this variant.  The variant itself carries only the
    # label; each sub-case carries its own source / compile result / svg.
    if topic.cases:
        cases = []
        for case in topic.cases:
            sub = _compile_one(topic, control_state, case.subs)
            sub["label"] = case.label
            cases.append(sub)
        return {"label": label, "cases": cases}

    return {"label": label, **_compile_one(topic, control_state, None)}


def _compile_one(
    topic: TopicTemplate,
    control_state: dict,
    extra_subs: dict[str, str] | None,
) -> dict[str, Any]:
    """Compile+run a single program and return its render-data dict (no label)."""
    source = generate_source(topic, control_state, extra_subs)
    # Bind each GAUGE: print to its marked code line BEFORE the markers are
    # stripped, so a gauge step can name the line that moved the count.
    gauge_lines = _extract_gauge_lines(source)
    # console_line_link (item 22): capture marked cout lines from the RAW source
    # (before _extract_hl_line strips the markers just below).
    link_lines = _extract_link_lines(source)
    # Lift the author-marked byte-grid source line, then strip its markers so the
    # compiled + displayed source is clean (the line is echoed beside the grid).
    byte_line, source = _extract_hl_line(source)
    # Topics flagged ``sanitize`` are gotchas whose point is a runtime fault
    # (double-free, use-after-move, null deref). Compile them with
    # AddressSanitizer so the crash yields a precise diagnostic on stderr rather
    # than a bare signal; ``-g`` keeps the report's function names readable.
    extra_flags = ["-fsanitize=address", "-g"] if getattr(topic, "sanitize", False) else []
    extra_flags = list(extra_flags) + list(getattr(topic, "extra_compile_flags", []) or [])
    # Output-flag tabs: inject this tab's flag set (e.g. -O2) into the compile.
    if "__opt__" in control_state:
        extra_flags += list(topic.flag_variants[int(control_state["__opt__"])]["flags"])
    std = control_state.get("__std__")
    std_kw = {"std": f"c++{std}"} if std else {}
    result = compile_and_run(source, extra_flags=extra_flags or None, **std_kw)
    # Bind real stdout lines to their marked cout source line (empty unless the
    # topic marked lines). ``source`` is already marker-free here (stripped above).
    link_source, link_console = _bind_console_link(
        source, _display_stdout(result.stdout), link_lines)

    # console_line_link tri-link keys: each line's l<i> key plus a v<N> key per
    # DATA integer (output-prefix stripped, so incidental label integers don't
    # key). A source line unions the value keys of every output bound to it
    # (loop-safe), so hovering it lights every box it printed.
    prefix_of = {f"l{i}": p for i, (_t, p, _s) in enumerate(link_lines)}

    def _console_keys(text, k):
        parts = [k] if k else []
        parts += _value_keys(text, prefix_of.get(k, ""))
        return " ".join(parts)

    def _src_keys(k):
        if not k:
            return ""
        parts = [k]
        for text, ck in link_console:
            if ck != k:
                continue
            for v in _value_keys(text, prefix_of.get(ck, "")):
                if v not in parts:
                    parts.append(v)
        return " ".join(parts)
    tri_source = [(t, _src_keys(k)) for t, k in link_source]
    tri_console = [(t, _console_keys(t, k)) for t, k in link_console]

    if result.status == "compile-failed":
        return {
            "source": source,
            "ptrdata": None,
            "ptrdata_steps": [],
            "gauge_steps": [],
            "svg": svg_renderer(None),
            "stdout": "",
            "membytes": "n/a",
            "failed": True,
            "error_kind": "compile",
            "byte_line": byte_line,
            "link_source": link_source,
            "link_console": link_console,
            "tri_source": tri_source,
            "tri_console": tri_console,
            "stderr": result.compiler_stderr,
            "perf_chart": {},
        }

    if result.status in ("execution-error", "execution-timeout"):
        # Compiled cleanly but the program crashed (segfault, ASan, abort,
        # non-zero exit) or timed out.  This is a *runtime* failure — surface it
        # as such, showing the crash diagnostic (stderr) rather than reporting a
        # green success with the discarded report.
        report = result.stderr or result.stdout or "(program crashed with no diagnostic output)"
        ptrdata = result.ptrdata
        return {
            "source": source,
            "ptrdata": ptrdata,
            "ptrdata_steps": parse_ptrdata_all(result.stdout),
            "gauge_steps": _gauge_steps_with_code(result.stdout, gauge_lines),
            "svg": svg_renderer(ptrdata),
            "stdout": _display_stdout(result.stdout),
            "membytes": result.memory_bytes or parse_membytes(result.stdout) or "n/a",
            "failed": True,
            "error_kind": "runtime",
            "byte_line": byte_line,
            "link_source": link_source,
            "link_console": link_console,
            "tri_source": tri_source,
            "tri_console": tri_console,
            "stderr": report,
            "perf_chart": {},
        }

    ptrdata = result.ptrdata
    membytes = result.memory_bytes or parse_membytes(result.stdout)

    return {
        "source": source,
        "ptrdata": ptrdata,
        "ptrdata_steps": parse_ptrdata_all(result.stdout),
        "gauge_steps": _gauge_steps_with_code(result.stdout, gauge_lines),
        "svg": svg_renderer(ptrdata),
        "stdout": _display_stdout(result.stdout),
        "membytes": membytes,
        "failed": False,
        "error_kind": None,
        "byte_line": byte_line,
        "link_source": link_source,
        "link_console": link_console,
        "tri_source": tri_source,
        "tri_console": tri_console,
        "stderr": "",
        "perf_chart": _perf_charts_from_stdout(topic, _display_stdout(result.stdout)),
    }


# ---------------------------------------------------------------------------
# Lab build
# ---------------------------------------------------------------------------


def build_lab(lab_id: str, topics: list[TopicTemplate], dist_dir: Path) -> None:
    """Build all HTML outputs for one lab into *dist_dir*.

    Raises ``RuntimeError`` if ``g++`` is not available.
    Writes:
      - ``dist_dir/topics/<topic_id>.html`` for each topic
      - ``dist_dir/lab_<lab_id>.html`` combining all topics
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. "
            "Install a C++ compiler before running the static build."
        )

    topics_dir = dist_dir / "topics"
    topics_dir.mkdir(parents=True, exist_ok=True)

    all_fragments: list[str] = []

    for topic in topics:
        control_states = expand_variants(topic)
        variants = [capture_variant(topic, cs) for cs in control_states]
        _attach_flag_variant_charts(topic, variants)
        fragment = render_fragment(topic, variants)
        all_fragments.append(fragment)

        # Per-topic standalone file
        per_topic_html = assemble_page([fragment], title=topic.name)
        (topics_dir / f"{topic.id}.html").write_text(per_topic_html, encoding="utf-8")

    # Per-lab combined file
    topic_meta = [(t.id, t.name) for t in topics]
    lab_html = assemble_page(all_fragments, title=f"C++ Lab — {lab_id}", topics=topic_meta)
    (dist_dir / f"lab_{lab_id}.html").write_text(lab_html, encoding="utf-8")


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------


def main() -> None:
    """Build both labs into ``dist/`` in the project root."""
    if shutil.which("g++") is None:
        print(
            "ERROR: g++ not found on PATH. "
            "Install a C++ compiler (e.g. Xcode Command Line Tools on macOS, "
            "or build-essential on Debian/Ubuntu) before running the static build.",
            file=sys.stderr,
        )
        sys.exit(1)

    project_root = Path(__file__).parent.parent
    dist_dir = project_root / "dist_labs"

    from .topic_yaml import load_topics

    pr = load_topics(project_root / "pointers_refs" / "topics")
    SMART_TOPICS = list(load_topics(project_root / "smart_ptrs" / "topics").values())

    pointers_refs_topics = [
        pr[i] for i in (
            "basic_ptr", "const_taxonomy", "ref_must_bind", "ref_no_null",
            "ref_rebind_illusion", "ref_const", "null_deref",
        )
    ]

    print("Building lab: pointers_refs …")
    build_lab("pointers_refs", pointers_refs_topics, dist_dir)

    print("Building lab: smart_ptrs …")
    build_lab("smart_ptrs", SMART_TOPICS, dist_dir)

    print(f"Done. Output in {dist_dir}/")


if __name__ == "__main__":
    main()
