"""Translate a YAML page spec into a self-contained HTML page of components.

A page spec is a flat list of *blocks*:

    title: Basic Pointer
    bake:                 # compile these TopicTemplates; expose variants as data
      bp: basic_ptr
    blocks:
      - callout_note: { id: intro, label: Concept, text: "${bp.explanation}" }
      - topic:        { id: types, source: bp }     # reusable topic-template cluster
      - memory_diagram: { id: d, ptrdata: ${bp.int.ptrdata} }

Each block is a single-key mapping ``{component_name: {args}}``.  The translator
pops ``id`` and forwards the rest as keyword args to the matching component in
:mod:`cpp_labs.components` — so the YAML key names *are* the component
parameters and the same component can appear any number of times (each instance
namespaced by its own ``id``).  ``${a.b.c}`` references resolve against the baked
data.  Two "smart" builders compose multiple components: ``topic`` (a variant_tabs
cluster over a baked topic) and ``heading``/``html`` (chrome).

`render_page(spec, data)` is pure (no g++); `build_page` bakes real output first.

This module is the subject-agnostic engine: it dispatches any page spec to the
component library and bakes any topic in the registry.  Per-subject page specs
live in their own packages (e.g. ``cpp_labs/basic_ptr/basic_ptr.page.yaml``).

Entry point: ``python -m cpp_labs.yaml_engine.render_page <page.yaml> [dist]``
"""

from __future__ import annotations

import html as _html

from cpp_labs import scaffold as _scaffold
import re
import shutil
import sys
from collections.abc import Sequence
from pathlib import Path
from typing import Any

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]

from .. import components as C
from ..build_html import (
    _attach_flag_variant_charts, capture_variant, expand_variants)

_REF_RE = re.compile(r"\$\{([^}]+)\}")


# ---------------------------------------------------------------------------
# Topic registry (resolve a bake name -> TopicTemplate)
# ---------------------------------------------------------------------------


def _topic_registry() -> dict[str, Any]:
    """Every subject's topics, auto-discovered from ``cpp_labs/*/topics``.

    No subject is named here: dropping in a new subject folder (a ``topics/``
    dir of YAML plus a layout) is enough for the engine to bake and render it.
    """
    from ..topic_yaml import discover_topics
    return discover_topics(Path(__file__).resolve().parents[1])


# ---------------------------------------------------------------------------
# Baking (impure — runs g++)
# ---------------------------------------------------------------------------


def _pre(text: str, language: str | None = None,
         scaffold: "Sequence[str]" = ()) -> str:
    # Every panel is per-line. The line-number toggle counts the <code>
    # children with a CSS counter, so a single-<code> panel would number a
    # whole program 1; the shape has to be the same on every page for the
    # header chip to mean the same thing on every page.
    return _pre_scaffolded(text, language, scaffold)


def _pre_scaffolded(text: str, language: str | None,
                    scaffold: "Sequence[str]") -> str:
    """A code panel whose instrumentation lines are dimmed.

    Lines matching a ``scaffold_lines`` substring are the page's own machinery
    (a shadow-stack recorder, a marker printf), not the lesson, and reading past
    them costs the student attention. They are dimmed with the ``.code-scaffold``
    rule, whose strength is one CSS token (``--code-dim``).

    Two properties are deliberately preserved:

    * **The panel is still copy-pasteable.** Every line is emitted verbatim
      inside the SAME ``<pre>``, separated by real newlines, so ``white-space:
      pre`` and the browser's copy of a ``<pre>`` are unchanged -- selecting the
      panel yields compilable source, dimming and all. This is why the lines are
      per-line ``<code>`` children of one ``<pre>``, rather than the bare
      ``<code class="cll-line">`` blocks the linked panels use: those sit outside
      a ``<pre>`` and had to re-declare white-space to keep their indentation.
    * **Syntax highlighting still runs.** ``hljs.highlightAll()`` selects
      ``pre code``, so each line element is highlighted on its own and keeps the
      class we put on it -- highlight.js adds classes, it does not remove them.
      One consequence: a construct spanning several lines (a block comment, a raw
      string) is highlighted per line, so keep those out of scaffolded topics.
    """
    lang = f" language-{language}" if language else ""
    # Drop trailing blank lines. A source block ends with a newline, so
    # split("\n") hands back one or two empty lines past the closing brace;
    # they were invisible until the line-number toggle numbered them, which
    # put a numbered blank line under every program.
    lines = text.split("\n")
    while len(lines) > 1 and not lines[-1].strip():
        lines.pop()
    out = []
    for line in _scaffold.flag_lines(lines, scaffold):
        line, is_dim = line
        dim = " code-scaffold" if is_dim else ""
        out.append(f'<code class="{lang.strip()}{dim}">{_html.escape(line)}</code>')
    # .code-lines tells the highlight-override layer that the <code> children
    # are LINES, not the usual single code block, so the theme's per-<code>
    # block styling (padding + its own background) is switched off for them.
    return (
        f'<pre class="code-lines" tabindex="0" role="region" '
        f'aria-label="Code listing">'
        + "\n".join(out) + "</pre>"
    )


