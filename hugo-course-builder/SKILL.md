---
name: hugo-course-builder
description: Build and maintain Hugo course websites using Zen theme. Use this skill whenever the user mentions Hugo, asks about content structure, front matter, taxonomies, page/section bundles, configuration, CSS management, or wants to reduce Hugo build errors. Covers initialization with Zen theme v0.161.0, course content architecture (modules, homework, resources), YAML front matter with custom taxonomies (difficulty, agents, C++ topics), bundle organization, and CSS best practices to keep styles clean and maintainable.
compatibility: Hugo v0.161.0+, Zen theme v6.3+
---

# Hugo Course Builder

This skill guides you through building and maintaining course websites with Hugo, the Zen theme, and Go-based content organization. It emphasizes clean architecture, proper use of bundles, and maintainable styling.

## Project Initialization

### Create and configure your site

```bash
# Create new Hugo project
hugo new site my-course-site

# Enter directory
cd my-course-site

# Initialize git (required for theme management)
git init

# Add Zen theme as submodule
git submodule add https://github.com/frjo/hugo-theme-zen.git themes/zen

# Create directory structure for Hugo 0.146+
mkdir -p content/modules content/homework content/resources layouts/_partials/head layouts/_shortcodes assets/css assets/js

# Create hugo.toml configuration
cat > hugo.toml << 'EOF'
baseURL = "https://example.com/"
languageCode = "en-us"
title = "Course Site"
theme = "zen"

[taxonomies]
  difficulty = "difficulties"
  agent = "agents"
  topic = "topics"
EOF

# Start development server
hugo server
```

**Why this structure:** Git submodules keep your theme versioned separately, preventing accidental modifications to vendored code. Taxonomies defined upfront prevent configuration conflicts later. **Note:** Hugo 0.146+ uses underscore prefixes (`_partials/`, `_shortcodes/`) to indicate special template directories.

## Content Architecture for Courses

### Directory structure

Organize your course content into three top-level sections:

```
content/
├── modules/           # Course modules (sections with child pages)
├── homework/          # Assignments (leaf bundles)
└── resources/         # Reference materials (leaf bundles)
```

### Section bundles (branch bundles)

Create section bundles for your modules. A section bundle contains `_index.md` and can have child pages:

```bash
# Create a module section
mkdir -p content/modules/module-01
cat > content/modules/module-01/_index.md << 'EOF'
---
title: "Module 1: Introduction to C++"
weight: 1
---

Overview of topics covered in this module.
EOF

# Add child pages to the module
cat > content/modules/module-01/lesson-01.md << 'EOF'
---
title: "Lesson 1: Basics"
weight: 1
---

Content here.
EOF
```

**Why section bundles:** They create logical groupings with their own list pages. Use `_index.md` (not `index.md`) to make this a section that generates a list page automatically.

### Leaf bundles (page bundles)

Use leaf bundles for assignments and resources that have associated files (PDFs, code samples, etc.):

```bash
# Create a homework leaf bundle
mkdir -p content/homework/assignment-01
cat > content/homework/assignment-01/index.md << 'EOF'
---
title: "Assignment 1: Basic Data Types"
difficulty: "beginner"
agents:
  - memory
  - reasoning
topics:
  - integers
  - pointers
dueDate: 2025-05-15
---

Assignment description and requirements.
EOF

# Add resources alongside the index
cp ~/Downloads/starter-code.cpp content/homework/assignment-01/
cp ~/Downloads/rubric.pdf content/homework/assignment-01/
```

**Why leaf bundles:** Resources stay alongside content. Hugo's `.Resources` method makes them accessible in templates without hardcoding paths. Use `index.md` (not `_index.md`) for leaf bundles—they don't create list pages.

**CSS benefit:** Leaf bundles create natural styling boundaries. A single assignment is a semantic unit—style it once as `.assignment`, not as `.homework-container`, `.assignment-title`, `.assignment-description`, `.assignment-resources`. This prevents CSS bloat.

## Front Matter Template (YAML)

### Standard template for assignments

Use this template for homework assignments:

```yaml
---
title: "Assignment Name"
weight: 1
difficulty: "beginner"          # beginner, intermediate, advanced
agents:
  - agent-type-1
  - agent-type-2
topics:
  - "C++ Topic 1"
  - "C++ Topic 2"
dueDate: 2025-05-15             # ISO date format
description: "Brief summary"
---
```

### Standard template for modules

```yaml
---
title: "Module Name"
weight: 1
description: "What students will learn"
---
```

**Why this structure:** YAML is human-readable and integrates cleanly with Hugo's data structures. Standard fields (`title`, `weight`, `description`) are reserved; custom fields (`difficulty`, `agents`, `topics`) go at the root level and are accessible in templates as `.Params.difficulty`, `.Params.agents`, etc.

