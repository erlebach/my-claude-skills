"""Interactive, accessible, zero-JS page-element components for the C++ lab.

Each public function in this module is a **pure renderer**: it takes plain data
(dicts/strings/lists) plus a caller-supplied ``comp_id`` and returns a
self-contained HTML-fragment string.  No function performs file, network, or
subprocess I/O, so every component is unit-testable without g++.

Contract (enforced by parametrized invariant tests in test_components.py):

* **Pure** — data in, HTML string out; deterministic; no I/O.
* **Zero-JS / zero-network** — interactivity is CSS only (`:checked`, `:hover`,
  `:focus`, `:target`, `<details>`).  No `<script>`, no external `src`/`href`.
* **id-namespaced** — every emitted ``id``/``name``/``for``/CSS selector is
  prefixed by the sanitised ``comp_id`` and restricted to ``[A-Za-z0-9_-]``, so
  multiple instances coexist in one document without id collision or
  ``:checked ~`` cross-contamination.
* **Color is never alone** — any meaning carried by color is also carried by
  text and a border/icon (WCAG 1.4.1).
* **Focus preserved** — state-driving radios/checkboxes are hidden by
  clip/off-screen, never ``display:none``/``visibility:hidden``.

The semantic color language lives in :data:`html_renderer.SEMANTIC_PALETTE` and
its ``:root`` ``--c-*`` tokens; components reference those tokens, never raw
hex, so chrome and SVG share one contrast-vetted palette.
"""

from __future__ import annotations

import html as _html
import re
from pathlib import Path
from typing import Any, Sequence

from .scaffold import flag_lines as _scaffold_flags
from .html_renderer import (
    _CSS,
    SEMANTIC_PALETTE,
    svg_renderer,
    _svg_boxchain,
    _svg_tree,
    _svg_buckets,
    _svg_set,
    _svg_frames_anatomy,
    _svg_perf_chart,
    _parse_frames,
    _frames_core,
)

# Vendored highlight.js (common bundle incl. C++) + theme, inlined for
# self-contained syntax highlighting. Loaded once at import; opt-in per page.
_VENDOR = Path(__file__).parent / "vendor" / "highlightjs"
_HLJS_JS = (_VENDOR / "highlight.min.js").read_text(encoding="utf-8")
_HLJS_CSS = (_VENDOR / "atom-one-dark.min.css").read_text(encoding="utf-8")
# WCAG AA fix (applied in our layer, not the vendored theme, so a re-fetch keeps it):
# atom-one-dark's comment #5c6370 is only 2.32:1 on its #282c34 bg. #9199a8 is 4.88:1
# and stays muted (dimmer than the #abb2bf code text). Inlined AFTER the theme so it wins.
_HLJS_OVERRIDE_CSS = (
    ".hljs-comment,.hljs-quote{color:#9199a8}"
    # A scaffolded panel (render_page._pre_scaffolded) is ONE <pre> holding one
    # <code> per line, so that dimming a line cannot cost copy fidelity. But the
    # vendored theme styles every highlighted <code> as a block with its own
    # padding and background — written for the usual one-<code>-per-<pre> case —
    # which turned each line into a separate boxed card with a gap under it.
    # Inside .code-lines the line elements are put back to plain inline text; the
    # <pre> keeps the single background and padding it already had.
    "\npre.code-lines > code.hljs{display:inline;padding:0;background:none;"
    "overflow-x:visible;border-radius:0}"
)

# Zero-JS "Monochrome" toggle for the highlighted code. A visually-hidden
# checkbox (placed just before <main>) drives a header-row label chip and, when
# checked, forces every highlight.js token span to inherit the base code colour
# — a single-colour ("monochrome") accessible view — without consuming any extra
# vertical space (the chip lives in the existing header row). It does NOT remove
# the SIA-R79 badge in colour mode (the spans stay in the DOM), but it provides
# the accessible monochrome view as a best-practice accommodation.
_MONO_TOGGLE_CSS = (
    ".mono-cb{position:absolute;width:1px;height:1px;overflow:hidden;"
    "clip:rect(0 0 0 0);white-space:nowrap}\n"
    ".mono-toggle{display:inline-flex;align-items:center;min-height:40px;"
    "padding:.2rem .8rem;border:1px solid var(--accent);border-radius:8px;"
    "background:var(--panel-bg);color:var(--accent);font:600 16px system-ui;"
    "cursor:pointer;white-space:nowrap}\n"
    ".mono-cb:focus-visible ~ header .mono-toggle{outline:2px solid var(--accent);"
    "outline-offset:2px}\n"
    ".mono-cb:checked ~ header .mono-toggle{background:var(--accent);color:#fff}\n"
    ".mono-cb:checked ~ main .hljs span{color:inherit !important}\n"
)

# Zero-JS "Line numbers" toggle, on every page that shows code. Same shape as
# the Monochrome chip above: a visually-hidden checkbox before <main> drives a
# header-row label and, when checked, numbers every code panel.
#
# The number is a CSS counter in ::before, never text in the DOM. So the code
# panel itself is untouched: a copy of it still yields compilable source, and
# the count cannot drift out of step with the lines the way a separate gutter
# column would.
#
# Wrapping is why the number is pulled into the <pre>'s own left padding with a
# negative margin instead of being laid out as a column. Panels soft-wrap by
# design (`white-space: pre-wrap` in _CSS), so a long line takes two visual
# rows; the padding moves the text column right and the number is the only
# thing living in the padding, so a wrapped continuation lands under the code,
# not under the number. The arithmetic has to stay consistent: the number box
# starts at 3.6 - 2.9 = 0.7rem (the panel's own left padding) and ends
# 0.7 + 1.9 + 1.0 = 3.6rem, which is the text column.
#
# The count is per <pre>, so each variant panel starts again at 1 -- which is
# what the sanitizer report cites, since every tab compiles as snippet.cpp.
_LINENO_CSS = (
    ".ln-cb{position:absolute;width:1px;height:1px;overflow:hidden;"
    "clip:rect(0 0 0 0);white-space:nowrap}\n"
    ".ln-toggle{display:inline-flex;align-items:center;min-height:40px;"
    "padding:.2rem .8rem;border:1px solid var(--accent);border-radius:8px;"
    "background:var(--panel-bg);color:var(--accent);font:600 16px system-ui;"
    "cursor:pointer;white-space:nowrap}\n"
    ".ln-cb:focus-visible ~ header .ln-toggle{outline:2px solid var(--accent);"
    "outline-offset:2px}\n"
    ".ln-cb:checked ~ header .ln-toggle{background:var(--accent);color:#fff}\n"
    ".ln-cb:checked ~ main pre.code-lines{padding-left:3.6rem;counter-reset:ln}\n"
    ".ln-cb:checked ~ main pre.code-lines > code{counter-increment:ln}\n"
    ".ln-cb:checked ~ main pre.code-lines > code::before{content:counter(ln);"
    "display:inline-block;width:1.9rem;margin-left:-2.9rem;margin-right:1rem;"
    "text-align:right;color:var(--code-dim);-webkit-user-select:none;"
    "user-select:none}\n"
    # A console_line_link panel holds its source as .cll-line blocks outside a
    # <pre>, so the pre.code-lines rules above cannot reach it -- and a toggle
    # that numbered eight panels out of nine would read as broken. Same
    # arithmetic; !important because those rules are emitted per instance under
    # an id selector (the idiom .code-scaffold and the Monochrome toggle use).
    # .cll-out is console output and is left alone.
    ".ln-cb:checked ~ main .cll-src{counter-reset:ln}\n"
    ".ln-cb:checked ~ main .cll-src .cll-line{counter-increment:ln;"
    "padding-left:3.6rem !important}\n"
    ".ln-cb:checked ~ main .cll-src .cll-line::before{content:counter(ln);"
    "display:inline-block;width:1.9rem;margin-left:-2.9rem;margin-right:1rem;"
    "text-align:right;color:var(--code-dim);-webkit-user-select:none;"
    "user-select:none}\n"
)


# Tri-link (code<->console<->diagram): highlight every element sharing a key
# with the hovered/focused one, scoped to one demo variant. Pure enhancement —
# the outline/stroke change (never colour alone) is the only visual; all a11y
# rides on static ARIA + focus (see console_line_link / _svg_boxchain).
_CLL_CSS = (
    ".cll-lit { outline:3px solid var(--c-link); outline-offset:-3px;"
    " background:#f3edff; }\n"
    ".cll-lit rect, rect.cll-lit { stroke:var(--c-link); stroke-width:3; }\n"
)
_CLL_JS = (
    "(function(){\n"
    "function grp(el){var s=el.closest('[data-cll-scope]');"
    "return s?s.getAttribute('data-cll-scope'):null;}\n"
    "function keys(el){return (el.getAttribute('data-cll')||'').split(/\\s+/)"
    ".filter(Boolean);}\n"
    "function box(el){return el.classList.contains('cll-node');}\n"
    "function paint(el,on){var sc=grp(el);if(sc===null)return;var ks=keys(el);"
    "if(!ks.length)return;var eb=box(el);\n"
    "document.querySelectorAll('[data-cll-scope=\"'+sc+'\"] [data-cll]')"
    ".forEach(function(t){var tb=box(t);\n"
    # A line-key (l<i>) links code<->console freely; a value-key (v<N>) lights a
    # target only when a diagram box is one endpoint -- so two output lines that
    # merely share a printed value never light each other (code<->console stays
    # line-precise; value-keys drive the box dimension only).
    "if(tk_hit(ks,keys(t),eb,tb))t.classList.toggle('cll-lit',on);});}\n"
    "function tk_hit(ks,tk,eb,tb){return tk.some(function(k){"
    "return ks.indexOf(k)>-1&&(k.charAt(0)==='l'||eb||tb);});}\n"
    "function on(e){var el=e.target.closest('[data-cll]');if(el)paint(el,true);}\n"
    "function off(e){var el=e.target.closest('[data-cll]');if(el)paint(el,false);}\n"
    "document.addEventListener('pointerover',on);"
    "document.addEventListener('pointerout',off);\n"
    "document.addEventListener('focusin',on);"
    "document.addEventListener('focusout',off);\n"
    "})();\n"
    # R1: recompute line/scatter coordinates client-side on axis toggle. Reads
    # each marker's raw data-x/data-y and the <g>'s embedded plot geometry;
    # ranges are recomputed from the markers (as the bar handler recomputes hi).
    # log lo = smallest positive value (fallback 1); linear lo = min.
    "function pcLine(g, axis, scale){\n"
    "  g.setAttribute('data-pc-'+axis+'scale', scale);\n"
    "  var L=+g.getAttribute('data-l'), R=+g.getAttribute('data-r'),\n"
    "      T=+g.getAttribute('data-t'), B=+g.getAttribute('data-b');\n"
    "  var xsc=g.getAttribute('data-pc-xscale'), ysc=g.getAttribute('data-pc-yscale');\n"
    "  var pts=[].slice.call(g.querySelectorAll('.pc-pt'));\n"
    "  function rng(getter, sc){ var vs=pts.map(getter);\n"
    "    var hi=Math.max.apply(null,vs);\n"
    "    if(sc==='log'){ var pos=vs.filter(function(v){return v>0;});\n"
    "      var lo=pos.length?Math.min.apply(null,pos):1; return [lo, Math.max(hi, lo*10)]; }\n"
    "    return [Math.min.apply(null,vs), hi]; }\n"
    "  function frac(v, lo, hi, sc){ if(sc==='log'){ v=Math.max(v,lo);\n"
    "      return (Math.log10(v)-Math.log10(lo))/((Math.log10(hi)-Math.log10(lo))||1);}\n"
    "    return (v-lo)/((hi-lo)||1); }\n"
    "  var xr=rng(function(p){return +p.getAttribute('data-x');}, xsc);\n"
    "  var yr=rng(function(p){return +p.getAttribute('data-y');}, ysc);\n"
    "  function PX(x){ return L + frac(x, xr[0], xr[1], xsc)*(R-L); }\n"
    "  function PY(y){ return B - frac(y, yr[0], yr[1], ysc)*(B-T); }\n"
    "  pts.forEach(function(p){ p.setAttribute('cx', PX(+p.getAttribute('data-x')).toFixed(1));\n"
    "    p.setAttribute('cy', PY(+p.getAttribute('data-y')).toFixed(1)); });\n"
    "  var lines={};\n"
    "  pts.forEach(function(p){ var s=p.getAttribute('data-series')||'';\n"
    "    (lines[s]=lines[s]||[]).push(PX(+p.getAttribute('data-x')).toFixed(1)+','+PY(+p.getAttribute('data-y')).toFixed(1)); });\n"
    "  [].slice.call(g.querySelectorAll('.pc-line')).forEach(function(pl){\n"
    "    var s=pl.getAttribute('data-series')||''; if(lines[s]) pl.setAttribute('points', lines[s].join(' ')); });\n"
    "  [].slice.call(g.querySelectorAll('.pc-xtick')).forEach(function(t){ t.setAttribute('x', PX(+t.getAttribute('data-x')).toFixed(1)); });\n"
    "  [].slice.call(g.querySelectorAll('.pc-ytick')).forEach(function(t){ t.setAttribute('y', PY(+t.getAttribute('data-y')).toFixed(1)); });\n"
    "  [].slice.call(g.querySelectorAll('.pc-xgrid')).forEach(function(l){ var x=PX(+l.getAttribute('data-x')).toFixed(1); l.setAttribute('x1',x); l.setAttribute('x2',x); });\n"
    "  [].slice.call(g.querySelectorAll('.pc-ygrid')).forEach(function(l){ var y=PY(+l.getAttribute('data-y')).toFixed(1); l.setAttribute('y1',y); l.setAttribute('y2',y); });\n"
    "}\n"
    "document.addEventListener('click',function(e){\n"
    "  var b=e.target.closest('[data-pc-toggle]'); if(!b) return;\n"
    "  var scale=b.getAttribute('data-pc-toggle');\n"
    "  var g=b.closest('.pc-fig').querySelector('[data-pc]');\n"
    "  var grp=b.parentNode; if(grp){var bs=grp.querySelectorAll('[data-pc-toggle]');\n"
    "    for(var i=0;i<bs.length;i++){bs[i].setAttribute('aria-pressed', bs[i]===b ? 'true':'false');}}\n"
    "  if(g.querySelector('.pc-pt')){ pcLine(g, b.getAttribute('data-pc-axis'), scale); return; }\n"
    "  var bars=[].slice.call(g.querySelectorAll('.pc-bar'));\n"
    "  var ys=bars.map(function(r){return parseFloat(r.getAttribute('data-y'));});\n"
    "  var top=24, bot=240, hi=Math.max.apply(null,ys);\n"
    "  var lo=(scale==='log')?1:0;\n"
    "  function frac(v){ if(scale==='log'){v=Math.max(v,lo);\n"
    "      return (Math.log10(v)-Math.log10(lo))/((Math.log10(hi)-Math.log10(lo))||1);}\n"
    "    return (v-lo)/((hi-lo)||1); }\n"
    "  bars.forEach(function(r,i){ var h=Math.max(2,Math.round(frac(ys[i])*(bot-top)));\n"
    "    r.setAttribute('height',h); r.setAttribute('y',bot-h); });\n"
    "  g.setAttribute('data-pc-scale',scale);\n"
    "});\n"
    # Hover readout: show the hovered bar's verbatim console substring (data-raw)
    # in the chart's .pc-tip text; clear it on mouseout.
    "function pctip(e,show){var r=e.target.closest('.pc-bar,.pc-pt');if(!r)return;\n"
    "  var g=r.closest('[data-pc]');if(!g)return;var t=g.querySelector('.pc-tip');\n"
    "  if(t)t.textContent=show?(r.getAttribute('data-raw')||''):'';}\n"
    "document.addEventListener('mouseover',function(e){pctip(e,true);});\n"
    "document.addEventListener('mouseout',function(e){pctip(e,false);});\n"
)

