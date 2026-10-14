"""Pydantic v2 models for the YAML DSL schema.

Defines all layout slide types, deck metadata, and the AnySlide discriminated union.
"""
from __future__ import annotations

import re
from datetime import date as _date
from typing import Annotated, Literal, Union

from pydantic import BaseModel, ConfigDict, Field, field_validator

_EASE_RE = re.compile(r'^[\w.]+(?:\([\d., ]+\))?$')

# Guardrail: reject obvious injection in CSS `color` values for display math
def _check_math_display_color(v: str | None) -> str | None:
    """Normalize and validate an optional ``math_display_color`` string."""
    if v is None:
        return None
    s = str(v).strip()
    if not s:
        return None
    if len(s) > 120:
        raise ValueError("math_display_color: max 120 characters")
    if ";" in s or "{" in s or "}" in s or "<" in s or "url(" in s.lower() or chr(92) in s:
        raise ValueError(
            "math_display_color: use a short CSS color (e.g. cyan, #0af, rgb(0, 200, 200));"
            " semicolons, angle brackets, backslashes, and url() are not allowed."
        )
    return s

# ---------------------------------------------------------------------------


def _check_footer_inset(v: str) -> str:
    """Validate CSS length for fixed footer `bottom` (viewport inset)."""
    s = str(v).strip()
    if not s:
        return '0.5in'
    if len(s) > 80:
        raise ValueError('footer_inset: max 80 characters')
    if ';' in s or '{' in s or '}' in s or '<' in s or 'url(' in s.lower():
        raise ValueError(
            'footer_inset: use a short CSS length (e.g. 0.5in, 1rem, 12px);'
            ' semicolons, angle brackets, and url() are not allowed.'
        )
    return s

# Base slide model
# ---------------------------------------------------------------------------

class SlideBase(BaseModel):
    """Base model shared by all slide layout types."""
    model_config = ConfigDict(extra='forbid')

    layout: str
    title: str
    subtitle: str | None = None
    notes: str | None = None
    skip: bool = False  # If True, slide is validated but excluded from compiled HTML
    math_display_scale: float | None = Field(
        default=None,
        ge=0.75,
        le=2.0,
        description='Override deck math_display_scale for this slide (None = inherit).',
    )
    math_display_center: bool | None = Field(
        default=None,
        description='Override deck math_display_center for this slide (None = inherit).',
    )
    math_display_color: str | None = Field(
        default=None,
        description='Override deck math_display_color for this slide (None = inherit).',
    )
    title_scale: float | None = Field(
        default=None,
        ge=0.75,
        le=4.0,
        description='Override deck title_scale for this slide (None = use deck default).',
    )
    content_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description='Override deck content_scale for this slide (None = use deck default).',
    )
    blockquote_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description='Override deck blockquote_scale for this slide (None = use deck default).',
    )

    mermaid_scale_mode: Literal['measured', 'fit'] | None = Field(
        default=None,
        description=(
            'Override Mermaid sizing mode for this slide (None = compiler default). '
            "'measured' tries to meet a readable on-screen label size; 'fit' just fits to panel."
        ),
    )
    mermaid_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description=(
            'Multiplier applied to Mermaid SVG scale for this slide (None = compiler default). '
            'Still capped to the available panel size.'
        ),
    )

    body: str | None = Field(None, exclude=True)  # Markdown body, excluded from JSON Schema

    @field_validator('math_display_color')
    @classmethod
    def _v_slide_math_color(cls, v: str | None) -> str | None:
        return _check_math_display_color(v)


# ---------------------------------------------------------------------------
# Animation (declarative GSAP; merged in compiler)
# ---------------------------------------------------------------------------