## Taxonomy Configuration

### Define custom taxonomies in hugo.toml

```toml
[taxonomies]
  difficulty = "difficulties"
  agent = "agents"
  topic = "topics"
```

### Use taxonomies in front matter

```yaml
---
title: "My Assignment"
difficulty: "intermediate"
agents:
  - planning
  - coding
topics:
  - "Dynamic Memory"
  - "Pointer Arithmetic"
---
```

**Why this matters:** Taxonomies generate automatic listing pages. Hugo creates `/difficulties/intermediate/`, `/agents/planning/`, `/topics/dynamic-memory/` pages that list all content with those terms. This enables filtering and discovery without custom code.

## CSS Best Practices with Zen

CSS complexity is the #1 source of bloat in course websites. Zen is minimalist by design—your job is to *keep it that way*. The bundle structure (sections, lessons, assignments) is your first line of defense against CSS sprawl.

### Structure First, Styles Second

**Key principle:** Organize your content architecture *first*, then style semantic units. Don't add CSS classes to work around poor content structure.

1. **Use section/leaf bundles to create semantic containers** — A module is a section bundle, a lesson is a leaf bundle. These are natural styling boundaries. Don't create wrapper divs—use the bundle structure.

2. **One CSS rule per semantic unit** — If you find yourself writing `.lesson-title`, `.lesson-content`, `.lesson-sidebar`, stop. Instead, use semantic HTML (`<article>`, `<aside>`, `<header>`) and let Zen's cascade handle it.

3. **Audit before adding** — Before writing a new CSS rule, check:
   - Does Zen already handle this? (Check `themes/zen/assets/css/`)
   - Can I use CSS custom properties instead? (Zen provides `--spacing-*`, `--color-*`, `--font-*`)
   - Does this rule serve multiple elements, or just one?

### Lean on Zen's foundation

The Zen theme uses modern vanilla CSS with nesting and CSS layers. Avoid adding new global styles unless necessary:

1. **Use Zen's existing components first** — Check `themes/zen/assets/css/` before writing new styles. Zen covers typography, spacing, colors, responsive layout.
2. **Leverage CSS custom properties** — Reuse Zen's variables:
   ```css
   /* Instead of writing new colors, use Zen's palette */
   color: var(--color-text);
   background: var(--color-background);
   padding: var(--spacing-2);
   ```

3. **Use CSS layers for specificity** — New styles go in a distinct layer:

```css
/* In assets/css/custom.css */
@layer course {
  /* Only add styles that Zen doesn't cover */
  .assignment-due-date {
    color: var(--color-accent);
    font-weight: bold;
  }
}
```

**Understand *why* this works, or it will surprise you.** `themes/zen/assets/css/styles.css:2` declares the order:

```css
@layer reset, fonts, vars, base, layouts, components, mobilemenu, print, zen;
```

Your layer name is **absent from that list**, so it is appended **last** and beats every theme rule regardless of selector specificity. That is why no override needs `!important`. Two consequences:

- **Load your stylesheet after the theme's**, or your `@layer course { … }` block declares `course` first and the theme's layers get appended *after* it — silently inverting the priority.
- **Layers only settle theme-vs-you.** *Within* your own layer, ordinary specificity still decides. A bare `.col-center` loses to your own earlier `.layout__main th, .layout__main td` rule — the classic symptom is a class that "does nothing" and an inline style that mysteriously was required.

4. **Keep overrides minimal** — Override Zen's styles only when you need *different behavior*, not decoration. Ask: "Does this need to look different, or am I just decorating?"

### Directory structure for custom CSS and JS

Put your own assets in **`assets/`, not `static/`**. Files in `static/` are copied verbatim and cannot be fingerprinted, minified, or bundled; only `assets/` is reachable by `resources.Get`.

```
assets/
├── css/
│   └── custom.css         # Your course-specific styles (keep it small!)
└── js/
    └── site.js
themes/zen/assets/css/     # Zen's built-in styles (don't modify these)
```

Zen ships an **empty `head/extra.html` hook**, called from `themes/zen/layouts/baseof.html:14`, specifically so you can add to `<head>` without touching the theme. Override it at `layouts/_partials/head/extra.html`:

```go-html-template
{{- /* Name the resource, check it, then fingerprint it. Piping a missing
       resource straight into `fingerprint` fails deep inside baseof.html
       without naming the file. */ -}}
{{- $css := resources.Get "css/custom.css" -}}
{{- if not $css -}}
  {{- errorf "head/extra: assets/css/custom.css not found" -}}
{{- else }}
<link rel="stylesheet" href="{{ ($css | fingerprint).RelPermalink }}">
{{- end }}
```

