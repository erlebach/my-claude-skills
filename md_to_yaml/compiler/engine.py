"""Compiler engine: validate-then-render pipeline."""
import base64
import json
import re
import shutil
import sys
from pathlib import Path

import yaml as _yaml

from jinja2 import Environment, FileSystemLoader, select_autoescape

from schema.animation_defaults import (
    SKILL_BULLET_FOCUS_DEFAULTS,
    SKILL_BULLET_STAGGER_DEFAULTS,
    SKILL_GSAP_SCRIPT_URL_DEFAULT,
)
from schema.models import BulletFocusSettings, BulletStaggerSettings, Deck
from compiler.validators import validate_deck, MERMAID_STARTERS
from compiler.renderers import (
    render_body,
    render_rich_text,
    get_pygments_css,
    render_code,
    render_image,
    wrap_svg_ada,
    render_mermaid,
)
from compiler.renderers.mermaid import _inject_text_color, bake_mermaid_in_html
from compiler.renderers.math import (
    extract_and_render_math,
    strip_math_display_inline_from_heading_html,
)

import html as _html

TEMPLATES_DIR = Path(__file__).parent / "templates"
FONTS_DIR = Path(__file__).parent / "fonts"


def _embedded_font_css(family: str) -> str | None:
    """An @font-face block with the family inlined, or None if it is not cached.

    A deck is otherwise self-contained -- --embed-images inlines every image --
    so the stylesheet link to Google was the one thing a reader had to fetch:
    offline they got a fallback font, online they made a request to Google that
    the deck never told them about. A font dropped in compiler/fonts/<slug>.woff2
    is inlined instead. Anything not cached still falls back to the Google link
    in base.html.j2, so naming a new font in a deck keeps working.

    The cached files are variable fonts, hence the `font-weight: 100 700` range:
    one file serves every weight the templates ask for (400, 600, 700) rather
    than three copies of the same base64.
    """
    slug = re.sub(r"[^a-z0-9]+", "-", family.lower()).strip("-")
    path = FONTS_DIR / f"{slug}.woff2"
    if not path.is_file():
        return None
    b64 = base64.b64encode(path.read_bytes()).decode("ascii")
    return (
        "@font-face {\n"
        f"  font-family: '{family}';\n"
        "  font-style: normal;\n"
        "  font-weight: 100 700;\n"
        "  font-display: swap;\n"
        f"  src: url(data:font/woff2;base64,{b64}) format('woff2');\n"
        "}"
    )


def _merge_bullet_stagger_config(deck: Deck, slide) -> dict[str, float | str] | None:
    """Resolve bullet stagger params: skill defaults, deck animation_defaults, slide overrides."""
    spec = getattr(slide, 'bullet_animation', None)
    if spec is None or spec is False:
        return None
    out = dict(SKILL_BULLET_STAGGER_DEFAULTS)
    ad = deck.metadata.animation_defaults
    if ad is not None and ad.bullet_stagger is not None:
        out.update(ad.bullet_stagger.model_dump(mode='python', exclude_none=True))
    if spec is True or spec == 'stagger':
        pass
    elif isinstance(spec, BulletStaggerSettings):
        out.update(spec.model_dump(mode='python', exclude_none=True))
    else:
        return None
    return out


def _bullet_stagger_json(cfg: dict[str, float | str] | None) -> str | None:
    """Serialize merged stagger config for a data-attribute on the slide section."""
    if cfg is None:
        return None
    return json.dumps(cfg, separators=(',', ':'))


def _merge_bullet_focus_config(deck: Deck, slide) -> dict[str, float | str] | None:
    """Resolve key-driven bullet focus params: skill defaults, deck animation_defaults, slide overrides."""
    spec = getattr(slide, 'bullet_focus', None)
    if spec is None or spec is False:
        return None
    out = dict(SKILL_BULLET_FOCUS_DEFAULTS)
    ad = deck.metadata.animation_defaults
    if ad is not None and getattr(ad, 'bullet_focus', None) is not None:
        out.update(ad.bullet_focus.model_dump(mode='python', exclude_none=True))
    if spec is True:
        pass
    elif isinstance(spec, BulletFocusSettings):
        out.update(spec.model_dump(mode='python', exclude_none=True))
    else:
        return None
    return out


