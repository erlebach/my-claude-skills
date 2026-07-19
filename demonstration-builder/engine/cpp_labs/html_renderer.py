"""HTML renderer for the C++ Pointer Lab static build.

Pure functions — no I/O, no compilation. All take plain dicts/lists and return
HTML strings. Tests can call these without invoking g++.
"""

from __future__ import annotations

import html as _html
import math
import re
import warnings
from typing import Any


# ---------------------------------------------------------------------------
# Semantic per-role color palette — single source of truth (WCAG AA)
# ---------------------------------------------------------------------------
#
# These five role tokens are the one contrast-vetted color language shared by
# prose, code, and the inline SVG diagrams.  Each value is >=4.5:1 against the
# white page background (--bg: #ffffff), so it is safe as a foreground color.
# The same hex values are emitted as `:root` CSS custom properties (--c-<role>)
# *and* used directly in the SVG palette, so a "blue address" in the code is a
# "blue box" in the diagram.  Color is always paired with text/border/icon —
# never the sole signal (WCAG 1.4.1).
SEMANTIC_PALETTE: dict[str, str] = {
    "addr": "#0b5394",   # blue   — addresses / pointer boxes
    "val": "#0b7d3e",    # green  — stored values
    "type": "#6b3fa0",   # purple — type names
    "const": "#9a6700",  # amber  — const / immutable
    "err": "#b00020",    # red    — errors / compile failures
    "link": "#7c3aed",   # violet — link-highlight affordance (hover/focus lights
                         #          code<->console<->box). NOT a diagram semantic:
                         #          kept distinct from val-green so a lit box is
                         #          never confused with an `hl` (acted-on) node.
}


# ---------------------------------------------------------------------------
# SVG geometry constants — vertical layout (tall + narrow); box font matches code panel
# ---------------------------------------------------------------------------

_BOX_FILL = "#e8f0ff"
_BOX_STROKE = SEMANTIC_PALETTE["addr"]
_ARROW_COLOR = SEMANTIC_PALETTE["addr"]
_NULL_COLOR = "#8b0000"
_LABEL_COLOR = "#1a1a1a"
_DIM_COLOR = "#555555"
_SHARED_COUNT_COLOR = "#4a7c20"
_LIVE_COLOR = SEMANTIC_PALETTE["val"]   # green — the dispatch path that actually runs
_REV_COLOR  = "#cc6600"                 # amber-orange — reverse/prev arrows; 6.4:1 vs white (WCAG AA)

# Vertical-layout geometry (tall + narrow). Box text is 14px to match the code panel.
_FONT = 14           # px, == code panel font-size (ui-monospace)
_LH = 22             # text line height within a box
_BOX_TOP_PAD = 20    # box top padding to first text baseline
_SVG_TEXT_ASCENDER = 4  # SVG <text> y is the baseline; add this to reach the visual top of glyphs
_TEXT_MID_DY = 5     # baseline nudge to vertically center 14px text in a box (~0.35*font)
_PAD = 16            # outer padding / gap between boxes
_SRC_W1 = 160        # source/target box width when a single source
_SRC_W2 = 120        # source box width when two sources sit side-by-side
_ARROW_GAP = 60      # vertical gap reserved for the arrow between rows
_STACK_RM = 34       # right margin channel for >=3 stacked-source arrows
_BOX_GAP = 12  # inter-box vertical gap in the stacked column
# Every box-chain node is this fixed width, so nodes are identical across all
# examples and all demos (the diagram panel is a constant size). The viewBox only
# grows past this when a note/label is wider (then the diagram scrolls); node
# boxes themselves never change width. Chosen to fill the ~393px diagram column
# at natural (1:1) scale so the 14px font is identical in every box-chain.
_BOXCHAIN_NODE_W = 340

# --- branching-diagram (tree / bucket) fixed geometry ---------------------
# Like the box-chain node width, these are UNIFORM across every demo so one edit
# restyles every tree/bucket across the curriculum. Nodes are a fixed size; the
# viewBox is driven by STRUCTURE (tree breadth/depth, bucket count/chain length),
# never by label length — a too-long label scrolls, it never widens the diagram.
_TREE_NODE_W = 96    # wider to fit "key → value" labels
_TREE_NODE_H = 44
_TREE_ROW_H = 84     # vertical pitch between tree depths
_TREE_COL_W = 112    # horizontal pitch between in-order columns
_BUCKET_SLOT_W = 54  # the [n] slot box
_BUCKET_ENTRY_W = 100
_BUCKET_BOX_H = 36
_BUCKET_ROW_H = 50   # vertical pitch between buckets
_BUCKET_GAP = 22     # horizontal gap (room for the chain connector)

_SET_BOX_W = 48      # set element box (disconnected — no connectors)
_SET_BOX_H = 44
_SET_GAP = 16        # gap between disconnected set elements
_SET_BRACE_W = 22    # width reserved for each set brace { }


_NODE_VALUE_RE = re.compile(r"-?\d+")


def _node_key(nd: dict) -> str | None:
    """The tri-link value key for a box: explicit ``key`` wins, else the first
    integer in the label. Returns ``None`` when neither exists (no key emitted)."""
    if nd.get("key"):
        return f"v{nd['key']}"
    m = _NODE_VALUE_RE.search(nd.get("label", ""))
    return f"v{m.group(0)}" if m else None


def _e(s: Any) -> str:
    """HTML-escape a value; return '?' for None/missing."""
    if s is None:
        return "?"
    return _html.escape(str(s))


# ---------------------------------------------------------------------------
# SVG building helpers
# ---------------------------------------------------------------------------


def _text(x: int, y: int, txt: str, color: str = _LABEL_COLOR, size: int = 14) -> str:
    return (
        f'<text x="{x}" y="{y}" font-size="{size}" '
        f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
    )


def _marker_defs(marker_id: str, color: str) -> str:
    """A reusable arrowhead <marker>. `orient="auto-start-reverse"` rotates it to
    the line direction, so vertical / diagonal / curved arrows all get a correct
    head. Fill is fixed per-diagram (one arrow color per diagram)."""
    return (
        f'<defs><marker id="{marker_id}" viewBox="0 0 10 10" refX="9" refY="5" '
        f'markerWidth="7" markerHeight="7" orient="auto-start-reverse">'
        f'<path d="M0,0 L10,5 L0,10 z" fill="{color}"/></marker></defs>'
    )


def _arrow_v(x1: int, y1: int, x2: int, y2: int, color: str, marker_id: str) -> str:
    """A straight arrow from (x1,y1) to (x2,y2) with a marker arrowhead.
    Endpoints are honored as given, so vertical and diagonal arrows are supported."""
    return (
        f'<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" '
        f'stroke-width="3" marker-end="url(#{marker_id})"/>'
    )


def _vbox(x: int, y: int, w: int, lines: list[tuple[str, str]], stroke: str,
          stroke_width: int = 2, rx: int = 8) -> tuple[str, int]:
    """Draw a box at (x,y) with stacked text `lines` (each a (text, color)
    pair). Height scales with the number of lines. Text is 14px monospace to
    match the code panel. `stroke_width` thickens the border for an emphasised
    (highlighted) box. `rx` is the corner radius — pass ``rx=0`` for square
    corners so consecutive contiguous cells abut into one block. Returns
    (svg, height)."""
    h = _BOX_TOP_PAD + len(lines) * _LH
    parts = [
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{_BOX_FILL}" stroke="{stroke}" stroke-width="{stroke_width}"/>'
    ]
    ty = y + _BOX_TOP_PAD + _SVG_TEXT_ASCENDER
    for txt, color in lines:
        parts.append(
            f'<text x="{x + 14}" y="{ty}" font-size="{_FONT}" '
            f'font-family="ui-monospace,monospace" fill="{color}">{_e(txt)}</text>'
        )
        ty += _LH
    return "".join(parts), h


