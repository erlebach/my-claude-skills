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
mkdir -p content/modules content/homework content/resources layouts/_partials layouts/_shortcodes static/css

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

3. **Use CSS layers for specificity** — New styles go in a distinct layer to prevent cascade collisions:

```css
/* In static/css/custom.css */
@layer course-specific {
  /* Only add styles that Zen doesn't cover */
  .assignment-due-date {
    color: var(--color-accent);
    font-weight: bold;
  }
}
```

4. **Keep overrides minimal** — Override Zen's styles only when you need *different behavior*, not decoration. Ask: "Does this need to look different, or am I just decorating?"

### Directory structure for custom CSS

```
static/
├── css/
│   └── custom.css         # Your course-specific styles (keep it small!)
themes/zen/assets/css/     # Zen's built-in styles (don't modify these)
```

Link in your `layouts/_partials/header.html` (Hugo 0.146+ uses `_partials`):

```html
<link rel="stylesheet" href="/css/custom.css">
```

### CSS Maintenance Checklist

- **Weekly:** Run `grep -r "^[^*].{" static/css/custom.css | wc -l` to count rules. If it's growing, audit for unused styles.
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

## Troubleshooting

| Issue | Cause | Fix |
|-------|-------|-----|
| Content doesn't appear | `draft: true` or `_index.md` in leaf bundle | Check front matter; use correct bundle type |
| Taxonomies don't generate pages | Taxonomy name mismatch between config and front matter | Use singular form in front matter, match `hugo.toml` config |
| Resources not accessible in templates | Resources in wrong directory | Use bundle structure; keep files adjacent to `index.md` |
| CSS getting too complex | Adding overrides without structure | Use CSS layers; audit for unused styles |
| Build errors about missing files | Relative path issues in templates | Use `.RelPermalink` and `.Resources` instead of hardcoded paths |

## Quick Reference

- **Start server:** `hugo server`
- **Build for production:** `hugo` (output in `public/`)
- **Create new content:** `hugo new content/path/to/file.md`
- **Check for errors:** `hugo --debug` shows detailed warnings
- **Update theme:** `git submodule update --remote`

## Links

- [Hugo Documentation](https://gohugo.io/documentation/)
- [Hugo 0.146+ Template System Overview](https://gohugo.io/templates/new-templatesystem-overview/) — Details on underscore-prefixed directories and the new template structure
- [Zen Theme Repository](https://github.com/frjo/hugo-theme-zen)
- [Zen Theme Demo](https://zen-demo.xdeb.org/)
