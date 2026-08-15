# SVG Diagrams with Rendered Math

Use hand-authored SVG (`.svg` files) instead of Mermaid when a diagram requires **rendered mathematical notation**. The compiler inlines SVG files with ADA wrapping and a bleach sanitizer that preserves `foreignObject`, MathML, and flexbox styles.

## How it works

- The compiler reads the `.svg` file and passes it through `compiler/renderers/svg.py:wrap_svg_ada()`.
- The bleach sanitizer allowlist includes `foreignObject`, `div`, `span`, MathML tags (`math`, `mrow`, `mi`, `mo`, `mn`, `msup`, …), and a `CSSSanitizer` that preserves flexbox layout properties.
- The browser renders inline MathML natively — no JavaScript library is needed.

## Anatomy of a math-bearing SVG box

Each labelled box is a `<rect>` paired with a `<foreignObject>` of the same position and size. The foreignObject contains a flex `<div>` with inline `<math>` elements.

```svg
<rect x="20" y="20" width="270" height="80" rx="6" fill="#1a4a8a"/>
<foreignObject x="20" y="20" width="270" height="80">
  <div xmlns="http://www.w3.org/1999/xhtml"
       style="box-sizing:border-box;width:270px;height:80px;
              display:flex;align-items:center;justify-content:center;
              color:#ffffff;font-size:22px;text-align:center;font-family:sans-serif;">
    Label:&nbsp;<math display="inline"><mrow>...</mrow></math>
  </div>
</foreignObject>
```

**Critical:** set both `width` and `height` as explicit **pixel values** on the `<div>` (not `100%`). Percentage heights inside `foreignObject` are unreliable across browsers and will cause top-alignment. Match the pixel values to the `foreignObject` dimensions exactly.

## Font sizes

Use font sizes **~30% larger** than typical HTML body text to compensate for the SVG viewport scaling applied by the slide layout:

| Context | Recommended `font-size` |
|---------|------------------------|
| Single-line box label | **22 px** |
| Two-line box label | **21 px** |
| Header / colored box | **21–22 px** |

These values produce text that reads at roughly the same visual size as the surrounding slide body (≈ 28 px in CSS) once the SVG is scaled to fit the column.

## Generating MathML

Use `latex2mathml` (already a compiler dependency) to convert LaTeX to MathML, then strip the redundant `xmlns` attribute:

```python
import latex2mathml.converter, re

def to_mathml(latex):
    ml = latex2mathml.converter.convert(latex)
    return re.sub(r'\s+xmlns="http://www\.w3\.org/1998/Math/MathML"', '', ml)

print(to_mathml(r'O(S^2 d)'))
# → <math display="inline"><mrow><mi>O</mi>...</mrow></math>
```

Paste the output directly into the `foreignObject` div.

## Two-line boxes

For boxes with two lines (label + cost), use `flex-direction:column` and `line-height:1.6`:

```svg
<foreignObject x="410" y="136" width="270" height="108">
  <div xmlns="http://www.w3.org/1999/xhtml"
       style="box-sizing:border-box;width:270px;height:108px;
              display:flex;flex-direction:column;
              align-items:center;justify-content:center;
              color:#e5e7eb;font-size:21px;text-align:center;
              font-family:sans-serif;line-height:1.6;">
    <span>Block-encode <math display="inline">...</math></span>
    <span><math display="inline">...</math></span>
  </div>
</foreignObject>
```

## Arrowheads

Define a marker in `<defs>` and reference it on `<line>` elements:

```svg
<defs>
  <marker id="arrowhead" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#aaaaaa"/>
  </marker>
</defs>
<line x1="155" y1="100" x2="155" y2="134"
      stroke="#aaaaaa" stroke-width="2" marker-end="url(#arrowhead)"/>
```

## ADA requirements

- Set `alt_text` on the `figure` or `two-column` column that references the SVG — the compiler injects it as `<title>` and `<desc>` inside the `<svg>` element and as `aria-label` on the wrapper `<div>`.
- Do **not** put decorative information in `alt_text`; describe the data and structure conveyed by the diagram.

## Sanitizer allowlist (reference)

`compiler/renderers/svg.py` allows:

- **SVG shape tags:** `svg`, `g`, `path`, `circle`, `rect`, `line`, `text`, `tspan`, `polygon`, `polyline`, `ellipse`, `marker`, `clipPath`, `linearGradient`, `radialGradient`, `stop`, `defs`, `use`, `symbol`, `title`, `desc`
- **foreignObject + HTML:** `foreignObject`, `div`, `span`, `p`
- **MathML:** `math`, `mrow`, `mi`, `mo`, `mn`, `msup`, `msub`, `msubsup`, `mfrac`, `mspace`, `mtext`, `mover`, `munder`, `munderover`, `mtable`, `mtr`, `mtd`, `ms`, `mstyle`, `merror`, `mpadded`, `mphantom`
- **Global attrs (`*`):** `id`, `class`, `style`, `transform`, `xmlns`, `marker-end`, `marker-start`
- **CSS properties (via `CSSSanitizer`):** `width`, `height`, `display`, `flex-direction`, `align-items`, `justify-content`, `box-sizing`, `color`, `background`, `background-color`, `font-size`, `font-weight`, `font-family`, `text-align`, `line-height`, `letter-spacing`, `margin*`, `padding*`, `border`, `border-radius`, `opacity`, `overflow`, `vertical-align`, `white-space`, `word-break`

To add a missing tag or property, edit `ALLOWED_SVG_TAGS`, `ALLOWED_SVG_ATTRS`, or `_CSS_SANITIZER` in `compiler/renderers/svg.py`.