def _files_html(comp_id: str, files: "Sequence[tuple[str, str]]",
                language: str | None) -> str:
    """One tab per project file, the Makefile included, each a normal code panel."""
    panels = [(name, _pre(text, "makefile" if name == "Makefile" else language))
              for name, text in files]
    return C.variant_tabs(comp_id, panels)


def _bake_program(v: dict[str, Any], language: str | None = None,
                  scaffold: "Sequence[str]" = (), files_id: str = "") -> dict[str, Any]:
    """Render-data for one compiled program (a variant or a sub-case)."""
    mem = v.get("membytes", "")
    return {
        "compile_cmd": v.get("compile_cmd", ""),
        "source": v.get("source", ""),
        "code_html": (_files_html(files_id, v["files"], language) if v.get("files")
                      else _pre(v.get("source", ""), language, scaffold)),
        "ptrdata": v.get("ptrdata"),
        "ptrdata_steps": v.get("ptrdata_steps", []),
        "gauge_steps": v.get("gauge_steps", []),
        "perf_chart": v.get("perf_chart", {}),
        "link_source": v.get("link_source", []),
        "link_console": v.get("link_console", []),
        "tri_source": v.get("tri_source", []),
        "tri_console": v.get("tri_console", []),
        "stdout": v.get("stdout", ""),
        "stderr": v.get("stderr", ""),
        "ok": not v.get("failed", False),
        "failed": v.get("failed", False),
        "error_kind": v.get("error_kind"),
        "exit_code": v.get("exit_code"),
        "bytes": mem.split() if mem and mem != "n/a" else [],
        "target_val": (v.get("ptrdata") or {}).get("target_val", "?"),
        # the author-marked source line to echo beside the byte grid (or "")
        "byte_line": v.get("byte_line", ""),
    }


def _bake_one(topic: Any, language: str | None = None) -> dict[str, Any]:
    variants = [capture_variant(topic, cs) for cs in expand_variants(topic)]
    scaffold = tuple(getattr(topic, "scaffold_lines", ()) or ())
    # Cross-variant perf_charts (from: variants / flag_variants) aggregate one
    # bar per variant across all tabs; attach here, once the full list exists.
    _attach_flag_variant_charts(topic, variants)
    entry: dict[str, Any] = {
        "explanation": topic.explanation,
        "variants": [v.get("label") or "default" for v in variants],
        # A flag_variants topic compiles ONE source at several flag sets; the
        # renderer shows the code once and tabs only the console (Tier 2).
        "output_tabs": bool(getattr(topic, "flag_variants", None)),
        # byte_grid decode mode (topic-level): "" = char row, "int32" = grouped ints.
        "byte_decode": getattr(topic, "byte_decode", ""),
        # Name shown in the byte_grid caption ("Raw bytes of <byte_var>"): the
        # dumped variable, so the grid points at its declaration in the code.
        "byte_var": getattr(topic, "byte_label", "") or getattr(topic, "target_var", ""),
    }
    for v in variants:
        label = v.get("label") or "default"
        if v.get("cases"):
            # A cases-topic: each variant bundles independently-compiled
            # sub-cases. Preserve them (each keeps its own compile verdict)
            # so the renderer can stack them; don't flatten to one program.
            entry[label] = {
                "cases": [{**_bake_program(c, language, scaffold),
                           "label": c.get("label", "")}
                          for c in v["cases"]],
            }
        else:
            entry[label] = _bake_program(v, language, scaffold,
                                         files_id=f"{topic.id}-{label}-files")
    return entry