class BulletStaggerSettings(BaseModel):
    """Optional GSAP stagger parameters for list items on a content slide.

    Omitted fields inherit from deck ``animation_defaults.bullet_stagger``,
    then from skill defaults in ``schema.animation_defaults``.
    """

    model_config = ConfigDict(extra='forbid')

    duration: float | None = Field(
        default=None,
        gt=0,
        le=10,
        description='Tween duration in seconds.',
    )
    stagger: float | None = Field(
        default=None,
        ge=0,
        le=5,
        description='Delay between each list item.',
    )
    ease: str | None = Field(
        default=None,
        max_length=48,
        description='GSAP ease string (e.g. power2.out).',
    )
    threshold: float | None = Field(
        default=None,
        gt=0,
        le=1,
        description='IntersectionObserver threshold for starting the animation.',
    )
    x_offset: float | None = Field(
        default=None,
        ge=-800,
        le=800,
        description='Initial horizontal offset in pixels before the tween.',
    )

    @field_validator('ease')
    @classmethod
    def _v_ease(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if len(s) > 48:
            raise ValueError('ease: max 48 characters')
        if not _EASE_RE.match(s):
            raise ValueError(
                'ease: use a GSAP ease name like power2.out or elastic.out(1, 0.3)'
            )
        return s


class BulletFocusSettings(BaseModel):
    """Optional GSAP key-driven focus parameters for list items.

    When a slide enables ``bullet_focus``, all list items start dimmed
    except the first; pressing ``key`` advances the focused bullet so
    that exactly one item is fully opaque while the others fade to
    ``dim``. Omitted fields inherit deck defaults, then skill defaults.
    """

    model_config = ConfigDict(extra='forbid')

    key: str | None = Field(
        default=None,
        min_length=1,
        max_length=8,
        description='Keyboard key that advances the focused bullet (e.g. "j").',
    )
    back_key: str | None = Field(
        default=None,
        min_length=1,
        max_length=8,
        description='Keyboard key that moves the focus to the previous bullet (e.g. "k").',
    )
    dim: float | None = Field(
        default=None,
        ge=0,
        le=1,
        description='Opacity applied to non-focused list items.',
    )
    duration: float | None = Field(
        default=None,
        gt=0,
        le=10,
        description='Tween duration in seconds for opacity transitions.',
    )
    ease: str | None = Field(
        default=None,
        max_length=48,
        description='GSAP ease string (e.g. power2.out).',
    )

    @field_validator('ease')
    @classmethod
    def _v_focus_ease(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if not _EASE_RE.match(s):
            raise ValueError(
                'ease: use a GSAP ease name like power2.out or elastic.out(1, 0.3)'
            )
        return s


class AnimationDefaults(BaseModel):
    """Deck-level defaults merged before per-slide animation overrides."""

    model_config = ConfigDict(extra='forbid')

    bullet_stagger: BulletStaggerSettings | None = None
    bullet_focus: BulletFocusSettings | None = None


# ---------------------------------------------------------------------------
# Layout-specific slide models
# ---------------------------------------------------------------------------

class TitleSlide(SlideBase):
    """Deck opener: big title + optional subtitle + optional author."""
    layout: Literal['title']
    author: str | None = None


class HeroSlide(SlideBase):
    """Section opener within a deck: section title + optional description."""
    layout: Literal['hero']
    description: str | None = None


class ContentSlide(SlideBase):
    """Presentation content slide: title + Markdown body (md_to_yaml default)."""
    layout: Literal['content']
    bullet_animation: bool | Literal['stagger'] | BulletStaggerSettings | None = Field(
        default=None,
        description=(
            'If true or "stagger", animate list items when the slide is revealed. '
            'Use an object to override duration, stagger, ease, threshold, or x_offset.'
        ),
    )
    bullet_focus: bool | BulletFocusSettings | None = Field(
        default=None,
        description=(
            'If true, dim all list items except the first; pressing the configured '
            'key (default "j") advances the focused bullet. Use an object to override '
            'key, dim opacity, duration, or ease.'
        ),
    )


class TranscribeSlide(SlideBase):
    """Dense transcription slide: same body pipeline as content; transcribe CSS in HTML."""

    layout: Literal['transcribe']
    bullet_animation: bool | Literal['stagger'] | BulletStaggerSettings | None = Field(
        default=None,
        description='Same as content slides: optional GSAP stagger for list items.',
    )
    bullet_focus: bool | BulletFocusSettings | None = Field(
        default=None,
        description='Same as content slides: optional key-driven bullet focus.',
    )


class DividerSlide(SlideBase):
    """Visual section break: title only (rendered as full-bleed divider)."""
    layout: Literal['divider']


class FigureSlide(SlideBase):
    """Image/diagram slide. Extension determines rendering: .jpg/.png/.gif/.webp → <img>, .svg → inline SVG, .mmd → Mermaid. alt_text required."""
    layout: Literal['figure']
    src: str
    alt_text: str
    figure_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description='Override deck figure_scale for this slide (None = use deck default).',
    )


class FigureWideSlide(SlideBase):
    """Wide-figure layout: full-width figure + two text columns below.

    Front matter holds figure metadata only (src, alt_text, caption, proportion).
    Body Markdown is parsed by the engine into summary, left-column, and
    right-column sections delimited by level-2 headings.
    """
    layout: Literal['figure-wide']
    src: str
    alt_text: str
    caption: str | None = None
    proportion: Literal['50/50', '40/60', '60/40'] = '50/50'
    figure_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description='Override deck figure_scale for this slide (None = use deck default).',
    )


