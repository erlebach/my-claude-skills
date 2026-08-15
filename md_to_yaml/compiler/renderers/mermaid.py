"""Mermaid diagram renderer: client-side rendering via Mermaid JS.

Embeds Mermaid source in a <pre class="mermaid"> block for browser-side rendering.
The base template includes the Mermaid JS library when diagrams are present.
"""
from __future__ import annotations

import html
import json
import re
import subprocess
import tempfile
from pathlib import Path

# Matches a Mermaid style directive that sets fill: but lacks a standalone color:.
# The negative lookbehind (?<![a-z-]) inside the lookahead excludes compound names
# like stroke-color: or fill-color: which would otherwise satisfy \bcolor:.
_FILL_WITHOUT_COLOR_RE = re.compile(
    r'(style\s+\S+\s+[^\n]*fill:[^\n,]+)(?![^\n]*(?<![a-z-])color:)'
)


def _inject_text_color(source: str) -> str:
    """Inject color:#000000 into style directives that set fill but omit color.

    Mermaid's dark theme inherits a near-white default text color, which fails
    contrast against light fills. This completes the author's intent. Authors
    should still set color: explicitly (see mermaid-best-practices.md) — this
    is the compiler safety net.
    """
    return _FILL_WITHOUT_COLOR_RE.sub(r'\1,color:#000000', source)


def render_mermaid(source: str, alt_text: str, slide_id: str, theme: str = 'dark') -> str:
    """Return a Mermaid block for client-side rendering with ADA attributes."""
    source = _inject_text_color(source)
    escaped = html.escape(source.strip())
    return (
        f'<div role="img" aria-label="{html.escape(alt_text)}">'
        f'<pre class="mermaid" aria-hidden="true">{escaped}</pre>'
        f'</div>'
    )


# --- Build-time bake (--bake-mermaid): runtime <pre class="mermaid"> -> inline SVG ---
#
# Matches a .diagram-container and the Mermaid <pre> inside it (across the optional
# role="img" wrapper), without spanning into the next container. Groups:
#   1 container tag start, 2 rest of container open tag, 3 content before the pre
#   (the role=img/aria-label wrapper that must be preserved), 4 escaped Mermaid source.
_BAKE_PRE_RE = re.compile(
    r'(<div class="diagram-container")'
    r'([^>]*>)'
    r'((?:(?!<div class="diagram-container").)*?)'
    r'<pre class="mermaid"[^>]*>(.*?)</pre>',
    re.S,
)


def _diagram_type(source: str) -> str:
    """First non-comment keyword of a Mermaid source (mirrors the runtime tagging)."""
    for raw in source.split("\n"):
        line = raw.strip()
        if not line or line.startswith("%%") or line.startswith("---"):
            continue
        return re.split(r"[\s:({]", line)[0].lower()
    return ""


def _mermaid_bake_config(theme: str, font: str) -> dict:
    """mmdc config mirroring the template's mermaid.initialize so baked geometry matches."""
    family = f"'{font}', sans-serif"
    return {
        "theme": 'dark' if theme == 'dark' else 'default',
        "fontFamily": family,
        "fontSize": 22,
        "htmlLabels": False,
        "flowchart": {"htmlLabels": False, "useMaxWidth": False},
        "sequence": {"useMaxWidth": False},
        "themeVariables": {"fontSize": "22px", "fontFamily": family},
    }


def _render_svg(source: str, cfg_path: Path, workdir: Path, n: int) -> str:
    """Render one Mermaid source to an inline <svg>, hidden from assistive tech."""
    mmd = workdir / f"d{n}.mmd"
    svg = workdir / f"d{n}.svg"
    mmd.write_text(source, encoding="utf-8")
    # Unique --svgId per diagram. mmdc otherwise names every SVG "my-svg" and
    # prefixes its <marker>/gradient/<style> ids with it; multiple baked SVGs in
    # one document would then collide, and a later diagram's edges would resolve
    # their arrowhead to the first diagram's marker (a cross-svg ref browsers
    # don't render) — making arrows disappear.
    subprocess.run(
        ["mmdc", "-i", str(mmd), "-o", str(svg), "-c", str(cfg_path),
         "-b", "transparent", "-q", "-I", f"mmd-bake-{n}"],
        check=True, capture_output=True,
    )
    out = svg.read_text(encoding="utf-8")
    out = out[out.index("<svg"):]                       # drop any XML prolog
    # The wrapping role="img"/aria-label div carries the accessible description;
    # hide the raw SVG tree so screen readers don't read the labels twice.
    out = out.replace("<svg ", '<svg aria-hidden="true" focusable="false" ', 1)
    return out


def bake_mermaid_in_html(html_str: str, theme: str = 'dark', font: str = 'IBM Plex Sans') -> str:
    """Replace each runtime <pre class="mermaid"> with an mmdc-rendered inline <svg>.

    The role="img"/aria-label ADA wrapper is preserved, and the container is tagged
    with data-mermaid-pre + data-diagram-type so the template's panel-fill sizer
    selects the baked SVG exactly as it does runtime-rendered diagrams.
    """
    if not _BAKE_PRE_RE.search(html_str):
        return html_str

    workdir = Path(tempfile.mkdtemp(prefix="bake_mermaid_"))
    cfg_path = workdir / "config.json"
    cfg_path.write_text(json.dumps(_mermaid_bake_config(theme, font)), encoding="utf-8")
    counter = {"n": 0}

    def repl(m: "re.Match[str]") -> str:
        counter["n"] += 1
        source = html.unescape(m.group(4)).strip()
        tag = f' data-mermaid-pre="1" data-diagram-type="{_diagram_type(source)}"'
        svg = _render_svg(source, cfg_path, workdir, counter["n"])
        return m.group(1) + tag + m.group(2) + m.group(3) + svg

    return _BAKE_PRE_RE.sub(repl, html_str)
