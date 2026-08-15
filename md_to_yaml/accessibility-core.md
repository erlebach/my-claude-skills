# Accessibility Core — WCAG 2.1/2.2 AA

All rules in this file are mandatory for every flavor. They override aesthetic preferences.

---

## Required Page Skeleton

Every slide deck must include all of the following in this exact order:

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Descriptive Page Title</title>
  <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
</head>
<body>
  <a class="skip-link" href="#main">Skip to main content</a>

  <nav id="sidebar" aria-label="Section navigation">
    <a href="#s0" class="nav-link"><span class="icon" aria-hidden="true">🏠</span> Overview</a>
    <a href="#s1" class="nav-link"><span class="icon" aria-hidden="true">📋</span> Section One</a>
    <!-- one link per slide section -->
  </nav>

  <nav id="dots" aria-label="Slide navigation">
    <button type="button" class="dot active" onclick="location.href='#s0'"
            aria-label="1 Overview">1</button>
    <button type="button" class="dot" onclick="location.href='#s1'"
            aria-label="2 Section One">2</button>
    <!-- one button per slide section -->
  </nav>

  <main id="main" tabindex="-1">

    <section class="slide slide-hero" id="s0">
      <div class="slide-number" aria-hidden="true">01 / N</div>
      <h1 class="slide-title">Slide Title Here</h1>
      ...
    </section>

    <section class="slide" id="s1">
      <div class="slide-number" aria-hidden="true">02 / N</div>
      <h2 class="slide-title">Section Title</h2>
      ...
    </section>

  </main>

  <script>
    mermaid.initialize({ startOnLoad: true, theme: 'FLAVOR_THEME', themeVariables: { /* see flavor file */ } });
    /* WCAG 1.1.1: Mermaid injects <svg role="img"> with no accessible name at render time.
       The wrapping <figure aria-labelledby aria-describedby> already provides full semantic
       context, so demote every Mermaid SVG to role="presentation" after render.
       IMPORTANT: Mermaid renders asynchronously — DOMContentLoaded fires before SVGs exist.
       Use a MutationObserver on each .mermaid-wrap so the patch fires the moment each SVG
       is injected, regardless of render timing. */
    function patchMermaidSvg(svg) {
      svg.setAttribute('role', 'presentation');
      svg.removeAttribute('aria-label');
    }
    const mermaidObserver = new MutationObserver(function (mutations) {
      mutations.forEach(function (mutation) {
        mutation.addedNodes.forEach(function (node) {
          if (node.nodeName === 'svg') { patchMermaidSvg(node); }
          if (node.querySelectorAll) {
            node.querySelectorAll('svg').forEach(patchMermaidSvg);
          }
        });
      });
    });
    document.addEventListener('DOMContentLoaded', function () {
      document.querySelectorAll('.mermaid-wrap').forEach(function (wrap) {
        mermaidObserver.observe(wrap, { childList: true, subtree: true });
      });
    });
  </script>
</body>
```

Skeleton rules — not optional:
- **First element after `<body>`** must be the skip link: `<a class="skip-link" href="#main">`
- **`<main>`** must have both `id="main"` and `tabindex="-1"`
- **Slide IDs** are sequential: `s0`, `s1`, `s2` … (zero-indexed)
- **First slide** uses `<h1 class="slide-title">`, all others use `<h2 class="slide-title">`
- **Sub-headings** within a slide use `<h3>` — never skip heading levels
- **Both nav elements must be in static HTML** — do not build nav with JavaScript

---

## Label in Name (WCAG 2.5.3)

If an interactive element has visible text, the accessible name **must contain** that visible text (case-insensitive). This is the most common failure caught by automated checkers.

**The dot navigation buttons are the primary risk.** Empty buttons with only `aria-label` pass structurally, but accessibility checkers may infer a visible label from the button's ordinal position or `title` attribute, causing a mismatch.

**Required pattern for dot buttons — always use a visible number:**

```html
<!-- CORRECT: visible text "1" is contained in aria-label "1 Overview" -->
<button type="button" class="dot active" onclick="location.href='#s0'"
        aria-label="1 Overview">1</button>