def _validate_panel_scale(v):
    """Shared panel_scale check: float or [horizontal, vertical], each 0.2-1.0."""
    if v is None:
        return v
    if isinstance(v, list) and len(v) != 2:
        raise ValueError('panel_scale list must be [horizontal, vertical]')
    for x in (v if isinstance(v, list) else [v]):
        if not 0.2 <= x <= 1.0:
            raise ValueError('panel_scale values must be between 0.2 and 1.0')
    return v


class DiagramSlide(SlideBase):
    """SVG/Mermaid diagram slide. alt_text is required for ADA compliance."""
    layout: Literal['diagram']
    alt_text: str
    panel_scale: float | list[float] | None = Field(
        default=None,
        description=(
            'Shrink the diagram panel relative to its default size (the full '
            'content area): a single fraction applies to both axes, a '
            'two-item list is [horizontal, vertical]. Each value 0.2-1.0.'
        ),
    )

    @field_validator('panel_scale')
    @classmethod
    def _check_panel_scale(cls, v):
        return _validate_panel_scale(v)


class ColumnContent(BaseModel):
    """Structured content for a two-column slide column."""
    model_config = ConfigDict(extra='forbid')

    type: Literal['figure', 'diagram']
    src: str | None = None       # path to image/diagram; extension determines rendering (.jpg/.png → <img>, .svg → inline SVG, .mmd → Mermaid)
    alt_text: str | None = None  # required for ADA; enforced by compiler
    source: str | None = None    # inline Mermaid source (legacy; prefer src with .mmd file)

    mermaid_scale_mode: Literal['measured', 'fit'] | None = Field(
        default=None,
        description=(
            'Override Mermaid sizing mode for this column (None = compiler default). '
            "'measured' tries to meet readable label size; 'fit' just fits to panel."
        ),
    )
    mermaid_scale: float | None = Field(
        default=None,
        ge=0.25,
        le=4.0,
        description=(
            'Multiplier applied to Mermaid SVG scale for this column (None = compiler default). '
            'Still capped to the available panel size.'
        ),
    )



class TwoColumnSlide(SlideBase):
    """Two-column layout. Structured columns go in left/right; free text goes in body."""
    layout: Literal['two-column']
    left: ColumnContent | None = None
    right: ColumnContent | None = None
    proportion: Literal['50/50', '40/60', '60/40'] = '50/50'
    panel_scale: float | list[float] | None = Field(
        default=None,
        description=(
            'Shrink diagram column panels relative to their default size (the '
            'full column band): a single fraction applies to both axes, a '
            'two-item list is [horizontal, vertical]. Each value 0.2-1.0.'
        ),
    )

    @field_validator('panel_scale')
    @classmethod
    def _check_panel_scale(cls, v):
        return _validate_panel_scale(v)


class QuoteSlide(SlideBase):
    """Pull-quote slide: title (the quote) + optional attribution."""
    layout: Literal['quote']
    attribution: str | None = None