# A visible, zero-JS keyboard-navigation help (native <details>) shown on every
# page in the header row. It benefits sighted keyboard users the most; screen
# readers get the navigation model from the radio-group roles/names natively.
_KBD_HELP_HTML = (
    '<details class="kbd-help">'
    '<summary><span aria-hidden="true">⌨</span> Keyboard</summary>'
    '<div class="kbd-panel">'
    '<dl>'
    '<dt><kbd>Tab</kbd> / <kbd>Shift</kbd>+<kbd>Tab</kbd></dt>'
    '<dd>Move between groups — topics, step numbers, zoom, and page controls.</dd>'
    '<dt><kbd>←</kbd> <kbd>→</kbd> arrow keys</dt>'
    '<dd>Move within a group — e.g. the step numbers or the topic list.</dd>'
    '<dt><kbd>Enter</kbd> / <kbd>Space</kbd></dt>'
    '<dd>Activate the control that has focus.</dd>'
    '</dl></div></details>'
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

# Visually hide a state-driving radio/checkbox WITHOUT dropping it from the
# focus order (clip/off-screen, never display:none — WCAG / keyboard).
_VH = (
    "position:absolute;width:1px;height:1px;"
    "overflow:hidden;clip:rect(0 0 0 0);white-space:nowrap"
)

# Human-readable names for the semantic roles (used by the color legend).
_ROLE_NAMES = {
    "addr": "Address",
    "val": "Value",
    "type": "Type",
    "const": "const / immutable",
    "err": "Error",
}


def _safe(s: Any) -> str:
    """Return a CSS-identifier-safe slug of *s* (``[A-Za-z0-9_-]`` only)."""
    return "".join(c if (str(c).isalnum() or c in "_-") else "_" for c in str(s))


def _e(s: Any) -> str:
    """HTML-escape a value for safe text/attribute interpolation."""
    return _html.escape(str(s))


# A cross-demo link, written in prose by demo NAME rather than by path:
#   ${demo:class_structure|class structure demonstration}
# Every character the marker uses is one html.escape leaves alone, so it survives
# escaping intact and the substitution runs AFTER _e — which is what lets the
# anchor be emitted raw while the link text stays escaped.
# The href is a bare sibling, correct in both the built tree (dist_labs/<name>.html)
# and the published one (course_site/static/rail/<name>.html). Making those two the
# same shape is what this construct is built on.
_DEMO_LINK_RE = re.compile(r"\$\{demo:([A-Za-z0-9_]+)\|([^}]*)\}")


def _demo_links(escaped: str) -> str:
    """Turn ``${demo:name|text}`` markers in already-escaped HTML into links."""
    return _DEMO_LINK_RE.sub(
        lambda m: f'<a href="{m.group(1)}.html">{m.group(2)}</a>', escaped)


# An external link, written in prose as `[text](https://…)`.
# Author's ruling, 2026-09-05: *"Please allow external links in Key Ideas and
# Vocabulary. External links will work regardless of where the website is
# located."* That is the point — the 2026-08-28 ban existed because a link
# BETWEEN pages of this corpus is fragile under a different deployment layout,
# and an outbound https URL is not. Cross-page references still use
# `${demo:name|text}`; this marker is for sources outside the corpus.
#
# Like the other two markers this runs AFTER escaping, so the URL arrives with
# `&` already written `&amp;` — which is what an href attribute wants — and the
# link text an author wrote stays escaped. https only: a rail page is served
# from `dist_labs/`, from the course site and from Canvas, and an http link is
# blocked as mixed content in all three, so `[text](http://…)` deliberately does
# not match and shows up as literal text (and `test_take_it_further.py` fails
# the build on one). A C++ lambda `[](…)` and `operator new[](…)` are the shapes
# that could collide; requiring `(https://` immediately after the `]` is what
# keeps them out.
_PROSE_LINK_RE = re.compile(r"\[([^\]\n]+)\]\((https://[^\s()<>]+)\)")


def _prose_links(escaped: str) -> str:
    """Turn ``[text](https://…)`` in already-escaped prose into an anchor."""
    return _PROSE_LINK_RE.sub(
        lambda m: f'<a href="{m.group(2)}" target="_blank" rel="noopener">'
                  f'{m.group(1)}</a>',
        escaped)


# `**bold**` in prose. The pattern needs a non-space just inside each delimiter
# and allows no `*` between them, so a C++ double pointer written in prose
# ("raw new[]/double**", "char** argv") is never paired into emphasis.
_EMPH_RE = re.compile(r"\*\*(?=\S)([^*\n]+?)(?<=\S)\*\*")

# `*italic*` in prose, after bold. Neither delimiter may touch a letter, digit,
# `_` or another `*` on its outer side, or a space on its inner side, and the
# span holds no `*`, `<` or `>`. So `*p and *q`, `a * b`, `x*y*z` and `char*` in
# a code span are never paired, and an italic can never reach across a <code>.
_ITAL_RE = re.compile(r"(?<![\w*])\*(?=[^\s*])([^*\n<>]+?)(?<=[^\s*])\*(?![\w*])")


def _emphasis(escaped: str) -> str:
    """Turn ``**text**`` into ``<strong>`` and ``*text*`` into ``<em>`` in
    already-escaped prose.

    Runs after escaping, like :func:`_demo_links`, so an authored angle bracket
    stays escaped and only this one marker produces markup. Prose only — code
    is rendered down a different path and never passes through here.
    """
    return _ITAL_RE.sub(r"<em>\1</em>", _EMPH_RE.sub(r"<strong>\1</strong>", escaped))


# `code` in prose. Runs after escaping, so the span's text is already safe;
# nowrap keeps a short token like `if constexpr` from breaking across lines.
_CODE_RE = re.compile(r"`([^`\n]+)`")


def _inline_code(escaped: str) -> str:
    """Turn ```code``` in already-escaped prose into ``<code>``."""
    return _CODE_RE.sub(r'<code style="white-space:nowrap">\1</code>', escaped)


# ---------------------------------------------------------------------------
# 3. Chrome components
# ---------------------------------------------------------------------------

# Extra CSS used by demo pages (page_shell).  No external/network reference.
COMPONENT_CSS = """
.demo-wrap { max-width: 100rem; margin: 0 auto; padding: 1rem 1.2rem; }
.demo-wrap h2 { font-size: 1.1rem; }
/* header row: title on the left, tool chips (keyboard help, monochrome) on the
   right — collapsed tools add no vertical space. */
header { display: flex; align-items: center; justify-content: space-between;
  gap: .75rem; flex-wrap: wrap; }
.hdr-tools { display: flex; align-items: center; gap: .5rem; flex-wrap: wrap; }
/* keyboard-navigation help: a compact chip whose panel floats (position:absolute)
   so opening it costs no layout height. */
/* margin:0 overrides the global `details { margin-top:.5rem }` so the Keyboard
   chip lines up with the Monochrome label in the flex header row. */
details.kbd-help { position: relative; margin: 0; }
details.kbd-help > summary { display: inline-flex; align-items: center; gap: .4rem;
  min-height: 40px; padding: .2rem .8rem; border: 1px solid var(--accent);
  border-radius: 8px; background: var(--panel-bg); color: var(--accent);
  font: 600 16px system-ui; cursor: pointer; list-style: none; white-space: nowrap; }
details.kbd-help > summary::-webkit-details-marker { display: none; }
details.kbd-help[open] > summary { background: var(--accent); color: #fff; }
.kbd-panel { position: absolute; right: 0; top: calc(100% + .3rem); z-index: 50;
  width: min(24rem, 92vw); border: 1px solid var(--border); border-radius: 8px;
  background: var(--panel-bg); box-shadow: 0 6px 20px rgba(0,0,0,.18);
  padding: .6rem .85rem; font: 13px/1.45 system-ui; text-align: left; }
.kbd-panel dl { margin: 0; }
.kbd-panel dt { font-weight: 700; margin-top: .4rem; }
.kbd-panel dt:first-child { margin-top: 0; }
.kbd-panel dd { margin: .1rem 0 0; }
.kbd-panel kbd { border: 1px solid var(--border); border-radius: 4px;
  padding: 0 .3rem; font: 12px ui-monospace, monospace; background: #fff; }
.legend { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: .6rem; }
.legend li { display: inline-flex; align-items: center; gap: .4rem;
  border: 1px solid var(--border); border-radius: 6px; padding: .2rem .5rem; }
.swatch { display: inline-block; width: 1rem; height: 1rem; border-radius: 3px;
  border: 1px solid var(--fg); }
.callout { border: 2px solid var(--accent); border-left-width: 6px;
  background: var(--panel-bg); border-radius: 0 6px 6px 0; padding: .5rem .8rem; margin: .6rem 0; }
.callout-label { font-weight: 700; }
.badge { display: inline-flex; align-items: center; gap: .35rem; font-weight: 700;
  border: 2px solid; border-radius: 6px; padding: .15rem .6rem; }
.console { border: 2px solid var(--border); border-radius: 8px; padding: .6rem .9rem;
  font: 14px/1.5 ui-monospace, monospace; white-space: pre-wrap; background: var(--panel-bg); }
.console-label { display: block; font-weight: 700; margin-bottom: .3rem; }
/* long-output disclosure: a caret toggle to reveal the folded overflow lines */
.console-more { margin-top: .4rem; }
.console-more > summary { cursor: pointer; font-weight: 700; min-height: 44px;
  display: inline-flex; align-items: center; gap: .4rem; list-style: none;
  color: var(--accent); }
.console-more > summary::-webkit-details-marker { display: none; }
.console-more > summary .caret { font-size: .9em; transition: transform .15s ease; }
.console-more[open] > summary .caret { transform: rotate(90deg); }
@media (prefers-reduced-motion: reduce) {
  .console-more > summary .caret { transition: none; }
}
.byte-grid-wrap { overflow-x: auto; max-width: 100%; }
/* Box-chain diagrams render at natural size (constant 14px font); if a diagram
   is wider than the panel it scrolls horizontally rather than shrinking. */
.dia-scroll { overflow-x: auto; max-width: 100%; }
/* Box-chain caption: wraps below the diagram so a long note never widens it. */
.build-cmd { font: 12.5px/1.5 ui-monospace, "SF Mono", Menlo, monospace;
  color: #5a6b8c; margin: .7rem 0 0; white-space: pre-wrap; overflow-wrap: anywhere; }
.build-cmd::before { content: "$ "; -webkit-user-select: none; user-select: none; }
.dia-note { font: 13px/1.5 system-ui; color: #5a6b8c; margin: .45rem 0 0;
  max-width: 100%; }
.byte-grid { border-collapse: collapse; }
.byte-grid caption { text-align: left; font-weight: 700; margin-bottom: .3rem; }
.byte-grid td, .byte-grid th { border: 1px solid var(--border); padding: .35rem .6rem;
  font: 15px ui-monospace, monospace; text-align: center; }
.byte-grid .byte-char { color: var(--accent); font-weight: 700; }
.byte-grid .byte-int { color: var(--accent); font-weight: 700; background: #eef4ff; }
.byte-src { margin: .1rem 0 .5rem; font-size: 15px; color: #444; }
.byte-src code { background: #f2f5fb; border: 1px solid var(--border); border-radius: 4px;
  padding: .1rem .35rem; font: 14px ui-monospace, monospace; color: #1a1a1a; }
/* scroll-affordance: a fixed bottom cue that a document page has more content
   below the fold. Hidden by default (so with JS off it never shows and the page
   just scrolls normally); a tiny inline script in page_shell adds .show only
   while there is genuinely more below the current scroll position. pointer-
   events:none so it never intercepts clicks; position:fixed so it adds no flow
   and cannot reflow neighbours. The caret+text ("more below") carry the meaning,
   never color alone (1.4.1); it only changes on user scroll, never auto-animates
   (2.2.2). */
.more-cue { position: fixed; left: 0; right: 0; bottom: 0; height: 3rem;
  display: flex; align-items: flex-end; justify-content: center;
  padding-bottom: .45rem; pointer-events: none; opacity: 0;
  transition: opacity .15s ease;
  background: linear-gradient(to top, var(--bg), transparent); }
.more-cue.show { opacity: 1; }
.more-cue-pill { font: 700 13px system-ui, sans-serif; color: var(--accent-fg);
  background: var(--accent); border-radius: 999px; padding: .15rem .7rem;
  box-shadow: 0 1px 4px rgba(0,0,0,.25); }
@media (prefers-reduced-motion: reduce) { .more-cue { transition: none; } }
"""


# Fixed "more below" scroll cue for document pages. The element is inert
# (aria-hidden, pointer-events:none) and hidden until the inline script proves
# there is more content below the current scroll position -- so it degrades to
# nothing with JS off, and it never lies. Reading scrollHeight/scrollY works in
# every browser (Safari included); unlike a forced scrollbar it does not depend
# on the OS overlay-scrollbar setting, which hides the macOS page scrollbar.
_MORE_CUE_HTML = (
    '<div id="more-cue" class="more-cue" aria-hidden="true">'
    '<span class="more-cue-pill">▾ more below</span></div>\n'
    "<script>\n"
    "(function(){\n"
    '  var cue=document.getElementById("more-cue");\n'
    "  if(!cue)return;\n"
    "  function u(){var d=document.documentElement;"
    'cue.classList.toggle("show",d.scrollHeight-window.innerHeight-window.scrollY>4);}\n'
    '  addEventListener("scroll",u,{passive:true});addEventListener("resize",u);u();\n'
    "})();\n"
    "</script>\n"
)


def page_shell(comp_id: str, body_html: str, *, title: str = "Demo",
               highlight: bool = False, tri_link: bool = False,
               home_href: str | None = None,
               home_label: str = "Course") -> str:
    """Wrap *body_html* in a complete, self-contained WCAG AA document.

    Declares ``lang``, exposes a skip link targeting the ``#main`` landmark,
    and inlines all CSS (theme + component styles).  No external/network
    reference is emitted, so the page pastes directly into Canvas.

    *home_href* is opt-in for a reason.  A rail page has no site chrome, so a
    reader who arrives from a bookmark, a pasted URL or an LMS link has no route
    back into the course — Back only helps someone who clicked in.  Passing a
    href emits one return link above the title.  It stays OFF by default because
    a relative href would resolve against Canvas's own parent once the page is
    pasted there, silently breaking the portability promised above; the caller
    that knows where the page will be served is the one that can supply it.

    The link renders inside ``<header>``, grouped with the ``<h1>`` in a
    ``.hdr-left`` div.  The header is a flex row with
    ``justify-content: space-between``, so the grouping is what keeps the row at
    two children and the title on the left; it also means both lines inherit the
    header's existing padding instead of needing one of their own.

    When *highlight* is true, the vendored highlight.js library and theme are
    inlined and run on load (``<pre><code class="language-XXX">`` blocks get
    coloured).  Still fully self-contained — nothing external is fetched — and
    it degrades gracefully: with JS off the code shows as plain text.
    """
    t = _e(title)
    hl_style = (f"<style>\n{_HLJS_CSS}\n{_HLJS_OVERRIDE_CSS}\n{_MONO_TOGGLE_CSS}\n</style>\n"
                if highlight else "")
    # Rides with *highlight*, like the Monochrome chip beside it: every page
    # that shows code gets the same two chips in the same place.
    ln_style = f"<style>\n{_LINENO_CSS}</style>\n" if highlight else ""
    ln_cb = ('<input type="checkbox" class="ln-cb" id="ln-code" '
             'aria-label="Number the lines of each code panel">\n'
             if highlight else "")
    ln_label = ('<label for="ln-code" class="ln-toggle" '
                'title="Number the lines of each code panel, to match the '
                'file:line a compiler or sanitizer report cites">Line '
                'numbers</label>\n'
                if highlight else "")
    # highlightAll() colours the <pre><code class="language-*"> panels. The
    # console_line_link source rows are standalone <code class="cll-line
    # language-*"> (not inside a <pre>), so highlight them per line explicitly —
    # this is the ONLY thing that gives the linked panel syntax colour (the link
    # itself is pure CSS). Console rows (.cll-out) are output, left unhighlighted.
    hl_script = (f"<script>\n{_HLJS_JS}\nhljs.highlightAll();\n"
                 "document.querySelectorAll('.cll-src .cll-line')"
                 ".forEach(function(el){hljs.highlightElement(el);});\n</script>\n"
                 if highlight else "")
    cll_style = f"<style>\n{_CLL_CSS}</style>\n" if tri_link else ""
    cll_script = f"<script>\n{_CLL_JS}</script>\n" if tri_link else ""
    # Zero-JS monochrome toggle (only meaningful when the code is highlighted).
    # The checkbox sits just before <main> so `:checked ~ main` reaches the code;
    # its label chip rides in the header row beside the title (no extra height).
    mono_cb = ('<input type="checkbox" class="mono-cb" id="mono-code" '
               'aria-label="Show code in a single colour (accessible monochrome view)">\n'
               if highlight else "")
    mono_label = ('<label for="mono-code" class="mono-toggle" '
                  'title="Show code in a single colour (accessible view)">Monochrome</label>\n'
                  if highlight else "")
    # Both the markup and its rule are conditional, so a page built without
    # home_href is byte-for-byte what it was before this parameter existed.
    # The arrow is decoration: aria-hidden keeps the accessible name to the
    # label alone, so it is announced as "Course", not "left arrow Course".
    # The link and the <h1> go in ONE div so the flex header row keeps exactly
    # two children (this group, and .hdr-tools) and the title stays left. The
    # group owns the stacking, and both lines inherit the header's own padding —
    # no second padding rule to keep in step with it.
    if home_href:
        home_open = ('<div class="hdr-left">\n'
                     f'<nav class="site-return"><a href="{_e(home_href)}">'
                     f'<span aria-hidden="true">&#8592;</span> {_e(home_label)}</a></nav>\n')
        home_close = "</div>\n"
        home_style = ("<style>\n"
                      ".hdr-left{display:flex;flex-direction:column;"
                      "align-items:flex-start;gap:.1rem;min-width:0}\n"
                      ".site-return a{font-size:.8rem;text-decoration:none;"
                      "border-bottom:1px solid currentColor}\n"
                      ".site-return a:hover{border-bottom-width:2px}\n"
                      "</style>\n")
    else:
        home_open = ""
        home_close = ""
        home_style = ""
    return (
        "<!DOCTYPE html>\n"
        '<html lang="en">\n'
        "<head>\n"
        '<meta charset="utf-8">\n'
        '<meta name="viewport" content="width=device-width, initial-scale=1">\n'
        f"<title>{t}</title>\n"
        f"<style>\n{_CSS}\n{COMPONENT_CSS}\n</style>\n"
        f"{hl_style}"
        f"{ln_style}"
        f"{cll_style}"
        f"{home_style}"
        "</head>\n"
        "<body>\n"
        '<a class="skip" href="#main">Skip to content</a>\n'
        f"{mono_cb}{ln_cb}"
        f"<header>\n{home_open}<h1>{t}</h1>\n{home_close}"
        f'<div class="hdr-tools">{_KBD_HELP_HTML}{mono_label}{ln_label}</div>\n'
        "</header>\n"
        '<main id="main">\n'
        f'<div class="demo-wrap">\n{body_html}\n</div>\n'
        "</main>\n"
        f"{hl_script}"
        f"{cll_script}"
        f"{_MORE_CUE_HTML}"
        "</body>\n"
        "</html>\n"
    )


def color_legend(comp_id: str) -> str:
    """Document the semantic palette: a colored swatch + text name per role."""
    p = _safe(comp_id)
    items = ""
    for role, name in _ROLE_NAMES.items():
        items += (
            f'<li><span class="swatch" style="background:var(--c-{role});'
            f'border:1px solid var(--fg)"></span> {_e(name)}</li>\n'
        )
    return (
        f'<ul class="legend" id="{p}" aria-label="Color legend">\n{items}</ul>\n'
    )


_CALLOUT_TONES = {"note": "--accent", "advanced": "--advanced"}


def callout_note(comp_id: str, text: str, *, label: str = "Note",
                 tone: str = "note") -> str:
    """A pedagogical aside distinguished by a text label and a border.

    ``tone="advanced"`` draws it in orange rather than the page accent, for the
    one aside that tells the reader a section is optional. The default tone is
    byte-identical to what it has always been, so adding this changed no
    existing page. Two tones only, and an unknown one raises: a typo that fell
    back to the default would be invisible in the built page.
    """
    p = _safe(comp_id)
    if tone not in _CALLOUT_TONES:
        raise ValueError(
            f"unknown callout tone {tone!r}; expected one of "
            f"{', '.join(sorted(_CALLOUT_TONES))}"
        )
    token = _CALLOUT_TONES[tone]
    label_style = "" if tone == "note" else f' style="color:var({token})"'
    return (
        f'<aside class="callout" id="{p}" '
        f'style="border:2px solid var({token});border-left-width:6px">\n'
        f'<span class="callout-label"{label_style}>{_e(label)}:</span> {_e(text)}\n'
        f"</aside>\n"
    )


def _prose_box(comp_id: str, body_html: str, *, title: str | None = None,
               css_class: str) -> str:
    """Draw a bordered box with some text inside.

    This is the one shared look for the vocabulary list and the concept boxes,
    so they all match. Give it a title to add a heading at the top of the box
    (screen readers then announce the box by that heading). Leave the title out
    for a plain box with no heading.

    Args:
        comp_id: A short unique name for this box, used to build its HTML ids.
        body_html: The ready-made HTML shown inside the box.
        title: Optional heading at the top of the box; ``None`` means no heading.
        css_class: The style class placed on the box so it can be styled.

    Returns:
        The box as a piece of HTML.
    """
    p = _safe(comp_id)
    if title is not None:
        tid = f"{p}-title"
        head = f'<h2 id="{tid}" style="font-size:1rem;margin:.2rem 0 .4rem">{_e(title)}</h2>\n'
        label_attr = f' aria-labelledby="{tid}"'
    else:
        head = ""
        label_attr = ""
    return (
        f'<section class="{css_class}" id="{p}"{label_attr} '
        f'style="border:2px solid var(--border);border-radius:8px;padding:.6rem .9rem;margin:.6rem 0">\n'
        f"{head}{body_html}\n"
        f"</section>\n"
    )


def glossary(comp_id: str, title: str, terms: Sequence[tuple[str, str]]) -> str:
    """A reusable term/definition list (prose vocabulary), rendered as a <dl>.

    Accessible: the <section> is labelled by its heading via aria-labelledby.
    """
    rows = ""
    for term, definition in terms:
        rows += f"<dt>{_e(term)}</dt><dd>{_prose_links(_demo_links(_e(definition)))}</dd>\n"
    return _prose_box(comp_id, f'<dl style="margin:0">\n{rows}</dl>',
                      title=title, css_class="glossary")


def concept_note(comp_id: str, text: str, *, label: str = "Key Idea",
                 open_: bool = False, footnote: str = "") -> str:
    """Show one example's Key Idea as a fold-away note.

    The note starts folded, showing just a "Key Idea" toggle styled as a
    button-like chip with a ``>`` caret that rotates down when opened, so it
    clearly reads as pressable. Clicking it (or pressing Enter/Space) opens it
    to reveal the text; clicking again folds it back. It works with the keyboard
    and with screen readers (the caret is decorative/``aria-hidden``; the native
    ``<details>`` announces its expanded state), and needs no scripting. Use it
    for the short note that says why one example is here.

    Args:
        comp_id: A short unique name for this note, used to build its HTML ids.
        text: The note's wording, shown once the reader opens it.
        label: The wording of the clickable line; defaults to "Key Idea".
        open_: Start already open instead of folded. Defaults to folded.
        footnote: Optional aside shown below the Key Idea, inside the same box,
            under a hairline rule and in smaller dim text. Use it for a remark
            about the page's own machinery — why an instrumentation line is in
            the code, say — which belongs beside the idea but is not the idea.
            Empty (the default) renders nothing at all.

    Returns:
        The fold-away note as a piece of HTML.
    """
    p = _safe(comp_id)
    # One <p> per blank-line-separated paragraph, same as the sidebar panel and
    # the in-tab Key Idea aside — a blank line in the source must survive as a
    # visible break here too, or a multi-paragraph note renders as one slab.
    inner = _paragraphs_html(text)
    if footnote:
        # Same box as the Key Idea (the author's ruling: the "why" sits with the
        # idea, not in a separate panel), but visually subordinate to it: a
        # hairline rule, smaller type, and --fg-dim (7.5:1 on --bg).
        inner += (
            f'\n<p id="{p}-fn" class="concept-footnote" '
            f'style="margin:.5rem 0 0;padding-top:.45rem;'
            f'border-top:1px solid var(--border);'
            f'font-size:.88em;color:var(--fg-dim)">{_e(footnote)}</p>'
        )
    body = _prose_box(f"{p}-box", inner, css_class="concept")
    op = " open" if open_ else ""
    return (
        f'<details id="{p}" class="concept"{op} style="margin:.4rem 0">\n'
        f'<summary class="concept-toggle">'
        f'<span class="caret" aria-hidden="true">▸</span>{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )


def glossary_note(comp_id: str, terms, *, label: str = "Memory glossary",
                  open_: bool = False) -> str:
    """A per-example glossary as a fold-away chip, matching ``concept_note``.

    Renders the same button-like ``<details class="concept">`` chip (rotating
    caret, keyboard + screen-reader friendly, zero-JS) but its body is a term
    list (``<dl>``) instead of prose. Carries the extra ``chip-inline`` class so
    it can sit on one row beside the Concept chip. ``terms`` is a sequence of
    ``(term, definition)`` pairs."""
    p = _safe(comp_id)
    rows = "".join(f"<dt>{_e(t)}</dt><dd>{_prose_links(_demo_links(_e(d)))}</dd>\n" for t, d in terms)
    body = _prose_box(f"{p}-box", f'<dl style="margin:0">\n{rows}</dl>',
                      css_class="concept")
    op = " open" if open_ else ""
    return (
        f'<details id="{p}" class="concept chip-inline"{op} '
        f'style="margin:.4rem 0 .4rem .6rem">\n'
        f'<summary class="concept-toggle">'
        f'<span class="caret" aria-hidden="true">▸</span>{_e(label)}</summary>\n'
        f"{body}"
        f"</details>\n"
    )


def concept_panel(comp_id: str, text: str, *, title: str = "Concept") -> str:
    """Show the whole page's Concept as its own titled panel.

    This is the "what this whole page teaches" note. It appears as an entry in
    the side list (like the Vocabulary entry) and is shown in full whenever it is
    picked — it does not fold away. For the fold-away note that belongs to a
    single example, use ``concept_note`` instead.

    Args:
        comp_id: A short unique name for this panel, used to build its HTML ids.
        text: The Concept wording.
        title: The heading shown at the top of the panel; defaults to "Concept".

    Returns:
        The panel as a piece of HTML.
    """
    return _prose_box(comp_id, _paragraphs_html(text),
                      title=title, css_class="concept")


# ---------------------------------------------------------------------------
# 4. memory-diagram
# ---------------------------------------------------------------------------


def memory_diagram(comp_id: str, ptrdata: dict[str, Any] | None) -> str:
    """Render pointer state as an accessible inline SVG.

    Delegates to :func:`html_renderer.svg_renderer`, which emits ``role="img"``
    with a ``<title>``/``<desc>`` (referenced by ``aria-labelledby``) narrated
    from the data; missing keys degrade to ``"?"`` and never raise.  The id is
    sanitised so a punctuated *comp_id* still yields CSS-safe element ids.
    """
    return svg_renderer(ptrdata, _safe(comp_id))


# ---------------------------------------------------------------------------
# 5. High-value interactions
# ---------------------------------------------------------------------------


def hover_link_diagram(comp_id: str, ptrdata: dict[str, Any] | None) -> str:
    """Hovering/focusing the diagram lights the arrow + target (CSS only), on top
    of the shared vertical diagram. Highlight is color *and* thicker stroke (a
    non-color cue); the figure is focusable so keyboard users get the same effect."""
    p = _safe(comp_id)
    svg = svg_renderer(ptrdata, p)          # the shared vertical diagram
    style = (
        f"#{p} {{ cursor: pointer; }}\n"
        f"#{p}:focus:not(:focus-visible) {{ outline: none; }}\n"
        f"#{p}:hover line, #{p}:focus line,"
        f"#{p}:hover path, #{p}:focus path"
        " { stroke: var(--c-val); stroke-width: 5; }"
    )
    return (
        f'<figure id="{p}" tabindex="0" '
        f'aria-label="pointer diagram — hover or focus to highlight the arrow" '
        f'style="margin:0">\n'
        f'<style>\n{style}\n</style>\n{svg}\n</figure>\n'
    )


def before_after_toggle(
    comp_id: str,
    before_svg: str,
    after_svg: str,
    *,
    labels: tuple[str, str] = ("Before", "After"),
    caption: str = "",
) -> str:
    """Switch one diagram between two pre-baked states via a 2-option radio."""
    p = _safe(comp_id)
    bid, aid = f"{p}-before", f"{p}-after"
    style = (
        f"#{p} .ba-state {{ display: none; }}\n"
        f"#{bid}:checked ~ .ba-stage .ba-before {{ display: block; }}\n"
        f"#{aid}:checked ~ .ba-stage .ba-after {{ display: block; }}\n"
        f"#{bid}:checked ~ .ba-tabs label[for=\"{bid}\"],"
        f"#{aid}:checked ~ .ba-tabs label[for=\"{aid}\"]"
        " { background: var(--accent); color: var(--accent-fg); }\n"
        f"#{p} .ba-tabs label {{ border:2px solid var(--border); border-radius:6px;"
        " padding:.3rem .8rem; min-height:44px; display:inline-flex; align-items:center;"
        " cursor:pointer; font-weight:700; }\n"
        f"#{bid}:focus-visible ~ .ba-tabs label[for=\"{bid}\"],"
        f"#{aid}:focus-visible ~ .ba-tabs label[for=\"{aid}\"]"
        " { outline: 3px solid var(--accent); outline-offset: 2px; }"
    )
    cap = f"<figcaption>{_e(caption)}</figcaption>\n" if caption else ""
    return (
        f'<figure id="{p}" style="margin:0">\n<style>\n{style}\n</style>\n'
        f'<input type="radio" name="{p}-ba" id="{bid}" style="{_VH}" checked>\n'
        f'<input type="radio" name="{p}-ba" id="{aid}" style="{_VH}">\n'
        f'<div class="ba-tabs" role="group" aria-label="Choose state">'
        f'<label for="{bid}">{_e(labels[0])}</label>'
        f'<label for="{aid}">{_e(labels[1])}</label></div>\n'
        f'<div class="ba-stage">\n'
        f'<div class="ba-state ba-before">{before_svg}</div>\n'
        f'<div class="ba-state ba-after">{after_svg}</div>\n'
        f"</div>\n{cap}</figure>\n"
    )


def predict_reveal_quiz(
    comp_id: str,
    question: str,
    options: Sequence[str],
    correct_index: int,
    *,
    explanation: str = "",
) -> str:
    """Radio answers reveal baked correct/incorrect feedback via ``:checked``.

    Correctness is signalled by text + an icon (✓/✗) in addition to color, and
    the real answer/explanation is baked in.
    """
    p = _safe(comp_id)
    style_lines = [f"#{p} .qfb {{ display: none; }}"]
    inputs, labels, feedback = "", "", ""
    for i, opt in enumerate(options):
        oid = f"{p}-opt{i}"
        correct = i == correct_index
        style_lines.append(f"#{oid}:checked ~ .qfb-wrap .qfb-{i} {{ display: block; }}")
        inputs += f'<input type="radio" name="{p}-q" id="{oid}" style="{_VH}">\n'
        labels += (
            f'<label for="{oid}" style="display:block;border:2px solid var(--border);'
            f'border-radius:6px;padding:.4rem .7rem;margin:.25rem 0;min-height:44px;'
            f'cursor:pointer">{_e(opt)}</label>\n'
        )
        if correct:
            feedback += (
                f'<p class="qfb qfb-{i}" style="border:2px solid var(--c-val);'
                f'border-radius:6px;padding:.4rem .7rem;color:var(--c-val)">'
                f'✓ Correct. {_e(explanation)}</p>\n'
            )
        else:
            feedback += (
                f'<p class="qfb qfb-{i}" style="border:2px solid var(--c-err);'
                f'border-radius:6px;padding:.4rem .7rem;color:var(--c-err)">'
                f'✗ Not quite — try again. (Answer: {_e(explanation)})</p>\n'
            )
    style = "\n".join(style_lines)
    return (
        f'<fieldset id="{p}" style="border:2px solid var(--border);border-radius:8px;padding:.6rem .8rem">\n'
        f"<style>\n{style}\n</style>\n"
        f"<legend>{_e(question)}</legend>\n"
        f"{inputs}{labels}"
        f'<div class="qfb-wrap">\n{feedback}</div>\n'
        f"</fieldset>\n"
    )


# ---------------------------------------------------------------------------
# 6. Output + status
# ---------------------------------------------------------------------------


def compile_status_badge(comp_id: str, ok: bool, *, label: str | None = None,
                         kind: str = "compile") -> str:
    """Build/run verdict shown by text + icon + border in addition to colour.

    ``kind`` distinguishes the two ways a program can fail so they never look
    alike: ``"compile"`` (red ``❌ Compile failed``) versus ``"runtime"`` (amber
    ``💥 Runtime error`` — the program compiled but crashed). Ignored when *ok*.
    A program that exits normally with a nonzero code is *ok* here: it shows
    ``✓ Compiled · exit code N`` (see ``build_html._crashed``).
    The icons match the tab-label glyphs: ✗ for a build the compiler rejects,
    💥 for a crash. ⚠ is reserved for the third case — a tab that compiles, runs,
    and is still wrong — so it never appears as a badge.
    """
    p = _safe(comp_id)
    if ok:
        icon, txt, color = "✓", label or "Compiled", "var(--c-val)"
    elif kind == "runtime":
        icon, txt, color = "💥", label or "Runtime error", "var(--c-const)"
    else:
        icon, txt, color = "❌", label or "Compile failed", "var(--c-err)"
    return (
        f'<span class="badge" id="{p}" '
        f'style="border:2px solid {color};color:{color}">'
        f"{icon} {_e(txt)}</span>"
    )


_OUTPUT_LINE_LIMIT = 12  # long output beyond this many lines folds into <details>


def _samp_pre(text: str) -> str:
    """Wrap sample output as a semantic ``<pre><samp>`` (never a bare ``<pre>``)."""
    return (f'<pre style="margin:0;background:none;color:inherit;padding:0">'
            f"<samp>{_e(text)}</samp></pre>")


def output_console(comp_id: str, text: str, *, error: bool = False,
                   title: str | None = None, kind: str = "compile") -> str:
    """Monospaced output block; the error variant is marked by text + border.

    On an error, ``kind`` picks the failure styling so a compile error and a
    runtime crash are unmistakably different: ``"compile"`` (red border,
    *Compiler error*) versus ``"runtime"`` (amber border, *Runtime error*).

    Very long output (compiler template/STL walls, ASan reports) is shortened:
    the first :data:`_OUTPUT_LINE_LIMIT` lines show inline and the remainder
    folds into a native ``<details>`` disclosure, keeping the panel readable.
    """
    p = _safe(comp_id)
    if error and kind == "runtime":
        heading = title or "Runtime error"
        border = "var(--c-const)"
        cls = "console console--runtime"
    elif error:
        heading = title or "Compiler error"
        border = "var(--c-err)"
        cls = "console console--err"
    else:
        heading = title or "Program output"
        border = "var(--border)"
        cls = "console"

    lines = text.split("\n")
    if len(lines) > _OUTPUT_LINE_LIMIT:
        head = "\n".join(lines[:_OUTPUT_LINE_LIMIT])
        rest = "\n".join(lines[_OUTPUT_LINE_LIMIT:])
        more = len(lines) - _OUTPUT_LINE_LIMIT
        body = (
            _samp_pre(head)
            + f'<details class="console-more"><summary>'
            + f'<span class="caret" aria-hidden="true">▸</span>'
            + f"Show {more} more line{'s' if more != 1 else ''}</summary>\n"
            + _samp_pre(rest)
            + "</details>\n"
        )
    else:
        body = _samp_pre(text)

    return (
        f'<div class="{cls}" id="{p}" style="border:2px solid {border}">'
        f'<span class="console-label">{_e(heading)}</span>'
        f"{body}"
        f"</div>\n"
    )


# ---------------------------------------------------------------------------
# 7. Secondary diagram interactions
# ---------------------------------------------------------------------------


def _byte_glyph(hex_byte: str) -> str:
    """Printable-ASCII character for a hex byte string, else ``·``.

    Bytes in the printable range (0x20–0x7e) render as their character; every
    other byte (a NUL, an address byte, the high byte of a length) renders as a
    middle dot, so text data reads as text and non-text bytes read as noise.
    """
    try:
        v = int(hex_byte, 16)
    except ValueError:
        return "·"
    return chr(v) if 0x20 <= v <= 0x7e else "·"


def _int_group_row(byte_values: Sequence[str], size: int, label: str) -> str:
    """A grouped decoded-int row: every *size* bytes → one ``colspan`` cell holding
    the little-endian signed value. A trailing partial group spans what it has."""
    cells = []
    for i in range(0, len(byte_values), size):
        grp = byte_values[i:i + size]
        try:
            raw = bytes(int(b, 16) for b in grp)
            txt = str(int.from_bytes(raw, "little", signed=True))
        except ValueError:
            txt = "?"
        cells.append(f'<td class="byte-int" colspan="{len(grp)}">{_e(txt)}</td>')
    return f'<tr><th scope="row">{_e(label)}</th>{"".join(cells)}</tr>\n'


def byte_grid(comp_id: str, byte_values: Sequence[str], *, caption: str = "Memory bytes",
              show_ascii: bool = True, decode: str = "") -> str:
    """Render a byte sequence as a labelled, captioned grid (little-endian).

    With ``show_ascii`` (the default) a third ``char`` row maps each byte to its
    printable-ASCII glyph (``·`` for non-printable), so string data reads as
    characters: a short string's inline ``h e l l o`` stands out plainly against
    the all-``·`` address bytes of a heap pointer.

    ``decode="int32"`` instead adds a grouped row that folds every 4 bytes into one
    ``colspan`` cell holding the decoded little-endian int — legible for a numeric
    array (an ``int arr[5]`` reads as ``10 | 20 | 30 | 40 | 50``, each value sitting
    over its 4 bytes), where the per-byte ``char`` row is noise. It replaces the
    char row, so the caller opts into exactly one third row.
    """
    p = _safe(comp_id)
    index_row = "".join(f'<th scope="col">{i}</th>' for i in range(len(byte_values)))
    value_row = "".join(f'<td class="byte-cell">{_e(b)}</td>' for b in byte_values)
    if decode == "int32":
        extra_row = _int_group_row(byte_values, 4, "int32")
    elif show_ascii:
        char_cells = "".join(
            f'<td class="byte-char">{_e(_byte_glyph(b))}</td>' for b in byte_values
        )
        extra_row = f'<tr><th scope="row">char</th>{char_cells}</tr>\n'
    else:
        extra_row = ""
    # A wide byte dump (e.g. a 32-byte std::string) is broader than the panel; the
    # scroll wrapper keeps it inside the column and adds a horizontal scrollbar
    # instead of letting the table overrun the page edge.
    # The caller (a <details> disclosure) usually carries the label in its
    # <summary>, so an empty caption suppresses the table's own <caption> rather
    # than duplicating that line; a non-empty caption still renders (direct use).
    caption_html = f"<caption>{_e(caption)}</caption>\n" if caption else ""
    return (
        f'<div class="byte-grid-wrap">\n'
        f'<table class="byte-grid" id="{p}">\n'
        f"{caption_html}"
        f'<thead><tr><th scope="row">byte</th>{index_row}</tr></thead>\n'
        f'<tbody><tr><th scope="row">value</th>{value_row}</tr>\n'
        f"{extra_row}"
        f"</tbody>\n"
        f"</table>\n"
        f"</div>\n"
    )


def code_line_link(
    comp_id: str,
    lines: Sequence[tuple[str, str | None]],
    ptrdata: dict[str, Any] | None = None,
) -> str:
    """Hovering/focusing a linked source line highlights its diagram box.

    Each linked line and its diagram box share a ``comp_id``-namespaced class so
    a CSS ``:hover``/``:focus`` rule connects them — no JavaScript.
    """
    pd = ptrdata or {}
    p = _safe(comp_id)
    keys = sorted({k for _c, k in lines if k})

    # The highlight uses the general-sibling combinator (`~`), so the linked
    # source line and the diagram box MUST be siblings under #{p}.  Lines are
    # therefore emitted as direct children of the container (not wrapped in a
    # <pre>, which would trap them one level down and break the rule); a shared
    # background makes the consecutive lines read as one code block.
    style_lines = [
        f"#{p} .cll-line {{ display:block; margin:0; padding:.1rem .7rem;"
        " font:14px/1.6 ui-monospace,monospace;"
        # Each source line is a <code> (not a <pre>), so the default
        # white-space:normal would collapse its leading indentation away.
        " white-space:pre-wrap;"
        " background:var(--code-bg); color:var(--code-fg); }",
        f"#{p} .cll-line:first-of-type {{ border-radius:8px 8px 0 0; padding-top:.5rem; }}",
        f"#{p} .cll-line:last-of-type {{ border-radius:0 0 8px 8px; padding-bottom:.5rem; }}",
        f"#{p} .cll-link {{ cursor:pointer; text-decoration:underline dotted; }}",
        f"#{p} .cll-diagram {{ margin-top:.6rem; }}",
    ]
    for k in keys:
        sk = _safe(k)
        style_lines.append(
            f"#{p} .ln-{sk}:hover ~ .cll-diagram .bx-{sk},"
            f"#{p} .ln-{sk}:focus ~ .cll-diagram .bx-{sk}"
            " { outline: 3px solid var(--c-link); background: #f3edff; }"
        )
    style = "\n".join(style_lines)

    code_lines = ""
    # Instrumentation lines recede here exactly as they do in the plain panel;
    # one rule, in cpp_labs/scaffold.py, so the two render paths cannot drift.
    dims = dict((c, d) for (c, d) in _scaffold_flags([c for c, _k in lines]))
    for code, k in lines:
        sc = " code-scaffold" if dims.get(code) else ""
        if k:
            sk = _safe(k)
            code_lines += (
                f'<code class="cll-line cll-link ln-{sk}{sc}" tabindex="0">'
                f'{_e(code)}</code>\n'
            )
        else:
            code_lines += f'<code class="cll-line{sc}">{_e(code)}</code>\n'

    boxes = ""
    for k in keys:
        sk = _safe(k)
        boxes += (
            f'<span class="bx bx-{sk}" '
            f'style="display:inline-block;border:1px solid var(--c-addr);'
            f'border-radius:6px;padding:.2rem .5rem;margin:.2rem">'
            f'{_e(k)} → {_e(pd.get("target_val", "?"))}</span>\n'
        )

    return (
        f'<div id="{p}" style="display:flex;flex-direction:column">\n'
        f"<style>\n{style}\n</style>\n"
        f"{code_lines}"
        f'<div class="cll-diagram">{boxes}</div>\n'
        f"</div>\n"
    )


def console_line_link(
    comp_id: str,
    source_lines: "Sequence[tuple[str, str | None]]",
    console_lines: "Sequence[tuple[str, str | None]]",
    language: str = "cpp",
    *,
    tri_source: "Sequence[tuple[str, str]] | None" = None,
    tri_console: "Sequence[tuple[str, str]] | None" = None,
) -> str:
    """Bidirectional hover link between real console output lines and the source
    ``cout`` that produced them (item 22; M10 trace-reading).

    Each keyed source line and the console line(s) it produced share a
    ``comp_id``-namespaced ``k-<key>`` class. Hovering/focusing either endpoint
    highlights both via ``:has()`` — order-independent, so the highlight goes both
    ways, no JavaScript. A CSS mirror of :func:`code_line_link`, extended to be
    bidirectional and to link line↔line instead of line↔box.

    Source lines carry ``language-<language>`` so the page's highlight.js pass
    (see :func:`page_shell`) colours them per line; the console rows stay plain
    (they are program output, not code).

    When *tri_source* and *tri_console* are both provided (tri-link mode), the
    component emits ``data-cll`` attributes on each keyed row instead of the
    ``k-<key>`` CSS classes, and omits the per-key ``:has()`` rules — the page
    JS handler drives highlighting in that mode."""
    p = _safe(comp_id)

    # --- Tri-link mode: data-cll attributes, no :has() CSS ---
    if tri_source is not None and tri_console is not None:
        def _rows_keyed(lines, keyed, lang=""):
            lc = f" language-{lang}" if lang else ""
            out = ""
            for (code, _k), (_t, keystr) in zip(lines, keyed):
                attr = f' data-cll="{_e(keystr)}"' if keystr else ""
                link = " cll-link" if keystr else ""
                tab = ' tabindex="0"' if keystr else ""
                out += f'<code class="cll-line{link}{lc}"{attr}{tab}>{_e(code)}</code>\n'
            return out

        style_lines = [
            f"#{p} .cll-line {{ display:block; margin:0; padding:.1rem .7rem;"
            " font:14px/1.6 ui-monospace,monospace;"
            # Each source line is a <code> (not a <pre>), so the default
            # white-space:normal would collapse its leading indentation away.
            " white-space:pre-wrap;"
            " background:var(--code-bg); color:var(--code-fg); }",
            # Program output is a light console panel, never dark code — the
            # output region overrides the shared dark .cll-line background.
            f"#{p} .cll-out .cll-line {{ background:var(--panel-bg);"
            " color:var(--fg); }",
            f"#{p} .cll-src .cll-line:first-of-type,"
            f"#{p} .cll-out .cll-line:first-of-type"
            " { border-radius:8px 8px 0 0; padding-top:.5rem; }",
            f"#{p} .cll-src .cll-line:last-of-type,"
            f"#{p} .cll-out .cll-line:last-of-type"
            " { border-radius:0 0 8px 8px; padding-bottom:.5rem; }",
            f"#{p} .cll-out {{ margin-top:.3rem; }}",
            f"#{p} .cll-label {{ font-weight:700; margin:.8rem 0 .2rem; }}",
            f"#{p} .cll-link {{ cursor:pointer; text-decoration:underline dotted; }}",
        ]
        style = "\n".join(style_lines)
        return (
            f'<div id="{p}" style="display:flex;flex-direction:column">\n'
            f"<style>\n{style}\n</style>\n"
            f'<div class="cll-src">\n{_rows_keyed(source_lines, tri_source, language)}</div>\n'
            f'<div class="cll-label">Program output</div>\n'
            f'<div class="cll-out">\n{_rows_keyed(console_lines, tri_console)}</div>\n'
            f"</div>\n"
        )

    # --- Original (non-tri) path ---
    keys = sorted({k for _c, k in source_lines if k}
                  | {k for _c, k in console_lines if k})
    style_lines = [
        f"#{p} .cll-line {{ display:block; margin:0; padding:.1rem .7rem;"
        " font:14px/1.6 ui-monospace,monospace;"
        # Each source line is a <code> (not a <pre>), so the default
        # white-space:normal would collapse its leading indentation away.
        " white-space:pre-wrap;"
        " background:var(--code-bg); color:var(--code-fg); }",
        # Program output is a light console panel, never dark code — the output
        # region overrides the shared dark .cll-line background.
        f"#{p} .cll-out .cll-line {{ background:var(--panel-bg);"
        " color:var(--fg); }",
        # Qualify by region: the cll-label between the two blocks would otherwise
        # break :first/:last-of-type rounding across them.
        f"#{p} .cll-src .cll-line:first-of-type,"
        f"#{p} .cll-out .cll-line:first-of-type"
        " { border-radius:8px 8px 0 0; padding-top:.5rem; }",
        f"#{p} .cll-src .cll-line:last-of-type,"
        f"#{p} .cll-out .cll-line:last-of-type"
        " { border-radius:0 0 8px 8px; padding-bottom:.5rem; }",
        f"#{p} .cll-out {{ margin-top:.3rem; }}",
        f"#{p} .cll-label {{ font-weight:700; margin:.8rem 0 .2rem; }}",
    ]
    # Only when keyed lines exist (no keys → no .cll-link elements → dead rule).
    if keys:
        style_lines.append(
            f"#{p} .cll-link {{ cursor:pointer; text-decoration:underline dotted; }}"
        )
    for k in keys:
        sk = _safe(k)
        # Fixed light-violet highlight bg → force dark text so it stays readable in
        # any theme (unlike code_line_link, whose highlight inherits --code-fg).
        style_lines.append(
            f"#{p}:has(.k-{sk}:hover) .k-{sk},"
            f"#{p}:has(.k-{sk}:focus) .k-{sk}"
            " { outline:3px solid var(--c-link); outline-offset:-3px;"
            " background:#f3edff; color:#111; }")
    style = "\n".join(style_lines)

    def _rows(lines: "Sequence[tuple[str, str | None]]", lang: str = "") -> str:
        # ``lang`` adds ``language-<lang>`` so highlight.js colours the row; the
        # console side passes "" (output is not code, must not be highlighted).
        lc = f" language-{lang}" if lang else ""
        # Dim instrumentation on the SOURCE side only: the console side is the
        # program's real output, where these markers have already been stripped.
        dims = (dict(_scaffold_flags([c for c, _k in lines])) if lang else {})
        out = ""
        for code, k in lines:
            sc = " code-scaffold" if dims.get(code) else ""
            if k:
                sk = _safe(k)
                out += (f'<code class="cll-line cll-link k-{sk}{lc}{sc}" tabindex="0">'
                        f"{_e(code)}</code>\n")
            else:
                out += f'<code class="cll-line{lc}{sc}">{_e(code)}</code>\n'
        return out

    return (
        f'<div id="{p}" style="display:flex;flex-direction:column">\n'
        f"<style>\n{style}\n</style>\n"
        f'<div class="cll-src">\n{_rows(source_lines, language)}</div>\n'
        f'<div class="cll-label">Program output</div>\n'
        f'<div class="cll-out">\n{_rows(console_lines)}</div>\n'
        f"</div>\n"
    )


# ---------------------------------------------------------------------------
# 8. Layout + stepped
# ---------------------------------------------------------------------------


def variant_tabs(comp_id: str, panels: Sequence[tuple[str, str]], *, selected: int = 0) -> str:
    """Switch between N labelled panels with native radios + ``:checked ~``.

    A single panel has nothing to switch between, so the tab strip is noise:
    render just its body in the same bordered container, with no radios/labels.
    """
    p = _safe(comp_id)
    if len(panels) == 1:
        _, body = panels[0]
        return (
            f'<div id="{p}">\n'
            f'<div class="vt-panels-{p}" style="border:2px solid var(--border);'
            f'border-radius:8px;padding:.7rem">\n{body}</div>\n'
            f"</div>\n"
        )
    style_lines = [f"#{p} .vt-panel-{p} {{ display: none; }}"]
    inputs, tabs, panel_html = "", "", ""
    for i, (label, body) in enumerate(panels):
        tid = f"{p}-t{i}"
        checked = " checked" if i == selected else ""
        style_lines.append(f"#{tid}:checked ~ .vt-panels-{p} .vt-p{i}-{p} {{ display: block; }}")
        style_lines.append(
            f'#{tid}:checked ~ .vt-tabs-{p} label[for="{tid}"]'
            " { background: var(--accent); color: var(--accent-fg); border-color: var(--accent); }")
        style_lines.append(
            f'#{tid}:focus-visible ~ .vt-tabs-{p} label[for="{tid}"]'
            " { outline: 3px solid var(--accent); outline-offset: 2px; }")
        inputs += f'<input type="radio" name="{p}-vt" id="{tid}" style="{_VH}"{checked}>\n'
        tabs += (
            f'<label for="{tid}" style="border:2px solid var(--border);border-radius:8px 8px 0 0;'
            f'padding:.4rem .9rem;min-height:44px;display:inline-flex;align-items:center;'
            f'cursor:pointer;font-weight:700">{_e(label)}</label>\n')
        panel_html += f'<div class="vt-panel-{p} vt-p{i}-{p}">{body}</div>\n'
    style = "\n".join(style_lines)
    return (
        f'<div id="{p}">\n<style>\n{style}\n</style>\n'
        f"{inputs}"
        f'<div class="vt-tabs-{p}" role="group" aria-label="Choose variant" '
        f'style="display:flex;gap:.3rem;flex-wrap:wrap">\n{tabs}</div>\n'
        f'<div class="vt-panels-{p}" style="border:2px solid var(--border);border-radius:0 8px 8px 8px;'
        f'padding:.7rem">\n{panel_html}</div>\n'
        f"</div>\n"
    )


def left_rail_layout(comp_id: str, items: Sequence[tuple[str, str]],
                     *, italic_count: int = 0, selected: int = 0) -> str:
    """Vertical radio rail (left) + panel area (right); one item visible at a time.

    Zero-JS (radio + ``:checked ~``). Reflows to a single column at narrow widths.
    Structural class names are id-namespaced (e.g. ``lr-panel-{p}``) so no class is
    ever shared across instances — nesting can never bleed styles or switching.

    ``italic_count`` renders the first N rail labels in italic (used to set a leading
    glossary entry apart from the demos). ``selected`` picks which panel is shown on
    load (default the first item); the mobile menu button labels that panel.
    """
    p = _safe(comp_id)
    style_lines = [
        f"#{p} {{ display:grid; grid-template-columns:minmax(0,14rem) minmax(0,1fr); gap:1rem; align-items:start; }}",
        f"#{p} .lr-rail-{p} {{ display:flex; flex-direction:column; gap:.3rem; }}",
        f"#{p} .lr-body-{p} {{ min-width:0; }}",
        f"#{p} .lr-panel-{p} {{ display:none; min-width:0; }}",
        f"#{p} .lr-menu-{p} {{ display:none; }}",  # menu toggle: shown only on narrow + JS
        f"@media (max-width:760px) {{ #{p} {{ grid-template-columns:minmax(0,1fr); }} }}",
        # progressive enhancement: with JS, narrow screens collapse the rail behind a menu
        f"@media (max-width:760px) {{ #{p}.lr-js .lr-menu-{p} {{ display:flex; }} }}",
        f"@media (max-width:760px) {{ #{p}.lr-js .lr-rail-{p} {{ display:none; }} }}",
        f"@media (max-width:760px) {{ #{p}.lr-js.lr-open .lr-rail-{p} {{ display:flex; }} }}",
    ]
    inputs, rail, panels = "", "", ""
    for i, (label, body) in enumerate(items):
        rid = f"{p}-r{i}"
        checked = " checked" if i == selected else ""
        italic = "font-style:italic;" if i < italic_count else ""
        style_lines.append(f"#{rid}:checked ~ .lr-body-{p} .lr-p{i}-{p} {{ display:block; }}")
        style_lines.append(
            f'#{rid}:checked ~ .lr-rail-{p} label[for="{rid}"]'
            " { background:var(--accent); color:var(--accent-fg); border-color:var(--accent); }")
        style_lines.append(
            f'#{rid}:focus-visible ~ .lr-rail-{p} label[for="{rid}"]'
            " { outline:3px solid var(--accent); outline-offset:2px; }")
        inputs += f'<input type="radio" name="{p}-lr" id="{rid}" style="{_VH}"{checked}>\n'
        rail += (
            f'<label for="{rid}" style="border:2px solid var(--border);border-radius:8px;'
            f'padding:.5rem .8rem;min-height:44px;display:flex;align-items:center;'
            f'cursor:pointer;font-weight:700;{italic}">{_e(label)}</label>\n')
        panels += f'<div class="lr-panel-{p} lr-p{i}-{p}">{body}</div>\n'
    style = "\n".join(style_lines)
    first = _e(items[selected][0]) if items else "Choose demo"
    menu = (
        f'<button type="button" class="lr-menu-{p}" aria-expanded="false" aria-controls="{p}-rail" '
        f'style="min-height:44px;align-items:center;gap:.5rem;border:2px solid var(--border);'
        f'border-radius:8px;padding:.5rem .8rem;cursor:pointer;font-weight:700">'
        f'<span aria-hidden="true">☰</span>'
        f'<span class="lr-menu-label-{p}">{first}</span></button>\n'
    )
    # Scoped progressive-enhancement script: toggle the menu, and close it (and update
    # the button label) when a demo is picked. Baseline works with JS off (rail visible).
    script = (
        "<script>\n(function(){\n"
        f'var r=document.getElementById("{p}");if(!r)return;r.classList.add("lr-js");\n'
        f'var b=r.querySelector(".lr-menu-{p}"),l=r.querySelector(".lr-menu-label-{p}");\n'
        'function s(o){r.classList.toggle("lr-open",o);'
        'b.setAttribute("aria-expanded",o?"true":"false");}\n'
        'b.addEventListener("click",function(){s(!r.classList.contains("lr-open"));});\n'
        f'r.querySelectorAll(\'input[name="{p}-lr"]\').forEach(function(x){{'
        'x.addEventListener("change",function(){'
        'var t=r.querySelector(\'label[for="\'+x.id+\'"]\');'
        "if(t&&l)l.textContent=t.textContent;s(false);});});\n"
        "})();\n</script>\n"
    )
    return (
        f'<div id="{p}" class="lr">\n<style>\n{style}\n</style>\n'
        f"{inputs}"
        f"{menu}"
        f'<div class="lr-rail-{p}" id="{p}-rail" role="group" aria-label="Choose demo">\n{rail}</div>\n'
        f'<div class="lr-body-{p}">\n{panels}</div>\n'
        f"{script}"
        f"</div>\n"
    )


def nav_shell(comp_id: str, items: Sequence[tuple[str, str]], *,
              style: str = "left_rail", leading: int = 0,
              selected: int | None = None) -> str:
    """Arrange a set of titled panels using one chosen navigation style.

    Each panel is a ``(title, html)`` pair. This one function handles all three
    styles, so a page can choose its style purely from its data:

    - ``"left_rail"``: a clickable list down the left; one panel shows at a time.
    - ``"top_tabs"``: a row of tabs across the top; one panel shows at a time.
    - ``"stacked"``: every panel shown one below another, with no switching.

    Args:
        comp_id: A short unique name for this block, used to build its HTML ids.
        items: The panels, in order, each a ``(title, html)`` pair.
        style: Which navigation style to use (see the list above).
        leading: How many of the first entries are reference material (such as
            Vocabulary or the page Concept) to set apart. The left-rail style
            shows them in italics; the other styles ignore this.
        selected: Which panel is open when the page loads, given by its position
            (0 is the first). The left-rail and top-tabs styles honour it; the
            stacked style ignores it. ``None`` means the first panel.

    Returns:
        The navigation block as a piece of HTML.

    Raises:
        ValueError: If ``style`` is not one of the three names above.
    """
    sel = 0 if selected is None else selected
    if style == "left_rail":
        return left_rail_layout(comp_id, items, italic_count=leading, selected=sel)
    if style == "top_tabs":
        return variant_tabs(comp_id, items, selected=sel)
    if style == "stacked":
        return "\n".join(body for _label, body in items)
    raise ValueError(
        f"unknown nav style {style!r}; valid choices: "
        "['left_rail', 'stacked', 'top_tabs']")


def code_diagram_panel(comp_id: str, code_html: str, diagram_html: str,
                       *, ratio: tuple[int, int] = (3, 1)) -> str:
    """Two-column code/diagram split; code scrolls; reflows to one column.

    ``ratio`` is (code_fraction, diagram_fraction) for the CSS grid tracks;
    the default (3, 1) gives the code three-quarters. Diagram-heavy subjects
    (stack frames, memory map) pass (2, 1) so the taller diagram gets more room.
    """
    p = _safe(comp_id)
    cf, df = ratio
    style = (
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,{cf}fr) minmax(0,{df}fr); gap: 1rem; }}\n"
        f"#{p} .cdp-code {{ min-width:0; }}\n"
        f"#{p} .cdp-diagram {{ min-width:0; }}\n"
        f"@media (max-width: 760px) {{ #{p} {{ grid-template-columns: minmax(0,1fr); }} }}"
    )
    return (
        f'<div id="{p}" class="cdp">\n<style>\n{style}\n</style>\n'
        f'<div class="cdp-code">{code_html}</div>\n'
        f'<div class="cdp-diagram">{diagram_html}</div>\n'
        f"</div>\n"
    )


