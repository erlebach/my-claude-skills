"""Markdown renderer: inline Markdown to HTML using Python-Markdown."""
from __future__ import annotations

import re
import markdown


def _normalize_list_indent(text: str) -> str:
    """Normalize list-item indentation to 4 spaces per nesting level.

    Python-Markdown requires 4 spaces per indent level (default tab_length).
    Authors sometimes write sub-bullets with 2-space indentation, or mix
    2- and 4-space within the same body.  This walks the lines and infers
    each list item's nesting level from its indentation relative to prior
    items (stack-based), then re-emits each item at exactly level*4 spaces.
    Non-list lines are passed through unchanged.
    """
    lines = text.split('\n')
    result = []
    stack = []  # list of (raw_indent, normalized_level)

    for line in lines:
        m = re.match(r'^( *)([-*+] .*)$', line)
        if m is None:
            result.append(line)
            continue

        raw_indent = len(m.group(1))
        rest = m.group(2)

        # Pop entries deeper than or equal to this line's indent.
        while stack and stack[-1][0] >= raw_indent:
            stack.pop()

        level = 0 if not stack else stack[-1][1] + 1
        stack.append((raw_indent, level))

        result.append(' ' * (level * 4) + rest)

    return '\n'.join(result)


def render_markdown(text: str) -> str:
    """Convert Markdown text to HTML.

    Uses extensions: tables, fenced_code, attr_list, md_in_html.
    Sub-list indentation is normalized to 4 spaces before parsing so that
    decks authored with 2-space indentation render correctly.
    """
    return markdown.markdown(
        _normalize_list_indent(text),
        extensions=['tables', 'fenced_code', 'attr_list', 'md_in_html'],
    )