<!-- WRONG: empty button — checker infers visible label from position, aria-label doesn't match -->
<button type="button" class="dot active" onclick="location.href='#s0'"
        aria-label="Go to Overview slide" title="Overview"></button>
```

Rules:
- **Never use `title` on dot buttons** — `title` is treated as a visible label by some checkers and creates a mismatch with `aria-label`
- The `aria-label` must **start with the visible number** (e.g. `"1 Overview"`, not `"Go to slide 1"`)
- Sidebar `<a>` links must have no `aria-label` — their accessible name comes from their visible link text directly

---

## Never Use ALL-CAPS Text

Never use ALL-CAPS in headings, labels, buttons, slide titles, or body content. ALL-CAPS reduces readability and causes screen readers to spell out individual letters. Only established abbreviations (HTML, CSS, ADA, API, GPU, etc.) are permitted in uppercase. Use `font-weight: bold` or `font-style: italic` for emphasis.

---

## Reading Order

DOM order must equal reading order. Never use CSS to reorder content visually:
- No `order` property in flex/grid
- No `grid-area` reordering
- No `position: absolute` for primary content flow
- No `direction: rtl` tricks

---

## Focus Visibility

```css
:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}
:focus:not(:focus-visible) {
  outline: none;
}
```

Do not suppress focus outlines for aesthetics. Change the color if needed, but keep it visible and high-contrast.

---

## Interactive Elements

All buttons, links, and controls must:
- Have `min-width: 24px` and `min-height: 24px`
- Be keyboard accessible — use native `<button>` and `<a>`
- Have an accessible label (visible text, `aria-label`, or `aria-labelledby`)
- Have visible focus

**Never use `<div onclick="...">` for interactive elements.**

---

## Headings

- No empty headings
- Headings must not skip levels: `h1` → `h2` → `h3` (never `h1` → `h3`)
- Every heading must be followed immediately by meaningful semantic content — a paragraph, list, figure, or table. Never place a bare `<div>` directly after a heading.

```html
<!-- BAD -->
<h2>Key Concepts</h2>
<div class="card-grid">...</div>

<!-- GOOD -->
<h2>Key Concepts</h2>
<p>The following concepts are central to this topic.</p>
<div class="card-grid">...</div>
```

---

## ARIA Naming Rules

`aria-label` is only valid on interactive elements, landmarks, form controls, images, and iframes. Do **not** use it on `<div>` or `<span>`.

**ARIA Decision Rule:**
1. Interactive, landmark, form control, image, or iframe? → `aria-label` may be used.
2. Layout container (`div`, `span`)? → Do **not** use `aria-label`.
3. Label seems necessary? → Use `<section>`, `<figure>+<figcaption>`, or visible text instead.

```html
<!-- BAD -->
<div class="pipeline" aria-label="Workflow">...</div>

<!-- GOOD -->
<figure class="pipeline-figure">
  <figcaption>Four-stage workflow: data, training, fine-tuning, serving.</figcaption>
  <div class="pipeline" aria-hidden="true"><!-- decorative --></div>
</figure>
```

---

## Images and Figures

```html
<figure>
  <img src="roc.png" alt="ROC curve showing true positive rate vs false positive rate">
  <figcaption>ROC curve illustrating classifier performance.</figcaption>
</figure>
```

- `alt` = meaning + purpose, not the filename
- Decorative images: `alt=""`
- Avoid redundancy between `alt` and `<figcaption>`
- **Figures are optional** — include a figure only when it adds genuine value. Omit it when the concept is better expressed through a Mermaid diagram, bullet list, or table.

---

## Mathematical Formulas

```html
<figure class="formula-block">
  <div>corr(X,Y) = cos_sim(X−X̄, Y−Ȳ)</div>
  <figcaption>Correlation formula: correlation equals cosine similarity between mean-centered X and Y.</figcaption>