def bake_all(bake: dict[str, str], language: str | None = None) -> dict[str, Any]:
    """Compile each ``name: topic_id`` and return ``{name: baked-entry}``.

    *language* (from the demo/page YAML) tags each source block with a
    ``language-XXX`` class for syntax highlighting; ``None`` keeps it classless.
    """
    registry = _topic_registry()
    data: dict[str, Any] = {}
    for name, topic_id in (bake or {}).items():
        if topic_id not in registry:
            raise KeyError(f"unknown topic id in bake: {topic_id!r}")
        data[name] = _bake_one(registry[topic_id], language)
    return data


# ---------------------------------------------------------------------------
# Reference resolution  ${a.b.c}
# ---------------------------------------------------------------------------


def _lookup(path: str, data: dict) -> Any:
    cur: Any = data
    for part in path.split("."):
        if isinstance(cur, dict):
            cur = cur[part]
        else:
            cur = getattr(cur, part)
    return cur


def _resolve(value: Any, data: dict) -> Any:
    if isinstance(value, str):
        m = _REF_RE.fullmatch(value.strip())
        if m:  # whole-value ref → substitute the real object (may be dict/list)
            return _lookup(m.group(1), data)
        # A ${demo:name|text} cross-demo marker is not a data reference. It is
        # resolved much later, in components._demo_links, once the surrounding
        # text has been escaped — so pass it through untouched rather than
        # letting _lookup fail on a name it was never meant to see.
        return _REF_RE.sub(
            lambda mo: mo.group(0) if mo.group(1).startswith("demo:")
            else str(_lookup(mo.group(1), data)), value)
    if isinstance(value, dict):
        return {k: _resolve(v, data) for k, v in value.items()}
    if isinstance(value, list):
        return [_resolve(v, data) for v in value]
    return value


# ---------------------------------------------------------------------------
# Dispatch: block name -> component / builder
# ---------------------------------------------------------------------------

_DISPATCH = {
    "callout_note": C.callout_note,
    "color_legend": C.color_legend,
    "memory_diagram": C.memory_diagram,
    "hover_link_diagram": C.hover_link_diagram,
    "before_after_toggle": C.before_after_toggle,
    "predict_reveal_quiz": C.predict_reveal_quiz,
    "compile_status_badge": C.compile_status_badge,
    "output_console": C.output_console,
    "byte_grid": C.byte_grid,
    "code_line_link": C.code_line_link,
    "variant_tabs": C.variant_tabs,
    "code_diagram_panel": C.code_diagram_panel,
    "stacked_subcases": C.stacked_subcases,
    "progressive_steps": C.progressive_steps,
    "glossary": C.glossary,
}

# Components whose one arg is a list of pair-dicts → list of tuples.
_PAIR_ARGS = {
    "progressive_steps": ("steps", ("summary", "content")),
    "variant_tabs": ("panels", ("label", "html")),
    "stacked_subcases": ("subcases", ("label", "html")),
    "glossary": ("terms", ("term", "def")),
}


def _adapt(name: str, args: dict) -> dict:
    if name in _PAIR_ARGS:
        key, (k1, k2) = _PAIR_ARGS[name]
        if key in args:
            args[key] = [(d[k1], d[k2]) for d in args[key]]
    if name == "before_after_toggle" and isinstance(args.get("labels"), list):
        args["labels"] = tuple(args["labels"])
    return args


# ---------------------------------------------------------------------------
# Smart builders (compose multiple components)
# ---------------------------------------------------------------------------


def _build_heading(args: dict, data: dict) -> str:
    level = int(args.get("level", 2))
    return f"<h{level}>{_html.escape(str(args['text']))}</h{level}>\n"


