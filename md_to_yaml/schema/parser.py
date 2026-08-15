"""Hybrid YAML+Markdown deck file parser.

File format:
- File consists of blocks delimited by --- lines (at start of line)
- First block between --- markers is deck metadata (YAML)
- Subsequent blocks are slides, each with:
  - YAML frontmatter between --- markers
  - Optional Markdown body after closing ---
- Slides are separated by the next --- (which opens the next slide's frontmatter)

Parsing strategy:
1. Strip the file and split on ^---$ boundaries using regex
2. First non-empty part is deck metadata YAML
3. Remaining parts alternate: frontmatter YAML, then body text, per slide
   Each slide consumes exactly 2 parts: frontmatter + body
   (body may be empty if the slide has no Markdown content)
"""
import re
from pathlib import Path

import yaml
from pydantic import TypeAdapter, ValidationError

from schema.models import AnySlide, Deck, DeckMetadata

FENCE_RE = re.compile(r'^---\s*$', re.MULTILINE)
_COMMENT_LINE = re.compile(r'^//.*$', re.MULTILINE)


def _strip_comments(text: str) -> str:
    """Remove lines starting with '//' before YAML or Markdown processing."""
    return _COMMENT_LINE.sub('', text)

_slide_adapter: TypeAdapter[AnySlide] = TypeAdapter(AnySlide)


def _fence_line_numbers(text: str) -> list[int]:
    """1-based line numbers of ``---`` fence rows."""
    lines: list[int] = []
    for i, line in enumerate(text.splitlines(), start=1):
        if FENCE_RE.match(line):
            lines.append(i)
    return lines


def _slide_frontmatter_start_line(fence_lines: list[int], slide_index: int) -> int | None:
    """First 1-based line of slide ``slide_index`` YAML (0 = first content slide)."""
    k = 2 + 2 * slide_index
    if k >= len(fence_lines):
        return None
    return fence_lines[k] + 1


def _append_slide_location_note(
    path: str | Path,
    raw_text: str,
    slide_index: int,
    exc: ValidationError,
) -> None:
    """Attach a source location note to a slide ``ValidationError``."""
    fence_lines = _fence_line_numbers(raw_text)
    start = _slide_frontmatter_start_line(fence_lines, slide_index)
    resolved = Path(path).resolve()
    slide_no = slide_index + 1
    if start is not None:
        msg = (
            f"{resolved}: slide {slide_no} (content slide index {slide_index}) — "
            f"frontmatter starts near line {start}"
        )
    else:
        msg = (
            f"{resolved}: slide {slide_no} (content slide index {slide_index}) — "
            "could not map to a line number (check ``---`` fences)"
        )
    exc.add_note(msg)




def parse_deck_file(path: str | Path) -> Deck:
    """Parse a hybrid YAML+Markdown deck file and return a validated Deck.

    Args:
        path: Path to the .yaml deck file.

    Returns:
        A validated Deck instance.

    Raises:
        ValueError: If the file is empty or metadata is malformed.
        pydantic.ValidationError: If any slide fails Pydantic validation.
    """
    raw_text = Path(path).read_text(encoding='utf-8')
    text = raw_text.strip()

    # Split on --- lines; the leading --- means the first part is empty
    parts = FENCE_RE.split(text)

    # Filter empty parts (the leading/trailing empty strings from split)
    non_empty = [p for p in parts if p.strip()]

    if not non_empty:
        raise ValueError("Empty deck file")

    # First part is deck metadata YAML
    metadata_raw = yaml.safe_load(_strip_comments(non_empty[0]))
    if not isinstance(metadata_raw, dict):
        raise ValueError(
            f"Deck metadata must be a YAML mapping, got {type(metadata_raw).__name__}"
        )
    metadata = DeckMetadata(**metadata_raw)

    # Remaining parts: pair up (frontmatter, body)
    # non_empty[1], non_empty[2] = slide1 frontmatter, slide1 body
    # non_empty[3], non_empty[4] = slide2 frontmatter, slide2 body
    # ...
    # If the last slide has no body, non_empty length may be odd (no trailing body part)
    slide_parts = non_empty[1:]
    slides = []

    i = 0
    while i < len(slide_parts):
        frontmatter_str = slide_parts[i]
        # Body is the next part; may not exist if this is the last slide with no body
        body_str = slide_parts[i + 1] if i + 1 < len(slide_parts) else ''

        frontmatter = yaml.safe_load(_strip_comments(frontmatter_str))
        if not isinstance(frontmatter, dict):
            i += 2
            continue

        # Detect 'body' in frontmatter YAML — body must appear as Markdown below the ---, not in YAML
        if 'body' in frontmatter:
            # Raise a clear error that mentions 'body'
            raise ValueError(
                f"Field 'body' found in YAML frontmatter. "
                "The slide body must be written as Markdown below the closing --- separator, "
                "not as a YAML field. Remove 'body:' from the frontmatter."
            )

        # Determine how many parts this slide consumed:
        # If body_str looks like frontmatter (has 'layout:' key when parsed), then
        # this slide has no body and the next part is the next slide's frontmatter.
        body_is_next_frontmatter = _looks_like_frontmatter(body_str)

        if body_is_next_frontmatter:
            # No body for this slide
            body = None
            i += 1  # advance by 1 (consumed only frontmatter)
        else:
            body = body_str.strip() or None
            i += 2  # advance by 2 (consumed frontmatter + body)

        frontmatter['body'] = body
        slide_idx = len(slides)
        try:
            slide = _slide_adapter.validate_python(frontmatter)
        except ValidationError as exc:
            _append_slide_location_note(path, raw_text, slide_idx, exc)
            raise
        slides.append(slide)

    return Deck(metadata=metadata, slides=slides)


def _looks_like_frontmatter(text: str) -> bool:
    """Heuristic: does this text look like YAML frontmatter (i.e. is the next slide's header)?

    We check if parsing it as YAML yields a dict with a 'layout' key.
    This distinguishes between a Markdown body and a YAML frontmatter block.
    """
    stripped = text.strip()
    if not stripped:
        return False
    try:
        parsed = yaml.safe_load(stripped)
        return isinstance(parsed, dict) and 'layout' in parsed
    except yaml.YAMLError:
        return False