**Never hardcode `href="/css/custom.css"`.** Two failures: the leading slash resolves against the *host root*, which 404s whenever the site deploys under a path segment (`https://example.edu/~user/course/`); and without a content hash a reader's cached copy survives every deploy, so the stylesheet drifts arbitrarily far behind the HTML that depends on it. `RelPermalink` on a fingerprinted resource solves both.

### CSS Maintenance Checklist

- **Weekly:** Run `grep -c "{" assets/css/custom.css` to count rules. If it's growing, audit for unused styles.
- **Before merging:** Check that no two rules share the same selector.
- **Quarterly:** Review Zen's theme variables—you may find a built-in solution for your "custom" styles.

**Why restraint matters:** CSS complexity grows *exponentially*. Each new rule makes maintenance harder, increases specificity conflicts, and slows down page loads. Zen is already minimal—protect that by making only necessary changes. For every 10 lines of CSS you add, you'll spend 100 lines debugging later.

## Common Hugo Patterns to Prevent Errors

### 1. Always use ISO dates

```yaml
# ✓ Correct
date: 2025-05-15

# ✗ Wrong (ambiguous, often fails parsing)
date: 05-15-2025
```

### 2. Taxonomy names must match in front matter

```toml
# In hugo.toml
[taxonomies]
  difficulty = "difficulties"
```

```yaml
# In front matter — use singular form
difficulty: "beginner"        # ✓ Correct
difficulties: "beginner"      # ✗ Wrong
```

### 3. Use `_index.md` for sections, `index.md` for leaf pages

- Sections (with children) → `_index.md`
- Leaf pages (no children) → `index.md`
- Wrong choice silently breaks list pages or hides content

### 4. Check bundle structure

```
content/modules/
├── module-01/
│   └── _index.md              # Section bundle ✓
│   └── lesson-01.md           # Child page ✓

content/homework/
├── assignment-01/
│   └── index.md               # Leaf bundle ✓
│   └── rubric.pdf             # Resource ✓
```

### 5. Draft content is hidden

Pages with `draft: true` don't appear in builds. Remove before publishing:

```yaml
---
title: "My Page"
draft: false              # Don't forget this!
---
```

## Templates for Common Tasks

### List all assignments by difficulty

Create `layouts/difficulties/single.html`:

```html
<h1>{{ .Title }}</h1>
<ul>
{{ range .Pages }}
  <li><a href="{{ .RelPermalink }}">{{ .Title }}</a></li>
{{ end }}
</ul>
```

### Reference resources in a page

In any template:

```html
{{ range .Resources }}
  <a href="{{ .RelPermalink }}">{{ .Title }}</a>
{{ end }}
```

This works because resources live in the bundle alongside `index.md`.

## Behaviours learned the hard way

Every item below broke a template that had been *written but not executed*. None produces an obvious error message; most produce a clean build and a wrong page. Read this section before writing templates.

### Data, sorting, and types

- **`site.Data` is deprecated since Hugo 0.156 — use `hugo.Data`.**
- **`.Pages.ByWeight` sorts weight-0 pages LAST**, so an "Orientation" or "Week 0" page lands at the end. Use `sort (site.GetPage "/modules").Pages "Params.weight"` instead.
- **A date pulled back out of a dict stored in a slice arrives as `interface{}`** — no methods are reachable, so `.Unix` fails. Compare `time.Format "2006-01-02"` strings, which sort and compare lexically exactly as the dates do.
- **`int` rejects a zero-padded string**: `int "08"` fails as invalid octal. To match a `module-08` directory against `weight: 8`, compare `printf "module-%02d"` against the name rather than parsing the number — which pins the padding convention as a bonus.
- **`.File.ContentBaseName`** gives the *directory* name for a branch bundle (`module-08`), which is what you want when validating a slug against front matter.

### Escaping and output

- **Go's HTML escaper turns `+` into `&#43;`**, mangling titles like `Modern C++ I`. Needs `transform.HTMLEscape | safeHTML`.
- **`jsonify` output inside `<script>` is JS-escaped into a quoted string literal unless piped through `safeJS`.** It will still `JSON.parse` — into a *string*, not an object, which is the confusing part.
- **`delimit` over a slice of partial output returns a plain string**, so HTML the partials produced gets escaped and the tags print as text. Pipe the result through `safeHTML`.
- **A trim marker eats the whitespace on its side.** `{{- x -}} – {{ y -}}` renders `x– y`, not `x – y`. Use a plain `}}` on the side where the space matters.
- **Shortcode output is exempt from `markup.goldmark.renderer.unsafe = false`.** Raw HTML typed in Markdown is dropped, but HTML emitted by a shortcode survives — Hugo substitutes it after Markdown rendering. This is why generated tables must be shortcodes.

### Control flow and error handling