class ComparisonSlide(SlideBase):
    """Side-by-side comparison: title + Markdown body with <!-- split --> marker."""
    layout: Literal['comparison']


class CodeSlide(SlideBase):
    """Code block slide: title + fenced code in Markdown body. Language for syntax highlighting."""
    layout: Literal['code']
    language: str = 'text'
    line_numbers: bool = False


class StepsSlide(SlideBase):
    """Numbered steps slide: title + ordered list in Markdown body."""
    layout: Literal['steps']


class SummarySlide(SlideBase):
    """Summary/recap slide: visually distinct from content (e.g., checkmark bullets)."""
    layout: Literal['summary']


class TableCell(BaseModel):
    """A table cell with optional colspan (for spanning header rows)."""
    model_config = ConfigDict(extra='forbid')
    text: str
    colspan: int = 1


class TableSlide(SlideBase):
    """Data table with accessible markup."""
    layout: Literal['table']
    caption: str | None = None
    headers: list[str] = Field(default_factory=list)
    rows: list[list[str | TableCell]] = Field(default_factory=list)
    row_headers: bool = False


class ProofSlide(SlideBase):
    """Proof or derivation slide (Mathematical flavor).

    Identical rendering to ContentSlide; distinguished layout type for
    future visual differentiation and slide-count statistics.
    """
    layout: Literal['proof']


# ---------------------------------------------------------------------------
# Discriminated union covering all layout types
# ---------------------------------------------------------------------------

AnySlide = Annotated[
    Union[
        TitleSlide,
        HeroSlide,
        ContentSlide,
        TranscribeSlide,
        DividerSlide,
        FigureSlide,
        FigureWideSlide,
        DiagramSlide,
        TwoColumnSlide,
        QuoteSlide,
        ComparisonSlide,
        CodeSlide,
        StepsSlide,
        SummarySlide,
        TableSlide,
        ProofSlide,
    ],
    Field(discriminator='layout'),
]


# ---------------------------------------------------------------------------
# Deck metadata and top-level deck container
# ---------------------------------------------------------------------------

VALID_FONTS = ('IBM Plex Sans', 'Inter', 'Fira Sans', 'Roboto', 'Source Sans 3')