def _bullet_focus_json(cfg: dict[str, float | str] | None) -> str | None:
    """Serialize merged focus config for a data-attribute on the slide section."""
    if cfg is None:
        return None
    return json.dumps(cfg, separators=(',', ':'))

def _mermaid_data_attrs(obj) -> str:
    """Serialize Mermaid scaling overrides to data-* attributes on .diagram-container."""
    attrs = []

    mode = getattr(obj, "mermaid_scale_mode", None)
    if mode:
        attrs.append(f' data-scale-mode="{_html.escape(str(mode).strip().lower())}"')

    scale = getattr(obj, "mermaid_scale", None)
    if scale is not None:
        attrs.append(f' data-scale-mult="{_html.escape(str(scale).strip())}"')

    return "".join(attrs)

def _render_col_html(col, base_dir: str, embed_images: bool, col_id: str, theme: str) -> str:
    """Render a TwoColumnSlide column to HTML, dispatching on src extension."""
    if col.src:
        ext = Path(col.src).suffix.lower()
        src_path = col.src if Path(col.src).is_absolute() else Path(base_dir) / col.src
        alt = col.alt_text or ""
        if ext == ".mmd":
            mermaid_source = _inject_text_color(Path(src_path).read_text(encoding="utf-8"))
            data_attrs = _mermaid_data_attrs(col)
            return (f'<div class="diagram-container"{data_attrs} role="img" aria-label="{_html.escape(alt)}">'
                    f'<pre class="mermaid" aria-hidden="true">{_html.escape(mermaid_source)}</pre></div>')
        elif ext == ".svg":
            raw_svg = Path(src_path).read_text(encoding="utf-8")
            return (f'<div class="diagram-container" role="img" aria-label="{_html.escape(alt)}">'
                    f'{wrap_svg_ada(raw_svg, alt, col_id)}</div>')
        else:
            return render_image(col.src, alt, embed=embed_images, base_dir=base_dir)
    elif col.source:
        mermaid_source = _inject_text_color(col.source)
        alt = col.alt_text or ""
        data_attrs = _mermaid_data_attrs(col)
        return (f'<div class="diagram-container"{data_attrs} role="img" aria-label="{_html.escape(alt)}">'
                f'<pre class="mermaid" aria-hidden="true">{_html.escape(mermaid_source)}</pre></div>')



def _parse_figure_wide_body(body: str | None, theme: str, macros: dict[str, str] | None = None) -> dict:
    """Parse a figure-wide slide body into summary + left/right column sections.

    Returns dict with keys:
        rendered_fw_summary, rendered_fw_left_heading,
        rendered_fw_left_body, rendered_fw_right_heading, rendered_fw_right_body
    All values are HTML strings or None.
    """
    empty = {
        "rendered_fw_summary": None,
        "rendered_fw_left_heading": None,
        "rendered_fw_left_body": None,
        "rendered_fw_right_heading": None,
        "rendered_fw_right_body": None,
    }
    if not body:
        return empty

    parts = re.split(r'(?:^|\n)## ', body.lstrip())
    sections = []
    for part in parts:
        if not part.strip():
            continue
        first_newline = part.find('\n')
        if first_newline == -1:
            heading = part.strip()
            content = ''
        else:
            heading = part[:first_newline].strip()
            content = part[first_newline:].strip()
        sections.append((heading, content))

    summary_html = None
    col_sections = []
    for heading, content in sections:
        if heading.lower() == 'summary':
            if content:
                class _SummaryProxy:
                    layout = 'content'
                proxy = _SummaryProxy()
                proxy.body = content
                summary_html = render_body(proxy, embed_images=False, theme=theme, macros=macros)
        else:
            col_sections.append((heading, content))

    def _render_col(heading, content):
        heading_html = render_rich_text(heading, theme, macros=macros) if heading else None
        body_html = None
        if content:
            class _ColProxy:
                layout = 'content'
            proxy = _ColProxy()
            proxy.body = content
            body_html = render_body(proxy, embed_images=False, theme=theme, macros=macros)
        return heading_html, body_html

    left_h = left_b = right_h = right_b = None
    if len(col_sections) >= 1:
        left_h, left_b = _render_col(*col_sections[0])
    if len(col_sections) >= 2:
        right_h, right_b = _render_col(*col_sections[1])

    return {
        "rendered_fw_summary": summary_html,
        "rendered_fw_left_heading": left_h,
        "rendered_fw_left_body": left_b,
        "rendered_fw_right_heading": right_h,
        "rendered_fw_right_body": right_b,
    }


