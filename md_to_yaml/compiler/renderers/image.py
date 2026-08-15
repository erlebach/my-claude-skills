"""Image renderer: path reference or base64 data URI embedding."""
from __future__ import annotations

import base64
import html
import os
import sys

_MIME_MAP = {
    '.png': 'image/png',
    '.jpg': 'image/jpeg',
    '.jpeg': 'image/jpeg',
    '.gif': 'image/gif',
    '.svg': 'image/svg+xml',
    '.webp': 'image/webp',
}


def render_image(
    src: str,
    alt_text: str,
    embed: bool = False,
    base_dir: str = '.',
) -> str:
    """Return an <img> HTML element.

    Args:
        src: Image path (relative to base_dir when embed=True).
        alt_text: Required alt text for ADA compliance.
        embed: When True, embed as base64 data URI.
        base_dir: Directory to resolve relative paths against.
    """
    if not alt_text:
        alt_text = os.path.splitext(os.path.basename(src))[0]
        print(f"WARNING: Missing alt text for image '{src}'; using filename '{alt_text}'", file=sys.stderr)

    if embed:
        resolved = os.path.join(base_dir, src)
        if os.path.isfile(resolved):
            ext = os.path.splitext(src)[1].lower()
            mime = _MIME_MAP.get(ext, 'application/octet-stream')
            with open(resolved, 'rb') as fh:
                data = base64.b64encode(fh.read()).decode('ascii')
            return f'<img src="data:{mime};base64,{data}" alt="{html.escape(alt_text)}">'
        else:
            print(f"WARNING: Image not found: {resolved}", file=sys.stderr)
            # Fall through to path reference

    return f'<img src="{src}" alt="{html.escape(alt_text)}">'