class DeckMetadata(BaseModel):
    """Deck-level metadata from the first frontmatter block.

    Attributes:
        flavor: If ``'transcript'``, HTML uses dense left-aligned styling for
            ``content`` and ``table`` slides (transcript / transcribe_to_html).
            Omitted for standard presentation decks.
    """
    model_config = ConfigDict(extra='forbid')

    title: str
    author: str | None = None
    date: _date | None = Field(default_factory=_date.today)
    theme: Literal['dark', 'light'] = 'dark'
    accent_color: str | None = None
    font: str = 'IBM Plex Sans'
    macros: str | None = None  # path to color-macro YAML file (relative to deck YAML)
    title_font_size: str = '2.4rem'
    title_top_margin: str = '0.5rem'
    flavor: Literal['transcript'] | None = None
    math_display_scale: float = Field(
        1.0,
        ge=0.75,
        le=2.0,
        description='Multiplier for $$...$$ display math font size vs slide body.',
    )
    math_display_center: bool = Field(
        True,
        description='If True, display math is centered; if False, aligned with body text.',
    )
    math_display_color: str | None = Field(
        default=None,
        description='Optional CSS color for $$...$$ (display / block) math in slide bodies and tables.',
    )
    view_scale: float = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description='Default in-page view scale for slide content (not the browser tab zoom).',
    )
    remember_view_scale: bool = Field(
        False,
        description='If True, persist view-scale adjustments in localStorage.',
    )
    autofit_floor: float = Field(
        0.5,
        ge=0.25,
        le=1.0,
        description=(
            'Smallest zoom autofit applies to a slide\'s content area. Below it the '
            'content scrolls and the slide is reported as needing a split.'
        ),
    )
    autofit_widen_max: float = Field(
        1.6,
        ge=1.0,
        le=3.0,
        description=(
            'Cap on how much wider (x canvas width) the content area may become while '
            'shrinking, so lines stay readable. 1.0 = never widen (tables then cannot fit).'
        ),
    )
    autofit_title_floor: float = Field(
        0.8,
        ge=0.5,
        le=1.0,
        description=(
            'Smallest zoom autofit applies to a title that does not fit one line. A title '
            'that still does not fit takes two lines at full size.'
        ),
    )
    bake_mermaid: bool = Field(
        False,
        description=(
            'If True, pre-render Mermaid diagrams to inline SVG at compile time '
            '(requires mmdc); makes the deck offline and cross-browser deterministic.'
        ),
    )
    title_scale: float = Field(
        1.0,
        ge=0.75,
        le=4.0,
        description=(
            'Multiplier for slide titles, heading stacks, and hero text '
            '(combined with --font-scale).'
        ),
    )
    content_scale: float = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description=(
            'Multiplier for body, captions, tables, code, and non-title prose '
            '(combined with --font-scale).'
        ),
    )
    blockquote_scale: float = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description=(
            'Multiplier for `>` blockquotes on top of content_scale (a blockquote is '
            '44px against 28px body, so 0.64 makes it body-sized).'
        ),
    )
    figure_scale: float = Field(
        1.0,
        ge=0.25,
        le=4.0,
        description=(
            'Default scale for layout: figure and figure-wide — multiplies the width '
            'cap and matching max-height (vh) so media scales proportionally; the figure '
            'panel uses width: fit-content up to the cap.'
        ),
    )
    figure_layout_debug: bool = Field(
        False,
        description=(
            'If True, draw red debug borders on layout: figure .figure-asset-wrap '
            '(panel) and inner graphic (img / .diagram-container).'
        ),
    )
    footer_scale: float = Field(
        1.0,
        ge=0.5,
        le=2.5,
        description=(
            'Multiplies the fixed bottom bar (page counter, view-scale, go-to) font sizes '
            'and padding; set on the root as CSS --footer-scale.'
        ),
    )
    footer_inset: str = Field(
        '0.5in',
        description=(
            'CSS length for the fixed footer nav distance from the viewport bottom '
            '(e.g. 0.5in — half a inch margin above the screen edge; default 0.5in was 1in).'
        ),
    )
    animation_defaults: AnimationDefaults | None = Field(
        default=None,
        description=(
            'Deck-wide animation defaults; merged with skill defaults, then per-slide '
            'bullet_animation overrides.'
        ),
    )
    gsap_script_url: str | None = Field(
        default=None,
        max_length=500,
        description=(
            'HTTPS URL for the GSAP script tag. When omitted, the md_to_yaml skill '
            'default CDN URL is used.'
        ),
    )

    @field_validator('gsap_script_url')
    @classmethod
    def _v_gsap_script_url(cls, v: str | None) -> str | None:
        if v is None:
            return None
        s = str(v).strip()
        if not s:
            return None
        if len(s) > 500:
            raise ValueError('gsap_script_url: max 500 characters')
        if not s.startswith('https://'):
            raise ValueError('gsap_script_url must start with https://')
        low = s.lower()
        if 'javascript:' in low or '<' in s or '\n' in s or '\r' in s:
            raise ValueError('gsap_script_url: invalid URL')
        return s

    @field_validator('footer_inset')
    @classmethod
    def _v_footer_inset(cls, v: str) -> str:
        return _check_footer_inset(v)

    @field_validator('math_display_color')
    @classmethod
    def _v_deck_math_color(cls, v: str | None) -> str | None:
        return _check_math_display_color(v)

    @field_validator('font')
    @classmethod
    def validate_font(cls, v: str) -> str:
        if v not in VALID_FONTS:
            raise ValueError(
                f"font must be one of: {', '.join(VALID_FONTS)}. Got: {v!r}"
            )
        return v


class Deck(BaseModel):
    """Top-level deck container: metadata + ordered list of slides."""
    metadata: DeckMetadata
    slides: list[AnySlide]