def _build_html(args: dict, data: dict) -> str:
    """Author HTML inserted verbatim. With ``concept``, the HTML sits in the left
    column and a Key Idea aside fills the right one, the same layout as
    ``prose_tabs`` with a concept (used by generated pages such as ag_pipeline)."""
    content = str(args.get("content", ""))
    if args.get("concept"):
        return C.code_concept_panel(f"{args['id']}-ccp", content, args["concept"],
                                    title=args.get("concept_title", "Key Idea"))
    return content


def _build_topic(args: dict, data: dict) -> str:
    """A demo_panel over a baked topic (thin adapter; content lives in components).

    ``diagram: false`` suppresses the memory diagram for subjects with no
    memory-model picture (operator overloading, classes, templates); default on.

    ``steps`` (optional, per-variant): a dict keyed by variant label; each value is
    ``{caption?, items: [{summary, detail}]}`` rendered as a "steps" diagram (an
    HTML stepper) in the right column, in place of the memory diagram.

    ``diagram_spec`` (optional, per-variant): a dict keyed by variant label; each
    value is a ``{nodes, links, note?}`` box-chain description rendered as a
    ``Structure`` SVG (paired with ``steps`` as diagram sub-tabs when both exist).

    ``aside_html`` (optional, per-variant): a dict keyed by the EXACT variant/tab
    label; each value is raw (unescaped) author HTML rendered in the right
    column of that tab, above the Key Idea aside — which then moves inside the
    tabs (ENGINE_REQUEST_prompt-panel). ``diagram: false`` topics only.

    ``concept_html`` (optional): raw author HTML inside the Key Idea box, below
    its text, e.g. links to diagrams of the example's code.

    ``tab_label``, ``tab_notes``, ``tab_intro`` and ``extra_tabs`` (optional):
    name the compiled tab of a single-variant topic, add a note under a tab's
    console, add a note at the top of a tab, and append tabs of author HTML only (see :func:`components.demo_panel`).
    """
    return C.demo_panel(args["id"], data[args["source"]],
                        diagram=args.get("diagram", True),
                        concept=args.get("concept"),
                        concept_title=args.get("concept_title", "Key Idea"),
                        concept_html=args.get("concept_html", ""),
                        steps=args.get("steps"),
                        diagram_spec=args.get("diagram_spec"),
                        aside_html=args.get("aside_html"),
                        gauge=args.get("gauge", False),
                        console_link=args.get("console_link", False),
                        link_diagram=args.get("link_diagram", False),
                        tab_label=args.get("tab_label"),
                        tab_notes=args.get("tab_notes"),
                        tab_intro=args.get("tab_intro"),
                        extra_tabs=args.get("extra_tabs"))


def _build_replay(args: dict, data: dict) -> str:
    """A replay exhibit: one recorded sequence, step by step (see components.replay_strip).

    ``steps`` is a list of ``{head, tabs: [{label, html}]}``: ``head`` is HTML shown above
    the step's tabs. ``strip_id`` (default ``id``) is the short CSS id of the strip.
    ``step_label`` names the outer tabs ("Iteration" by default). With ``concept``, the
    strip sits in the left column beside a Key Idea, as in ``prose_tabs``.
    """
    steps = [(s.get("head", ""), [(t["label"], t["html"]) for t in s["tabs"]])
             for s in args["steps"]]
    strip = C.replay_strip(args.get("strip_id", args["id"]), steps,
                           step_label=args.get("step_label", "Iteration"))
    if args.get("concept"):
        return C.code_concept_panel(f"{args['id']}-ccp", strip, args["concept"],
                                    title=args.get("concept_title", "Key Idea"))
    return strip


def _build_prose_tabs(args: dict, data: dict) -> str:
    """Tabs of author HTML only, with no compiled program, beside a Key Idea.

    ``panels`` is a list of ``{label, html}``. With ``concept``, the tab strip
    sits in the left column and the Key Idea aside fills the right one, the
    same layout as a ``diagram: false`` topic; without it, just the tabs.
    """
    panels = [(p["label"], p["html"]) for p in args["panels"]]
    tabs = C.variant_tabs(args["id"], panels)
    if args.get("concept"):
        return C.code_concept_panel(f"{args['id']}-ccp", tabs, args["concept"],
                                    title=args.get("concept_title", "Key Idea"))
    return tabs