</figure>
```

Never use `aria-label` on the formula `<div>`. The `<figcaption>` must be visible and read the formula in plain English.

---

## Color and Contrast

**The 4.5:1 rule applies to all text without exception.**

- All text (body, labels, captions, code): ≥ 4.5:1 contrast ratio against its background
- Large text (≥ 18pt regular or ≥ 14pt bold): ≥ 3:1 minimum
- Muted/dimmed text must still meet 4.5:1
- Never rely on color alone to convey meaning

**Mermaid diagrams — additional rule:**
Whenever a `style` directive sets `fill:`, it **must** also set `color:` explicitly.
See [`mermaid-best-practices.md`](mermaid-best-practices.md) for approved color pairs,
theme guidance, and the full authoring checklist.

**Pre-approved dark-theme pairs:**
| Text | Background | Ratio |
|------|-----------|-------|
| `#e6edf3` | `#0d1117` | 15.8:1 ✓ |
| `#8b949e` | `#0d1117` | 5.9:1 ✓ |
| `#58a6ff` | `#0d1117` | 6.4:1 ✓ |
| `#3fb950` | `#0d1117` | 5.0:1 ✓ |
| `#f0883e` | `#0d1117` | 4.6:1 ✓ |

**Pre-approved light-theme pairs:**
| Text | Background | Ratio |
|------|-----------|-------|
| `#1e1a12` | `#faf7f2` | 17.1:1 ✓ |
| `#3d3d3d` | `#ffffff` | 10.7:1 ✓ |
| `#5a6a7e` | `#faf7f2` | 5.0:1 ✓ |
| `#b5451b` | `#faf7f2` | 5.2:1 ✓ |
| `#1a56a0` | `#ffffff` | 7.2:1 ✓ |

---

## Zoom and Reflow

- Content must remain readable and usable at 200% zoom
- Do not use fixed heights on text containers
- Do not hide overflow in ways that clip text
- Prefer wrapping layouts over absolute positioning

---

## Reduced Motion

```css
@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

---

## Required CSS Baseline (all flavors)

```css
body {
  font-family: Arial, Helvetica, sans-serif; /* override in flavor with web font + fallback */
  font-size: 21px;
  line-height: 1.5;
}
h1 { font-size: 42px; }
h2 { font-size: 32px; }
p  { margin-bottom: 1.5em; }

button, input {
  min-width: 24px;
  min-height: 24px;
  font-size: 21px;
}

:focus-visible {
  outline: 2px solid #005fcc;
  outline-offset: 2px;
}
:focus:not(:focus-visible) { outline: none; }