_env = Environment(
    loader=FileSystemLoader(str(TEMPLATES_DIR)),
    autoescape=select_autoescape(["html"]),
    keep_trailing_newline=True,
)


def compile_deck(
    deck: Deck,
    output_path: str,
    yaml_path: str = "",
    embed_images: bool = False,
    include_skipped: bool = False,
    include_notes: bool = True,
    figure_layout_debug: bool = False,
    bake_mermaid: bool = False,
) -> None:
    """Validate deck and render to a self-contained HTML file.

    Errors (missing alt_text, bad contrast) halt with exit code 1.
    Warnings (layout variety, bullet limits) print to stderr but produce output.

    Slides with ``skip: true`` are always validated but excluded from the
    rendered HTML unless ``include_skipped=True`` is passed.

    If ``figure_layout_debug`` is True (CLI ``--figure-layout-debug``) or
    ``deck.metadata.figure_layout_debug`` is True, layout figure debug borders
    are enabled in the HTML output.
    """
    yaml_dir = str(Path(yaml_path).parent) if yaml_path else str(Path(output_path).parent)
    errors, warnings = validate_deck(deck, base_dir=yaml_dir)

    for w in warnings:
        print(w, file=sys.stderr)

    if errors:
        for e in errors:
            print(e, file=sys.stderr)
        sys.exit(1)

    macros: dict[str, str] = {}
    if deck.metadata.macros:
        macros_path = Path(yaml_dir) / deck.metadata.macros
        try:
            macros = _yaml.safe_load(macros_path.read_text(encoding="utf-8")) or {}
        except FileNotFoundError:
            print(f"WARNING: macros file not found: {macros_path}", file=sys.stderr)

    html = _render(
        deck,
        output_path=output_path,
        yaml_dir=yaml_dir,
        embed_images=embed_images,
        include_skipped=include_skipped,
        include_notes=include_notes,
        macros=macros,
        figure_layout_debug=bool(figure_layout_debug)
        or bool(deck.metadata.figure_layout_debug),
        bake_mermaid=bool(bake_mermaid) or bool(deck.metadata.bake_mermaid),
    )
    Path(output_path).write_text(html, encoding="utf-8")