def _build_concept(args: dict, data: dict) -> str:
    """Build one example's fold-away Concept note from its YAML block.

    Any ``${...}`` references in the block's text have already been filled in
    with real values before this runs.

    Args:
        args: The concept block's fields, already filled in: ``id`` and ``text``,
            plus optional ``label`` (the clickable line), ``open`` (start
            already open) and ``footnote`` (a dim remark below the Key Idea,
            in the same box).
        data: The page's baked data. Not needed here, because the text is already
            filled in; kept so every builder has the same shape.

    Returns:
        The Concept note as a piece of HTML.
    """
    return C.concept_note(args["id"], args["text"],
                          label=args.get("label", "Key Idea"),
                          open_=args.get("open", False),
                          footnote=args.get("footnote", ""))


def _build_glossary_note(args: dict, data: dict) -> str:
    """Build one example's fold-away glossary chip from its YAML block.

    ``args["terms"]`` is a list of ``{term, def}`` maps (already ``${...}``-
    resolved); converted to (term, definition) pairs for the component."""
    terms = [(t["term"], t["def"]) for t in args["terms"]]
    return C.glossary_note(args["id"], terms,
                           label=args.get("label", "Memory glossary"),
                           open_=args.get("open", False))


_BUILDERS = {
    "heading": _build_heading,
    "html": _build_html,
    "topic": _build_topic,
    "prose_tabs": _build_prose_tabs,
    "replay": _build_replay,
    "concept": _build_concept,
    "glossary_note": _build_glossary_note,
}


# ---------------------------------------------------------------------------
# Rendering
# ---------------------------------------------------------------------------


def _render_block(block: dict, data: dict) -> str:
    if len(block) != 1:
        raise ValueError(f"a block must have exactly one key, got {list(block)}")
    (name, raw_args), = block.items()
    args = _resolve(raw_args or {}, data)
    if name in _BUILDERS:
        return _BUILDERS[name](args, data)
    if name not in _DISPATCH:
        raise KeyError(f"unknown block type: {name!r}")
    args = _adapt(name, dict(args))
    cid = args.pop("id")
    return _DISPATCH[name](cid, **args)


def _glossary_from_source(args: dict, base: Path) -> tuple[str, str]:
    """Load a shared ``*.glossary.yaml`` file and render it to HTML.

    Both a layout's ``header:`` and its ``sidebar:`` can name a glossary by
    file (``source:``) rather than writing its terms inline; this is the one
    place that turns such a reference into rendered HTML.

    Args:
        args: The glossary block's arguments. ``source`` (required) is the
            glossary file's path relative to *base*; ``id`` (optional, default
            ``"glossary"``) becomes the section's HTML id.
        base: The folder the layout file lives in, used to resolve ``source``.

    Returns:
        A ``(title, html)`` pair — *title* is the file's ``title:`` (default
        ``"Glossary"``), *html* is the rendered glossary section. Callers that
        need a label (e.g. the sidebar) reuse *title* as the default label.
    """
    g = load_spec(Path(base) / args["source"])
    _check_demo_links(g, str(Path(base) / args["source"]), _demo_names())
    terms = [(t["term"], t["def"]) for t in g.get("terms", [])]
    title = g.get("title", "Glossary")
    html = C.glossary(args.get("id", "glossary"), title, terms)
    return title, html


def _render_header(blocks: list, base_dir: Path) -> str:
    """Render a layout's ``header:`` blocks once.

    A ``glossary`` block with a ``source:`` key loads a shared
    ``*.glossary.yaml`` file (relative to *base_dir*) and renders it; all
    other blocks (color_legend, heading, html, or an inline glossary without
    ``source:``) are dispatched through ``_render_block`` as normal.
    """
    out = []
    for block in blocks or []:
        (name, raw), = block.items()
        args = dict(raw or {})
        if name == "glossary" and "source" in args:
            _, html = _glossary_from_source(args, base_dir)
            out.append(html)
        else:
            out.append(_render_block(block, {}))
    return "\n".join(out)


