"""Code renderer: Pygments syntax highlighting.

Generates styled HTML spans scoped under .slide-code to avoid CSS conflicts.
"""
from __future__ import annotations

import re

from pygments import highlight
from pygments.formatters import HtmlFormatter
from pygments.lexers import TextLexer, get_lexer_by_name


def _get_style(theme: str) -> str:
    return 'monokai' if theme == 'dark' else 'tango'


def _fix_linenos_pre(html: str) -> str:
    """Replace the line-number <pre> with a <div> styled as pre.

    Pygments linenos mode produces a <table> with two <pre> elements:
    one for line numbers (not code) and one for actual code. Accessibility
    checkers flag the line-number <pre> as improper use of preformatted text.
    """
    # The linenos <pre> is inside <td class="linenos">...<pre>...</pre>...</td>
    # Replace only that one with a <div> that preserves whitespace visually
    html = re.sub(
        r'(<div class="linenodiv">)<pre([^>]*)>(.*?)</pre>(</div>)',
        r'\1<div\2 style="white-space:pre" aria-hidden="true">\3</div>\4',
        html,
        count=1,
        flags=re.DOTALL,
    )
    return html


def render_code(
    source: str,
    language: str,
    line_numbers: bool = False,
    theme: str = 'dark',
) -> str:
    """Return Pygments-highlighted HTML for source code.

    Args:
        source: Raw source code string.
        language: Pygments lexer alias (e.g. 'python', 'javascript').
        line_numbers: Include line number markup when True.
        theme: 'dark' -> monokai, 'light' -> friendly.
    """
    style = _get_style(theme)
    try:
        lexer = get_lexer_by_name(language, stripall=True)
    except Exception:
        lexer = TextLexer()

    formatter = HtmlFormatter(
        style=style,
        linenos=line_numbers,
        cssclass='slide-code',
    )
    html = highlight(source, lexer, formatter)

    if line_numbers:
        # Fix line-number <pre> first (before the code <pre> replacement)
        html = _fix_linenos_pre(html)

    # Wrap code <pre> spans in <code> so <pre> is recognized as code content
    # and make pre keyboard-accessible for scrollable content
    html = html.replace('<pre>', '<pre tabindex="0"><code>', 1)
    html = html.replace('</pre>', '</code></pre>', 1)
    return html


def get_pygments_css(theme: str = 'dark') -> str:
    """Return Pygments CSS rules scoped to .slide-code."""
    style = _get_style(theme)
    formatter = HtmlFormatter(style=style, cssclass='slide-code')
    return formatter.get_style_defs('.slide-code')