def _render(
    deck: Deck,
    output_path: str = ".",
    yaml_dir: str = "",
    embed_images: bool = False,
    include_skipped: bool = False,
    include_notes: bool = True,
    macros: dict[str, str] | None = None,
    figure_layout_debug: bool = False,
    bake_mermaid: bool = False,
) -> str:
    """Render deck to HTML string using Jinja2 templates."""
    template = _env.get_template("base.html.j2")

    render_slides = deck.slides if include_skipped else [
        s for s in deck.slides if not getattr(s, "skip", False)
    ]

    # Every layout template emits `slide.notes` as a hidden <aside>. Clearing the
    # field here drops those blocks from the HTML in one place, rather than adding
    # the same guard to all fifteen templates.
    if not include_notes:
        render_slides = [s.model_copy(update={"notes": None}) for s in render_slides]

    slides_context = []
    for i, slide in enumerate(render_slides):
        slide_id = f"slide-{i + 1}"
        fw_ctx = {
            "rendered_fw_summary": None,
            "rendered_fw_left_heading": None,
            "rendered_fw_left_body": None,
            "rendered_fw_right_heading": None,
            "rendered_fw_right_body": None,
        }
        rendered_body = (
            render_body(slide, embed_images=embed_images, theme=deck.metadata.theme, macros=macros)
            if getattr(slide, "body", None)
            else None
        )

        rendered_table_headers = None
        rendered_table_rows = None
        rendered_table_caption = None
        rendered_description = None
        if slide.layout == "table":
            thm = deck.metadata.theme
            if getattr(slide, "headers", None):
                rendered_table_headers = [
                    render_rich_text(h, thm, macros=macros) for h in slide.headers
                ]
            rendered_table_rows = [
                [
                    {
                        "html": render_rich_text(cell.text, thm, macros=macros),
                        "colspan": cell.colspan,
                    }
                    if hasattr(cell, "colspan")
                    else {"html": render_rich_text(str(cell), thm, macros=macros), "colspan": 1}
                    for cell in row
                ]
                for row in slide.rows
            ]
            if getattr(slide, "caption", None):
                rendered_table_caption = render_rich_text(slide.caption, thm, macros=macros)
        if slide.layout == "hero" and getattr(slide, "description", None):
            rendered_description = render_rich_text(
                slide.description, deck.metadata.theme, macros=macros
            )

        rendered_code = None
        rendered_image = None
        rendered_svg = None
        rendered_mermaid_html = None

        rendered_title = strip_math_display_inline_from_heading_html(
            extract_and_render_math(str(slide.title), macros=macros)
        )
        rendered_subtitle = None
        if getattr(slide, "subtitle", None):
            rendered_subtitle = strip_math_display_inline_from_heading_html(
                extract_and_render_math(str(slide.subtitle), macros=macros)
            )
        rendered_author_line = None
        if slide.layout == "title" and getattr(slide, "author", None):
            rendered_author_line = strip_math_display_inline_from_heading_html(
                extract_and_render_math(str(slide.author), macros=macros)
            )

        _math_marker = "<math"
        title_has_math = _math_marker in rendered_title or (
            rendered_subtitle is not None and _math_marker in rendered_subtitle
        ) or (
            rendered_author_line is not None and _math_marker in rendered_author_line
        )

        if slide.layout == "code" and getattr(slide, "body", None):
            code_body = slide.body.strip()
            trailing_body = ""
            # Strip markdown code fences if present. The closing fence is the
            # LAST line that is exactly ``` — searching from the end so a code
            # sample may itself contain fences. Anything after that line is
            # slide prose, and belongs below the panel rather than inside it.
            if code_body.startswith("```"):
                lines = code_body.split("\n")
                lines = lines[1:]  # remove opening fence
                close_at = next(
                    (j for j in range(len(lines) - 1, -1, -1)
                     if lines[j].strip() == "```"),
                    None,
                )
                if close_at is not None:
                    trailing_body = "\n".join(lines[close_at + 1:]).strip()
                    lines = lines[:close_at]
                code_body = "\n".join(lines)
            rendered_code = render_code(
                code_body,
                slide.language,
                slide.line_numbers,
                deck.metadata.theme,
            )
            # Always reset rendered_body — the pre-computed value was rendered
            # from the whole body, fenced code included, which must not be
            # repeated underneath the panel.
            if trailing_body:
                class _BodyProxy:
                    body = trailing_body
                    layout = "content"
                rendered_body = render_body(
                    _BodyProxy(), embed_images=embed_images,
                    theme=deck.metadata.theme, macros=macros,
                )
            else:
                rendered_body = None
        elif slide.layout == "figure":
            base_dir = yaml_dir or str(Path(output_path).parent)
            ext = Path(slide.src).suffix.lower()
            if ext == ".mmd":
                mmd_path = slide.src if Path(slide.src).is_absolute() else Path(base_dir) / slide.src
                mermaid_source = Path(mmd_path).read_text(encoding="utf-8")
                rendered_mermaid_html = render_mermaid(mermaid_source, slide.alt_text, slide_id, theme=deck.metadata.theme)
            elif ext == ".svg":
                svg_path = slide.src if Path(slide.src).is_absolute() else Path(base_dir) / slide.src
                raw_svg = Path(svg_path).read_text(encoding="utf-8")
                rendered_svg = wrap_svg_ada(raw_svg, slide.alt_text, slide_id)
            else:
                rendered_image = render_image(
                    slide.src,
                    slide.alt_text,
                    embed=embed_images,
                    base_dir=base_dir,
                )
        elif slide.layout == "diagram" and getattr(slide, "body", None):
            if slide.body.strip().startswith(MERMAID_STARTERS):
                # Split body into Mermaid source and optional caption body.
                # Mermaid header line is flush-left; subsequent lines are indented.
                # Caption (if any) follows after a blank line.
                parts = slide.body.split("\n\n", 1)
                mermaid_source = parts[0]
                caption_body = parts[1].strip() if len(parts) > 1 else ""
                rendered_mermaid_html = render_mermaid(
                    mermaid_source, slide.alt_text, slide_id,
                    theme=deck.metadata.theme,
                )
                # Always reset rendered_body — the pre-computed value contains the
                # raw Mermaid source rendered as text, which must not be shown.
                if caption_body:
                    class _BodyProxy:
                        body = caption_body
                        layout = "content"
                    rendered_body = render_body(_BodyProxy(), embed_images=embed_images, theme=deck.metadata.theme, macros=macros)
                else:
                    rendered_body = None
            else:
                rendered_svg = wrap_svg_ada(slide.body, slide.alt_text, slide_id)

        rendered_left_col = None
        rendered_right_col = None
        if slide.layout == "two-column":
            base_dir = yaml_dir or str(Path(output_path).parent)
            if slide.left:
                rendered_left_col = _render_col_html(slide.left, base_dir, embed_images, f"{slide_id}-left", deck.metadata.theme)
            if slide.right:
                rendered_right_col = _render_col_html(slide.right, base_dir, embed_images, f"{slide_id}-right", deck.metadata.theme)

        if slide.layout == 'figure-wide':
            fw_ctx = _parse_figure_wide_body(
                getattr(slide, 'body', None), deck.metadata.theme, macros=macros
            )
            base_dir = yaml_dir or str(Path(output_path).parent)
            ext = Path(slide.src).suffix.lower()
            if ext == ".mmd":
                mmd_path = slide.src if Path(slide.src).is_absolute() else Path(base_dir) / slide.src
                mermaid_source = Path(mmd_path).read_text(encoding="utf-8")
                rendered_mermaid_html = render_mermaid(
                    mermaid_source, slide.alt_text, slide_id, theme=deck.metadata.theme
                )
            elif ext == ".svg":
                svg_path = slide.src if Path(slide.src).is_absolute() else Path(base_dir) / slide.src
                raw_svg = Path(svg_path).read_text(encoding="utf-8")
                rendered_svg = wrap_svg_ada(raw_svg, slide.alt_text, slide_id)
            else:
                rendered_image = render_image(
                    slide.src, slide.alt_text, embed=embed_images, base_dir=base_dir
                )

        slide_math_scale = getattr(slide, "math_display_scale", None)
        eff_math_scale = (
            slide_math_scale
            if slide_math_scale is not None
            else deck.metadata.math_display_scale
        )
        slide_math_center = getattr(slide, "math_display_center", None)
        eff_math_center = (
            slide_math_center
            if slide_math_center is not None
            else deck.metadata.math_display_center
        )
        eff_math_scale = float(eff_math_scale)
        eff_math_center = bool(eff_math_center)
        slide_math_color = getattr(slide, "math_display_color", None)
        eff_math_color = (
            slide_math_color
            if slide_math_color is not None
            else deck.metadata.math_display_color
        )
        if eff_math_color is not None and not str(eff_math_color).strip():
            eff_math_color = None

        slide_title_scale = getattr(slide, "title_scale", None)
        eff_title_scale = float(
            slide_title_scale
            if slide_title_scale is not None
            else deck.metadata.title_scale
        )
        slide_content_scale = getattr(slide, "content_scale", None)
        eff_content_scale = float(
            slide_content_scale
            if slide_content_scale is not None
            else deck.metadata.content_scale
        )
        slide_blockquote_scale = getattr(slide, "blockquote_scale", None)
        eff_blockquote_scale = float(
            slide_blockquote_scale
            if slide_blockquote_scale is not None
            else deck.metadata.blockquote_scale
        )
        eff_figure_scale = None
        if slide.layout in ("figure", "figure-wide"):
            slide_fig_scale = getattr(slide, "figure_scale", None)
            eff_figure_scale = float(
                slide_fig_scale
                if slide_fig_scale is not None
                else deck.metadata.figure_scale
            )

        panel_scale = getattr(slide, "panel_scale", None)
        if panel_scale is None:
            panel_scale_x = panel_scale_y = None
        elif isinstance(panel_scale, (list, tuple)):
            panel_scale_x, panel_scale_y = float(panel_scale[0]), float(panel_scale[1])
        else:
            panel_scale_x = panel_scale_y = float(panel_scale)

        bsc = _merge_bullet_stagger_config(deck, slide)
        bfc = _merge_bullet_focus_config(deck, slide)
        slides_context.append(
            {
                "slide": slide,
                "slide_id": slide_id,
                "rendered_title": rendered_title,
                "title_has_math": title_has_math,
                "rendered_subtitle": rendered_subtitle,
                "rendered_author_line": rendered_author_line,
                "rendered_body": rendered_body,
                "rendered_table_headers": rendered_table_headers,
                "rendered_table_rows": rendered_table_rows,
                "rendered_table_caption": rendered_table_caption,
                "rendered_description": rendered_description,
                "rendered_code": rendered_code,
                "rendered_image": rendered_image,
                "rendered_svg": rendered_svg,
                "rendered_mermaid": rendered_mermaid_html,
                "mermaid_data_attrs": _mermaid_data_attrs(slide),
                "rendered_left_col": rendered_left_col,
                "rendered_right_col": rendered_right_col,
                "rendered_fw_summary": fw_ctx["rendered_fw_summary"],
                "rendered_fw_left_heading": fw_ctx["rendered_fw_left_heading"],
                "rendered_fw_left_body": fw_ctx["rendered_fw_left_body"],
                "rendered_fw_right_heading": fw_ctx["rendered_fw_right_heading"],
                "rendered_fw_right_body": fw_ctx["rendered_fw_right_body"],
                "math_display_scale": eff_math_scale,
                "math_display_center": eff_math_center,
                "math_display_color": eff_math_color,
                "title_scale": eff_title_scale,
                "content_scale": eff_content_scale,
                "blockquote_scale": eff_blockquote_scale,
                "figure_scale": eff_figure_scale,
                "panel_scale_x": panel_scale_x,
                "panel_scale_y": panel_scale_y,
                "bullet_stagger_json": _bullet_stagger_json(bsc),
                "bullet_focus_json": _bullet_focus_json(bfc),
            }
        )

    pygments_css = (
        get_pygments_css(deck.metadata.theme)
        if any(s.layout == "code" for s in render_slides)
        else ""
    )

    has_mermaid = any(s["rendered_mermaid"] for s in slides_context) or any(
        s["rendered_left_col"] and "mermaid" in s["rendered_left_col"] or
        s["rendered_right_col"] and "mermaid" in s["rendered_right_col"]
        for s in slides_context
    )
    mermaid_theme = 'dark' if deck.metadata.theme == 'dark' else 'default'

    has_bullet_animation = any(
        s.get('bullet_stagger_json') or s.get('bullet_focus_json')
        for s in slides_context
    )
    gsap_script_url = (
        deck.metadata.gsap_script_url or SKILL_GSAP_SCRIPT_URL_DEFAULT
    )

    # Bake only when actually requested AND mmdc is available. If requested but
    # mmdc is missing, fall back to the runtime path (and keep the loader) rather
    # than emit gated-out diagrams that would render blank.
    effective_bake = bool(bake_mermaid) and has_mermaid and shutil.which("mmdc") is not None
    if bake_mermaid and has_mermaid and not effective_bake:
        print(
            "WARNING: bake_mermaid requested but 'mmdc' (mermaid-cli) not found; "
            "rendering runtime Mermaid instead.",
            file=sys.stderr,
        )

    html = template.render(
        deck=deck,
        slides=slides_context,
        total=len(render_slides),
        pygments_css=pygments_css,
        has_mermaid=has_mermaid,
        mermaid_theme=mermaid_theme,
        figure_layout_debug=figure_layout_debug,
        has_bullet_animation=has_bullet_animation,
        gsap_script_url=gsap_script_url,
        bake_mermaid=effective_bake,
        embedded_font_css=_embedded_font_css(deck.metadata.font),
    )
    if effective_bake:
        html = bake_mermaid_in_html(
            html, theme=deck.metadata.theme, font=deck.metadata.font
        )
    return html
