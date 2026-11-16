"""SVG renderer: sanitization and ADA-compliant wrapping.

Uses bleach for allowlist-based attribute stripping to prevent XSS via
CSS-based event handlers, onclick, and SVG <use> xlink attacks.
"""
from __future__ import annotations

import re

import bleach
from bleach.css_sanitizer import CSSSanitizer

_CSS_SANITIZER = CSSSanitizer(allowed_css_properties=[
    'width', 'height', 'min-width', 'max-width', 'min-height', 'max-height',
    'display', 'flex-direction', 'align-items', 'justify-content',
    'box-sizing', 'color', 'background', 'background-color',
    'font-size', 'font-weight', 'font-family', 'font-style',
    'text-align', 'line-height', 'letter-spacing',
    'margin', 'margin-top', 'margin-bottom', 'margin-left', 'margin-right',
    'padding', 'padding-top', 'padding-bottom', 'padding-left', 'padding-right',
    'border', 'border-radius', 'opacity', 'overflow',
    'vertical-align', 'white-space', 'word-break',
    # SVG paint and stroke properties (2026-11-16): without them a figure that
    # colors its shapes with style="fill:…" rendered black, and dashed lines solid.
    'fill', 'stroke', 'stroke-width', 'stroke-dasharray', 'stroke-dashoffset',
    'stroke-linecap', 'stroke-linejoin', 'stroke-opacity', 'fill-opacity',
    'text-anchor', 'dominant-baseline',
])

ALLOWED_SVG_TAGS = [
    'svg', 'g', 'path', 'circle', 'rect', 'line', 'text', 'tspan',
    'defs', 'use', 'symbol', 'title', 'desc', 'polygon', 'polyline',
    'ellipse', 'marker', 'clipPath', 'linearGradient', 'radialGradient', 'stop',
    # foreignObject + inline MathML support inside SVG
    'foreignObject', 'div', 'span', 'p',
    'math', 'mrow', 'mi', 'mo', 'mn', 'msup', 'msub', 'msubsup',
    'mfrac', 'mspace', 'mtext', 'mover', 'munder', 'munderover', 'mtable',
    'mtr', 'mtd', 'ms', 'mstyle', 'merror', 'mpadded', 'mphantom',
]

ALLOWED_SVG_ATTRS = {
    '*': ['id', 'class', 'style', 'transform', 'xmlns', 'marker-end', 'marker-start'],
    'svg': [
        'viewBox', 'xmlns', 'xmlns:xlink', 'width', 'height',
        'fill', 'stroke', 'stroke-width', 'font-size', 'text-anchor',
        'dominant-baseline',
    ],
    'g': ['fill', 'stroke', 'stroke-width', 'transform'],
    'path': ['d', 'fill', 'stroke', 'stroke-width'],
    'circle': ['cx', 'cy', 'r', 'fill', 'stroke', 'stroke-width'],
    'rect': ['x', 'y', 'width', 'height', 'rx', 'ry', 'fill', 'stroke', 'stroke-width'],
    'line': ['x1', 'y1', 'x2', 'y2', 'stroke', 'stroke-width', 'marker-end'],
    'text': ['x', 'y', 'font-size', 'text-anchor', 'dominant-baseline', 'fill'],
    'tspan': ['x', 'y', 'dx', 'dy'],
    'use': ['xlink:href', 'href', 'x', 'y', 'width', 'height'],
    'symbol': ['viewBox', 'width', 'height'],
    'polygon': ['points', 'fill', 'stroke', 'stroke-width'],
    'polyline': ['points', 'fill', 'stroke', 'stroke-width'],
    'ellipse': ['cx', 'cy', 'rx', 'ry', 'fill', 'stroke', 'stroke-width'],
    'marker': ['id', 'markerWidth', 'markerHeight', 'refX', 'refY', 'orient', 'markerUnits'],
    'clipPath': ['id'],
    'linearGradient': ['id', 'x1', 'y1', 'x2', 'y2', 'gradientUnits'],
    'radialGradient': ['id', 'cx', 'cy', 'r', 'fx', 'fy', 'gradientUnits'],
    'stop': ['offset', 'stop-color', 'stop-opacity'],
    'title': [],
    'desc': [],
    'defs': [],
    'foreignObject': ['x', 'y', 'width', 'height'],
    'div': ['xmlns', 'style', 'class'],
    'span': ['class', 'style'],
    'p': ['style'],
    'math': ['display', 'xmlns'],
    'mspace': ['width'],
    'mstyle': ['mathcolor', 'mathsize', 'displaystyle'],
    'mpadded': ['width', 'height', 'depth', 'lspace', 'voffset'],
}


