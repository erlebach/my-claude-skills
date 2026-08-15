"""Rich content renderers package.

Exports render_body() orchestrator and individual renderer functions.
Math extraction runs before Markdown to prevent delimiter mangling (Pitfall 1).
"""
from __future__ import annotations

import re

from compiler.renderers.code import get_pygments_css, render_code
from compiler.renderers.image import render_image
from compiler.renderers.markdown import render_markdown
from compiler.renderers.math import expand_color_macros, extract_and_render_math, postprocess_emphasized_mathml
from compiler.renderers.mermaid import render_mermaid
from compiler.renderers.svg import sanitize_svg, wrap_svg_ada

_MATH_BLOCK = re.compile(r'<math\b[^>]*>.*?</math>', re.DOTALL | re.IGNORECASE)
_COMMENT_LINE = re.compile(r'^//.*$', re.MULTILINE)


def strip_comment_lines(text: str) -> str:
    """Remove lines starting with '//' (slide-author comments, never rendered)."""
    return _COMMENT_LINE.sub('', text)


def _shield_math(text: str) -> tuple[str, list[str]]:
    """Replace <math>…</math> spans with inline placeholders.

    Python-Markdown treats a line that begins with <math> as raw block HTML and
    parses trailing text on the same line as a separate paragraph (breaking
    cells like "$S$ large"). Swapping the math for an opaque inline token keeps
    the cell content as one paragraph; the token is restored after Markdown.
    """
    saved: list[str] = []

    def stash(match: re.Match) -> str:
        saved.append(match.group(0))
        return f'\x00MATH{len(saved) - 1}\x00'

    return _MATH_BLOCK.sub(stash, text), saved


def _restore_math(html: str, saved: list[str]) -> str:
    for i, frag in enumerate(saved):
        html = html.replace(f'\x00MATH{i}\x00', frag)
    return html

__all__ = [
    'render_rich_text',
    'render_body',
    'strip_comment_lines',
    'render_code',
    'get_pygments_css',
    'render_image',
    'render_markdown',
    'expand_color_macros',
    'extract_and_render_math',
    'postprocess_emphasized_mathml',
    'render_mermaid',
    'sanitize_svg',
    'wrap_svg_ada',
]


def render_rich_text(text: str, theme: str = 'dark', macros: dict[str, str] | None = None) -> str:
    """Run math extraction then Markdown on a short string (e.g. table cell).

    Table and title templates historically used HTML-escaping only, which left
    ``$...$`` visible as raw text. Use this for any field that should support
    the same inline math and Markdown as slide bodies.

    Args:
        text: Source string (may contain ``$...$`` / ``$$...$$`` and Markdown).
        theme: Reserved for future theme-specific rendering; unused today.
        macros: Optional color-macro dict (name → hex) from deck ``macros:`` file.

    Returns:
        HTML safe to inject with ``| safe`` in Jinja (contains MathML / tags).

    """
    del theme  # reserved
    if not text or not str(text).strip():
        return ''
    text = extract_and_render_math(str(text), macros=macros)
    text, saved = _shield_math(text)
    # These fields are inline fragments: a leading '>' or '#' is data
    # (e.g. ">10K rps"), not a blockquote/heading. Escape it so Markdown
    # renders the character literally.
    lead = text.lstrip()[:1]
    if lead in ('>', '#'):
        text = text.replace(lead, '\\' + lead, 1)
    text = render_markdown(text)
    text = _restore_math(text, saved)
    return postprocess_emphasized_mathml(text)


def render_body(slide, embed_images: bool = False, theme: str = 'dark', macros: dict[str, str] | None = None) -> str:
    """Orchestrate body rendering for a slide.

    Processing order:
      1. Math extraction ($$...$$ and $...$) -> MathML
      2. Markdown rendering -> HTML

    Args:
        slide: Any slide model instance with an optional ``body`` field.
        embed_images: When True, embed image files as base64 data URIs.
        theme: 'dark' or 'light' — controls code highlighting theme.
        macros: Optional color-macro dict (name → hex) from deck ``macros:`` file.

    Returns:
        Rendered HTML string, or empty string if slide has no body.
    """
    body = getattr(slide, 'body', None)
    if not body:
        return ''

    body = strip_comment_lines(body)

    # Step 1: Extract and render math before Markdown processes $ delimiters
    body = extract_and_render_math(body, macros=macros)

    # Step 2: Render remaining Markdown to HTML
    body = render_markdown(body)
    body = postprocess_emphasized_mathml(body)

    return body