def zoomable(comp_id: str, inner_html: str, *, label: str = "⤢ Enlarge") -> str:
    """Wrap HTML in a zero-JS click-to-enlarge container with zoom levels.

    A visually-hidden but keyboard-focusable checkbox drives the open state; the
    visible ``label`` chip opens it. When checked, the SAME ``.zoom-content``
    (``inner_html`` verbatim — never duplicated, so any SVGs inside keep their
    one-to-one ``role="img"`` AND stay interactive) is scaled IN PLACE.

    The key sizing property: ``.zoom-content`` stays in normal flow, so it keeps
    the width it had in the right panel (a diagram shrunk to fit its column
    renders at that shrunk "panel size"). The zoom-level radios then apply
    ``transform: scale(k)`` — a visual-only scale relative to that panel size, no
    reflow. So **1× is byte-identical to the panel**, 2× is exactly twice the
    panel, etc. (An earlier version promoted the panel to a fixed ``fit-content``
    overlay, which re-based the diagram to its *natural* size — so 1× rendered
    larger than the panel. Scaling in place fixes that.) A fixed full-viewport
    ``.zoom-backdrop`` dims the page; the scaled diagram sits above it and grows
    from its column (``transform-origin: top right``) over the code to its left.
    Five levels — 0.5× / 0.75× / 1× / 1.5× / 2×, default 1.5×; clicking the
    backdrop or ✕ closes. 44px touch targets; no ESC (that would need scripting)."""
    p = _safe(comp_id)
    # (sid, label, aria, scale-factor) — a transform:scale multiplier, relative
    # to the diagram's panel-rendered size (so 1× == the size in the panel).
    levels = [
        ("zl0", "0.5×", "half size", "0.5"),
        ("zl1", "0.75×", "three-quarter size", "0.75"),
        ("zl2", "1×", "actual size", "1"),
        ("zl3", "1.5×", "1.5 times", "1.5"),
        ("zl4", "2×", "2 times", "2"),
    ]
    default = "zl3"
    active_sel = ", ".join(
        f"#{p} #{p}-{sid}:checked ~ .zoom-bar label[for={p}-{sid}]"
        for sid, _lab, _aria, _z in levels)
    # Visible keyboard focus (WCAG 2.4.7) on the hidden zoom-level radios.
    focus_sel = ", ".join(
        f"#{p} #{p}-{sid}:focus-visible ~ .zoom-bar label[for={p}-{sid}]"
        for sid, _lab, _aria, _z in levels)
    scale_css = "".join(
        f"#{p} .zoom-cb:checked ~ .zoom-body #{p}-{sid}:checked ~ .zoom-content"
        f" {{ transform:scale({z}); }}\n"
        for sid, _lab, _aria, z in levels)
    style = (
        # hidden-but-focusable controls
        f"#{p} .zoom-cb, #{p} .zl {{ position:absolute; width:1px; height:1px;"
        f" overflow:hidden; clip:rect(0 0 0 0); white-space:nowrap; }}\n"
        f"#{p} .zoom-open {{ display:inline-flex; align-items:center; min-height:44px;"
        f" padding:.2rem .7rem; margin:.2rem 0 .4rem; border:1px solid var(--border,#bbb);"
        f" border-radius:8px; background:var(--panel-bg,#fff); cursor:pointer;"
        f" font:13px system-ui; width:fit-content; }}\n"
        f"#{p} .zoom-cb:focus-visible ~ .zoom-open {{ outline:2px solid var(--accent,#2a6);"
        f" outline-offset:2px; }}\n"
        f"#{p} .zoom-bar, #{p} .zoom-close, #{p} .zoom-backdrop {{ display:none; }}\n"
        # --- open state: scale the diagram IN PLACE (keeps its panel size as the
        # scale base, so 1x == panel and kx == k*panel) ---
        # Dimming backdrop: a fixed full-viewport label; clicking it closes.
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-backdrop {{ display:block;"
        f" position:fixed; inset:0; z-index:1000; background:rgba(0,0,0,.5); }}\n"
        # The diagram stays in flow (keeps its panel width as the scale base) and
        # is lifted above the backdrop; scale_css (below) grows it from its column
        # position over the code to its left. transform is visual-only (no reflow).
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-content {{ position:relative;"
        f" z-index:1002; transform-origin:top right; }}\n"
        # toolbar: fixed at the viewport top so the level controls stay reachable
        # while the diagram expands over the page below.
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-bar {{ display:flex; flex-wrap:wrap;"
        f" gap:.4rem; align-items:center; position:fixed; top:0; left:0; right:0;"
        f" z-index:1003; padding:.5rem; background:#f4f6fb;"
        f" border-bottom:1px solid #ccc; }}\n"
        f"#{p} .zoom-bar .zlab {{ min-height:44px; display:inline-flex; align-items:center;"
        f" padding:.2rem .7rem; border:1px solid #bbb; border-radius:6px; background:#fff;"
        f" cursor:pointer; font:13px system-ui; }}\n"
        f"{active_sel} {{ background:#2a7f54; color:#fff; border-color:#2a7f54; }}\n"
        f"{focus_sel} {{ outline:3px solid var(--accent); outline-offset:2px; }}\n"
        f"#{p} .zoom-cb:checked ~ .zoom-body .zoom-close {{ display:inline-flex;"
        f" margin-left:auto; align-items:center; justify-content:center; min-width:44px;"
        f" min-height:44px; border:1px solid #bbb; border-radius:8px; background:#fff;"
        f" cursor:pointer; font-size:20px; }}\n"
        + scale_css
    )
    radios = "".join(
        f'<input type="radio" class="zl" name="{p}-zl" id="{p}-{sid}"'
        f'{" checked" if sid == default else ""} aria-label="{aria}">'
        for sid, _lab, aria, _h in levels)
    zlabs = "".join(
        f'<label for="{p}-{sid}" class="zlab">{lab}</label>'
        for sid, lab, _aria, _h in levels)
    return (
        f'<div id="{p}" class="zoomwrap"><style>{style}</style>'
        f'<input type="checkbox" class="zoom-cb" id="{p}-zcb" '
        f'aria-label="Enlarge diagram">'
        f'<label for="{p}-zcb" class="zoom-open">{_e(label)}</label>'
        f'<div class="zoom-body">'
        + radios
        + f'<div class="zoom-bar" role="group" aria-label="Zoom level">'
        + zlabs
        + f'<label for="{p}-zcb" class="zoom-close" aria-label="Close" '
        f'title="Close">✕</label>'
        f'</div>'
        f'<div class="zoom-content">{inner_html}</div>'
        f'<label for="{p}-zcb" class="zoom-backdrop" aria-hidden="true"></label>'
        f'</div></div>'
    )



# Marking text changed after a lesson was taught (author, 2026-10-12). A demo
# taught in a past lesson is a record of that lesson, so a later edit says so:
#   [added <when>] Paragraph text.   -> a labelled box: "Added <when>."
#   Paragraph text. [changed <date>: the text as taught]
#                                    -> the paragraph, then a <details> line
#                                       that opens the text as taught.
_ADDED_RE = re.compile(r"\A\[added ([^\]\n]+)\]\s*")
_CHANGED_RE = re.compile(r"\s*\[changed ([^:\]\n]+): ([^\]\n]+)\]\s*\Z")


def _prose_inline(s: str) -> str:
    return _emphasis(_inline_code(_prose_links(_demo_links(_e(s)))))


def _paragraph_html(p: str, margin: str) -> str:
    added = _ADDED_RE.match(p)
    if added:
        label = added.group(1).rstrip(".")
        return (f'<div class="prose-added" style="margin:{margin};'
                'border-left:4px solid var(--accent);padding:.2rem 0 .2rem .6rem">'
                f'<p style="margin:0"><strong>Added {_e(label)}.</strong></p>'
                f'<p style="margin:.3rem 0 0">{_prose_inline(p[added.end():])}</p></div>')
    changed = _CHANGED_RE.search(p)
    if changed:
        when = changed.group(1).strip().rstrip(".")
        return (f'<p style="margin:{margin}">{_prose_inline(p[:changed.start()])}</p>'
                '<details class="prose-changed" style="margin:.2rem 0 0">'
                f'<summary style="cursor:pointer;font-size:.9em">Changed {_e(when)}. '
                'Show the text as taught.</summary>'
                f'<p style="margin:.3rem 0 0;opacity:.85">{_prose_inline(changed.group(2))}</p>'
                '</details>')
    return f'<p style="margin:{margin}">{_prose_inline(p)}</p>'


def _paragraphs_html(text: str) -> str:
    """Escape *text* into one ``<p>`` per blank-line-separated paragraph.

    A source string with a blank line in it (a YAML folded scalar turns that
    into one literal ``\\n``) becomes one paragraph per line here. Text with
    no blank line stays exactly one ``<p style="margin:0">`` — today's
    behaviour, unchanged. A paragraph carrying an ``[added …]`` or
    ``[changed …: …]`` marker is rendered as described above ``_ADDED_RE``.
    """
    paragraphs = [p for p in text.split("\n") if p.strip()]
    return "".join(
        _paragraph_html(p, "0" if i == 0 else ".6rem 0 0")
        for i, p in enumerate(paragraphs)
    )


def _concept_aside_body(title: str, text: str) -> str:
    """The Key Idea aside's inner markup, shared by both aside renderers.

    Extracted so the outer two-column panel (:func:`code_concept_panel`) and the
    standalone in-tab aside (:func:`_concept_aside`) compose the identical
    (escaped) content — one place to change the aside's body.
    """
    body = _paragraphs_html(text)
    return f'<b class="ccp-title">{_e(title)}</b>' + body


def _concept_aside(comp_id: str, text: str, *, title: str = "Key Idea") -> str:
    """The Key Idea aside as a standalone block, for INSIDE a tab panel.

    Same look as the aside :func:`code_concept_panel` renders (same body, same
    box styles), but self-scoped (own id + <style>) so it can sit in a
    per-variant right column — the ``aside_html`` stack
    (ENGINE_REQUEST_prompt-panel) — instead of the outer two-column wrap.
    """
    p = _safe(comp_id)
    style = (
        f"#{p} {{ min-width: 0; max-height: calc(100vh - 4rem); overflow-y: auto;"
        f" border-left: 4px solid var(--accent); background: var(--panel-bg);"
        f" border-radius: 0 6px 6px 0; padding: .5rem .8rem; }}\n"
        f"#{p} .ccp-title {{ display: block; font-weight: 700; margin-bottom: .3rem; }}"
    )
    return (
        f'<aside id="{p}" class="ccp-aside">\n<style>\n{style}\n</style>\n'
        + _concept_aside_body(title, text)
        + "</aside>\n"
    )


def code_concept_panel(comp_id: str, main_html: str, concept_text: str,
                       *, title: str = "Key Idea") -> str:
    """Two-column split: the demo on the left, a titled Key Idea aside on the right.

    Used on subjects with no memory diagram so the otherwise-empty right column
    carries the per-example Concept instead. The aside is capped to the left
    column's height and scrolls internally (``overflow-y:auto``) so a long
    concept never stretches the panel; it is absolutely positioned so the row
    height is driven by the code, not the concept. On narrow screens it reflows
    below the code and shows in full.

    Args:
        comp_id: A short unique name, used to build CSS-safe element ids.
        main_html: The left column's content (the code/tabs cluster).
        concept_text: The Key Idea prose shown in the right aside.
        title: The bold heading on the aside; defaults to "Key Idea".

    Returns:
        The two-column panel as a piece of HTML.
    """
    p = _safe(comp_id)
    style = (
        # Code gets ~two-thirds; the prose Concept wraps comfortably in the rest.
        f"#{p} {{ display: grid; grid-template-columns: minmax(0,2fr) minmax(0,1fr);"
        f" gap: 1rem; align-items: start; }}\n"
        f"#{p} .ccp-main {{ min-width: 0; }}\n"
        # Top-aligned aside sized to its own content (no forced stretch, so a
        # short concept never leaves a tall empty box); capped to the viewport
        # and scrolls internally so a long concept never stretches the page.
        # Box styles mirrored in _concept_aside (drift guard: test_aside_box_styles_match_outer_panel).
        f"#{p} .ccp-aside {{ min-width: 0; max-height: calc(100vh - 4rem); overflow-y: auto;"
        f" border-left: 4px solid var(--accent); background: var(--panel-bg);"
        f" border-radius: 0 6px 6px 0; padding: .5rem .8rem; }}\n"
        f"#{p} .ccp-title {{ display: block; font-weight: 700; margin-bottom: .3rem; }}\n"
        f"@media (max-width: 760px) {{ #{p} {{ grid-template-columns: minmax(0,1fr); }} }}"
    )
    return (
        f'<div id="{p}" class="ccp">\n<style>\n{style}\n</style>\n'
        f'<div class="ccp-main">{main_html}</div>\n'
        f'<aside class="ccp-aside">'
        + _concept_aside_body(title, concept_text)
        + "</aside>\n"
        f"</div>\n"
    )


def stacked_subcases(comp_id: str, subcases: Sequence[tuple[str, str]]) -> str:
    """Stack independent sub-cases at natural height (the page scrolls).

    An earlier fixed ``max-height`` boxed the stacked cases into a small
    scroll-region that floated in empty space on tall screens; letting them flow
    fills that space and shows every case's code in full.
    """
    p = _safe(comp_id)
    style = f"#{p} {{ min-width: 0; }}"
    cases = ""
    for label, body in subcases:
        cases += (
            f'<section class="ssc-case" style="border:1px solid var(--border);'
            f'border-radius:8px;padding:.6rem;margin-bottom:.8rem">\n'
            f"<h3>{_e(label)}</h3>\n{body}\n</section>\n"
        )
    return f'<div id="{p}" class="ssc">\n<style>\n{style}\n</style>\n{cases}</div>\n'


def frames_anatomy_details(comp_id: str, pd: dict) -> str:
    """A native <details> disclosure wrapping the full per-frame anatomy SVG."""
    p = _safe(comp_id)
    return (
        f'<details style="margin-top:.5rem;border:1px solid #ddd;border-radius:6px;'
        f'padding:.3rem .6rem"><summary style="cursor:pointer;min-height:44px;'
        f'font-weight:600">Show full frame anatomy</summary>\n'
        + _svg_frames_anatomy(pd, f"{p}-an")
        + "</details>\n"
    )


def stepped_frames(comp_id: str, steps, *, with_anatomy: bool = False) -> str:
    """Zero-JS CSS-radio stepper over frame snapshots: one radio + one frame SVG
    per step; selecting a step shows that snapshot. Frames present at a deeper
    step but gone at the current one are drawn ghost (reclaimed). Defaults to
    the deepest step. Assumes each step's frame list is a prefix of the deepest
    (true for straight call chains and recursion).

    When ``with_anatomy`` is set, a <details> "Show full frame anatomy" is
    emitted *inside the same container* holding one per-step anatomy table; the
    same step radios drive it, so the anatomy always matches the selected step
    (all frames live at that step, not just main)."""
    p = _safe(comp_id)
    ptrbytes, deepest = 8, []
    parsed = []
    for s in steps:
        pb, frames = _parse_frames(s)
        parsed.append(frames)
        if len(frames) > len(deepest):
            ptrbytes, deepest = pb, frames
    default = max(range(len(parsed)), key=lambda i: len(parsed[i])) if parsed else 0

    inputs, labels, views, ans = [], [], [], []
    css = [f"#{p} .sf-v {{ display:none; }}"]
    if with_anatomy:
        css.append(f"#{p} .sf-an {{ display:none; }}")
    for i, frames in enumerate(parsed):
        checked = " checked" if i == default else ""
        inputs.append(f'<input type="radio" name="{p}-step" id="{p}-s{i}"{checked} '
                      f'style="position:absolute;opacity:0">')
        labels.append(
            f'<label for="{p}-s{i}" style="cursor:pointer;border:1px solid #bbb;'
            f'border-radius:6px;padding:2px 9px;font:13px system-ui;'
            f'min-height:44px;display:inline-flex;align-items:center">'
            f'{i + 1}</label>')
        svg = _frames_core(deepest, f"{p}-fr{i}", solid=len(frames))
        views.append(f'<div class="sf-v sf-v{i}">{svg}</div>')
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-views .sf-v{i} {{ display:block; }}")
        css.append(f"#{p} #{p}-s{i}:checked ~ .sf-steps label[for={p}-s{i}] "
                   f"{{ background:#2a7f54; color:#fff; border-color:#2a7f54; }}")
        # Visible keyboard focus (WCAG 2.4.7): the radio is hidden, so forward
        # the focus ring to its step-number label.
        css.append(f"#{p} #{p}-s{i}:focus-visible ~ .sf-steps label[for={p}-s{i}] "
                   f"{{ outline:3px solid var(--accent); outline-offset:2px; }}")
        if with_anatomy:
            an_svg = _svg_frames_anatomy(steps[i], f"{p}-an{i}")
            ans.append(f'<div class="sf-an sf-an{i}">{an_svg}</div>')
            css.append(f"#{p} #{p}-s{i}:checked ~ .sf-anwrap .sf-an{i} "
                       f"{{ display:block; }}")
    anatomy = ""
    if with_anatomy:
        anatomy = (
            f'<details class="sf-anwrap" style="margin-top:.5rem;border:1px solid #ddd;'
            f'border-radius:6px;padding:.3rem .6rem"><summary style="cursor:pointer;'
            f'min-height:44px;font-weight:600">Show full frame anatomy</summary>'
            + "".join(ans) + "</details>"
        )
    return (
        f'<div id="{p}"><style>{chr(10).join(css)}</style>'
        + "".join(inputs)
        + f'<div class="sf-steps" role="group" aria-label="Step through the call stack" '
        f'style="display:flex;gap:6px;margin-bottom:8px">'
        + "".join(labels) + "</div>"
        + f'<div class="sf-views">' + "".join(views) + "</div>"
        + anatomy
        + "</div>"
    )


def stepped_boxchain(comp_id: str, steps: list, link_values: bool = False) -> str:
    """Zero-JS CSS-radio stepper over box-chain diagram states.

    ``steps`` is a list of box-chain spec dicts (each ``{title?, nodes, links?,
    note?}``). Selecting a step number reveals that state's SVG; all others are
    hidden. Defaults to the first step. Follows the same CSS-radio pattern as
    ``stepped_frames``. Hover-tooltip on each step button shows the step title.

    ``link_values`` threads tri-link value keys into each step's box-chain (see
    :func:`_svg_boxchain`), so a value's box is highlightable from the linked
    console/source in whichever frame is currently shown. The duplicate-value
    warning is per-step (each step is its own spec), so a value legitimately
    repeating across steps does not false-trigger it."""
    p = _safe(comp_id)
    inputs, labels, views = [], [], []
    # A step's SVG width is driven by its widest text line; a long per-step `note`
    # used to inflate it — so a wordy step rendered wider AND, once past the column
    # width, `max-width:100%` scaled every node down. Fix: pull the note OUT of the
    # SVG and render it as a wrapping HTML caption, so every step's SVG is the same
    # box-driven width and boxes are identical size in every step. The views sit in
    # a bounded, keyboard-focusable scroll region so a tall chain scrolls the PANEL,
    # not the page (WCAG 2.1.1: focusable region; diagrams are exempt from the
    # 1.4.10 no-2D-scroll rule).
    css = [
        f"#{p} .sbc-views {{ overflow:auto; max-height:60vh; }}",
        # A shown step is a flex row: the SVG on the left, its explanation in a panel
        # to the RIGHT (using the empty space next to the narrow chain) so the caption
        # is visible without scrolling to the bottom of the diagram. Zero JS.
        # ...but only while both fit. The chain is a fixed-width drawing, so in a
        # narrow diagram column (426px on a rail page) the note's 11rem minimum
        # left the SVG less than its own width and the browser SHRANK it, clipping
        # the right edge of every box — measured, not guessed. `flex-wrap` drops
        # the note underneath instead, and the SVG never shrinks below its
        # intrinsic width. Wide columns are unaffected: both still sit side by side.
        f"#{p} .sbc-v {{ display:none; gap:1rem; align-items:flex-start;"
        f" flex-wrap:wrap; }}",
        f"#{p} .sbc-v > svg {{ flex:0 0 auto; max-width:100%; }}",
        f"#{p} .sbc-note {{ margin:0; flex:1; min-width:11rem;"
        f" font:14px/1.5 system-ui; color:#222; background:#eef3fb;"
        f" border-left:3px solid #0b5394; padding:.55rem .75rem; border-radius:4px; }}",
        # When a step has an `aside: true` node (a detached, just-unlinked box) the
        # caption cell becomes a column: the note on top, the detached node BELOW it,
        # filling the space beside the chain instead of a wide empty SVG column.
        f"#{p} .sbc-side {{ flex:1; min-width:11rem; display:flex;"
        f" flex-direction:column; align-items:flex-start; gap:.6rem; }}",
        f"#{p} .sbc-side .sbc-note {{ flex:0 0 auto; }}",
    ]
    for i, step in enumerate(steps):
        title = step.get("title", "")
        checked = " checked" if i == 0 else ""
        inputs.append(
            f'<input type="radio" name="{p}-step" id="{p}-s{i}"{checked} '
            f'style="position:absolute;opacity:0">')
        labels.append(
            f'<label for="{p}-s{i}" title="{_e(title)}" '
            f'style="cursor:pointer;border:1px solid #bbb;border-radius:6px;'
            f'padding:2px 9px;font:13px system-ui;min-height:44px;'
            f'display:inline-flex;align-items:center">{i + 1}</label>')
        # Unique id prefix per step so SVG element ids never collide across steps.
        # Strip the note so it can't drive the SVG width; render it as a wrapping
        # HTML caption below the chain instead (keeps every step's width equal).
        note = step.get("note")
        spec = {k: v for k, v in step.items() if k != "note"}
        # `aside: true` nodes render as a compact box BELOW the note (in the caption
        # column), not in the chain — so the chain SVG stays narrow and the detached
        # node fills the otherwise-empty space under the caption.
        nodes = spec.get("nodes", [])
        aside = [n for n in nodes if n.get("aside")]
        if aside:
            spec = {**spec, "nodes": [n for n in nodes if not n.get("aside")]}
        svg = _svg_boxchain(spec, f"{p}-s{i}bc", link_values=link_values)
        note_html = f'<p class="sbc-note">{_e(note)}</p>' if note else ""
        if aside:
            clean = [{k: v for k, v in n.items() if k != "aside"} for n in aside]
            aside_svg = _svg_boxchain({"nodes": clean}, f"{p}-s{i}as",
                                      link_values=link_values)
            caption = (f'<div class="sbc-side">{note_html}'
                       f'<div class="sbc-aside">{aside_svg}</div></div>')
        else:
            caption = note_html
        views.append(f'<div class="sbc-v sbc-v{i}">{svg}{caption}</div>')
        css.append(
            f"#{p} #{p}-s{i}:checked ~ .sbc-views .sbc-v{i} {{ display:flex; }}")
        css.append(
            f"#{p} #{p}-s{i}:checked ~ .sbc-steps label[for={p}-s{i}] "
            f"{{ background:#0b5394; color:#fff; border-color:#0b5394; }}")
        css.append(
            f"#{p} #{p}-s{i}:focus-visible ~ .sbc-steps label[for={p}-s{i}] "
            f"{{ outline:3px solid var(--accent);outline-offset:2px; }}")
    return (
        f'<div id="{p}"><style>{chr(10).join(css)}</style>'
        + "".join(inputs)
        + f'<div class="sbc-steps" role="group" '
        f'aria-label="Step through diagram states" '
        f'style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">'
        + "".join(labels) + "</div>"
        + f'<div class="sbc-views" tabindex="0" role="region" '
        f'aria-label="Diagram viewport — scroll to see the full chain">'
        + "".join(views) + "</div>"
        + "</div>"
    )


def step_gauge(comp_id: str, steps: list) -> str:
    """Zero-JS CSS-radio stepper over a build-derived "fuel bar" gauge.

    ``steps`` is the list from :func:`compiler_runner.parse_gauge_all` —
    ``[{series, value, max|None, label}]`` in program order. Each step draws a
    filled bar whose numeric value is ALSO shown as text (WCAG 1.4.1: never the
    bar length alone). When a step carries an explicit ``max`` (e.g. a vector's
    capacity) the capacity TRACK is scaled to the global-max capacity, so a
    doubling capacity reads as a doubling track length; without a max the track
    is the sequence peak (e.g. ``use_count``). Capacity gauges render two levels
    in distinct colours — blue ``size`` fill inside a green ``capacity`` band,
    with a colour legend below the bar — and the grey rail runs 25% past the
    largest capacity so the capacity level stays visible even at peak. Same
    CSS-radio mechanism as :func:`stepped_boxchain`; no JS. Returns "" for no
    steps."""
    p = _safe(comp_id)
    if not steps:
        return ""
    values = [s["value"] for s in steps]
    peak = max(max(values), 1)
    refs = [(s["max"] if s.get("max") is not None else peak) for s in steps]
    global_max = max(max(refs), 1)
    # Two-level bar ONLY when a real capacity (max) exists: the fill (size) sits
    # inside a coloured capacity band so the two quantities read as distinct
    # colours (blue = size in use, green = allocated capacity). For use_count
    # (no max) there is no capacity concept, so the band stays neutral grey and
    # the widget degenerates to a single blue fill.
    has_max = any(s.get("max") is not None for s in steps)
    cap_bg = "#6aa84f" if has_max else "#dfe6ef"
    # The rail (grey track) runs slightly PAST the largest capacity so the
    # capacity band never reaches the rail's end — its right edge (the capacity
    # level) stays visible even at peak capacity. Capacity gauges only; a
    # use_count peak still fills its rail (no headroom).
    rail_max = global_max * 1.25 if has_max else global_max

    css = [
        f"#{p} .sg-v {{ display:none; }}",
        f"#{p} .sg-head {{ font:14px system-ui; color:#222; margin-bottom:4px; }}",
        f"#{p} .sg-head b {{ font-size:18px; }}",
        # The header numbers are colour-keyed to the bar: blue = size, green =
        # capacity, so the label reads the same two levels the bar shows. Green
        # is darkened from the band for text-contrast (WCAG).
        f"#{p} .sg-sz {{ color:#0b5394; }}",
        f"#{p} .sg-cp {{ color:#38761d; }}",
        f"#{p} .sg-rail {{ height:22px; background:#eef1f5; border:1px solid #cdd3db;"
        f" border-radius:4px; overflow:hidden; }}",
        # The capacity box (a real ``max``) fills a fraction of the rail; the
        # value fill sits inside it. For use_count (no max) the cap box is the
        # whole rail, so the widget degenerates to a single fill bar.
        f"#{p} .sg-cap {{ height:100%; background:{cap_bg};"
        f" border-right:1px solid #38761d; box-sizing:border-box; }}"
        if has_max else
        f"#{p} .sg-cap {{ height:100%; background:{cap_bg};"
        f" border-right:1px solid #b6c0cd; box-sizing:border-box; }}",
        f"#{p} .sg-fill {{ height:100%; background:#0b5394; }}",
        f"#{p} .sg-note {{ margin:.5rem 0 0; font:14px/1.5 system-ui; color:#222;"
        f" background:#eef3fb; border-left:3px solid #0b5394; padding:.5rem .7rem;"
        f" border-radius:4px; }}",
        # The marked code line that produced this step's value (author-bracketed
        # in the source, lifted verbatim — cannot drift). Omitted for steps with
        # no natural line (scope-exit / destructor).
        f"#{p} .sg-code {{ margin:.4rem 0 0; font:12px/1.4 ui-monospace,monospace;"
        f" color:#555; }}",
        f"#{p} .sg-code code {{ background:#f3f4f6; padding:1px 5px;"
        f" border-radius:3px; color:#1a1a1a; }}",
    ]
    inputs, labels, views = [], [], []
    for i, s in enumerate(steps):
        value = s["value"]
        vmax = s.get("max")
        tmax = vmax if vmax is not None else peak
        cap_pct = 100 * tmax / rail_max
        fill_pct = (100 * value / tmax) if tmax else 0
        series = _e(s.get("series", ""))
        label = _e(s.get("label", ""))
        # "size 3 / capacity 4" with each number colour-keyed to its bar level;
        # no-max gauges (use_count) show just the single blue count.
        if vmax is not None:
            head_html = (f'{series} <b class="sg-sz">{value}</b>'
                         f' / capacity <b class="sg-cp">{_e(str(vmax))}</b>')
        else:
            head_html = f'{series} <b class="sg-sz">{value}</b>'
        code = s.get("code")
        code_html = (f'<div class="sg-code">from <code>{_e(code)}</code></div>'
                     if code else "")
        aria = (f"{s.get('series', '')} {value}"
                + (f" of {vmax}" if vmax is not None else "")
                + (f" — {s.get('label', '')}" if s.get("label") else "")
                + (f"; from {code}" if code else ""))
        checked = " checked" if i == 0 else ""
        inputs.append(
            f'<input type="radio" name="{p}-step" id="{p}-s{i}"{checked} '
            f'style="position:absolute;opacity:0">')
        labels.append(
            f'<label for="{p}-s{i}" title="{label}" '
            f'style="cursor:pointer;border:1px solid #bbb;border-radius:6px;'
            f'padding:2px 9px;font:13px system-ui;min-height:44px;'
            f'display:inline-flex;align-items:center">{i + 1}</label>')
        # A step carrying a link key joins the code<->console highlight group of
        # the line that moved the count, so hovering the step lights that line
        # (and hovering the line lights the step). Pure enhancement: the key is
        # absent unless the topic marked the line, and all a11y rides on the
        # aria-label above.
        gk = f' data-cll="{_e(s["key"])}"' if s.get("key") else ""
        views.append(
            f'<div class="sg-v sg-v{i}"{gk} role="img" aria-label="{_e(aria)}">'
            f'<div class="sg-head">{head_html}</div>'
            f'<div class="sg-rail"><div class="sg-cap" style="width:{cap_pct:g}%">'
            f'<div class="sg-fill" style="width:{fill_pct:g}%"></div></div></div>'
            f'{code_html}'
            f'<p class="sg-note">{label}</p></div>')
        css.append(f"#{p} #{p}-s{i}:checked ~ .sg-views .sg-v{i} {{ display:block; }}")
        css.append(
            f"#{p} #{p}-s{i}:checked ~ .sg-steps label[for={p}-s{i}] "
            f"{{ background:#0b5394; color:#fff; border-color:#0b5394; }}")
        css.append(
            f"#{p} #{p}-s{i}:focus-visible ~ .sg-steps label[for={p}-s{i}] "
            f"{{ outline:3px solid var(--accent);outline-offset:2px; }}")
    # Static colour key below the bar (capacity gauges only) — decorative
    # (aria-hidden): the numbers are already announced per step, so this
    # reinforces the two levels for sighted readers without screen-reader noise.
    legend = ""
    if has_max:
        css.append(
            f"#{p} .sg-legend {{ display:flex; gap:1.2rem; margin-top:.55rem;"
            f" font:13px system-ui; color:#333; }}")
        css.append(
            f"#{p} .sg-legend .sw {{ display:inline-block; width:12px;"
            f" height:12px; border-radius:2px; margin-right:6px;"
            f" vertical-align:-1px; }}")
        legend = (
            f'<div class="sg-legend" aria-hidden="true">'
            f'<span><i class="sw" style="background:#0b5394"></i>size — in use</span>'
            f'<span><i class="sw" style="background:{cap_bg}"></i>capacity — allocated</span>'
            f'</div>')
    return (
        f'<figure id="{p}" style="margin:0"><style>{chr(10).join(css)}</style>'
        + "".join(inputs)
        + '<div class="sg-steps" role="group" aria-label="Step through the count" '
        'style="display:flex;gap:6px;flex-wrap:wrap;margin-bottom:8px">'
        + "".join(labels) + "</div>"
        + '<div class="sg-views">' + "".join(views) + "</div>"
        + legend
        + "</figure>"
    )


def perf_chart_panel(comp_id: str, charts: dict) -> str:
    """Render one or more perf_chart bar charts with a y-axis linear/log toggle.

    charts: {chart_id: {"spec": spec, "points": [...]}}. Buttons carry
    data-pc-toggle; the _CLL_JS handler (Task 6) rescales bars from data-y.
    """
    blocks = []
    for cid, ch in charts.items():
        spec = ch["spec"]
        svg = _svg_perf_chart(spec, ch["points"], f"{comp_id}-{cid}")
        mode = spec.get("mode", "bar")

        def _group(axis, label):
            scale = (spec.get(axis) or {}).get("scale", "linear")
            buttons = "".join(
                f'<button type="button" data-pc-toggle="{s}" data-pc-axis="{axis}" '
                f'aria-pressed="{"true" if s == scale else "false"}">{s}</button>'
                for s in ("linear", "log"))
            return (f'<div class="pc-toggle" role="group" aria-label="{label}">'
                    + buttons + '</div>')

        if mode in ("line", "scatter"):
            toggle = _group("x", "x-axis scale") + _group("y", "y-axis scale")
        else:  # bar: y toggle only
            toggle = _group("y", "y-axis scale")
        blocks.append(f'<figure class="pc-fig">{toggle}{svg}</figure>')
    return "".join(blocks)


def _console_body(pid: str, v: dict) -> str:
    """The compile badge + program console for one baked variant (no code block).

    Shared by the ordinary per-variant panel (:func:`_demo_variant_body`) and the
    output-tabs layout (:func:`demo_panel`), where the code shows once and only
    this console is tabbed.
    """
    kind = v.get("error_kind") or "compile"
    # The exact g++ line this tab was built with, above the verdict it produced.
    # It goes here rather than into the code panel because a comment line at the
    # top of the source would shift every line number the compiler and sanitizer
    # reports cite, and rather than into the console because that panel is the
    # program's own output. On an output-tabs topic (flag_variants) the code is
    # shown once and only this body is tabbed, which is exactly where a per-tab
    # flag set needs to appear.
    cmd = v.get("compile_cmd") or ""
    cmd_html = (f'<p class="build-cmd">{_e(cmd)}</p>' if cmd else "")
    # A program that ran to its end and returned a nonzero code (a test
    # harness reporting FAIL) compiled and did not crash: the badge says so and
    # names the code, which is the run's verdict for any script that calls it.
    code = v.get("exit_code")
    label = f"Compiled · exit code {code}" if code else None
    badge = (cmd_html
             + '<div style="margin-top:.8rem">'
             + compile_status_badge(f"{pid}-badge", v["ok"], kind=kind, label=label)
             + "</div>")
    if v["ok"]:
        out = output_console(f"{pid}-out", v["stdout"], error=False, kind=kind)
        if code and (v.get("stderr") or "").strip():
            out += output_console(f"{pid}-err", v["stderr"], error=False, kind=kind,
                                  title="Standard error")
        return badge + out
    # A crash is not a compile error. The program RAN, and what it printed before
    # it died is evidence -- often the whole point of the tab, as when a line that
    # a destructor would have printed is missing. Show that first, then the
    # diagnostic that killed it. A failed COMPILE has no stdout, so it is
    # unaffected.
    # ...but not when the error panel is ALREADY showing that stdout: a program
    # that fails with an empty stderr (a test harness exiting non-zero, say) has
    # its stdout used as the diagnostic (see build_html's `report` fallback), and
    # printing it twice would be noise -- and would double every count a test
    # pins on it.
    pre = ""
    out = (v.get("stdout") or "").strip()
    if kind == "runtime" and out and out != (v.get("stderr") or "").strip():
        pre = output_console(f"{pid}-pre", v["stdout"], error=False, kind="compile")
    return badge + pre + output_console(f"{pid}-out", v["stderr"], error=True, kind=kind)


def _demo_variant_body(pid: str, v: dict, caption: str, diagram: bool = True,
                       *, step_diagram: dict | None = None,
                       struct_spec: "dict | list | None" = None, byte_decode: str = "",
                       aside_slot: str = "", concept_aside: str = "",
                       aside_grid: bool = False,
                       gauge: bool = False, console_link: bool = False,
                       link_diagram: bool = False) -> str:
    """One compiled program: code+diagram split, badge, output, collapsed bytes.

    The byte box is data-driven: it is emitted only when byte data exists. A
    variant with no bytes (e.g. a failed compile that never printed MEMBYTES)
    omits it rather than rendering a degenerate empty grid.

    ``diagram=False`` drops the memory diagram (and the two-column split),
    showing the code full-width — for subjects with no memory-model picture.

    ``aside_slot``/``concept_aside`` (both pre-rendered HTML) form the right-
    column stack for ``diagram=False`` variants — the prompt slot above the
    in-tab Key Idea aside (ENGINE_REQUEST_prompt-panel). ``aside_grid`` forces
    the two-column grid for these variants even when both are empty, so the
    code-column width never changes between tabs.

    When ``diagram=True`` but this variant has no ``ptrdata`` (a compile-error
    gotcha or a value-pass tab), the two-column grid is KEPT — so the code
    column's width never changes between variants — but the right cell is left
    empty rather than rendering the ``_svg_unknown`` "no diagram" placeholder.
    """
    # Build-derived count-over-time bar (use_count, size/capacity). It is a
    # diagram, so it lives in the RIGHT diagram column — as a sub-tab beside the
    # box-chain when one exists, or filling the column on variants that carry no
    # structural picture (e.g. shared_ptr's fan-in "two owners" / "reset" tabs).
    gauge_html = (step_gauge(f"{pid}-gauge", v["gauge_steps"])
                  if gauge and v.get("gauge_steps") else "")
    # No separate opt-in flag (unlike `gauge`): a variant only carries
    # v["perf_chart"] when the author declared a perf_chart: block in the topic
    # YAML, so the block's presence IS the opt-in. The `diagram` gate still
    # suppresses it for diagram:false topics.
    perf_html = (perf_chart_panel(f"{pid}-pc", v["perf_chart"])
                 if diagram and v.get("perf_chart") else "")
    # The LEFT-column content is the same in every branch (with or without a
    # diagram): either the console_line_link block or the plain code+console.
    # console_line_link (item 22) replaces the code+console with the bidirectional
    # linked block when this variant marked its cout lines — but only for a CLEAN
    # run: a compile error / runtime crash keeps its normal error display (a linked
    # block would show stdout-only and hide the crash report, e.g. a double-free
    # tab whose crash IS the lesson). Computing it once lets it appear beside a
    # diagram too, not only in the full-width no-diagram case.
    have_link = (console_link and not v.get("failed")
                 and v.get("link_source")
                 and any(k for _c, k in v.get("link_console", [])))
    if link_diagram and have_link:
        left = console_line_link(f"{pid}-cll", v["link_source"], v["link_console"],
                                 tri_source=v.get("tri_source", []),
                                 tri_console=v.get("tri_console", []))
    elif have_link:
        left = console_line_link(f"{pid}-cll", v["link_source"], v["link_console"])
    else:
        left = v["code_html"] + _console_body(pid, v)
    if diagram and (struct_spec or step_diagram or gauge_html or perf_html):
        # Structural SVG (declarative box-chain), the paced steps stepper, and/or
        # the step-gauge. When more than one exists they become sub-tabs on the
        # diagram panel; a single one fills the column directly. Whole thing zooms.
        reps = []
        if struct_spec:
            if isinstance(struct_spec, list):
                reps.append(("Structure", stepped_boxchain(
                    f"{pid}-bc", struct_spec,
                    link_values=(link_diagram and have_link))))
            else:
                kind = struct_spec.get("kind", "chain")
                if kind == "tree":
                    reps.append(("Structure", _svg_tree(struct_spec, f"{pid}-tr")))
                elif kind == "buckets":
                    reps.append(("Structure", _svg_buckets(struct_spec, f"{pid}-bk")))
                elif kind == "set":
                    reps.append(("Structure", _svg_set(struct_spec, f"{pid}-st")))
                elif kind == "chain":
                    reps.append(("Structure", _svg_boxchain(struct_spec, f"{pid}-bc",
                                 link_values=(link_diagram and have_link))))
                else:
                    raise ValueError(
                        f"_demo_variant_body: unknown struct_spec kind {kind!r} "
                        f"(expected 'chain', 'tree', 'buckets', or 'set')")
        if step_diagram:
            items = [(s["summary"], _e(s["detail"]))
                     for s in step_diagram.get("items", [])]
            reps.append(("Dispatch walk",
                         steps_diagram(f"{pid}-steps", items,
                                       expr=step_diagram.get("expr"),
                                       caption=step_diagram.get("caption"))))
        if gauge_html:
            # Label the sub-tab by the counted series (e.g. "use_count"); hidden
            # when the gauge is the only representation in the column.
            series = (v["gauge_steps"][0].get("series") or "count")
            reps.append((series, gauge_html))
        if perf_html:
            reps.append(("Chart", perf_html))
        inner = (variant_tabs(f"{pid}-dtabs", reps) if len(reps) > 1
                 else reps[0][1])
        diagram_html = zoomable(f"{pid}-zoom", inner)
        # The compile badge + program console live in the LEFT (code) column, so
        # they match the code window's width instead of spanning the full panel.
        code_block = code_diagram_panel(f"{pid}-cdp", left,
                                        diagram_html, ratio=(2, 1))
    elif diagram:
        pd = v.get("ptrdata")
        steps = v.get("ptrdata_steps") or []
        ptype = (pd or {}).get("type")
        frame_steps = [s for s in steps if s.get("type") == "frames"]
        ratio = (3, 1)
        if len(frame_steps) > 1:
            diagram_html = zoomable(
                f"{pid}-zoom",
                stepped_frames(f"{pid}-md", frame_steps, with_anatomy=True))
            ratio = (2, 1)
        elif ptype == "frames":
            diagram_html = zoomable(
                f"{pid}-zoom",
                memory_diagram(f"{pid}-md", pd)
                + frames_anatomy_details(f"{pid}-fa", pd))
            ratio = (2, 1)
        elif ptype == "memmap":
            diagram_html = zoomable(f"{pid}-zoom", memory_diagram(f"{pid}-md", pd))
            ratio = (2, 1)
        else:
            diagram_html = memory_diagram(f"{pid}-md", pd) if pd else ""
        code_block = code_diagram_panel(f"{pid}-cdp", left,
                                        diagram_html, ratio=ratio)
    elif aside_grid:
        # No diagram, but the aside pathway (ENGINE_REQUEST_prompt-panel) claims
        # the right column: the per-variant prompt slot above the in-tab Key
        # Idea aside. The grid renders for EVERY tab in the group — even one
        # whose slot and concept are both empty (an empty right cell) — so the
        # code column's width never changes between tabs (same invariant as the
        # kept-grid empty-diagram case above).
        code_block = code_diagram_panel(f"{pid}-acp", left,
                                        aside_slot + concept_aside,
                                        ratio=(2, 1))
    else:
        # No diagram and no aside grid: the linked block (or plain code+console)
        # fills the width.
        code_block = left
    if link_diagram and have_link:
        code_block = f'<div data-cll-scope="{pid}">{code_block}</div>'
    body = code_block
    if v["bytes"]:
        # Echo the marked source line above the grid so the dump names the exact
        # line of code it came from (disambiguates e.g. two `arr`s in scope).
        src_line = v.get("byte_line", "")
        line_html = (f'<div class="byte-src">from <code>{_e(src_line)}</code></div>\n'
                     if src_line else "")
        body += (
            f'<details style="margin-top:.6rem"><summary style="min-height:44px;'
            f'cursor:pointer">{_e(caption)}</summary>\n'
            + line_html
            + byte_grid(f"{pid}-bytes", v["bytes"], caption="", decode=byte_decode)
            + "</details>\n"
        )
    return body


def demo_panel(comp_id: str, entry: dict, diagram: bool = True,
               *, concept: str | None = None, concept_title: str = "Key Idea",
               steps: dict | None = None, diagram_spec: dict | None = None,
               aside_html: dict | None = None,
               gauge: bool = False, console_link: bool = False,
               link_diagram: bool = False,
               tab_label: str | None = None,
               tab_notes: dict | None = None,
               tab_intro: dict | None = None,
               extra_tabs: Sequence[dict] | None = None) -> str:
    """One demo's inner content: a variant_tabs cluster over a topic's baked data.

    A cases-topic variant carries a ``cases`` list; its sub-cases are stacked
    (each with its own compile verdict) inside the tab. Layout-agnostic.

    ``diagram=False`` suppresses the per-program memory diagram (see
    :func:`_demo_variant_body`).  When ``concept`` is given *and* there is no
    diagram, the whole cluster is placed in the left column and the concept fills
    the otherwise-empty right column as a titled aside (see
    :func:`code_concept_panel`); with a diagram, the concept is left to the
    demo's own ``concept`` block and this argument is ignored.

    ``aside_html`` (per-variant, keyed by tab label, values RAW/unescaped
    HTML) puts each tab's slot in the right column beside its code, with the
    Key Idea aside beneath it INSIDE the tab; the outer two-column wrap is
    then skipped. Ignored when ``diagram`` is true, on output-tabs topics, and
    on cases variants (ENGINE_REQUEST_prompt-panel).

    ``tab_label`` names the compiled tab of a single-variant topic (otherwise
    "default"). ``tab_notes`` (keyed by shown tab label, raw HTML) adds a note
    under that tab's console. ``tab_intro`` (keyed by shown tab label, raw HTML)
    puts a note at the top of that tab, above its code; it applies to
    ``extra_tabs`` too. ``extra_tabs`` (a list of ``{label, html}``)
    appends tabs that hold only author HTML — a model reply with no code, say —
    so they sit in the same strip, beside the same Key Idea, as the compiled one.
    """
    cid = _safe(comp_id)

    # aside_html (ENGINE_REQUEST_prompt-panel): a per-variant raw-HTML slot in
    # the right column, keyed by tab label. Active only for diagram-less
    # topics; on output_tabs and cases variants it is ignored (no consumer —
    # YAGNI, see the request doc).
    aside_active = bool(aside_html) and not diagram

    # Output-tabs layout (flag_variants topic): one source compiled at several
    # flag sets. Show the code ONCE, then tab only the console below it — the
    # source is identical across variants by construction, so repeating it per
    # tab would just hide the one thing that changes (the compiler flags).
    if entry.get("output_tabs"):
        first = entry[entry["variants"][0]]
        console_panels = []
        for label in entry["variants"]:
            v = entry[label]
            pid = f"{cid}-{_safe(label)}"
            console_panels.append((label, _console_body(pid, v)))
        cluster = (
            first["code_html"]
            + '<div style="margin-top:.8rem">'
            + variant_tabs(cid, console_panels)
            + "</div>"
        )
        # A cross-variant perf_chart is shared across all tabs (attached to every
        # variant), so render it ONCE in a diagram column beside the code+console
        # cluster — the output-tabs layout has no per-variant diagram column.
        if diagram and first.get("perf_chart"):
            chart = zoomable(f"{cid}-pczoom",
                             perf_chart_panel(f"{cid}-pc", first["perf_chart"]))
            return code_diagram_panel(f"{cid}-cdp", cluster, chart, ratio=(2, 1))
        if concept and not diagram:
            return code_concept_panel(f"{cid}-ccp", cluster, concept, title=concept_title)
        return cluster

    decode = entry.get("byte_decode", "")
    bvar = entry.get("byte_var", "")
    # Name the dumped variable in the caption so the byte grid points at its
    # declaration in the code (e.g. "Raw bytes of arr"); fall back when unknown.
    byte_caption = (f"Raw bytes of {bvar} (little-endian)" if bvar
                    else "Raw bytes (little-endian)")
    panels = []
    for label in entry["variants"]:
        v = entry[label]
        pid = f"{cid}-{_safe(label)}"
        # cases-variants render stacked sub-cases; per-variant Structure/steps
        # diagrams (struct_spec/step_diagram) are not threaded here by design.
        if "cases" in v:
            subcases = []
            for j, case in enumerate(v["cases"]):
                spid = f"{pid}-c{j}"
                body = _demo_variant_body(spid, case, byte_caption,
                                          diagram=diagram, byte_decode=decode)
                subcases.append((case["label"], body))
            body = stacked_subcases(f"{pid}-ssc", subcases)
        else:
            body = _demo_variant_body(pid, v, byte_caption,
                                      diagram=diagram,
                                      step_diagram=(steps or {}).get(label),
                                      struct_spec=(diagram_spec or {}).get(label),
                                      byte_decode=decode,
                                      aside_slot=((aside_html or {}).get(label, "")
                                                  if aside_active else ""),
                                      concept_aside=(_concept_aside(f"{pid}-ka", concept,
                                                                    title=concept_title)
                                                     if aside_active and concept else ""),
                                      aside_grid=aside_active,
                                      gauge=gauge,
                                      console_link=console_link,
                                      link_diagram=link_diagram)
        shown = tab_label if (tab_label and len(entry["variants"]) == 1) else label
        body = (tab_intro or {}).get(shown, "") + body + (tab_notes or {}).get(shown, "")
        panels.append((shown, body))
    for extra in extra_tabs or ():
        panels.append((extra["label"],
                       (tab_intro or {}).get(extra["label"], "") + extra["html"]))
    tabs = variant_tabs(cid, panels)
    if concept and not diagram and not aside_active:
        return code_concept_panel(f"{cid}-ccp", tabs, concept, title=concept_title)
    return tabs


def progressive_steps(comp_id: str, steps: Sequence[tuple[str, str]]) -> str:
    """Ordered student-paced reveals using native ``<details>/<summary>``."""
    p = _safe(comp_id)
    items = ""
    for i, (summary, content) in enumerate(steps):
        items += (
            f"<li><details>\n"
            f'<summary style="min-height:44px;padding:.3rem 0;cursor:pointer">{_e(summary)}</summary>\n'
            f"<div>{content}</div>\n"
            f"</details></li>\n"
        )
    return f'<ol id="{p}" class="psteps">\n{items}</ol>\n'


def steps_diagram(comp_id: str, items: Sequence[tuple[str, str]], *,
                  expr: str | None = None, caption: str | None = None) -> str:
    """A "steps" diagram for the right column: expression header + caption + stepper.

    Args:
        comp_id: A short unique name, used to build CSS-safe element ids.
        items: The ordered ``(summary, detail)`` reveals for the paced stepper.
        expr: The full expression being traced (e.g. ``v * 3 - 2 * w + x = (4, 4)``).
            Shown prominently at the top in monospace — the anchor for the trace.
        caption: A one-line framing note shown under the expression.

    Returns:
        The steps diagram as a self-styled piece of HTML. Scoped styles live under
        ``#{comp_id}`` so they never leak to other steppers on the page.
    """
    p = _safe(comp_id)
    style = (
        f"#{p} .sd-expr {{ font: 600 1.05rem/1.45 ui-monospace, monospace;"
        f" padding: .25rem .5rem .55rem; border-bottom: 2px solid var(--border);"
        f" margin-bottom: .55rem; overflow-x: auto; }}\n"
        f"#{p} .sd-cap {{ font-size: 1rem; line-height: 1.4; color: #555;"
        f" margin: 0 0 .7rem; }}\n"
        # Number each step with a CSS counter rendered as a FLEX SIBLING of the box
        # (not the native <ol> marker, whose position drifts when the <details> opens
        # and changes height). This keeps the label-to-box gap constant open or closed.
        f"#{p} .psteps {{ list-style: none; counter-reset: sd-step;"
        f" padding-left: 0; margin: 0; }}\n"
        f"#{p} .psteps > li {{ counter-increment: sd-step; display: flex;"
        f" align-items: flex-start; gap: .55rem; margin-bottom: .45rem; }}\n"
        # The number box matches the summary's 44px min-height and flex-centers its
        # glyph, so the number lines up with the box's (vertically-centered) label —
        # open or closed. li stays flex-start so it hugs the summary, not the tall li.
        f'#{p} .psteps > li::before {{ content: counter(sd-step) ".";'
        f" flex: 0 0 1.6rem; box-sizing: border-box; min-height: 44px;"
        f" display: flex; align-items: center; justify-content: flex-end;"
        f" font-weight: 700; color: var(--fg); }}\n"
        # margin:0 defeats any global `details {{ margin }}` rule — as a flex item that
        # margin would push the box down and break its alignment with the number.
        f"#{p} .psteps > li > details {{ flex: 1 1 auto; min-width: 0; margin: 0; }}\n"
        f"#{p} .psteps summary {{ list-style: none; display: flex; align-items: center;"
        f" justify-content: space-between; gap: .5rem; font-size: 1rem;"
        f" padding: .45rem .6rem !important; border: 1px solid var(--border);"
        f" border-radius: 6px; background: #fff; box-sizing: border-box; }}\n"
        f"#{p} .psteps summary::-webkit-details-marker {{ display: none; }}\n"
        f'#{p} .psteps summary::after {{ content: "＋"; font-weight: 700;'
        f" color: var(--accent); }}\n"
        f'#{p} .psteps details[open] > summary::after {{ content: "−"; }}\n'
        f"#{p} .psteps details[open] > summary {{ background: var(--panel-bg); }}\n"
        f"#{p} .psteps details > div {{ padding: .35rem .55rem .1rem; color: #333;"
        f" font-size: .95rem; line-height: 1.5; }}\n"
    )
    head = ""
    if expr:
        head += f'<div class="sd-expr">{_e(expr)}</div>\n'
    if caption:
        head += f'<p class="sd-cap">{_e(caption)}</p>\n'
    return (f'<div id="{p}" class="steps-diagram">\n<style>\n{style}</style>\n'
            f'{head}{progressive_steps(f"{p}-ol", items)}</div>\n')


# ---------- replay exhibit: a recorded sequence, step by step ----------
# A replay page replays one recorded process (for example one pipeline run) whose steps
# happen in a fixed order: step 2's input contains step 1's output. The outer strip is
# the sequence (step 1 preselected, so the spine is always visible); each step holds an
# inner strip of toggle tabs with NO tab preselected (a second, identical-looking label
# targets the strip's hidden "none" radio, so clicking an open tab closes it).
# First used by ag_pipeline (2026-07-23); made a reusable block on 2026-10-17.

# NO display property in _RP_LABEL: label visibility is controlled by each strip's
# stylesheet, and an inline display would override it (the duplicate-tabs bug of 2026-07-23).
_RP_LABEL = ("border:2px solid var(--border);border-radius:8px 8px 0 0;padding:.4rem .9rem;"
             "min-height:44px;align-items:center;cursor:pointer;font-weight:700")
_RP_HIDDEN = ("position:absolute;width:1px;height:1px;overflow:hidden;clip:rect(0 0 0 0);"
              "white-space:nowrap")
_RP_PANELS = "border:2px solid var(--border);border-radius:0 8px 8px 8px;padding:.7rem"
_RP_ACTIVE = "background:var(--accent);color:var(--accent-fg);border-color:var(--accent)"


def replay_inner_strip(gid: str, tabs: Sequence[tuple[str, str]],
                       aria: str = "Iteration content") -> str:
    """One step's tabs: a toggle strip with nothing preselected.

    Args:
        gid: A short CSS-safe id for this strip.
        tabs: ``(label, html)`` pairs, in the order the step happened.
        aria: The accessible name of the tab group.
    """
    n = len(tabs)
    css = [f"#{gid} .pnl{{display:none}}", f"#{gid} .pnls{{display:none}}",
           f"#{gid} .strip label{{display:inline-flex}}", f"#{gid} .strip .cls{{display:none}}"]
    for k in range(1, n + 1):
        css += [
            f"#{gid}-t{k}:checked ~ .strip .opn{k}{{display:none}}",
            f"#{gid}-t{k}:checked ~ .strip .cls{k}{{display:inline-flex;{_RP_ACTIVE}}}",
            f"#{gid}-t{k}:checked ~ .pnls{{display:block}}",
            f"#{gid}-t{k}:checked ~ .pnls .pnl{k}{{display:block}}",
        ]
    radios = [f'<input type="radio" name="{gid}" id="{gid}-t0" style="{_RP_HIDDEN}" checked>']
    radios += [f'<input type="radio" name="{gid}" id="{gid}-t{k}" style="{_RP_HIDDEN}">'
               for k in range(1, n + 1)]
    labels = []
    for k, (name, _) in enumerate(tabs, 1):
        labels.append(f'<label class="opn{k}" for="{gid}-t{k}" style="{_RP_LABEL}">{name}</label>')
        labels.append(f'<label class="cls cls{k}" for="{gid}-t0" style="{_RP_LABEL}">{name}</label>')
    panels = [f'<div class="pnl pnl{k}">{content}</div>' for k, (_, content) in enumerate(tabs, 1)]
    return (f'<div id="{gid}"><style>' + "\n".join(css) + "</style>"
            + "".join(radios)
            + f'<div class="strip" role="group" aria-label="{aria}" style="display:flex;gap:.3rem;flex-wrap:wrap">'
            + "".join(labels) + "</div>"
            + f'<div class="pnls" style="{_RP_PANELS}">' + "".join(panels) + "</div></div>")


def replay_strip(gid: str, steps: Sequence[tuple[str, Sequence[tuple[str, str]]]], *,
                 step_label: str = "Iteration", aria: str = "Pipeline iterations",
                 inner_aria: str = "Iteration content") -> str:
    """A replay exhibit: an outer strip of steps, each with an inner strip of toggle tabs.

    Args:
        gid: A short CSS-safe id; step k's inner strip gets the id ``{gid}-i{k}-tabs``.
        steps: One ``(head_html, tabs)`` pair per step, in order. ``head_html`` is shown
            above the step's tabs (for example its verdict line); ``tabs`` is a list of
            ``(label, html)`` pairs.
        step_label: The word on each outer tab, followed by the step number.
        aria: The accessible name of the outer strip.
        inner_aria: The accessible name of each inner strip.

    Returns:
        The strip as HTML. Step 1 is preselected; no inner tab is.
    """
    n = len(steps)
    panels = [head + replay_inner_strip(f"{gid}-i{k}-tabs", tabs, inner_aria)
              for k, (head, tabs) in enumerate(steps, 1)]
    css = [f"#{gid} > .ipnls > .ipnl{{display:none}}", f"#{gid} .istrip label{{display:inline-flex}}"]
    for k in range(1, n + 1):
        css += [
            f'#{gid}-i{k}:checked ~ .istrip label[for="{gid}-i{k}"]{{{_RP_ACTIVE}}}',
            f"#{gid}-i{k}:checked ~ .ipnls > .ipnl{k}{{display:block}}",
        ]
    radios = "".join(
        f'<input type="radio" name="{gid}-iter" id="{gid}-i{k}" style="{_RP_HIDDEN}"{" checked" if k == 1 else ""}>'
        for k in range(1, n + 1))
    labels = "".join(f'<label for="{gid}-i{k}" style="{_RP_LABEL}">{step_label} {k}</label>'
                     for k in range(1, n + 1))
    body = "".join(f'<div class="ipnl ipnl{k}">{p}</div>' for k, p in enumerate(panels, 1))
    return (f'<div id="{gid}"><style>' + "\n".join(css) + "</style>" + radios
            + f'<div class="istrip" role="group" aria-label="{aria}" style="display:flex;gap:.3rem;flex-wrap:wrap">'
            + labels + "</div>"
            + f'<div class="ipnls" style="{_RP_PANELS}">' + body + "</div></div>")