# Presentation attributes that only change how a shape is painted (2026-11-16).
# They were stripped before, so dashed lines became solid and bold labels plain.
_PAINT_ATTRS = [
    'opacity', 'fill-opacity', 'stroke-opacity', 'stroke-dasharray', 'stroke-dashoffset',
    'stroke-linecap', 'stroke-linejoin', 'vector-effect', 'shape-rendering',
]
_TEXT_ATTRS = ['font-weight', 'font-family', 'font-style', 'letter-spacing', 'dx', 'dy',
               'stroke', 'stroke-width', 'paint-order']
for _tag in ('svg', 'g', 'path', 'circle', 'rect', 'line', 'polygon', 'polyline', 'ellipse',
             'text', 'tspan'):
    ALLOWED_SVG_ATTRS.setdefault(_tag, [])
    ALLOWED_SVG_ATTRS[_tag] = list(dict.fromkeys(ALLOWED_SVG_ATTRS[_tag] + _PAINT_ATTRS))
for _tag in ('svg', 'g', 'text', 'tspan'):
    ALLOWED_SVG_ATTRS[_tag] = list(dict.fromkeys(
        ALLOWED_SVG_ATTRS[_tag] + _TEXT_ATTRS + ['fill', 'font-size', 'text-anchor']))


# ---------------------------------------------------------------- <style> blocks
# bleach removes <style>. An SVG drawn with classes and CSS custom properties then
# loses every color. Keep the block: clean it, and scope every rule to this one SVG,
# so that it cannot change the rest of the deck once the SVG is inlined.
_STYLE_RE = re.compile(r'<style\b[^>]*>(.*?)</style>', re.S | re.I)
_CSS_BAD = re.compile(r'@import|url\s*\(\s*(?![\'"]?#)|expression\s*\(|javascript:|behavior\s*:|-moz-binding|</', re.I)


def _scope_selector(sel: str, scope: str) -> list[str]:
    """Scope one selector to the SVG with id `scope`.

    `:root` and `svg` mean the SVG itself. The first compound selector may also
    match the SVG itself (a class on the root, as in `.fig text`), so emit both
    `#scope X …` and `#scope:is(X) …`.
    """
    sel = sel.strip()
    if not sel:
        return []
    if sel in (':root', 'svg', ':scope'):
        return [f'#{scope}']
    first, _, rest = sel.partition(' ')
    out = [f'#{scope} {sel}']
    if not first.startswith(('>', '+', '~')):
        root_first = 'svg' if first in (':root', 'svg') else first
        out.append(f'#{scope}:is({root_first}) {rest}'.rstrip() if rest else f'#{scope}:is({root_first})')
    return out


def scope_svg_styles(css: str, scope: str) -> str:
    """Clean a <style> block and scope its rules to `#scope`. Drops at-rules
    (@import, @font-face, @media …) and any rule that loads a URL or script."""
    import tinycss2
    out = []
    for rule in tinycss2.parse_stylesheet(css, skip_comments=True, skip_whitespace=True):
        if rule.type != 'qualified-rule':
            continue                      # at-rules and parse errors are dropped
        prelude = tinycss2.serialize(rule.prelude)
        body = tinycss2.serialize(rule.content)
        if _CSS_BAD.search(prelude) or _CSS_BAD.search(body):
            continue
        sels = [s for part in prelude.split(',') for s in _scope_selector(part, scope)]
        if sels:
            out.append(f"{', '.join(sels)} {{{body}}}")
    return '\n'.join(out)