- **`else with` is not valid Go template syntax** — `else` accepts only `if`.
- **`errorf` logs and continues**, so one root fault cascades into dozens of downstream errors that bury it. Gate dependent loops behind a validity flag (`{{ if $termOK }}`) so the message naming the real fault is the one the user sees.
- **A guard is not verified until you have made it fire.** Every check written in a batch should be exercised by deliberately breaking the data — repeatedly, this is what catches guards that never worked.
- **`resources.Get` piped straight into `fingerprint`** dies inside `baseof.html` naming no file when the asset is missing. Name the resource, check it, then fingerprint.

### URLs

- **With `canonifyURLs = true`, `absURL` on a leading-slash path resolves against the host root, not the baseURL path.** Strip the slash first. Note that `canonifyURLs` rewrites `href`/`src` *attributes* at output time but never touches string literals inside a JSON `<script>` — so URLs you hand to JavaScript must be made absolute explicitly.
- **A production build is not a preview build.** The dev `baseURL` usually has no path segment, which hides every path-resolution bug until deploy. Verify URL-shaped changes with a real build.

### Zen theme specifics

- **Zen styles any `<ul>` that is a DIRECT child of `<article>` or `<aside>` as a table** (`themes/zen/assets/css/_zen.css:45`) — `display: table` / `table-row`, with `content: '\2981'` in a generated first cell. Nesting the same list one level deeper silently opts it out of *both* the bullet and the column layout. Two lists in one card will then disagree on the glyph and on both column edges.
- **Zen ships a `.visually-hidden` component** — use it to name an intentionally empty `<th>`, which is otherwise announced as nothing at all and leaves each row's first cell unlabelled.
- **Cascade layers, not specificity, are why your overrides win** — see the CSS section above.

### The dev server

- **A running `hugo server` holds `.hugo_build.lock`, and a plain `hugo` blocks on it indefinitely with no message.** It presents as a hang, not an error. Use `hugo --noBuildLock -d /tmp/checkbuild` for verification builds while the preview is up.
- **Never run bare `hugo` beside a running preview** — it writes production output into `public/`, which the server may then serve. Start the preview with **`-M`** (`--renderToMemory`) so the two cannot collide, and always direct verification builds elsewhere with `-d`.
- **`hugo server` does not watch a top-level directory created after it started.** Add `assets/` to an existing project and the site 500s until you restart the server.

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Content doesn't appear | `draft: true` or `_index.md` in leaf bundle | Check front matter; use correct bundle type |
| Taxonomies don't generate pages | Taxonomy name mismatch between config and front matter | Use singular form in front matter, match `hugo.toml` config |
| Resources not accessible in templates | Resources in wrong directory | Use bundle structure; keep files adjacent to `index.md` |
| CSS getting too complex | Adding overrides without structure | Use CSS layers; audit for unused styles |
| Build errors about missing files | Relative path issues in templates | Use `.RelPermalink` and `.Resources` instead of hardcoded paths |
| `hugo` hangs with no output | A running `hugo server` holds `.hugo_build.lock` | `hugo --noBuildLock -d /tmp/checkbuild` |
| Site 500s right after adding `assets/` | `hugo server` does not watch a top-level dir created after startup | Restart the server |
| A CSS class "does nothing" | Out-specified by another rule in *your own* layer | Match the element too (`td.col-center`), not just the class |
| CSS/JS 404 on the deployed site only | Hardcoded `/css/...`, resolved against the host root | `resources.Get` + `RelPermalink` |
| A stale stylesheet survives deploys | Asset in `static/`, so unfingerprinted | Move to `assets/`, pipe through `fingerprint` |
| Orientation/Week 0 sorts last | `.Pages.ByWeight` puts weight 0 at the end | `sort … "Params.weight"` |
| `JSON.parse` yields a string, not an object | `jsonify` inside `<script>` was JS-escaped | Pipe through `safeJS` |

## Quick Reference

- **Start server:** `hugo server -M` (`-M` = render to memory, so a stray `hugo` cannot poison what the preview serves)
- **Build for production:** `hugo` (output in `public/`)
- **Verification build while the preview runs:** `hugo --noBuildLock -d /tmp/checkbuild`
- **Create new content:** `hugo new content/path/to/file.md`
- **Check for errors:** `hugo --debug` shows detailed warnings
- **Update theme:** `git submodule update --remote`

## Links

- [Hugo Documentation](https://gohugo.io/documentation/)
- [Hugo 0.146+ Template System Overview](https://gohugo.io/templates/new-templatesystem-overview/) — Details on underscore-prefixed directories and the new template structure
- [Zen Theme Repository](https://github.com/frjo/hugo-theme-zen)
- [Zen Theme Demo](https://zen-demo.xdeb.org/)
