<!DOCTYPE html>
<html lang="en" data-theme="{{ deck.metadata.theme }}">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  {# MathML namespace URI (declared once here; <math> nodes omit redundant xmlns) #}
  <meta name="mathml-namespace-uri" content="http://www.w3.org/1998/Math/MathML">
  <title>{{ deck.metadata.title | e }}</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family={{ deck.metadata.font | replace(' ', '+') }}:wght@400;600;700&display=swap" rel="stylesheet">
  <style>
    *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }

    :root[data-theme="dark"] {
      --bg: #0d1117;
      --bg2: #161b22;
      --text: #e6edf3;
      --muted: #8b949e;
      --accent: {% if deck.metadata.accent_color %}{{ deck.metadata.accent_color }}{% else %}#f0a500{% endif %};
      --border: #30363d;
      --slide-frame: #4a5568;      /* slide outer border — visible on dark bg */
      --font-family: '{{ deck.metadata.font }}', sans-serif;
      --two-col-title-gap: 0.5in;           /* gap between slide title and two-column content area */
      --two-col-fig-max-height: 100%;       /* image height cap in two-col (single figure). 100% = fill column; use e.g. 78vh to cap */
      --two-col-both-fig-max-height: 100%;  /* image height cap when both columns have figures */
    }

    :root[data-theme="light"] {
      --bg: #ffffff;
      --bg2: #f6f8fa;
      --text: #1f2328;
      --muted: #656d76;
      --slide-frame: #a0aab4;      /* slide outer border — visible on light bg */
      --accent: {% if deck.metadata.accent_color %}{{ deck.metadata.accent_color }}{% else %}#b06800{% endif %};
      --border: #d1d9e0;
      --font-family: '{{ deck.metadata.font }}', sans-serif;
    }

    html, body {
      height: 100%;
      overflow-x: hidden;
      overflow-y: hidden;
      background: var(--bg);
      color: var(--text);
      font-family: var(--font-family);
    }

    .skip-link {
      position: absolute;
      left: -9999px;
      top: 0;
      z-index: 1000;
      background: var(--accent);
      color: var(--bg);
      padding: 0.5rem 1rem;
    }
    .skip-link:focus { left: 0; }

    #slide-counter {
      position: fixed;
      bottom: 1rem;
      right: 1rem;
      font-size: 0.875rem;
      color: var(--muted);
      z-index: 100;
    }

    main {
      scroll-snap-type: y mandatory;
      overflow-y: auto;
      overflow-x: hidden;
      height: 100vh;
      width: 100vw;
    }

    section[role="group"] {
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      padding: 1in;
      scroll-snap-align: start;
      border: 2px solid var(--slide-frame);
    }
    /* Title and divider slides: centered (presentation default) */
    section[role="group"].slide-title,
    section[role="group"].slide-divider {
      justify-content: center;
    }
    .slide-content-area {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
    }

    /* Math (MathML) inside headings — "inline math" keeps MathML inline-flow;
       plain "inline" is ignored by Chromium's MathML layout engine. */
    h1 math, h2 math, h3 math {
      display: inline math;
      font-size: inherit;
    }
    /* Override text-wrap: balance for headings with math to prevent fragments from stacking */
    h1:has(math), h2:has(math), h3:has(math) {
      text-wrap: wrap;
    }
    /* Class-based fallback when :has() is unsupported or balance still wins (see engine title_has_math) */
    section.slide-heading-math h1,
    section.slide-heading-math h2,
    section.slide-heading-math h3 {
      text-wrap: wrap !important;
    }
    section.slide-heading-math h1 math,
    section.slide-heading-math h2 math,
    section.slide-heading-math h3 math {
      display: inline math !important;
      vertical-align: baseline;
    }

    /* Title slide (h1) — ADA projection scale */
    h1 {
      font-size: clamp(48px, 10vw, 96px);
      font-weight: 700;
      line-height: 1.0;
      text-wrap: balance;
      margin-bottom: 1rem;
      text-align: center;
      color: var(--text);
    }
    .slide-title .subtitle {
      font-size: clamp(22px, 2.8vw, 34px);
      text-align: center;
      color: var(--muted);
      margin-bottom: 0.5rem;
    }
    .slide-title .author {
      font-size: clamp(20px, 2.2vw, 28px);
      text-align: center;
      color: var(--muted);
    }

    h2 {
      font-size: clamp(32px, 5vw, 52px);
      font-weight: 700;
      line-height: 1.1;
      text-wrap: balance;
      margin-bottom: 1rem;
      color: var(--accent);
      text-align: center;
    }

    /* **$...$** / **text $x$** in YAML: accent like h2; plain text in span needs color too */
    .deck-math-emphasis {
      color: var(--accent);
      font-weight: 700;
    }
    .deck-math-emphasis math,
    .deck-math-emphasis math * {
      color: var(--accent);
    }
    h3 {
      font-size: clamp(22px, 2.8vw, 34px);
      font-weight: 600;
      margin-bottom: 0.5rem;
    }
    .divider-slide h2 { font-size: clamp(48px, 8vw, 80px); }

    .slide-body {
      font-size: clamp(20px, 2.2vw, 28px);
      line-height: 1.6;
      text-align: left;
    }
    .slide-body ul,
    .slide-body ol { padding-left: 2rem; }
    .slide-body ol { padding-left: 2.5rem; }
    .slide-body ol li { padding-left: 0.5rem; }
    .slide-body li { margin-bottom: 0.75em; }

    /* Display equations ($$...$$) rendered as <math display="block"> */
    .slide-body math[display="block"] {
      display: block;
      margin: 0.85em auto;
      text-align: center;
    }
    /* Prevent double margin when the paragraph wrapper contains only block math */
    .slide-body p:has(> math[display="block"]:only-child) {
      margin: 0;
    }

    /* Markdown tables in body */
    .slide-body table {
      width: 100%;
      border-collapse: separate;
      border-spacing: 0;
      margin: 1.5rem 0;
    }
    .slide-body th,
    .slide-body td {
      padding: 0.65em 1.4em;
      text-align: left;
      border-bottom: 1px solid var(--border);
    }
    .slide-body th {
      color: var(--accent);
      font-weight: 700;
      border-bottom: 2px solid var(--border);
    }
    .slide-body tr:last-child td { border-bottom: none; }
    .slide-body td:first-child { color: var(--accent); font-weight: 700; }
    .slide-body th:not(:last-child),
    .slide-body td:not(:last-child) { padding-right: 2.5em; }

    /* Markdown **bold** in body: same accent as h2 (not only **$x$** / **text $x$** spans) */
    .slide-body strong {
      color: var(--accent);
      font-weight: 700;
    }

    .hero-description {
      font-size: clamp(22px, 2.8vw, 34px);
      color: var(--muted);
      text-align: center;
    }
    .hero-body {
      font-size: clamp(20px, 2.4vw, 30px);
      color: var(--muted);
      text-align: center;
      max-width: 50em;
      margin: 1rem auto 0;
      line-height: 1.6;
    }

    figcaption {
      font-size: clamp(18px, 1.8vw, 24px);
      color: var(--muted);
      margin-top: 0.75rem;
    }

    .two-col {
      display: grid;
      gap: 2rem;
      align-items: stretch;
      min-height: 0;
      height: 100%;
    }
    .two-col-50-50 { grid-template-columns: 1fr 1fr; }
    .two-col-40-60 { grid-template-columns: 2fr 3fr; }
    .two-col-60-40 { grid-template-columns: 3fr 2fr; }
    .two-col > .col-left,
    .two-col > .col-right {
      min-height: 0;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: center;
    }
    section[role="group"].slide-two-column,
    section[role="group"].slide-comparison {
      height: 100vh;
      max-height: 100vh;
      overflow: hidden;
    }
    .slide-two-column .slide-content-area,
    .slide-comparison .slide-content-area {
      min-height: 0;
      margin-top: var(--two-col-title-gap);
    }
    .two-col img { min-height: 0; flex-shrink: 1; }
    /* Comparison slide: first bold line in each column is the column heading */
    section.slide-comparison .two-col-50-50 > .slide-body > p:first-of-type {
      margin-bottom: 1rem;
    }
    section.slide-comparison .two-col-50-50 > .slide-body > p:first-of-type strong {
      font-size: clamp(24px, 2.9vw, 36px);
      font-weight: 700;
      color: var(--accent);
      line-height: 1.25;
      display: block;
    }
    .two-col img { max-width: 100%; max-height: var(--two-col-fig-max-height); object-fit: contain; display: block; margin: 0 auto; }
    /* When both columns have figures: center images, add spacing around the grid */
    .two-col-both { justify-items: center; margin-top: 1.5rem; margin-bottom: 1.5rem; }
    .two-col-caption-above { margin-bottom: 1.5rem; }
    .two-col-both img { max-height: var(--two-col-both-fig-max-height); }

    blockquote {
      font-size: clamp(28px, 3.5vw, 44px);
      font-style: italic;
      border-left: 4px solid var(--accent);
      padding-left: 1.5rem;
    }
    .attribution { color: var(--muted); margin-top: 1rem; }

    pre {
      background: var(--bg2);
      border: 1px solid var(--border);
      border-radius: 0.5rem;
      padding: 1.5rem;
      overflow-x: auto;
      overflow-y: auto;
      max-height: 70vh;
      font-size: clamp(15px, 1.6vw, 20px);
      line-height: 1.6;
    }
    pre:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
    code { font-family: 'IBM Plex Mono', monospace; font-size: clamp(15px, 1.6vw, 20px); }

    .slide-code { overflow: auto; max-height: 75vh; border-radius: 0.5rem; }
    .slide-codetable { width: 100%; border-collapse: collapse; }
    .slide-codetable td.linenos { vertical-align: top; padding-right: 0.5em; border-right: 1px solid var(--border); user-select: none; width: 1%; white-space: nowrap; }
    .slide-codetable td.code { vertical-align: top; padding-left: 1em; width: 99%; }
    .slide-codetable td.code pre { border: none; padding: 0; margin: 0; max-height: none; }

    .diagram-container { text-align: center; max-height: 75vh; overflow: auto; }
    .diagram-container svg { max-width: 100%; max-height: 52vh; }
    /* Standalone diagram: JS post-processes SVG sizing after Mermaid renders */
    .slide-diagram .diagram-container svg { display: block; margin: 0 auto; }
    pre.mermaid { background: transparent; border: none; padding: 0; max-height: none; text-align: center; }
    /* Gutter between diagram and caption text below */
    .diagram-caption { margin-top: 1.5rem; }

    /* Standalone diagram slide: container fills content area and centers diagram vertically */
    .slide-diagram .slide-content-area > .diagram-container {
      flex: 1;
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: stretch;
    }
    /* Inner wrapper and pre must center their SVG content horizontally */
    .slide-diagram .diagram-container > [role="img"],
    .slide-diagram .diagram-container > pre.mermaid {
      text-align: center;
    }
    /* Two-column diagram column: center within the column cell */
    .slide-two-column .diagram-container {
      display: flex;
      flex-direction: column;
      justify-content: center;
      align-items: stretch;
      height: 100%;
    }
    .slide-two-column .diagram-container > [role="img"],
    .slide-two-column .diagram-container > pre.mermaid {
      text-align: center;
    }

    .figure-container { text-align: center; flex: 1; display: flex; flex-direction: column; justify-content: center; }
    .figure-container img { max-width: 80%; max-height: 70vh; margin: 0 auto; display: block; }
    /* Single figure slide (no body text): figure dominates */
    .figure-only .figure-container img { max-width: 90%; max-height: 75vh; }
    /* Single diagram slide: diagram dominates */
    .diagram-only .diagram-container { max-height: 80vh; }
    .diagram-only .diagram-container svg { max-height: 75vh; }

    .divider-slide { align-items: center; text-align: center; }

    /* layout: transcribe — dense left-aligned body (transcribe_to_html skill) */
    section.slide-transcribe {
      justify-content: flex-start;
      align-items: stretch;
    }
    section.slide-transcribe .slide-content-area {
      justify-content: flex-start;
    }
    section.slide-transcribe h2 {
      font-size: 16pt;
      font-weight: 600;
      line-height: 1.35;
      text-wrap: balance;
      margin-bottom: 0.5rem;
      color: var(--text);
      text-align: left;
    }
    /* Override balance for transcribe headings with math */
    section.slide-transcribe h2:has(math) {
      text-wrap: wrap;
    }
    section.slide-transcribe .slide-body {
      font-size: 14pt;
      line-height: 1.45;
      text-align: left;
    }
    section.slide-transcribe .slide-body p {
      margin: 0 0 0.85em 0;
    }
    section.slide-transcribe .slide-body p:last-child {
      margin-bottom: 0;
    }
    section.slide-transcribe .slide-body li {
      margin-bottom: 0.35em;
    }
    section.slide-transcribe .slide-body strong {
      color: var(--text);
      font-weight: 700;
    }

    /* flavor: transcript — same dense left alignment using layout: content (+ table) */
    main.deck-flavor-transcript section.slide-content,
    main.deck-flavor-transcript section.slide-table {
      justify-content: flex-start;
      align-items: stretch;
    }
    main.deck-flavor-transcript section.slide-content .slide-content-area,
    main.deck-flavor-transcript section.slide-table .slide-content-area {
      justify-content: flex-start;
    }
    main.deck-flavor-transcript section.slide-content h2,
    main.deck-flavor-transcript section.slide-table h2 {
      font-size: 16pt;
      font-weight: 600;
      line-height: 1.35;
      text-wrap: balance;
      margin-bottom: 0.5rem;
      color: var(--text);
      text-align: left;
    }
    /* Override balance for transcript flavor headings with math */
    main.deck-flavor-transcript section.slide-content h2:has(math),
    main.deck-flavor-transcript section.slide-table h2:has(math) {
      text-wrap: wrap;
    }
    main.deck-flavor-transcript section.slide-content .slide-body {
      font-size: 14pt;
      line-height: 1.45;
      text-align: left;
    }
    main.deck-flavor-transcript section.slide-content .slide-body p {
      margin: 0 0 0.85em 0;
    }
    main.deck-flavor-transcript section.slide-content .slide-body p:last-child {
      margin-bottom: 0;
    }
    main.deck-flavor-transcript section.slide-content .slide-body li {
      margin-bottom: 0.35em;
    }
    main.deck-flavor-transcript section.slide-content .slide-body strong,
    main.deck-flavor-transcript section.slide-table .slide-body strong {
      color: var(--text);
      font-weight: 700;
    }
    main.deck-flavor-transcript section.slide-table .table-scroll-wrapper {
      font-size: 14pt;
      line-height: 1.45;
    }
    main.deck-flavor-transcript section.slide-table .table-caption {
      text-align: left;
      font-size: 14pt;
      caption-side: top;
    }

    .steps-list {
      counter-reset: step;
      list-style: none;
      padding: 0;
    }
    .steps-list li {
      counter-increment: step;
      margin-bottom: 1rem;
      padding-left: 2.5rem;
      position: relative;
    }
    .steps-list li::before {
      content: counter(step);
      position: absolute;
      left: 0;
      color: var(--accent);
      font-weight: 700;
    }

    .summary-list { list-style: none; padding: 0; }
    .summary-list li::before { content: '\2713 '; color: var(--accent); font-weight: 700; }

    .table-scroll-wrapper { overflow-x: auto; max-width: 100%; }
    .table-scroll-wrapper:focus { outline: 2px solid var(--accent); outline-offset: 2px; }
    .table-scroll-wrapper table { width: 100%; border-collapse: collapse; }
    .table-scroll-wrapper th, .table-scroll-wrapper td { padding: 0.5em 1em; border: 1px solid var(--accent, #d4a017); text-align: left; font-size: clamp(18px, 1.9vw, 26px); }
    .table-scroll-wrapper tr.span-row td {
      color: var(--muted);
      font-style: italic;
      font-size: clamp(15px, 1.5vw, 20px);
      border-top: 2px solid var(--accent);
      border-left: none;
      border-right: none;
      padding-top: 0.6em;
    }
    .table-scroll-wrapper caption {
      font-size: clamp(18px, 1.8vw, 24px);
      font-weight: bold;
      caption-side: bottom;
      margin-top: 0.75em;
      text-align: left;
      color: var(--muted);
    }
    .code-language-label { position: absolute; top: 0.25em; right: 0.5em; font-size: 0.75em; opacity: 0.6; }

    .slide-notes { display: none; }

    @media print {
      @page { size: landscape; margin: 0; }
      html, body {
        overflow: visible !important;
        height: auto !important;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      main { overflow: visible !important; height: auto !important; scroll-snap-type: none !important; }
      section[role="group"] {
        break-after: page;
        height: 100vh;
        overflow: hidden;
        -webkit-print-color-adjust: exact !important;
        print-color-adjust: exact !important;
      }
      #slide-counter { display: none !important; }
    }

    .visually-hidden {
      position: absolute;
      width: 1px;
      height: 1px;
      padding: 0;
      margin: -1px;
      overflow: hidden;
      clip: rect(0, 0, 0, 0);
      white-space: nowrap;
      border: 0;
    }
    {{ pygments_css | safe }}
  </style>
</head>
<body>
  <a href="#main-content" class="skip-link">Skip to content</a>
  <main id="main-content" role="region" aria-roledescription="carousel" aria-label="{{ deck.metadata.title | e }}"{% if deck.metadata.flavor == 'transcript' %} class="deck-flavor-transcript"{% endif %}>
    <div id="slide-counter" aria-live="polite" aria-atomic="true">1 / {{ total }}</div>
    {% for s in slides %}
    {% set slide = s.slide %}
    {% set slide_id = s.slide_id %}
    {% set rendered_title = s.rendered_title %}
    {% set rendered_subtitle = s.rendered_subtitle %}
    {% set rendered_author_line = s.rendered_author_line %}
    {% set rendered_body = s.rendered_body %}
    {% set rendered_table_headers = s.rendered_table_headers %}
    {% set rendered_table_rows = s.rendered_table_rows %}
    {% set rendered_table_caption = s.rendered_table_caption %}
    {% set rendered_description = s.rendered_description %}
    {% set rendered_code = s.rendered_code %}
    {% set rendered_image = s.rendered_image %}
    {% set rendered_svg = s.rendered_svg %}
    {% set rendered_mermaid = s.rendered_mermaid %}
    {% set rendered_left_col = s.rendered_left_col %}
    {% set rendered_right_col = s.rendered_right_col %}
    {% set title_has_math = s.title_has_math %}
    {% set extra_class = '' %}
    {% if slide.layout == 'figure' and not slide.body %}{% set extra_class = ' figure-only' %}{% endif %}
    {% if slide.layout == 'diagram' and not slide.body %}{% set extra_class = ' diagram-only' %}{% endif %}
    {% if title_has_math %}{% set extra_class = extra_class ~ ' slide-heading-math' %}{% endif %}
    <section id="{{ slide_id }}" role="group" class="slide-{{ slide.layout }}{{ extra_class }}" aria-roledescription="slide" aria-label="Slide {{ loop.index }} of {{ total }}" aria-labelledby="{{ slide_id }}-heading">
      {% include slide.layout ~ '.html.j2' %}
    </section>
    {% endfor %}
  </main>
  <script>
  (function() {
    var slides = Array.from(document.querySelectorAll('[role="group"]'));
    var idx = 0;
    var counter = document.getElementById('slide-counter');

    // Keep idx in sync with the visible slide (handles find-in-page, direct scroll, etc.)
    var observer = new IntersectionObserver(function(entries) {
      entries.forEach(function(entry) {
        if (entry.isIntersecting) {
          idx = slides.indexOf(entry.target);
          counter.textContent = (idx + 1) + ' / ' + slides.length;
        }
      });
    }, { threshold: 0.5 });
    slides.forEach(function(s) { observer.observe(s); });

    function goTo(n) {
      idx = Math.max(0, Math.min(n, slides.length - 1));
      slides[idx].scrollIntoView({behavior: 'instant', block: 'start'});
      counter.textContent = (idx + 1) + ' / ' + slides.length;
    }
    document.addEventListener('keydown', function(e) {
      if (e.target.closest('[role="region"]')) return; // let table scroll handle its own keys
      if (e.key === 'ArrowRight' || e.key === 'ArrowDown' || e.key === ' ') {
        e.preventDefault(); goTo(idx + 1);
      } else if (e.key === 'ArrowLeft' || e.key === 'ArrowUp') {
        e.preventDefault(); goTo(idx - 1);
      } else if (e.key === 'Home') {
        e.preventDefault(); goTo(0);
      } else if (e.key === 'End') {
        e.preventDefault(); goTo(slides.length - 1);
      }
    });
  })();
  </script>
  {% if has_mermaid %}
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@11/dist/mermaid.esm.min.mjs';
    mermaid.initialize({
      startOnLoad: false,
      theme: '{{ mermaid_theme }}',
      flowchart: { useMaxWidth: false, htmlLabels: true },
      sequence: { useMaxWidth: false },
    });
    await mermaid.run();
    // Mermaid sets explicit width/height/style attributes on SVGs which override CSS.
    // Remove them and scale SVG to fill the available container space.
    document.querySelectorAll('.slide-diagram .diagram-container svg').forEach(svg => {
      svg.removeAttribute('width');
      svg.removeAttribute('height');
      svg.removeAttribute('style');
      svg.style.display = 'block';
      svg.style.margin = '0 auto';
      // Override CSS max-width/max-height rules that would otherwise cap the SVG.
      svg.style.maxWidth = 'none';
      svg.style.maxHeight = 'none';

      const slide = svg.closest('section[role="group"]');
      const hasCaption = slide && slide.querySelector('.diagram-caption');

      // Compute available space from slide dimensions (container.clientHeight is 0 at
      // this point because flex sizing depends on SVG content — measure directly instead).
      const pad = 96; // 1in at 96dpi
      const h2 = slide && slide.querySelector('h2');
      const titleH = h2 ? h2.getBoundingClientRect().height : 60;
      const captionH = hasCaption ? 60 : 0;
      // clientWidth excludes scrollbar; subtract a small buffer to prevent overflow.
      const availW = document.documentElement.clientWidth - pad * 2 - 4;
      const availH = window.innerHeight - pad * 2 - titleH - captionH - 8;

      const vb = svg.viewBox && svg.viewBox.baseVal;
      if (vb && vb.width > 0 && vb.height > 0) {
        const ar = vb.width / vb.height;
        let w = availW;
        let h = w / ar;
        if (h > availH) { h = availH; w = h * ar; }
        svg.style.width = w + 'px';
        svg.style.height = h + 'px';
      } else {
        svg.style.maxWidth = '75vw';
        svg.style.maxHeight = hasCaption ? '52vh' : '72vh';
        svg.style.width = '100%';
      }
    });
    document.querySelectorAll('.slide-two-column .diagram-container svg').forEach(svg => {
      svg.removeAttribute('width');
      svg.removeAttribute('height');
      svg.removeAttribute('style');
      svg.style.maxWidth = '95%';
      svg.style.maxHeight = '60vh';
      svg.style.width = '100%';
      svg.style.display = 'block';
      svg.style.margin = '0 auto';
    });
  </script>
  {% endif %}
</body>
</html>