def render_fragment(spec: dict, data: dict) -> str:
    """Translate *spec*'s blocks to HTML — no page shell. Pure (no g++)."""
    return "\n".join(_render_block(b, data) for b in spec.get("blocks", []))


def render_page(spec: dict, data: dict) -> str:
    """Translate *spec* (with pre-baked *data*) into a self-contained page.

    Pure — no I/O, no g++.  Use :func:`build_page` to bake and write.
    """
    body = render_fragment(spec, data)
    return C.page_shell("page", body, title=spec.get("title", "Topic"))


def load_spec(path: Path | str) -> dict:
    if yaml is None:  # pragma: no cover
        raise RuntimeError("pyyaml not installed — run: pip install pyyaml")
    with open(path, encoding="utf-8") as f:
        return yaml.safe_load(f)


def build_page(spec_path: Path | str, dist_dir: Path) -> Path:
    """Load *spec_path*, bake its topics with g++, render, and write the page.

    Raises ``RuntimeError`` (before baking) if g++ is unavailable.  Returns the
    written file path (``<dist>/<stem>/<stem>.html``, one subdir per page).
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first."
        )
    spec = load_spec(spec_path)
    data = bake_all(spec.get("bake", {}), spec.get("language"))
    page = render_page(spec, data)
    stem = Path(spec_path).stem.replace(".page", "")
    out = Path(dist_dir) / stem / f"{stem}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def _build_sidebar(sidebar: list, base: Path) -> list:
    """Build the page's side-list entries from a layout's ``sidebar:`` list.

    Each item in the list names one kind of entry:

    - ``glossary``: opens a vocabulary file and shows its terms.
    - ``concept``: a short "what this page teaches" note written right there in
      the layout.

    The entries keep the order they were written in, which is the order they
    appear in the side list.

    Args:
        sidebar: The layout's list of side entries. Each entry is a mapping with
            exactly one key naming its kind (``glossary`` or ``concept``).
        base: The folder the layout file lives in, used to find any files a
            ``glossary`` entry points to.

    Returns:
        One ``(label, html)`` pair per side entry, in order.

    Raises:
        ValueError: If an entry has more than one key.
        KeyError: If an entry names a kind other than ``glossary`` or ``concept``.
    """
    items = []
    for entry in sidebar or []:
        if len(entry) != 1:
            raise ValueError(f"a sidebar entry must have exactly one key, got {list(entry)}")
        (kind, a), = entry.items()
        if kind == "glossary":
            title, body = _glossary_from_source(a, base)
            label = a.get("label", title)
        elif kind == "concept":
            label = a.get("label", "Main takeaway")
            # optional `title:` is the heading inside the panel; it defaults to the rail label
            body = C.concept_panel(a.get("id", "concept"), a["text"], title=a.get("title", label))
        else:
            raise KeyError(f"unknown sidebar entry type: {kind!r}")
        items.append((label, body))
    return items


_DEMO_MARKER_RE = re.compile(r"\$\{demo:([A-Za-z0-9_]+)\|")


def _demo_names() -> set[str]:
    """Every demo a ``${demo:...}`` marker may name — one per layout spec."""
    labs = Path(__file__).parents[1]
    return {p.stem[:-len(".rail")] for p in labs.glob("*/layouts/*.rail.yaml")}


def _check_demo_links(spec: Any, source: str, known: set[str]) -> None:
    """Raise if *spec* names a demo that has no layout.

    ``components._demo_links`` is deliberately subject-agnostic — it turns a
    marker into an anchor and has no idea what a demo is. So a typo would
    otherwise ship as a link to a page that does not exist. This is the one
    place that knows the layout set, so it is where the check belongs, and it
    runs before baking so the build fails rather than the reader.
    """
    if isinstance(spec, str):
        for name in _DEMO_MARKER_RE.findall(spec):
            if name not in known:
                raise KeyError(
                    f"{source}: ${{demo:{name}|...}} names no demo — there is no "
                    f"cpp_labs/*/layouts/{name}.rail.yaml. "
                    f"Known demos: {', '.join(sorted(known))}")
    elif isinstance(spec, dict):
        for v in spec.values():
            _check_demo_links(v, source, known)
    elif isinstance(spec, list):
        for v in spec:
            _check_demo_links(v, source, known)


def build_layout(layout_path: "Path | str", dist_dir: Path,
                 home_href: str | None = None) -> Path:
    """Bake+compose a layout spec into one standalone page.

    Writes ``<dist>/<name>.html``, where *name* is the layout stem with a
    trailing ``.rail`` stripped. Flat and unsuffixed, so the built tree has the
    same shape as the published one (``course_site/static/rail/<name>.html``)
    and a link between two demos is the same sibling ``href`` in both. Raises
    before baking if g++ is unavailable.

    *home_href* is passed through to :func:`components.page_shell` to emit a
    return-to-site link; see that docstring for why it is opt-in. For the course
    website, whose rail pages sit one level down at ``<root>/rail/<name>.html``,
    the value is ``"../"`` — relative, so it survives deployment under a path
    segment where a leading-slash href would resolve to the host root.
    """
    if shutil.which("g++") is None:
        raise RuntimeError(
            "g++ not found on PATH. This page bakes real compiler output at "
            "build time; install a C++ compiler first.")
    layout_path = Path(layout_path)
    base = layout_path.parent
    spec = load_spec(layout_path)

    # Check every cross-demo marker on the layout, its glossaries and its topics
    # before anything is compiled: a typo should fail the build, not render as a
    # link to a page that is not there.
    known = _demo_names()
    _check_demo_links(spec, str(layout_path), known)

    style = spec.get("style", "left_rail")

    header_html = _render_header(spec.get("header", []), base)

    # Sidebar entries declared on the layout become leading rail entries (rendered
    # in full as a panel), set apart from the demos by an italic label.
    sidebar_items = _build_sidebar(spec.get("sidebar", []), base)
    items = list(sidebar_items)
    for demo_ref in spec.get("demos", []):
        demo_spec = load_spec(base / demo_ref)
        _check_demo_links(demo_spec, str(base / demo_ref), known)
        data = bake_all(demo_spec.get("bake", {}), demo_spec.get("language"))
        # A topic's `explanation` reaches the page through the registry rather
        # than through load_spec, so the baked entry is where its markers are
        # visible to this check.
        _check_demo_links(data, str(base / demo_ref) + " (baked topic)", known)
        fragment = render_fragment(demo_spec, data)
        items.append((demo_spec.get("title", "Demo"), fragment))

    n = len(sidebar_items)
    nav = C.nav_shell("lab", items, style=style, leading=n,
                      selected=(n if n < len(items) else 0))
    body = f"{header_html}\n{nav}" if header_html else nav
    page = C.page_shell("page", body, title=spec.get("title", "Lab"), highlight=True,
                        tri_link=True, home_href=home_href)

    stem = layout_path.stem
    name = stem[:-len(".rail")] if stem.endswith(".rail") else stem
    out = Path(dist_dir) / f"{name}.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(page, encoding="utf-8")
    return out


def main() -> None:
    if shutil.which("g++") is None:
        print("ERROR: g++ not found on PATH; these pages bake real compiler output.",
              file=sys.stderr)
        sys.exit(1)
    # --home <href> emits a return-to-site link (layout specs only). Kept off by
    # default so a page built for Canvas stays self-contained.
    argv = list(sys.argv[1:])
    home_href = None
    if "--home" in argv:
        i = argv.index("--home")
        if i + 1 >= len(argv):
            print("ERROR: --home needs an href, e.g. --home ../", file=sys.stderr)
            sys.exit(2)
        home_href = argv[i + 1]
        del argv[i:i + 2]
    if not argv:
        print("usage: python -m cpp_labs.yaml_engine.render_page "
              "<page.yaml> [dist_dir] [--home <href>]", file=sys.stderr)
        sys.exit(2)
    spec_path = Path(argv[0])
    dist = Path(argv[1]) if len(argv) > 1 else Path(__file__).parents[2] / "dist_labs"
    spec_probe = load_spec(spec_path)
    out = (build_layout(spec_path, dist, home_href=home_href)
           if "demos" in spec_probe else build_page(spec_path, dist))
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