@media (prefers-reduced-motion: reduce) {
  *, *::before, *::after {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

Web fonts are allowed if the fallback stack ends with `Arial, Helvetica, sans-serif`. Preferred: IBM Plex Sans, Source Sans 3, DM Sans.

---

## Forbidden Patterns

| Pattern | Replace with |
|---------|-------------|
| `<div onclick="...">` | `<button>` or `<a href>` |
| `<pre class="mermaid">` | `<div class="mermaid">` — Mermaid syntax is never displayed to users (replaced by SVG at runtime), so `<pre>` is semantically wrong and prevents user spacing adjustments (WCAG 1.4.12) |
| `<div aria-label="...">` | `<section>`, `<figure>+<figcaption>`, or visible text |
| `<span aria-label="...">` | visible text or semantic element |
| `aria-hidden="true"` on meaningful text | Remove — only hide decorative elements |
| Consecutive headings with no content between | Insert `<p>`, list, figure, or table |
| Heading immediately followed by `<div>` | Insert `<p>` before the `<div>` |
| Empty dot button with `aria-label="Go to X slide"` and `title="X"` | Visible number text inside button; `aria-label="N Name"` containing that number; no `title` |
| `text-align: justify` | Left-aligned text |
| Fixed heights on text containers | `min-height` or unconstrained height |
| ALL-CAPS text (non-abbreviation) | Mixed case with bold or italic for emphasis |
| Nav built dynamically by JavaScript | Static nav in HTML |
| Skipped heading levels (`h1` → `h3`) | Sequential levels only |

---

## Final Verification Checklist

Before delivering, verify every item:

- [ ] `<nav id="sidebar">` in static HTML — one `<a>` per slide, not built by JS
- [ ] `<nav id="dots">` in static HTML — one `<button type="button">` per slide, not built by JS
- [ ] Skip link is **first element after `<body>`**
- [ ] `<main id="main" tabindex="-1">` present (both attributes required)
- [ ] Single `<main>` landmark on the page
- [ ] `h1` on slide 0, `h2` on slides 1+, `h3` for sub-headings; no skipped levels
- [ ] No two consecutive headings without content between them
- [ ] No heading immediately followed by a bare `<div>`
- [ ] Each slide section has a visible heading as its primary accessible name
- [ ] All images have meaningful `alt` text (or `alt=""` if decorative)
- [ ] All interactive elements have `aria-label` and keyboard access
- [ ] All buttons have `type="button"`
- [ ] All interactive elements have `min-width: 24px; min-height: 24px`
- [ ] Dot buttons contain a visible number (e.g. `1`) as their text content, and `aria-label` starts with that number (e.g. `aria-label="1 Overview"`) — **no `title` attribute** on dots (it conflicts with Label in Name)
- [ ] Focus outline visible on all interactive elements
- [ ] Sidebar icon spans have `aria-hidden="true"`
- [ ] `<div class="slide-number" aria-hidden="true">` on each slide
- [ ] Contrast ≥ 4.5:1 for all text including muted/dim labels
- [ ] No `<div onclick>` or `<span onclick>`
- [ ] Navigation links are descriptive (no "click here")
- [ ] `prefers-reduced-motion` CSS block present
- [ ] DOM order matches reading order
- [ ] Slide IDs use `s0`, `s1`, `s2` … matching sidebar hrefs and dot onclick targets
- [ ] Content readable at 200% zoom — no fixed heights on text containers
- [ ] No `aria-label` on `<div>` or `<span>`
- [ ] No ALL-CAPS text (scan every heading, button, label, title, paragraph)
- [ ] Mermaid diagram `<script>` initialized at bottom of `<body>`
- [ ] Post-render patch present: a `MutationObserver` on each `.mermaid-wrap` sets `role="presentation"` and removes `aria-label` on every Mermaid SVG as it is injected (WCAG 1.1.1 — Mermaid renders asynchronously after `DOMContentLoaded`, so `querySelectorAll` at load time finds nothing; `MutationObserver` fires at the moment each SVG appears)
- [ ] Every Mermaid `<figure>` has both `aria-labelledby="fig-SLUG"` and `aria-describedby="fig-SLUG-desc"`
- [ ] Every Mermaid figure has a visible `<figcaption id="fig-SLUG">` (brief label for sighted users)
- [ ] Every Mermaid figure has a `<div id="fig-SLUG-desc" class="sr-only">` with full prose describing every node, connection, and conclusion
- [ ] `.sr-only` CSS class is present in the stylesheet
- [ ] All `fig-*` IDs are unique across the page
- [ ] No bare `<div class="mermaid-wrap">` exists outside a `<figure>`
- [ ] SVG diagrams: no Unicode sub/superscript characters or HTML entities used for math in `<text>` elements
- [ ] SVG diagrams: all mathematical notation uses `<foreignObject>` + MathML (`<math xmlns="http://www.w3.org/1998/Math/MathML">`)
- [ ] SVG diagrams: every `<foreignObject>` has explicit `width` and `height` large enough to avoid clipping
- [ ] Every Mermaid `style` directive with `fill:` also has explicit `color:` — see [`mermaid-best-practices.md`](mermaid-best-practices.md)
