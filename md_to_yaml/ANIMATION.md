# Animation controls

Two controls, both on `content` and `transcribe` slides, plus two deck-level keys.
The compiler resolves them into JSON `data-` attributes on the slide's `<section>`;
a GSAP-based runtime in the page is what acts on them.

> **Status in this copy: the attributes are emitted, and nothing consumes them.**
> Verified 2026-08-15 — see *Is it working?* at the end before you plan a lecture
> around these. The schema, the merge logic, and the attribute output all work; the
> runtime is missing from the live template.

---

## `bullet_animation` — list items appear in sequence

```yaml
---
layout: content
title: Findings
bullet_animation: true          # or "stagger"
---
- First
- Second
- Third
```

Bullets tween in when the slide scrolls into view. Pass an object to override any
parameter; unspecified ones keep their default.

| Setting | Default | Meaning |
|---|---|---|
| `duration` | `0.45` | Tween length, seconds |
| `stagger` | `0.12` | Delay between consecutive items, seconds |
| `ease` | `power2.out` | GSAP ease string |
| `threshold` | `0.45` | IntersectionObserver threshold that starts the animation |
| `x_offset` | `-24.0` | Horizontal offset in px before the tween — negative slides in from the left |

```yaml
bullet_animation:
  duration: 0.6
  stagger: 0.2
  x_offset: 0        # fade in place instead of sliding
```

## `bullet_focus` — walk the list one item at a time

```yaml
---
layout: content
title: Findings
bullet_focus: true
---
```

Dims every list item except the current one; a keypress advances the focus. This is the
lecture control — it stops a room reading ahead while you are still on item one.

| Setting | Default | Meaning |
|---|---|---|
| `key` | `j` | Advances the focused bullet |
| `back_key` | `k` | Moves focus back |
| `dim` | `0.25` | Opacity of unfocused items |
| `duration` | `0.3` | Opacity tween, seconds |
| `ease` | `power2.out` | GSAP ease string |

The two compose: `bullet_animation` controls how bullets *arrive*, `bullet_focus`
controls which one is *live*.

## Deck-level keys

```yaml
---
title: My deck
animation_defaults:
  bullet_stagger:
    duration: 0.6
    ease: power1.inOut
  bullet_focus:
    key: n
    dim: 0.15
gsap_script_url: https://example.edu/js/gsap.min.js
---
```

| Key | Default | Meaning |
|---|---|---|
| `animation_defaults.bullet_stagger` | skill defaults above | Deck-wide `bullet_animation` parameters |
| `animation_defaults.bullet_focus` | skill defaults above | Deck-wide `bullet_focus` parameters |
| `gsap_script_url` | `https://cdn.jsdelivr.net/npm/gsap@3/dist/gsap.min.js` | Where GSAP loads from. Must start with `https://`, max 500 characters. |

**Merge order**, per slide: skill defaults → deck `animation_defaults` → the slide's own
`bullet_animation` / `bullet_focus` object. Each layer overrides only the fields it names.

`animation_defaults` alone animates nothing — it sets parameters. A slide must still opt
in with `bullet_animation:` or `bullet_focus:`.

## Animation costs you self-containment

A deck with no animation makes **zero external requests** and works offline, on a plane,
from a memory stick. Turn on either control and the page fetches GSAP from a CDN at view
time. For a classroom on unreliable wifi, or a file students keep for the term, that is a
real trade — download GSAP and point `gsap_script_url` at a local copy if you need both.

Mermaid has the same property: a deck containing a `diagram` slide fetches Mermaid from a
CDN unless compiled with `--bake-mermaid`.

## Accessibility

`accessibility-core.md` requires a `prefers-reduced-motion` block, and the compiler emits
one. Respect it: motion must be decoration, never the only way information is conveyed. A
`bullet_focus` deck must still make sense when every bullet is at full opacity — which is
what a student gets in the printed or reduced-motion version.

## Is it working?

The controls emit their configuration but no runtime reads it. Checked on 2026-08-15:

```bash
cd ~/.claude/skills/md_to_yaml
grep -c "data-bullet-stagger" compiler/templates/base.html.j2       # 1 — the emitter
grep -c "dataset.bulletStagger\|bulletFocus" compiler/templates/base.html.j2      # 0 — no consumer
grep -c "gsap" compiler/templates/base.html.j2                      # 0 — script tag never written
grep -c "dataset.bulletStagger\|bulletFocus" compiler/templates/base.html.j2.bak  # present
```

Compile any deck with `bullet_animation: true` and the output carries
`data-bullet-stagger="{…}"` on the section, no `gsap` anywhere, and no `j`/`k` in the
keyboard handler — which binds only arrows, space, `g`/`G`, `Home`/`End`, `Escape`, and
the zoom keys.

The runtime, including the `<script src="{{ gsap_script_url }}">` tag, exists in
`compiler/templates/base.html.j2.bak`. The live template is the larger, newer file and
does not carry it. So this is a regression in the vendored copy, not a design decision.

`SKILL.md` notes that `compiler/` and `schema/` are copies of an upstream `md_to_yaml`
project. Fix it there and re-copy — patching the vendored template here would be
overwritten by the next sync, and would leave the two templates disagreeing in the
meantime.

## See also

- `CSS_CONTROLS.md` — scaling text, figures, and page chrome
- `accessibility-core.md` — reduced motion, contrast, focus visibility
