"""Math renderer: LaTeX to MathML conversion using latex2mathml.

Handles both inline ($...$) and display ($$...$$) math.
Math extraction must run BEFORE Markdown rendering to prevent delimiter mangling.
"""
from __future__ import annotations

import re

import latex2mathml.converter

# latex2mathml emits xmlns on every <math>; in text/html the namespace is implicit.
_MATHML_XMLNS_ATTR = re.compile(
    r'\s+xmlns="http://www\.w3\.org/1998/Math/MathML"',
)


def strip_mathml_xmlns(mathml_fragment: str) -> str:
    """Remove redundant MathML xmlns from a converter fragment.

    In HTML5, ``<math>`` is in the MathML namespace without an xmlns attribute.
    The deck template records the URI once in ``<head>`` for clarity.

    Args:
        mathml_fragment: Raw string from latex2mathml (one root ``<math>``…).

    Returns:
        Same fragment without ``xmlns="http://www.w3.org/1998/Math/MathML"``.

    """
    return _MATHML_XMLNS_ATTR.sub("", mathml_fragment)


# Opening <math display="inline"> in slide headings; some UAs/layout break on this.
_MATH_OPEN_DISPLAY_INLINE_GT = re.compile(
    r'<math\s+display\s*=\s*["\']inline\s*["\']\s*>',
    flags=re.IGNORECASE,
)
# Rare: other attributes after display="inline" before >
_MATH_OPEN_DISPLAY_INLINE_ATTR = re.compile(
    r'<math\s+display\s*=\s*["\']inline\s*["\']\s+',
    flags=re.IGNORECASE,
)


def strip_math_display_inline_from_heading_html(html: str) -> str:
    """Drop ``display="inline"`` from ``<math>`` in heading HTML only.

    latex2mathml always sets ``display="inline"`` on ``$...$`` output; for
    ``<h1>``/``<h2>``/``<h3>`` titles, omitting the attribute avoids bad line
    breaking in some browsers while keeping body math unchanged.

    Args:
        html: Rendered title, subtitle, or author line (may contain ``<math>``).

    Returns:
        Same string with ``display="inline"`` (or ``'inline'``) removed from
        each opening ``<math>`` tag.

    """
    if not html or "<math" not in html:
        return html
    out = _MATH_OPEN_DISPLAY_INLINE_ATTR.sub("<math ", html)
    out = _MATH_OPEN_DISPLAY_INLINE_GT.sub("<math>", out)
    return out


def render_math_inline(tex: str) -> str:
    """Convert inline LaTeX expression to MathML with display='inline'."""
    return strip_mathml_xmlns(
        latex2mathml.converter.convert(tex, display="inline")
    )


def render_math_display(tex: str) -> str:
    """Convert display LaTeX expression to MathML with display='block'."""
    return strip_mathml_xmlns(
        latex2mathml.converter.convert(tex, display="block")
    )


def expand_color_macros(tex: str, macros: dict[str, str]) -> str:
    """Replace \\name with \\color{hex} for each entry in macros.

    Macros are defined in a color_macros YAML file referenced by ``macros:`` in
    deck metadata. This runs inside each $...$ / $$...$$ span before latex2mathml
    sees the expression, so authors write e.g. ``{\\accent S^2 d}`` instead of
    hardcoding ``{\\color{#f0a500} S^2 d}``.
    """
    for name, color in macros.items():
        tex = tex.replace(f'\\{name}', f'\\color{{{color}}}')
    return tex


def extract_and_render_math(text: str, macros: dict[str, str] | None = None) -> str:
    """Replace $$...$$ and $...$ spans with rendered MathML.

    Processes display math ($$...$$) first to avoid matching $$ as two $'s.

    Args:
        text: Source text potentially containing ``$...$`` / ``$$...$$``.
        macros: Optional dict mapping macro names to hex color strings (loaded
            from a ``macros:`` YAML file in deck metadata). Expanded inside
            each math span before conversion.
    """
    _macros = macros or {}

    # Display math: $$...$$ (may span multiple lines, non-greedy)
    def replace_display(match: re.Match) -> str:
        tex = match.group(1)
        if _macros:
            tex = expand_color_macros(tex, _macros)
        try:
            return render_math_display(tex)
        except Exception:
            return match.group(0)

    text = re.sub(r'\$\$(.*?)\$\$', replace_display, text, flags=re.DOTALL)

    # Inline math: $...$ (non-greedy, single line)
    def replace_inline(match: re.Match) -> str:
        tex = match.group(1)
        if _macros:
            tex = expand_color_macros(tex, _macros)
        try:
            return render_math_inline(tex)
        except Exception:
            return match.group(0)

    text = re.sub(r'\$(.+?)\$', replace_inline, text)

    return text


# Markdown **...** becomes <strong>...</strong>. When inline math was already
# converted to <math>, patterns include:
#   - <strong><math>...</math></strong>  (**$x$**)
#   - <strong>text <math>...</math></strong>  (**text $x$**)
# Browsers often ignore font-weight on MathML; replace the whole <strong> block
# with a span using var(--accent) like slide headings (base.html.j2).
_STRONG_CONTAINING_MATHML = re.compile(
    r'<strong>((?:(?!</strong>).)*?<math\b[^>]*>.*?</math>(?:(?!</strong>).)*?)</strong>',
    re.DOTALL | re.IGNORECASE,
)


def postprocess_emphasized_mathml(html: str) -> str:
    """Turn ``<strong>`` regions that contain MathML into an accent-colored span.

    Covers **$x$** (math only) and **text $x$** (label + math): Python-Markdown
    emits ``<strong>text <math>...</math></strong>``, which the old
    strong-then-math-only regex missed, so math stayed default body color.

    Args:
        html: Fragment or full slide body HTML (may contain multiple matches).

    Returns:
        HTML with each ``<strong>`` that wraps at least one ``<math>...</math>``
        replaced by
        ``<span class="deck-math-emphasis" role="presentation">...</span>``
        (same inner nodes, without ``<strong>``).

    """
    if not html or "<strong>" not in html.lower() or "<math" not in html.lower():
        return html
    return _STRONG_CONTAINING_MATHML.sub(
        r'<span class="deck-math-emphasis" role="presentation">\1</span>',
        html,
    )