def _stack_svg(p: str, title: str, desc: str,
               sources: list[dict], target: "dict | None",
               *, arrow_color: str = _ARROW_COLOR) -> str:
    """Vertical memory diagram. `sources`/`target` are box specs
    ({"lines": [(text,color)...], "stroke": color}). Encodes the source-count
    rule: <=2 sources sit side-by-side and converge onto the target; >=3 stack
    in a column with arrows routed down the right. `target=None` draws no arrow
    (e.g. weak_ptr)."""
    n = len(sources)
    marker_id = f"{p}-ah"
    body = _marker_defs(marker_id, arrow_color) if target is not None else ""

    if n >= 3:
        # Stacked column; arrows route down a right-side channel into the target.
        ws = _SRC_W1
        x = _PAD
        y = _PAD
        right_edges = []
        for s in sources:
            svg, h = _vbox(x, y, ws, s["lines"], s["stroke"])
            body += svg
            right_edges.append((x + ws, y + h // 2))
            y += h + _BOX_GAP
        chan = x + ws + _STACK_RM // 2
        ty = y - _BOX_GAP + _ARROW_GAP
        tsvg, th = _vbox(x, ty, ws, target["lines"], target["stroke"]) if target else ("", 0)
        body += tsvg
        if target is not None:
            for ex, ey in right_edges:
                body += (
                    f'<path d="M{ex} {ey} H{chan} V{ty + th // 2} H{x + ws}" '
                    f'fill="none" stroke="{arrow_color}" stroke-width="3" '
                    f'marker-end="url(#{marker_id})"/>'
                )
        vb_w = ws + 2 * _PAD + _STACK_RM
        vb_h = ty + th + _PAD if target else y - _BOX_GAP + _PAD
        return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)

    # n <= 2: converge. Sources in a top row, target centered below.
    sw = _SRC_W1 if n == 1 else _SRC_W2
    tw = _SRC_W1
    row_w = n * sw + (n - 1) * _PAD
    vb_w = max(row_w + 2 * _PAD, tw + 2 * _PAD)
    start_x = (vb_w - row_w) // 2
    src_y = _PAD
    src_h = 0
    bottoms = []
    for i, s in enumerate(sources):
        bx = start_x + i * (sw + _PAD)
        svg, h = _vbox(bx, src_y, sw, s["lines"], s["stroke"])
        body += svg
        src_h = max(src_h, h)
        bottoms.append((bx + sw // 2, src_y + h))

    if target is None:
        vb_h = src_y + src_h + _PAD
        return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)

    tgt_y = src_y + src_h + _ARROW_GAP
    tgt_x = (vb_w - tw) // 2
    tsvg, th = _vbox(tgt_x, tgt_y, tw, target["lines"], target["stroke"])
    body += tsvg
    tip_x = vb_w // 2
    for bx, by in bottoms:
        body += _arrow_v(bx, by, tip_x, tgt_y, arrow_color, marker_id)
    if n == 1:
        _, src_bottom = bottoms[0]
        body += (
            f'<text x="{tip_x + 8}" y="{(src_bottom + tgt_y) // 2}" font-size="13" '
            f'fill="{_DIM_COLOR}">points to</text>'
        )
    vb_h = tgt_y + th + _PAD
    return _wrap_svg(p, title, desc, body, vb_w=vb_w, vb_h=vb_h)


def _wrap_svg(p: str, title_text: str, desc_text: str, body: str,
              *, vb_w: int = 500, vb_h: int = 160, fill_width: bool = False,
              natural: bool = False) -> str:
    """Wrap *body* in an accessible SVG shell. `p` is the unique id prefix.
    `vb_w`/`vb_h` set the viewBox. Default sizing is `width:{vb_w}px; max-width:100%;
    height:auto`: the box renders at its intrinsic width (14 user-units ≈ 14px,
    matching the code panel), capped to 100% of its container so it scales *down*
    in a narrow column — right for the fixed-scale pointer/memory diagrams.

    `fill_width=True` uses `width:100%` instead, so the SVG scales UP to fill its
    column (right for a chart, which has no natural pixel size). This is safe with
    the current `zoomable`, which scales the content IN PLACE (normal flow, keeps
    its column width) — the old fit-content overlay that collapsed a percentage
    width is gone, so there is no definite-basis problem anymore.

    `natural=True` renders at exactly `width:{vb_w}px` with NO `max-width` cap, so
    the SVG NEVER scales down — its font stays a constant 14px regardless of the
    column width. Used for box-chains (whose node width is fixed, so they fit the
    column at 1:1); the caller wraps them in an `overflow-x:auto` container so an
    over-wide one scrolls instead of shrinking the font."""
    title_id = f"{p}-title"
    desc_id = f"{p}-desc"
    if fill_width:
        size_css = "width:100%;max-width:100%"
    elif natural:
        size_css = f"width:{vb_w}px"          # intrinsic size, never scaled down
    else:
        size_css = f"width:{vb_w}px;max-width:100%"
    return (
        f'<svg viewBox="0 0 {vb_w} {vb_h}" role="img" '
        f'aria-labelledby="{title_id} {desc_id}" '
        f'style="{size_css};height:auto;background:#fff;'
        f'border:1px solid #c5cee0;border-radius:8px">'
        f'<title id="{title_id}">{_e(title_text)}</title>'
        f'<desc id="{desc_id}">{_e(desc_text)}</desc>'
        f'{body}'
        f'</svg>'
    )


# ---------------------------------------------------------------------------
# Six diagram renderers (port of the six _draw_* methods in app_base.py)
# ---------------------------------------------------------------------------


def _svg_raw(pd: dict, p: str) -> str:
    addr, tgt, val = pd.get("ptr_addr", "?"), pd.get("target_addr", "?"), pd.get("target_val", "?")
    src = {"lines": [("ptr", _LABEL_COLOR), (str(addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "raw pointer diagram",
                      f"ptr at {_e(addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_null(pd: dict, p: str) -> str:
    addr = pd.get("ptr_addr", "0x0")
    src = {"lines": [("ptr", _LABEL_COLOR), (str(addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [("NULL", _NULL_COLOR)], "stroke": _NULL_COLOR}
    return _stack_svg(p, "null pointer diagram", f"ptr at {_e(addr)} points to NULL.",
                      [src], dst, arrow_color=_NULL_COLOR)


def _svg_ref(pd: dict, p: str) -> str:
    ref_addr, tgt, val = pd.get("ref_addr", "?"), pd.get("target_addr", "?"), pd.get("target_val", "?")
    src = {"lines": [("ref", _LABEL_COLOR), (str(ref_addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "reference diagram",
                      f"ref at {_e(ref_addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_unique(pd: dict, p: str) -> str:
    ptr_addr, tgt, val = pd.get("ptr_addr", "?"), pd.get("target_addr", "?"), pd.get("val", "?")
    is_null = pd.get("is_null", "0") == "1"
    src = {"lines": [("unique_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)], "stroke": _BOX_STROKE}
    if is_null:
        dst = {"lines": [("NULL", _NULL_COLOR)], "stroke": _NULL_COLOR}
        return _stack_svg(p, "unique_ptr diagram", f"unique_ptr at {_e(ptr_addr)} → NULL.",
                          [src], dst, arrow_color=_NULL_COLOR)
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "unique_ptr diagram",
                      f"unique_ptr at {_e(ptr_addr)} → val={_e(val)} at {_e(tgt)}.", [src], dst)


def _svg_shared(pd: dict, p: str) -> str:
    ptr_addr, ptr2_addr = pd.get("ptr_addr", "?"), pd.get("ptr2_addr")
    tgt, val, use_count = pd.get("target_addr", "?"), pd.get("val", "?"), pd.get("use_count", "?")
    if ptr2_addr:
        sources = [
            {"lines": [("sp1", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)], "stroke": _BOX_STROKE},
            {"lines": [("sp2", _LABEL_COLOR), (str(ptr2_addr), _DIM_COLOR)], "stroke": _BOX_STROKE},
        ]
    else:
        sources = [{"lines": [("shared_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR)],
                    "stroke": _BOX_STROKE}]
    dst = {"lines": [(f"val={val}", _LABEL_COLOR), (str(tgt), _DIM_COLOR),
                     (f"use_count={use_count}", _SHARED_COUNT_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "shared_ptr diagram",
                      f"shared_ptr at {_e(ptr_addr)} → val={_e(val)}, use_count={_e(use_count)}.",
                      sources, dst)


def _svg_weak(pd: dict, p: str) -> str:
    ptr_addr, expired, use_count = pd.get("ptr_addr", "?"), pd.get("expired", "?"), pd.get("use_count", "?")
    src = {"lines": [("weak_ptr", _LABEL_COLOR), (str(ptr_addr), _DIM_COLOR),
                     (f"expired={expired}", _LABEL_COLOR),
                     (f"use_count={use_count}", _SHARED_COUNT_COLOR)], "stroke": _BOX_STROKE}
    return _stack_svg(p, "weak_ptr diagram",
                      f"weak_ptr at {_e(ptr_addr)}, expired={_e(expired)}, use_count={_e(use_count)}.",
                      [src], None)


def _svg_boxchain(spec: "dict | None", p: str, link_values: bool = False) -> str:
    """Render a declarative vertical box-chain diagram.

    `spec` is a dict: ``nodes`` (each ``{id, label, rows?}``), ``links``
    (each ``{from, to, label?, live?}``), and an optional ``note``. Boxes are
    stacked top->bottom in ``nodes`` order and connected by downward arrows;
    a ``live`` link is drawn in the accent color. Width auto-sizes to the widest
    line (box rows, note, and link labels) so text never clips. All visual style comes from the module-level
    constants, so one edit restyles every box-chain diagram."""
    spec = spec or {}
    nodes = spec.get("nodes", [])
    links = spec.get("links", [])
    note = spec.get("note")
    has_rev = any(lk.get("rev") for lk in links)

    if link_values:
        seen_keys: dict[str, int] = {}
        for _nd in nodes:
            if _nd.get("kind") == "label":
                continue
            _k = _node_key(_nd)
            if _k:
                seen_keys[_k] = seen_keys.get(_k, 0) + 1
        _dupes = [k for k, n in seen_keys.items() if n > 1]
        if _dupes:
            warnings.warn(
                f"tri-link: ambiguous duplicate box value(s) {_dupes} in {p} — "
                f"add an explicit `key:` to disambiguate.", stacklevel=2)
    _FWD_X = 10   # px offset from center so forward/backward arrows don't overlap

    char_w = 8.5          # ~advance of one 14px ui-monospace glyph
    min_w = _SRC_W1       # 160; never narrower than the memory boxes
    marker_id = f"{p}-ah"
    marker_live = f"{p}-ahL"
    marker_rev = f"{p}-ahR"

    # 1. width = widest single line across all boxes (label + rows), padded.
    def _lines(nd):
        return [nd.get("label", "")] + list(nd.get("rows", []) or [])
    longest = 0
    for nd in nodes:
        for ln in _lines(nd):
            longest = max(longest, len(ln))
    # Link labels are drawn beside the arrows; include them so the viewBox is wide
    # enough. The NOTE is NOT included — it is pulled out of the SVG and rendered as
    # a wrapping HTML caption below (so a long note never widens the diagram; every
    # box-chain stays the fixed node width, mirroring stepped_boxchain's caption).
    for lk in links:
        if lk.get("label"):
            longest = max(longest, len(lk["label"]))
    # Node boxes are a FIXED width (uniform across every example and demo). The
    # viewBox extends past it only if a node/link line is wider (rare — then it
    # scrolls); `min_w` floors it so a lone long line never clips.
    w = _BOXCHAIN_NODE_W
    content_w = max(min_w, int(longest * char_w) + 2 * _PAD)

    def _render_node(nd, bx, by):
        """Render one box at (bx, by); return (svg, height). Handles dim/hl styling,
        contig square corners, and the tri-link cll-node wrapper. Shared by the main
        vertical stack and the right-hand `aside` column."""
        dim = nd.get("dim")
        label_color = _DIM_COLOR if dim else _LABEL_COLOR
        lines = [(nd.get("label", ""), label_color)]
        for r in (nd.get("rows") or []):
            lines.append((r, _DIM_COLOR))
        # `hl: true` marks the node this step acts on — accent border, drawn thicker.
        if nd.get("hl"):
            stroke, sw = _LIVE_COLOR, 3
        elif dim:
            stroke, sw = _DIM_COLOR, 2
        else:
            stroke, sw = _BOX_STROKE, 2
        svg, h = _vbox(bx, by, w, lines, stroke, stroke_width=sw,
                       rx=0 if nd.get("contig") else 8)
        key = _node_key(nd) if link_values else None
        if key:
            # A focusable, named group so the tri-link handler can light this box
            # and keyboard users can reach it. Highlight is a stroke change, not colour.
            aria = _e(" ".join(
                nd.get("label", "").replace("node:", "list node").split()))
            svg = (f'<g class="cll-node" data-cll="{_e(key)}" tabindex="0" '
                   f'role="img" aria-label="{aria}">{svg}</g>')
        return svg, h

    # 2. stack boxes top->bottom, remembering each box's y-range and center-x.
    body = _marker_defs(marker_id, _ARROW_COLOR) + _marker_defs(marker_live, _LIVE_COLOR)
    if has_rev:
        body += _marker_defs(marker_rev, _REV_COLOR)
    x = _PAD
    cx = x + w // 2
    y = _PAD
    geom = {}   # id -> (top, bottom)
    for idx, nd in enumerate(nodes):
        # `aside: true` — a detached node (e.g. a just-unlinked list node) is not
        # part of the chain. It is rendered separately (below the caption) by
        # stepped_boxchain, so the chain SVG stays narrow; here it is skipped.
        if nd.get("aside"):
            continue
        # A `kind: label` node is a group header (e.g. "list a") — bold text with a
        # rule, no box, no ports; links never attach to it. It lets ONE diagram show
        # two lists (source + destination) stacked as labelled groups, e.g. splice.
        if nd.get("kind") == "label":
            body += (
                f'<text x="{x}" y="{y + _FONT}" font-size="14" '
                f'font-family="system-ui" font-weight="700" '
                f'fill="{_LABEL_COLOR}">{_e(nd.get("label", ""))}</text>'
                f'<line x1="{x}" y1="{y + _LH + 2}" x2="{x + w}" y2="{y + _LH + 2}" '
                f'stroke="{_BOX_STROKE}" stroke-width="1"/>'
            )
            h = _LH + 6
            geom[nd.get("id", "")] = (y, y + h)
            y += h + _BOX_GAP
            continue
        # `dim: true` fades a box (grey border + grey text) for a node that is
        # deliberately NOT part of the action — e.g. the EXCLUDED `last` boundary of
        # a half-open splice range, which stays put while the range moves.
        # `contig: true` models contiguous memory (e.g. a vector's slots): between
        # two consecutive contig cells there is zero gap, so they abut into one block
        # (a shared divider), unlike gap-and-arrow-separated list nodes.
        svg, h = _render_node(nd, x, y)
        body += svg
        geom[nd.get("id")] = (y, y + h)
        nxt = nodes[idx + 1] if idx + 1 < len(nodes) else None
        if nd.get("contig") and nxt and nxt.get("contig"):
            y += h                         # contiguous cells share an edge (no gap)
        else:
            y += h + _ARROW_GAP
    bottom_y = max(_PAD * 2, y - _ARROW_GAP + _PAD)   # last box bottom + padding; clamp so empty specs stay valid

    # 3. arrows between linked boxes (downward); live link uses the accent marker.
    #    When any link is bidirectional (rev:true), forward arrows shift right by
    #    _FWD_X and a reverse (prev) arrow is drawn left by _FWD_X so they don't overlap.
    for lk in links:
        a, b = geom.get(lk.get("from")), geom.get(lk.get("to"))
        if not a or not b:
            continue
        fwd_x = cx + (_FWD_X if has_rev else 0)
        color = _LIVE_COLOR if lk.get("live") else _ARROW_COLOR
        mid = marker_live if lk.get("live") else marker_id
        body += _arrow_v(fwd_x, a[1], fwd_x, b[0], color, mid)
        if lk.get("label"):
            body += _text(_PAD, (a[1] + b[0]) // 2, lk["label"], _DIM_COLOR, 13)
        if lk.get("rev"):
            rev_x = cx - _FWD_X
            body += _arrow_v(rev_x, b[0], rev_x, a[1], _REV_COLOR, marker_rev)

    # viewBox is the fixed node column, widened only if a node/link line needs it.
    vb_h = bottom_y
    vb_w = max(w + 2 * _PAD, content_w)
    svg = _wrap_svg(p, "box-chain diagram",
                    "A vertical chain of boxes connected by arrows.", body,
                    vb_w=vb_w, vb_h=vb_h, natural=True)
    # natural size => constant 14px font; scroll (not shrink) if a line is wider
    # than the column. The note is a wrapping HTML caption BELOW the SVG, so its
    # length never changes the diagram width — every box-chain is the same size.
    note_html = f'<p class="dia-note">{_e(note)}</p>' if note else ""
    return f'<div class="dia-scroll">{svg}</div>{note_html}'


def _centered_box(x: int, y: int, w: int, h: int, label: str, stroke: str) -> str:
    """A fixed-size rounded box with a single 14px label centered both ways.
    Shared by _svg_tree, _svg_buckets, and _svg_set (small nodes read better centered than
    _vbox's left-aligned text). Fill/stroke come from the shared palette, so one
    edit restyles every tree/bucket node."""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="8" '
        f'fill="{_BOX_FILL}" stroke="{stroke}" stroke-width="2"/>'
        f'<text x="{x + w // 2}" y="{y + h // 2 + _TEXT_MID_DY}" font-size="{_FONT}" '
        f'font-family="ui-monospace,monospace" text-anchor="middle" '
        f'fill="{_LABEL_COLOR}">{_e(label)}</text>'
    )


def _svg_tree(spec: "dict | None", p: str) -> str:
    """Render a declarative binary-tree diagram (map / set). `spec` keys:
    ``nodes`` (each {id, label, left?, right?, root?}) and an optional ``note``.
    A node's x is its IN-ORDER-traversal column and y is its depth, so the picture
    reads left-to-right in sorted key order; edges are plain diagonal lines (a tree
    edge is not a directional pointer). Fixed node size + `natural=True` sizing =>
    a constant 14px font, mirroring _svg_boxchain. The note is an HTML `.dia-note`
    caption (never SVG text), so its length never widens the diagram."""
    spec = spec or {}
    nodes = spec.get("nodes", [])
    note = spec.get("note")
    by_id = {nd["id"]: nd for nd in nodes}
    root_id = next((nd["id"] for nd in nodes if nd.get("root")),
                   nodes[0]["id"] if nodes else None)
    order: list[str] = []
    depth: dict[str, int] = {}
    seen: set[str] = set()

    def walk(nid, d):
        if nid is None or nid not in by_id:
            return
        if nid in seen:
            raise ValueError(
                f"_svg_tree: node {nid!r} is reachable twice — cyclic or shared "
                f"child reference in the tree spec")
        seen.add(nid)
        nd = by_id[nid]
        walk(nd.get("left"), d + 1)
        depth[nid] = d
        order.append(nid)
        walk(nd.get("right"), d + 1)

    walk(root_id, 0)
    col = {nid: i for i, nid in enumerate(order)}
    max_depth = max(depth.values(), default=0)

    def left_x(nid):
        return _PAD + col[nid] * _TREE_COL_W

    def cx(nid):
        return left_x(nid) + _TREE_NODE_W // 2

    def top_y(nid):
        return _PAD + depth[nid] * _TREE_ROW_H

    body = ""
    # edges first so nodes overlay them
    for nid in order:
        nd = by_id[nid]
        for child in (nd.get("left"), nd.get("right")):
            if child in depth:
                body += (
                    f'<line x1="{cx(nid)}" y1="{top_y(nid) + _TREE_NODE_H}" '
                    f'x2="{cx(child)}" y2="{top_y(child)}" '
                    f'stroke="{_BOX_STROKE}" stroke-width="2"/>'
                )
    # nodes (root in the accent color, like the box-chain live path)
    for nid in order:
        nd = by_id[nid]
        stroke = _LIVE_COLOR if nd.get("root") else _BOX_STROKE
        body += _centered_box(left_x(nid), top_y(nid), _TREE_NODE_W, _TREE_NODE_H,
                              nd.get("label", ""), stroke)
    vb_w = _PAD * 2 + max(1, len(order)) * _TREE_COL_W
    vb_h = _PAD * 2 + max_depth * _TREE_ROW_H + _TREE_NODE_H
    svg = _wrap_svg(p, "binary-tree diagram",
                    "An ordered binary tree; in-order traversal visits keys in sorted order.",
                    body, vb_w=vb_w, vb_h=vb_h, natural=True)
    note_html = f'<p class="dia-note">{_e(note)}</p>' if note else ""
    return f'<div class="dia-scroll">{svg}</div>{note_html}'


def _svg_buckets(spec: "dict | None", p: str) -> str:
    """Render a declarative hash-bucket diagram (unordered_map). `spec` keys:
    ``buckets`` (ordered; each {slot, entries}) and an optional ``note``. Buckets
    stack vertically; each bucket's `entries` list lays out horizontally as a
    collision chain joined by short connectors (a bucket IS a list — one entry is
    a singleton, many is a chain). Empty buckets show a dim ∅. Fixed sizes +
    `natural=True` => constant 14px font, mirroring _svg_boxchain."""
    spec = spec or {}
    buckets = spec.get("buckets", [])
    note = spec.get("note")
    body = ""
    max_chain = 0
    for i, b in enumerate(buckets):
        entries = b.get("entries") or []
        max_chain = max(max_chain, len(entries))
        y = _PAD + i * _BUCKET_ROW_H
        body += _centered_box(_PAD, y, _BUCKET_SLOT_W, _BUCKET_BOX_H,
                              f"[{b.get('slot', i)}]", _BOX_STROKE)
        if not entries:
            body += _text(_PAD + _BUCKET_SLOT_W + _BUCKET_GAP,
                          y + _BUCKET_BOX_H // 2 + _TEXT_MID_DY, "∅", _DIM_COLOR)
            continue
        prev_right = _PAD + _BUCKET_SLOT_W
        cy = y + _BUCKET_BOX_H // 2
        for entry in entries:
            ex = prev_right + _BUCKET_GAP
            body += (f'<line x1="{prev_right}" y1="{cy}" x2="{ex}" y2="{cy}" '
                     f'stroke="{_BOX_STROKE}" stroke-width="2"/>')
            body += _centered_box(ex, y, _BUCKET_ENTRY_W, _BUCKET_BOX_H,
                                  str(entry), _BOX_STROKE)
            prev_right = ex + _BUCKET_ENTRY_W
    vb_w = _PAD * 2 + _BUCKET_SLOT_W + max(1, max_chain) * (_BUCKET_GAP + _BUCKET_ENTRY_W)
    vb_h = _PAD * 2 + max(0, len(buckets) - 1) * _BUCKET_ROW_H + _BUCKET_BOX_H
    svg = _wrap_svg(p, "hash-bucket diagram",
                    "A hash table bucket array; each key lands in a bucket by its hash.",
                    body, vb_w=vb_w, vb_h=vb_h, natural=True)
    note_html = f'<p class="dia-note">{_e(note)}</p>' if note else ""
    return f'<div class="dia-scroll">{svg}</div>{note_html}'


def _svg_set(spec: "dict | None", p: str) -> str:
    """Render a std::set as a DISCONNECTED sorted collection: unique elements as
    separate boxes (NO edges) in sorted order, wrapped in set braces { }. Any
    ``rejected`` duplicates are drawn dimmed and struck-through below the row. This
    foregrounds the SET ABSTRACTION (unique + sorted, no hierarchy) rather than the
    red-black-tree implementation (that story is map's). Fixed sizes + `natural=True`
    => constant 14px font; the note is a `.dia-note` HTML caption, so its length
    never widens the diagram."""
    spec = spec or {}
    elements = spec.get("elements", [])
    rejected = spec.get("rejected") or []
    note = spec.get("note")
    n = len(elements)
    x0 = _PAD + _SET_BRACE_W                        # first element x (after '{')
    y = _PAD
    cy = y + _SET_BOX_H // 2
    brace_y = cy + 11                               # baseline for the 34px braces
    body = (f'<text x="{_PAD}" y="{brace_y}" font-size="34" '
            f'font-family="ui-monospace,monospace" fill="{_LABEL_COLOR}">{{</text>')
    for i, el in enumerate(elements):
        ex = x0 + i * (_SET_BOX_W + _SET_GAP)
        body += _centered_box(ex, y, _SET_BOX_W, _SET_BOX_H, str(el), _BOX_STROKE)
    last_right = x0 + (max(1, n) - 1) * (_SET_BOX_W + _SET_GAP) + _SET_BOX_W
    close_x = last_right + _SET_GAP // 2
    body += (f'<text x="{close_x}" y="{brace_y}" font-size="34" '
             f'font-family="ui-monospace,monospace" fill="{_LABEL_COLOR}">}}</text>')
    vb_h = _PAD * 2 + _SET_BOX_H
    if rejected:
        ry = y + _SET_BOX_H + _SET_GAP
        for i, el in enumerate(rejected):
            rx = x0 + i * (_SET_BOX_W + _SET_GAP)
            box = _centered_box(rx, ry, _SET_BOX_W, _SET_BOX_H, str(el), _DIM_COLOR)
            strike = (f'<line x1="{rx + 7}" y1="{ry + _SET_BOX_H // 2}" '
                      f'x2="{rx + _SET_BOX_W - 7}" y2="{ry + _SET_BOX_H // 2}" '
                      f'stroke="{_DIM_COLOR}" stroke-width="2"/>')
            body += f'<g opacity="0.45">{box}{strike}</g>'
        vb_h = _PAD * 2 + _SET_BOX_H + _SET_GAP + _SET_BOX_H
    vb_w = close_x + _SET_BRACE_W + _PAD
    svg = _wrap_svg(p, "set diagram",
                    "A set drawn as a sorted collection of unique elements, with no hierarchy between them.",
                    body, vb_w=vb_w, vb_h=vb_h, natural=True)
    note_html = f'<p class="dia-note">{_e(note)}</p>' if note else ""
    return f'<div class="dia-scroll">{svg}</div>{note_html}'


def _pc_scale(v: float, lo: float, hi: float, scale: str) -> float:
    """Map value v in [lo,hi] to a 0..1 fraction under 'linear' or 'log'."""
    if scale == "log":
        lo = max(lo, 1e-9)
        v = max(v, lo)
        return (math.log10(v) - math.log10(lo)) / (math.log10(hi) - math.log10(lo) or 1.0)
    return (v - lo) / ((hi - lo) or 1.0)


_SUPERSCRIPT = str.maketrans("0123456789-", "⁰¹²³⁴⁵⁶⁷⁸⁹⁻")


def _pow10_label(v: float) -> str:
    """Consistent axis-tick label. Exact powers of ten render as ``10ⁿ`` (short
    and unambiguous on a log axis, no mixed 1e+08/100000 clutter); any non-power
    fallback value uses compact ``{:g}``."""
    if v > 0:
        e = round(math.log10(v))
        if abs(v - 10.0 ** e) <= 1e-6 * v:
            return "10" + str(e).translate(_SUPERSCRIPT)
    return f"{v:g}"


def _nice_ticks(lo: float, hi: float) -> list[float]:
    """Decade axis-tick values: every power of ten within ``[lo, hi]``. Suits a
    LOG axis over positive data (the bubble-vs-quicksort log-log consumer) and is
    labelled ``10ⁿ`` by :func:`_pow10_label`. Positions are recomputed per-scale
    by the renderer/JS from each tick's raw value.

    Pure decades avoid the collide-and-mixed-format clutter of also plotting the
    raw data min/max as ticks. If fewer than two decades fall in range (a
    sub-decade span), fall back to the endpoints so the axis still shows two
    labels. A linear-scale line chart would get sparse/geometric ticks -- make
    this helper scale-aware before authoring a linear-axis line consumer.
    Degenerate lo==hi -> a single tick."""
    if hi <= lo:
        return [lo]
    decades: list[float] = []
    p = 10.0 ** math.floor(math.log10(lo)) if lo > 0 else 1.0
    while p <= hi * (1 + 1e-9):
        if p >= lo * (1 - 1e-9):
            decades.append(p)
        p *= 10.0
    return decades if len(decades) >= 2 else [lo, hi]


def _svg_perf_chart(spec: dict, points: list[dict], p: str) -> str:
    """Vertical themed bar chart. Bars carry raw data-y + data-cll for the
    y-axis toggle (Task 6) and console-hover (existing _CLL_JS)."""
    mode = spec.get("mode", "bar")
    if mode in ("line", "scatter"):
        return _svg_perf_line(spec, points, p, connect=(mode == "line"))
    y_scale = (spec.get("y") or {}).get("scale", "linear")
    y_label = (spec.get("y") or {}).get("label", "")
    plot_top, plot_bot, plot_left = 24, 240, 54
    bar_w, gap = 64, 56
    ys = [pt["y"] for pt in points] or [1.0]
    # linear bars start at 0; log bars start at 1 (10^0) so a bar's height is
    # proportional to its order of magnitude and the smallest bar stays visible
    # instead of collapsing to the floor (which happens if the baseline == min).
    lo = 0.0 if y_scale == "linear" else 1.0
    hi = max(ys)
    vb_w = plot_left + len(points) * (bar_w + gap) + 16
    body = [
        f'<line x1="{plot_left}" y1="{plot_top}" x2="{plot_left}" y2="{plot_bot}" stroke="var(--border)"/>',
        f'<line x1="{plot_left}" y1="{plot_bot}" x2="{vb_w-6}" y2="{plot_bot}" stroke="var(--border)"/>',
        f'<text x="6" y="{plot_top+8}" class="pc-axis">{_e(y_label)}</text>',
    ]
    x = plot_left + gap
    for pt in points:
        frac = _pc_scale(pt["y"], lo, hi, y_scale)
        h = max(2, round(frac * (plot_bot - plot_top)))
        y0 = plot_bot - h
        key = pt.get("cll", "")
        attr = f' data-cll="{_e(key)}"' if key else ""
        body.append(
            f'<rect class="pc-bar" data-y="{pt["y"]}" data-raw="{_e(pt["raw"])}"'
            f'{attr} x="{x}" y="{y0}" width="{bar_w}" height="{h}"'
            f'><title>{_e(pt["raw"])}</title></rect>'
        )
        body.append(
            f'<text class="pc-cat" x="{x+bar_w/2:.0f}" y="{plot_bot+20}" '
            f'text-anchor="middle">{_e(pt.get("label",""))}</text>'
        )
        x += bar_w + gap
    # Hover readout: filled by the _CLL_JS mouseover handler with the hovered
    # bar's verbatim console substring (data-raw). Rendered last (on top).
    body.append(
        f'<text class="pc-tip" x="{vb_w/2:.0f}" y="16" text-anchor="middle"></text>'
    )
    svg = (
        f'<g data-pc data-pc-scale="{y_scale}">' + "".join(body) + "</g>"
    )
    return _wrap_svg(p, "perf chart",
                     f"bar chart of measured values; y-axis {y_scale} scale",
                     svg, vb_w=vb_w, vb_h=plot_bot + 30, fill_width=True)


def _svg_perf_line(spec: dict, points: list[dict], p: str, *, connect: bool) -> str:
    """Multi-series line/scatter chart. Each series is one polyline (+ markers);
    scatter omits the connector. Both axes map through _pc_scale; the chart <g>
    carries plot geometry as data-* so the _CLL_JS toggle recomputes coordinates
    client-side (R1). Markers carry data-x/data-y/data-raw/data-cll for hover
    (reused console-link handler)."""
    x_scale = (spec.get("x") or {}).get("scale", "linear")
    y_scale = (spec.get("y") or {}).get("scale", "linear")
    x_label = (spec.get("x") or {}).get("label", "")
    y_label = (spec.get("y") or {}).get("label", "")
    L, R, T, B = 56, 404, 24, 240          # plot box: left, right, top, bottom
    xs = [pt["x"] for pt in points] or [0.0, 1.0]
    ys = [pt["y"] for pt in points] or [0.0, 1.0]

    def _rng(vals, scale):
        hi = max(vals)
        if scale == "log":
            pos = [v for v in vals if v > 0]
            lo = min(pos) if pos else 1.0
            return lo, max(hi, lo * 10)   # keep hi > lo > 0 so log10 is safe
        return min(vals), hi

    xlo, xhi = _rng(xs, x_scale)
    ylo, yhi = _rng(ys, y_scale)

    def _px(x):
        return L + _pc_scale(x, xlo, xhi, x_scale) * (R - L)

    def _py(y):
        return B - _pc_scale(y, ylo, yhi, y_scale) * (B - T)

    order: list[str] = []
    series: dict[str, list[dict]] = {}
    for pt in points:
        s = pt.get("series", "")
        if s not in series:
            series[s] = []
            order.append(s)
        series[s].append(pt)

    xticks = _nice_ticks(xlo, xhi)
    yticks = _nice_ticks(ylo, yhi)
    body = []
    # Gridlines first, so they sit behind the axes, curves, and markers. Each
    # carries its raw data value so the _CLL_JS toggle repositions it in step
    # with the ticks/markers (R1).
    for tx in xticks:
        gx = _px(tx)
        body.append(
            f'<line class="pc-grid pc-xgrid" data-x="{tx}" x1="{gx:.1f}" y1="{T}" '
            f'x2="{gx:.1f}" y2="{B}" stroke="var(--border)" stroke-opacity="0.5" '
            f'stroke-dasharray="3 3"/>')
    for ty in yticks:
        gy = _py(ty)
        body.append(
            f'<line class="pc-grid pc-ygrid" data-y="{ty}" x1="{L}" y1="{gy:.1f}" '
            f'x2="{R}" y2="{gy:.1f}" stroke="var(--border)" stroke-opacity="0.5" '
            f'stroke-dasharray="3 3"/>')
    body += [
        f'<line x1="{L}" y1="{T}" x2="{L}" y2="{B}" stroke="var(--border)"/>',
        f'<line x1="{L}" y1="{B}" x2="{R}" y2="{B}" stroke="var(--border)"/>',
        f'<text x="6" y="14" class="pc-axis">{_e(y_label)}</text>',
        f'<text x="{R}" y="{B+30}" text-anchor="end" class="pc-axis">{_e(x_label)}</text>',
    ]
    for tx in xticks:
        body.append(
            f'<text class="pc-tick pc-xtick" data-x="{tx}" x="{_px(tx):.1f}" '
            f'y="{B+16}" text-anchor="middle">{_pow10_label(tx)}</text>')
    for ty in yticks:
        body.append(
            f'<text class="pc-tick pc-ytick" data-y="{ty}" x="{L-6}" '
            f'y="{_py(ty):.1f}" dominant-baseline="middle" '
            f'text-anchor="end">{_pow10_label(ty)}</text>')

    for i, s in enumerate(order):
        color = _FRAME_STROKES[i % len(_FRAME_STROKES)]
        pts = series[s]
        if connect and len(pts) > 1:
            coords = " ".join(f"{_px(pt['x']):.1f},{_py(pt['y']):.1f}" for pt in pts)
            body.append(
                f'<polyline class="pc-line" data-series="{_e(s)}" points="{coords}" '
                f'fill="none" stroke="{color}" stroke-width="2"/>')
        for pt in pts:
            key = pt.get("cll", "")
            attr = f' data-cll="{_e(key)}"' if key else ""
            body.append(
                f'<circle class="pc-pt" data-series="{_e(s)}" data-x="{pt["x"]}" '
                f'data-y="{pt["y"]}" data-raw="{_e(pt["raw"])}"{attr} '
                f'cx="{_px(pt["x"]):.1f}" cy="{_py(pt["y"]):.1f}" r="4" '
                f'fill="{color}"><title>{_e(pt["raw"])}</title></circle>')

    if len(order) > 1:
        ly = T + 4
        for i, s in enumerate(order):
            color = _FRAME_STROKES[i % len(_FRAME_STROKES)]
            body.append(
                f'<rect class="pc-legend" x="{R-90}" y="{ly}" width="10" height="10" '
                f'fill="{color}"/>'
                f'<text class="pc-legend" x="{R-76}" y="{ly+9}">{_e(s)}</text>')
            ly += 16

    body.append(
        f'<text class="pc-tip" x="{(L+R)//2}" y="16" text-anchor="middle"></text>')

    svg = (
        f'<g data-pc data-pc-xscale="{x_scale}" data-pc-yscale="{y_scale}" '
        f'data-l="{L}" data-r="{R}" data-t="{T}" data-b="{B}">'
        + "".join(body) + "</g>"
    )
    return _wrap_svg(p, "perf chart",
                     f"line chart of measured (x, y) pairs; "
                     f"x-axis {x_scale}, y-axis {y_scale} scale",
                     svg, vb_w=R + 16, vb_h=B + 36, fill_width=True)


def _svg_unknown(pd: dict, p: str) -> str:
    # No box structure to stack; use _wrap_svg directly with a minimal fallback label.
    ptype = pd.get("type", "?") if pd else "?"
    body = _text(16, 40, f"type={_e(ptype)} — no diagram", _DIM_COLOR, 13)
    return _wrap_svg(p, f"diagram ({_e(ptype)})", "No diagram available.", body,
                     vb_w=220, vb_h=80)


# ---------------------------------------------------------------------------
# Stack-frame diagram family (type=frames) and process memory map (type=memmap)
# ---------------------------------------------------------------------------

_FRAME_STROKES = ["#cc6666", "#9966cc", "#6699cc", "#22aa88", "#cc8844", "#6688aa"]
_ADDR_AXIS = "#2a7f54"      # green: addresses increase upward (AA: 4.9:1 vs white)
_STACK_AXIS = "#cc6600"     # orange: stack grows downward
_SCHEM_COLOR = "#999999"    # grey: schematic (computed, not measured)


def _parse_frames(pd: dict) -> "tuple[int, list[dict]]":
    """Parse a frames ptrdata dict into (ptrbytes, frames). Each frame is
    ``{name, addr, local, bytes, pbytes}`` outermost->innermost. Missing pieces
    degrade to ``"?"`` / ``0`` (never raises)."""
    try:
        ptrbytes = int(pd.get("ptrbytes", "8"))
    except (TypeError, ValueError):
        ptrbytes = 8
    frames = []
    for entry in (pd.get("live", "") or "").split(","):
        if not entry:
            continue
        parts = entry.split(":")

        def _get(i):
            return parts[i] if i < len(parts) else "?"

        def _int(i):
            try:
                return int(parts[i])
            except (IndexError, ValueError):
                return 0

        frames.append({"name": _get(0), "addr": _get(1), "local": _get(2),
                       "bytes": _int(3), "pbytes": _int(4)})
    return ptrbytes, frames


def _frames_core(frames: list, p: str, *, solid: "int | None" = None) -> str:
    """Vertical stack of call frames. Outermost (e.g. main) on top at the
    highest address; each deeper call a box below at a lower address; SP marker
    on the innermost *solid* frame. Frames at index >= ``solid`` are drawn ghost
    (dashed) -- used by the stepper to show a reclaimed frame after a return.
    Dual axis: addresses increase upward (green), stack grows downward
    (orange)."""
    if solid is None:
        solid = len(frames)
    box_w, box_h, gap, pad, left = 210, 54, 10, 12, 58
    n = len(frames)
    vb_w = left + box_w + pad + 44
    vb_h = pad + n * (box_h + gap) + pad + 4
    parts = []
    # address axis (up, green) on the far left
    axis_top, axis_bot = pad + 6, vb_h - pad
    parts.append(
        f'<line x1="{left - 40}" y1="{axis_bot}" x2="{left - 40}" y2="{axis_top}" '
        f'stroke="{_ADDR_AXIS}" stroke-width="2"/>'
        f'<path d="M{left - 44} {axis_top + 8} L{left - 40} {axis_top} '
        f'L{left - 36} {axis_top + 8} z" fill="{_ADDR_AXIS}"/>'
        f'<text x="{left - 48}" y="{(axis_top + axis_bot) // 2}" font-size="11" '
        f'fill="{_ADDR_AXIS}" text-anchor="middle" '
        f'transform="rotate(-90 {left - 48} {(axis_top + axis_bot) // 2})">'
        f'addresses increase</text>'
    )
    # stack-growth axis (down, orange) on the far right
    rx = vb_w - 12
    parts.append(
        f'<line x1="{rx}" y1="{axis_top}" x2="{rx}" y2="{axis_bot}" '
        f'stroke="{_STACK_AXIS}" stroke-width="2"/>'
        f'<path d="M{rx - 4} {axis_bot - 8} L{rx} {axis_bot} L{rx + 4} '
        f'{axis_bot - 8} z" fill="{_STACK_AXIS}"/>'
        f'<text x="{rx + 4}" y="{(axis_top + axis_bot) // 2}" font-size="11" '
        f'fill="{_STACK_AXIS}" text-anchor="middle" '
        f'transform="rotate(90 {rx + 4} {(axis_top + axis_bot) // 2})">'
        f'stack grows</text>'
    )
    y = pad
    for i, f in enumerate(frames):
        ghost = i >= solid
        stroke = _SCHEM_COLOR if ghost else _FRAME_STROKES[i % len(_FRAME_STROKES)]
        dash = ' stroke-dasharray="5 4"' if ghost else ""
        fill = "#f7f7f7" if ghost else "#ffffff"
        parts.append(
            f'<rect x="{left}" y="{y}" width="{box_w}" height="{box_h}" rx="8" '
            f'fill="{fill}" stroke="{stroke}" stroke-width="2"{dash}/>'
        )
        is_sp = (not ghost) and (i == solid - 1)
        title = f'{_e(f["name"])}()' + ("  &#8592; SP" if is_sp else "")
        if ghost:
            parts.append(
                f'<text x="{left + 14}" y="{y + 31}" font-size="12" '
                f'font-family="ui-monospace,monospace" fill="{_SCHEM_COLOR}">'
                f'{_e(f["name"])}() reclaimed on return</text>'
            )
        else:
            parts.append(
                f'<text x="{left + 14}" y="{y + 22}" font-size="13" '
                f'font-family="system-ui" font-weight="600" fill="#1a1a1a">'
                f'{title}</text>'
                f'<text x="{left + 14}" y="{y + 42}" font-size="12" '
                f'font-family="ui-monospace,monospace" fill="#b00000">'
                f'&amp;{_e(f["local"])} = {_e(f["addr"])}</text>'
            )
        y += box_h + gap
    body = "".join(parts)
    return _wrap_svg(
        p, "call stack frames",
        "Stack frames, main on top at the highest address; deeper calls at "
        "lower addresses. Addresses increase upward; the stack grows downward.",
        body, vb_w=vb_w, vb_h=vb_h)


def _svg_frames(pd: dict, p: str) -> str:
    """Single-snapshot dispatch entry for ``type=frames``."""
    _pb, frames = _parse_frames(pd)
    return _frames_core(frames, p)


def _svg_frames_anatomy(pd: dict, p: str) -> str:
    """Expanded per-frame anatomy: a three-column table (slot · address · size)
    for every live frame. The local's row is the real measured address (red);
    params / return-addr / saved-FP rows carry schematic addresses (grey)
    computed by stacking the known slot sizes above the measured local. Only
    the local address is measured; the rest are illustrative."""
    ptrbytes, frames = _parse_frames(pd)
    row_h, hdr_h, frame_gap, pad, left = 18, 16, 10, 12, 40
    col_addr, col_size = 190, 290
    parts = [
        f'<text x="{left}" y="{pad + 10}" font-size="9" fill="#999">slot</text>'
        f'<text x="{col_addr}" y="{pad + 10}" font-size="9" fill="#999">address</text>'
        f'<text x="{col_size}" y="{pad + 10}" font-size="9" fill="#999">size</text>'
    ]
    y = pad + hdr_h
    for i, f in enumerate(frames):
        # slots high->low: [param?], return address, saved FP, local
        try:
            base = int(f["addr"], 16)
        except (ValueError, TypeError):
            base = None
        rows = []  # (label, addr_or_None, bytes, measured)
        savedfp = (base + f["bytes"]) if base is not None else None
        retaddr = (savedfp + ptrbytes) if savedfp is not None else None
        param = (retaddr + ptrbytes) if (retaddr is not None and f["pbytes"]) else None
        if f["pbytes"]:
            rows.append((f'parameter: {f["pbytes"]}B', param, f["pbytes"], False))
        rows.append(("return address", retaddr, ptrbytes, False))
        rows.append(("saved frame ptr", savedfp, ptrbytes, False))
        rows.append((f'local: {f["local"]}', base, f["bytes"], True))
        fh = hdr_h // 2 + len(rows) * row_h + 6
        stroke = _FRAME_STROKES[i % len(_FRAME_STROKES)]
        parts.append(
            f'<rect x="{left - 8}" y="{y - 12}" width="{col_size + 40}" '
            f'height="{fh}" rx="6" fill="#ffffff" stroke="{stroke}" '
            f'stroke-width="2"/>'
            f'<text x="{left}" y="{y + 2}" font-size="12" font-weight="600" '
            f'fill="#1a1a1a">{_e(f["name"])}()</text>'
        )
        ry = y + row_h
        for label, addr, nbytes, measured in rows:
            addr_s = f"0x{addr:x}" if addr is not None else "?"
            acol = "#b00000" if measured else _SCHEM_COLOR
            parts.append(
                f'<text x="{left}" y="{ry}" font-size="11" '
                f'fill="#333">{_e(label)}</text>'
                f'<text x="{col_addr}" y="{ry}" font-size="10" '
                f'font-family="ui-monospace,monospace" fill="{acol}">{addr_s}</text>'
                f'<text x="{col_size}" y="{ry}" font-size="10" '
                f'font-family="ui-monospace,monospace" fill="#0066cc">'
                f'{nbytes} B</text>'
            )
            ry += row_h
        y = ry + frame_gap
    vb_w = col_size + 72
    vb_h = y + pad
    return _wrap_svg(p, "full frame anatomy",
                     "Each frame's slots with byte sizes and addresses; only "
                     "the local address is measured, the rest are schematic.",
                     "".join(parts), vb_w=vb_w, vb_h=vb_h)


_MEMMAP_ORDER = ["stack", "heap", "bss", "data", "text"]   # high -> low address
_MEMMAP_LABEL = {
    "stack": "params, auto variables",
    "heap": "dynamic variables",
    "bss": "uninitialized global/static",
    "data": "initialized global/static",
    "text": "machine instructions",
}
_MEMMAP_FILL = {
    "stack": "#d6e8f5", "heap": "#e7e0f2", "bss": "#f0e6d0",
    "data": "#e0e8d0", "text": "#f5d6d6",
}


def _svg_memmap(pd: dict, p: str) -> str:
    """Whole-process memory map: text (low) -> stack (high), heap grows up and
    stack grows down toward each other. One real address per region."""
    regions = {}
    for entry in (pd.get("regions", "") or "").split(","):
        if not entry:
            continue
        parts = entry.split(":")
        key = parts[0]
        regions[key] = {"addr": parts[1] if len(parts) > 1 else "?",
                        "label": parts[2] if len(parts) > 2 else ""}
    box_w, box_h, gap, pad, left = 210, 46, 8, 26, 30
    vb_w = left + box_w + 130
    vb_h = pad + len(_MEMMAP_ORDER) * (box_h + gap) + pad
    parts = [f'<text x="{left + box_w // 2}" y="14" font-size="11" fill="#555" '
             f'text-anchor="middle">high memory</text>']
    y = pad
    for key in _MEMMAP_ORDER:
        r = regions.get(key, {"addr": "?", "label": _MEMMAP_LABEL.get(key, "")})
        fill = _MEMMAP_FILL.get(key, "#ffffff")
        parts.append(
            f'<rect x="{left}" y="{y}" width="{box_w}" height="{box_h}" rx="6" '
            f'fill="{fill}" stroke="#888" stroke-width="1.5"/>'
            f'<text x="{left + 12}" y="{y + 20}" font-size="12" font-weight="600" '
            f'fill="#1a1a1a">{_e(key)}</text>'
            f'<text x="{left + 12}" y="{y + 38}" font-size="10" '
            f'font-family="ui-monospace,monospace" fill="#b00000">'
            f'{_e(r["addr"])}</text>'
            f'<text x="{left + box_w + 8}" y="{y + 26}" font-size="10" '
            f'fill="#666">{_e(_MEMMAP_LABEL.get(key, ""))}</text>'
        )
        y += box_h + gap
    parts.append(f'<text x="{left + box_w // 2}" y="{vb_h - 8}" font-size="11" '
                 f'fill="#555" text-anchor="middle">low memory</text>')
    return _wrap_svg(p, "process memory map",
                     "Process regions from text (low) to stack (high); heap "
                     "grows up and the stack grows down.",
                     "".join(parts), vb_w=vb_w, vb_h=vb_h)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------


def svg_renderer(ptrdata: dict[str, Any] | None, svg_id: str = "d") -> str:
    """Return an inline SVG string for one pointer-data snapshot.

    *svg_id* is used as a prefix for the ``<title id>`` and ``<desc id>``
    attributes so that multiple SVGs in the same document have unique ids.
    Pass a unique string per variant (e.g. ``f"{topic_id}-v{i}"``).

    Dispatches on ``ptrdata["type"]``.  Missing keys degrade to ``"?"`` rather
    than raising.  Returns an accessible SVG with ``role="img"``,
    ``<title>``, and ``<desc>`` elements.
    """
    if not ptrdata:
        return _svg_unknown({}, svg_id)
    ptr_type = ptrdata.get("type")
    dispatch = {
        "raw": _svg_raw,
        "null": _svg_null,
        "ref": _svg_ref,
        "unique": _svg_unique,
        "shared": _svg_shared,
        "weak": _svg_weak,
        "frames": _svg_frames,
        "memmap": _svg_memmap,
    }
    fn = dispatch.get(ptr_type)
    if fn:
        return fn(ptrdata, svg_id)
    return _svg_unknown(ptrdata, svg_id)


# ---------------------------------------------------------------------------
# CSS for the WCAG AA theme (inlined by assemble_page)
# ---------------------------------------------------------------------------

_CSS = """
:root {
  --fg:        #1a1a1a;
  --fg-dim:    #555555;
  --bg:        #ffffff;
  --panel-bg:  #f6f8fc;
  --border:    #4a4a4a;
  --accent:    #0b5394;
  --accent-fg: #ffffff;
  --code-bg:   #1d2433;
  --code-fg:   #e8edf6;
  --ok:        #0a6b2e;
  /*SEMANTIC_TOKENS*/
}
* { box-sizing: border-box; }
body {
  font-size: 16px; line-height: 1.5;
  font-family: -apple-system, "Segoe UI", system-ui, sans-serif;
  color: var(--fg); background: var(--bg);
  margin: 0; padding: 0;
}
/* legacy DPG-style lab shell: lock to viewport, panels scroll internally.
   Document pages (page_shell) opt OUT by not carrying the class. */
body.lab-shell { height: 100vh; overflow: hidden; display: flex; flex-direction: column; }
:focus-visible { outline: 3px solid var(--accent); outline-offset: 2px; }
.skip {
  position: absolute; left: -9999px; top: 0;
  background: var(--accent); color: var(--accent-fg);
  padding: .4rem .8rem; z-index: 10; border-radius: 0 0 6px 0;
}
.skip:focus { left: 0; }
header { padding: .5rem 1rem; border-bottom: 3px solid var(--accent); flex-shrink: 0; }
header h1 { margin: 0; font-size: 1.2rem; }
/* topic-nav: zero-JS tab bar using radio + CSS sibling */
.vtopic {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
.topic-nav {
  display: flex; flex-wrap: wrap; gap: .3rem;
  padding: .4rem .8rem; background: var(--panel-bg);
  border-bottom: 2px solid var(--border); flex-shrink: 0;
}
.topic-nav label {
  display: inline-flex; align-items: center;
  min-height: 44px; padding: .3rem .9rem;
  border: 2px solid var(--border); border-radius: 6px;
  background: var(--bg); cursor: pointer;
  font-size: 14px; font-weight: 700;
}
.topic-nav label:hover { background: #e2e9f5; }
/* lab-content fills remaining viewport height */
.lab-content { flex: 1 1 0; overflow: hidden; }
/* all topic panels hidden by default; shown by :checked sibling rule */
.topic-panel { display: none; height: 100%; }
/* topic explanation compact header */
.topic-header { padding: .3rem .8rem; }
.topic-header h2 { font-size: 1rem; margin: 0 0 .2rem; }
.explanation {
  border-left: 4px solid var(--accent); background: var(--panel-bg);
  padding: .4rem .8rem; border-radius: 0 4px 4px 0; font-size: .9rem;
}
/* variant tab controls */
.vradio {
  position: absolute; width: 1px; height: 1px;
  overflow: hidden; clip: rect(0 0 0 0); white-space: nowrap;
}
.tabs { display: flex; gap: .4rem; flex-wrap: wrap; margin-bottom: -1px; padding: .3rem .8rem 0; }
.tabs label {
  display: inline-flex; align-items: center;
  min-height: 44px; min-width: 44px; padding: .4rem .9rem;
  border: 2px solid var(--border); border-bottom: none;
  border-radius: 8px 8px 0 0; background: var(--panel-bg);
  cursor: pointer; font-size: 15px; font-weight: 700; font-family: ui-monospace, monospace;
}
.tabs label:hover { background: #e2e9f5; }
/* panels area fills remaining height in topic-panel */
.panels {
  border: 2px solid var(--border); border-radius: 0 8px 8px 8px;
  background: var(--bg); margin: 0 .8rem;
  flex: 1 1 0; min-height: 0; overflow: hidden;
  display: flex; flex-direction: column;
}
.panel { display: none; flex: 1 1 0; min-height: 0; overflow-y: auto; }
/* multi-case: each stacked sub-case keeps a usable height; .panel scrolls */
.case { margin-bottom: 1rem; }
.case:last-child { margin-bottom: 0; }
.case-label { font-size: 1rem; margin: .2rem 0 .5rem; }
.case .panel-grid { height: auto; }
.case .diagram-col figure { flex: 0 0 auto; min-height: 200px; }
/* panel-grid: left = scrolling code col, right = flex diagram col */
.panel-grid {
  display: grid; grid-template-columns: 1fr 1fr; gap: 1rem;
  height: 100%; padding: .8rem;
}
@media (max-width: 760px) { .panel-grid { grid-template-columns: 1fr; } }
.code-col { overflow-y: auto; }
.diagram-col { display: flex; flex-direction: column; }
h3 { font-size: .95rem; margin: 0 0 .3rem; }
pre {
  background: var(--code-bg); color: var(--code-fg);
  padding: .7rem .9rem; border-radius: 8px;
  /* soft-wrap long lines so the full code is always visible (no horizontal
     scroll); preserves indentation via pre-wrap. */
  white-space: pre-wrap; overflow-wrap: anywhere;
  font: 14px/1.5 ui-monospace, "SF Mono", Menlo, monospace; margin: 0;
}
.out {
  background: var(--panel-bg); border: 1px solid #c5cee0;
  border-radius: 8px; padding: .6rem .9rem;
  font: 14px/1.5 ui-monospace, monospace; white-space: pre-wrap;
}
.out .ok { color: var(--ok); font-weight: 700; }
.out .err { color: #8b0000; font-weight: 700; }
.out--err { border: 2px solid #c20000; background: #fff5f5; }
details { margin-top: .5rem; }
summary { cursor: pointer; font-weight: 600; min-height: 44px; padding: .3rem 0; }
/* per-example Concept: a button-like chip with a rotating caret so it clearly
   reads as pressable. Native details/summary — zero-JS, keyboard + SR. */
details.concept > summary {
  display: inline-flex; align-items: center; gap: .5rem; width: fit-content;
  min-height: 44px; padding: .3rem .9rem;
  border: 2px solid var(--accent); border-radius: 8px;
  background: var(--panel-bg); color: var(--accent); font-weight: 700;
  cursor: pointer; list-style: none;
}
details.concept > summary::-webkit-details-marker { display: none; }
details.concept > summary:hover { background: #e2e9f5; }
details.concept > summary .caret { font-size: .96em; transition: transform .15s ease; }
details.concept[open] > summary .caret { transform: rotate(90deg); }
@media (prefers-reduced-motion: reduce) {
  details.concept > summary .caret { transition: none; }
}
/* Two chips on one row: a Concept chip immediately followed by an inline
   glossary chip both go inline-block; a lone Concept chip is unaffected. The
   horizontal gap is set by the glossary chip's own inline left margin (an inline
   style attribute outranks this stylesheet, so the gap can't live here). */
details.concept.chip-inline,
details.concept:has(+ details.concept.chip-inline) {
  display: inline-block; vertical-align: top;
}
figure { margin: 0; flex: 1 1 0; min-height: 0; display: flex; flex-direction: column; }
figcaption { color: var(--fg-dim); font-size: .85rem; margin-top: .3rem; flex-shrink: 0; }
.pc-bar { fill: var(--accent); }
.pc-bar:hover { fill: var(--accent); stroke: var(--fg); stroke-width: 2; }
.pc-cat, .pc-axis { fill: var(--fg-dim); font-size: 10px; }
.pc-tip { fill: var(--fg); font-size: 11px; font-weight: 700; }
.pc-fig { margin: 0; }
.pc-toggle { display: flex; gap: 6px; justify-content: center; margin: 4px 0; }
.pc-toggle button[aria-pressed="true"], .pc-toggle button:focus { outline: 2px solid var(--accent); }
"""


def _semantic_token_lines() -> str:
    """Render the semantic palette as `:root` custom-property declarations."""
    return "\n  ".join(f"--c-{role}: {hexv};" for role, hexv in SEMANTIC_PALETTE.items())


# Inject the single-source palette into the theme `:root` so the CSS tokens and
# the SVG palette can never drift (both read from SEMANTIC_PALETTE).
_CSS = _CSS.replace("/*SEMANTIC_TOKENS*/", _semantic_token_lines())


def _css_checked_rules(tid: str, variant_ids: list[str]) -> str:
    """Generate the :checked-based tab/panel show rules for one topic."""
    lines = []
    for vid in variant_ids:
        lines.append(
            f'#{vid}:checked ~ .tabs label[for="{vid}"] '
            f'{{ background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }}'
        )
    for vid in variant_ids:
        lines.append(
            f'#{vid}:focus-visible ~ .tabs label[for="{vid}"] '
            f'{{ outline: 3px solid var(--accent); outline-offset: 2px; }}'
        )
    for vid in variant_ids:
        panel_id = f"{tid}-panel-{vid.replace(tid + '-', '', 1)}"
        lines.append(
            f'#{vid}:checked ~ .panels #{panel_id} {{ display: block; }}'
        )
    return "\n".join(lines)


def render_fragment(topic: Any, variants: list[dict[str, Any]]) -> str:
    """Return a self-contained ``<section>`` for *topic* with all *variants*.

    Each variant dict carries ``{"label", "svg", "source", "stdout",
    "membytes", "failed", "stderr"}``.

    When exactly one variant is supplied, no radio controls are emitted.
    Every ``id``, radio ``name``, and CSS selector is namespaced by
    ``topic.id``.  The first variant is ``checked``.
    """
    tid = topic.id
    name = _html.escape(topic.name)
    explanation = _html.escape(topic.explanation)

    if len(variants) == 1:
        return _render_single_variant(tid, name, explanation, variants[0])

    def _vid(i: int, label: str) -> str:
        # Slug must be a valid CSS identifier: ids are referenced in
        # unescaped `#id:checked ~ ...` selectors, where raw '(', ')', ','
        # are parse errors that silently kill the variant-switching rule.
        safe = label.strip().replace("/", "_").replace("*", "ptr")
        safe = "".join(c if (c.isalnum() or c in "_-") else "_" for c in safe)
        return f"{tid}-v{i}-{safe}"

    vids = [_vid(i, v["label"]) for i, v in enumerate(variants)]
    css_rules = _css_checked_rules(tid, vids)

    radios = ""
    for i, (vid, _v) in enumerate(zip(vids, variants)):
        checked = " checked" if i == 0 else ""
        radios += (
            f'<input class="vradio" type="radio" '
            f'name="{tid}-type" id="{vid}"{checked}>\n'
        )

    tab_labels = ""
    for vid, v in zip(vids, variants):
        tab_labels += f'<label for="{vid}">{_html.escape(v["label"])}</label>\n'

    panels = ""
    for i, (vid, v) in enumerate(zip(vids, variants)):
        suffix = vid[len(tid) + 1:]
        panel_id = f"{tid}-panel-{suffix}"
        # Each SVG in the document needs a unique id prefix
        svg_id_prefix = f"{tid}-svg-v{i}"
        panels += (
            f'<section class="panel" id="{panel_id}" '
            f'aria-label="{_html.escape(v["label"])} variant">\n'
            + _panel_body(v, svg_id_prefix)
            + "</section>\n"
        )

    return (
        f'<style>\n{css_rules}\n</style>\n'
        f'<section class="topic" id="{tid}" style="display:flex;flex-direction:column;height:100%">\n'
        f'<div class="topic-header">\n'
        f'<h2>{name}</h2>\n'
        f'<div class="explanation">{explanation}</div>\n'
        f'</div>\n'
        + radios
        + f'<div class="tabs" role="group" aria-label="Choose variant">\n{tab_labels}</div>\n'
        + f'<div class="panels">\n{panels}</div>\n'
        + f'</section>\n'
    )


def _render_single_variant(tid: str, name: str, explanation: str, v: dict) -> str:
    return (
        f'<section class="topic" id="{tid}" style="display:flex;flex-direction:column;height:100%">\n'
        f'<div class="topic-header">\n'
        f'<h2>{name}</h2>\n'
        f'<div class="explanation">{explanation}</div>\n'
        f'</div>\n'
        + _panel_body(v, f"{tid}-svg")
        + f'</section>\n'
    )


def _panel_body(v: dict, svg_id_prefix: str = "d") -> str:
    # Multi-case variant: render each independently-compiled sub-case under
    # its own labelled block, with a unique svg-id prefix per case.
    cases = v.get("cases")
    if cases:
        blocks = ""
        for j, case in enumerate(cases):
            blocks += (
                f'<div class="case">\n'
                f'<h3 class="case-label">{_html.escape(case.get("label", ""))}</h3>\n'
                + _case_block(case, f"{svg_id_prefix}-c{j}")
                + '</div>\n'
            )
        return blocks
    return _case_block(v, svg_id_prefix)


def _case_block(v: dict, svg_id_prefix: str = "d") -> str:
    source = _html.escape(v.get("source", ""))
    stdout = v.get("stdout", "")
    stderr = v.get("stderr", "")
    membytes = v.get("membytes", "n/a")
    failed = v.get("failed", False)

    # Re-render SVG with a unique per-variant prefix to avoid duplicate ids
    # when multiple variants appear in one document.  Fall back to the
    # pre-rendered svg field if ptrdata is not stored.  When there is no
    # pointer data (compile failure, or a topic with no diagram), leave the
    # diagram column empty rather than drawing a "no diagram" placeholder.
    ptrdata = v.get("ptrdata")
    no_diagram = "ptrdata" in v and not ptrdata
    if no_diagram:
        diagram_col = '<div class="diagram-col diagram-col--empty"></div>\n'
    else:
        if "ptrdata" in v:
            svg = svg_renderer(ptrdata, svg_id_prefix)
        else:
            svg = v.get("svg") or svg_renderer(None, svg_id_prefix)
        diagram_col = (
            f'<div class="diagram-col">\n'
            f'<h3>Memory diagram</h3>\n'
            f'<figure>\n'
            f'{svg}\n'
            f'<figcaption>Addresses are real output from a 64-bit build; frozen here for stable study.</figcaption>\n'
            f'</figure>\n'
            f'</div>\n'
        )

    if failed:
        out_html = (
            f'<div class="out out--err">'
            f'<span class="err">Compile failed.</span><br>'
            f'<pre style="margin-top:.5rem"><samp>{_html.escape(stderr)}</samp></pre>'
            f'</div>'
        )
    else:
        out_html = (
            f'<div class="out">'
            f'<span class="ok">Compiled and ran successfully.</span><br>'
            f'{_html.escape(stdout)}'
        )
        if membytes and membytes != "n/a":
            out_html += (
                f'<details><summary>Raw bytes of <code>ptr</code> (8 bytes)</summary>'
                f'<code>{_html.escape(membytes)}</code> &mdash; little-endian'
                f'</details>'
            )
        out_html += '</div>'

    return (
        f'<div class="panel-grid">\n'
        f'<div class="code-col">\n'
        f'<h3>Generated code</h3>\n'
        f'<pre><code>{source}</code></pre>\n'
        f'<h3 style="margin-top:.8rem">Program output</h3>\n'
        f'{out_html}\n'
        f'</div>\n'
        f'{diagram_col}'
        f'</div>\n'
    )


def _topic_nav_css(topics: list[tuple[str, str]]) -> str:
    """Generate per-topic :checked rules for topic-level tab switching."""
    lines = []
    for tid, _name in topics:
        lines.append(
            f'#t-{tid}:checked ~ .topic-nav label[for="t-{tid}"] '
            f'{{ background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }}'
        )
    for tid, _name in topics:
        lines.append(
            f'#t-{tid}:checked ~ .lab-content #tp-{tid} {{ display: flex; flex-direction: column; }}'
        )
    return "\n".join(lines)


def assemble_page(
    fragments: list[str],
    title: str = "C++ Pointer Lab",
    topics: list[tuple[str, str]] | None = None,
) -> str:
    """Wrap *fragments* into a complete WCAG AA HTML document.

    All CSS is inlined.  No external scripts, stylesheets, or network
    resources are referenced.

    *topics* is an optional list of ``(id, name)`` tuples.  When two or more
    entries are supplied, a zero-JS topic-navigation tab bar is generated and
    each fragment is wrapped in a ``<div id="tp-{id}" class="topic-panel">``.
    When ``topics`` is ``None`` or has fewer than 2 entries the output is
    identical to the old single-page layout (backward compatible).
    """
    use_topic_nav = topics is not None and len(topics) >= 2

    if use_topic_nav:
        # Topic radio inputs — first children of <body> so CSS sibling combinator
        # can reach both .topic-nav and .lab-content that follow.
        topic_radios = ""
        for i, (tid, _name) in enumerate(topics):
            checked = " checked" if i == 0 else ""
            topic_radios += (
                f'<input class="vtopic" type="radio" '
                f'name="topic-sel" id="t-{tid}" aria-hidden="true"{checked}>\n'
            )

        nav_labels = ""
        for tid, name in topics:
            nav_labels += f'<label for="t-{tid}">{_html.escape(name)}</label>\n'
        topic_nav = f'<nav class="topic-nav" aria-label="Topics">\n{nav_labels}</nav>\n'

        panel_css = _topic_nav_css(topics)
        extra_style = f'<style>\n{panel_css}\n</style>\n'

        wrapped = ""
        for (tid, _name), frag in zip(topics, fragments):
            wrapped += f'<div id="tp-{tid}" class="topic-panel">\n{frag}\n</div>\n'

        body_open = f'<main class="lab-content" id="main">\n'
        body_close = f'</main>\n'
        body_inner = wrapped
    else:
        topic_radios = ""
        topic_nav = ""
        extra_style = ""
        body_open = f'<main id="main">\n'
        body_close = f'</main>\n'
        body_inner = "\n".join(fragments) + "\n"

    return (
        f'<!DOCTYPE html>\n'
        f'<html lang="en">\n'
        f'<head>\n'
        f'<meta charset="utf-8">\n'
        f'<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f'<title>{_html.escape(title)}</title>\n'
        f'<style>\n{_CSS}\n</style>\n'
        f'{extra_style}'
        f'</head>\n'
        f'<body class="lab-shell">\n'
        f'{topic_radios}'
        f'<a class="skip" href="#main">Skip to lab content</a>\n'
        f'<header>\n'
        f'<h1>{_html.escape(title)}</h1>\n'
        f'</header>\n'
        f'{topic_nav}'
        f'{body_open}'
        f'{body_inner}'
        f'{body_close}'
        f'</body>\n'
        f'</html>\n'
    )