def _extract_styles(raw_svg: str) -> tuple[str, str]:
    """Remove the <style> blocks from the SVG; return (svg, their joined CSS)."""
    css = '\n'.join(m.group(1) for m in _STYLE_RE.finditer(raw_svg))
    return _STYLE_RE.sub('', raw_svg), css


def _stripped_report(before: str, after: str) -> str:
    """Name the tags and attributes that sanitizing removed, for a compile warning."""
    tag = re.compile(r'<([A-Za-z][\w:-]*)')
    att = re.compile(r'\s([A-Za-z_:][\w:.-]*)\s*=')
    lost_t = sorted(set(tag.findall(before)) - set(tag.findall(after)))
    lost_a = sorted(set(att.findall(before)) - set(att.findall(after))
                    - {'role', 'aria-labelledby', 'aria-label', 'aria-describedby'})  # the wrapper adds its own
    parts = []
    if lost_t:
        parts.append('tags ' + ', '.join(lost_t))
    if lost_a:
        parts.append('attributes ' + ', '.join(lost_a))
    return '; '.join(parts)


def sanitize_svg(raw_svg: str) -> str:
    """Strip dangerous tags and attributes from SVG using bleach allowlist."""
    return bleach.clean(raw_svg, tags=ALLOWED_SVG_TAGS, attributes=ALLOWED_SVG_ATTRS,
                        css_sanitizer=_CSS_SANITIZER, strip=True)


def _normalize_svg_dimensions(svg: str) -> str:
    """Replace fixed width/height on <svg> tag with responsive values, preserve viewBox."""
    # Replace width="..." and height="..." attributes on the opening <svg tag
    svg = re.sub(r'(<svg[^>]*?)\bwidth="[^"]*"', r'\1width="100%"', svg, count=1)
    svg = re.sub(r'(<svg[^>]*?)\bheight="[^"]*"', r'\1height="auto"', svg, count=1)
    return svg


def wrap_svg_ada(svg: str, alt_text: str, slide_id: str) -> str:
    """Sanitize SVG, normalize dimensions, and inject ADA accessibility attributes.

    Adds role="img", aria-labelledby, <title>, and <desc> elements.
    """
    raw = svg
    svg, css = _extract_styles(svg)
    svg = sanitize_svg(svg)
    svg = _normalize_svg_dimensions(svg)

    # Scope id on the root <svg>; the scoped <style> goes in as its first child.
    scope = f'{slide_id}-svg'
    svg = re.sub(r'(<svg\b[^>]*?)\sid="[^"]*"', r'\1', svg, count=1)
    svg = re.sub(r'<svg\b', f'<svg id="{scope}"', svg, count=1)
    scoped = scope_svg_styles(css, scope) if css.strip() else ''

    lost = _stripped_report(_STYLE_RE.sub('', raw), svg)
    if lost:
        import sys
        print(f'WARNING {slide_id}: the SVG sanitizer removed {lost}. '
              'Use attributes it keeps, or a PNG (see svg.md).', file=sys.stderr)

    title_id = f'{slide_id}-svg-title'
    desc_id = f'{slide_id}-svg-desc'

    # Inject role + aria-labelledby into the <svg> opening tag
    svg = re.sub(
        r'<svg\b',
        f'<svg role="img" aria-labelledby="{title_id} {desc_id}"',
        svg,
        count=1,
    )

    # Inject <title> and <desc> as first children of <svg>
    injection = (
        f'<title id="{title_id}">{alt_text}</title>'
        f'<desc id="{desc_id}">{alt_text}</desc>'
        + (f'<style>{scoped}</style>' if scoped else '')
    )
    # Insert after the closing > of the opening <svg ...> tag
    svg = re.sub(r'(<svg[^>]*>)', lambda m: m.group(1) + injection, svg, count=1)

    return svg
