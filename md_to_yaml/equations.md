# Equation Guidelines for YAML DSL Slide Generation

> **Purpose:** Guide the LLM on correct math delimiter usage in slide YAML. The compiler converts `$...$` / `$$...$$` to MathML via **latex2mathml** (not KaTeX) — incorrect delimiter choice or unsupported macros cause rendering problems.

---

## Rule: Inline vs Display Math

| Delimiter | Name | When to Use | Rendering |
|-----------|------|-------------|-----------|
| `$...$` | Inline | Short expressions within a sentence or bullet point | Flows with surrounding text |
| `$$...$$` | Display | Standalone equations that deserve their own line | Centered on a separate line, larger |

**Default to inline (`$...$`).** Only use display (`$$...$$`) when the equation is the focal point of the slide — a derivation, a key formula being introduced, or a multi-line expression.

---

## YAML quoting and LaTeX

Math strings live inside YAML scalars (slide titles, captions, **`table`** `headers` / `rows` cells, flow-style list items). **Single-quoted** and **double-quoted** rules differ; mistakes strip or corrupt backslashes before LaTeX reaches the compiler.

### Double-quoted YAML (`"..."`)

YAML treats many `\X` sequences as **escapes**. Examples that break math:

| Written in YAML | Typical interpretation | Effect on math |
|-----------------|------------------------|----------------|
| `"$\alpha$"` | `\a` is an escape | Corrupt / wrong output |
| `"$\tilde{O}$"` | `\t` is **tab** | `$` + tab + `ilde{O}$` — `\tilde` gone |
| `"$\sqrt{N}$"` | `\s` handling varies by parser | Unreliable |

**If you use double quotes**, emit a **literal** backslash with `\\` so the following character is not read as an escape, e.g. **`"$\\tilde{O}(d^{3/2}\\sqrt{N})$"`** (each `\\` → one `\` in the loaded string). For heavy math, **single quotes** are usually clearer.

### Single-quoted YAML (`'...'`)

In single-quoted scalars, **backslash is not special** (only `''` escapes a quote). **One** `\` in the file → **one** `\` in the string.

**Pitfall — doubled backslashes:** writing `'\\tilde{O}(d^{3/2}\\sqrt{N})'` loads **two** backslashes before `tilde` and before `sqrt`. In LaTeX, **`\\`** is a **line break**; `\tilde` and `\sqrt` never form — previews show plain `tildeO`, `sqrtN`, or broken MathML (`mspace linebreak`, letters `s`, `q`, `r`, `t`).

**Correct (single-quoted):**

```yaml
'$\tilde{O}(d^{3/2}\sqrt{N})$ under stated assumptions'
```

**Wrong (single-quoted):**

```yaml
'$\\tilde{O}(d^{3/2}\\sqrt{N})$ under stated assumptions'
```

### `table` cells

The compiler runs **`extract_and_render_math`** on each cell — same rules as bodies. Prefer **single-quoted** row cells whenever a cell contains `\tilde`, `\sqrt`, `\mathcal`, etc.

```yaml
rows:
  - ['Regime', '$O(N^2 d)$', '$\tilde{O}(d^{3/2}\sqrt{N})$']
```

---

## Good Examples

### Inline math in bullet points

```yaml
---
layout: content
title: "Grid-Based Clustering: Strengths and Weaknesses"
---
- Complexity depends on grid resolution, not number of points
- Remove cells with density below threshold $\tau$
- Bandwidth parameter $\sigma$ controls kernel smoothness
- A unit is **dense** if fraction of points exceeds $\tau$
```

### Inline math in running text

```yaml
---
layout: content
title: "DENCLUE: Key Properties"
---
- Clusters whose attractor density is below minimum threshold $\xi$ are discarded
- Set $k \leftarrow 2$ and begin iterating
- Sensitive to bandwidth parameter $\sigma$
```

### Display math for a key formula being introduced

```yaml
---
layout: two-column
title: "DENCLUE: Kernel Density Estimation"
proportion: 50/50
left:
  type: diagram
  alt_text: "Flowchart of kernel density estimation process"
  source: |
    graph TD
      A[Each data point x] --> B[Compute kernel]
      B --> C[Sum all kernels]
      C --> D[Find local maxima]
---
**Gaussian kernel formula:**

$$K(y) = e^{-\text{distance}(\mathbf{x}, \mathbf{y})^2 / 2\sigma^2}$$

- Each point contributes a smooth density bump
- Bandwidth $\sigma$ controls smoothness
```

### Display math for a multi-step derivation

```yaml
---
layout: content
title: "Deriving the Update Rule"
---
The gradient of the loss function leads to the update rule:

$$\theta_{t+1} = \theta_t - \eta \nabla_\theta \mathcal{L}(\theta_t)$$

where $\eta$ is the learning rate and $\nabla_\theta \mathcal{L}$ is the gradient.
```

---

## Bad Examples (DO NOT do this)

### Using display math for short inline references

```yaml
# BAD — $$\tau$$ renders as a centered block, breaking the sentence flow
- Remove cells with density below threshold $$\tau$$
- Bandwidth parameter $$\sigma$$ controls smoothness

# GOOD — $\tau$ flows inline with the text
- Remove cells with density below threshold $\tau$
- Bandwidth parameter $\sigma$ controls smoothness
```

### Using display math inside bullet points

```yaml
# BAD — display math in a bullet creates awkward spacing
- A unit is **dense** if $$\frac{n}{N} > \tau$$

# GOOD — inline math keeps the bullet compact
- A unit is **dense** if $\frac{n}{N} > \tau$

# ALSO GOOD — if the formula is complex, give it its own line after the bullet list
A unit is **dense** when its point fraction exceeds the threshold:

$$\frac{n_{\text{cell}}}{N_{\text{total}}} > \tau$$
```

### Mixing delimiters inconsistently

```yaml
# BAD — mixing $$...$$ and $...$ for equivalent expressions
- Threshold $$\tau$$ must be chosen carefully
- Bandwidth $\sigma$ affects smoothness

# GOOD — consistent inline style for same-level references
- Threshold $\tau$ must be chosen carefully
- Bandwidth $\sigma$ affects smoothness
```

---

## Decision Rule

Ask yourself: **"Is this equation the main point of the slide, or is it supporting text?"**

- **Supporting text** (parameters, variable names, short expressions in bullets) → `$...$`
- **Main point** (the formula being taught, a key derivation, a standalone equation) → `$$...$$`

When in doubt, use `$...$`. Display math should appear at most 1-2 times per deck, not on every slide.

---

## Coloring sub-expressions

The compiler uses **latex2mathml**, not KaTeX. This matters for color support:

| Form | Supported? | Notes |
|---|---|---|
| `\textcolor{#hex}{expr}` | ❌ | Emitted as literal text — breaks math |
| `\color{#hex}{group}` | ⚠️ | `\color` is a switch; leaks color past `}` |
| `{\color{#hex} expr}` | ✅ | Correct: outer braces scope the switch |

**Add color manually where pedagogically useful** — don't color for decoration. Use the grouped switch form:

```yaml
# Single-quoted YAML — one backslash, no escaping needed
- Cost: '$L(12Sd^2 + 2{\color{#f0a500} S^2 d})$'
```

### Color macro file (recommended — avoid hardcoding hex in YAML)

Define named colors once in a `color_macros.yaml` file alongside the deck:

```yaml
# color_macros.yaml
accent: "#f0a500"     # matches dark theme --accent
accent_light: "#b06800"  # matches light theme --accent
warn: "#e74c3c"
highlight: "#3b82f6"
```

Reference it in deck metadata:

```yaml
---
title: "My Deck"
theme: dark
macros: color_macros.yaml
---
```

Then use `\macroname` (backslash + key) in any math expression:

```yaml
# Single-quoted YAML
- Cost: '$L(12Sd^2 + 2{\accent S^2 d})$'
- Error: '${\warn \epsilon}$ must stay small'
```

Python expands `\accent` → `\color{#f0a500}` before latex2mathml runs, so no hex ever appears in the YAML source. The macro file is shared across all decks in the same directory.

**YAML quoting rule for macros**: single-quoted YAML is cleanest (one `\` in the file = one `\` in the string). In double-quoted YAML, double the backslash: `"${\\accent S^2 d}$"`.

**Do not** ask the LLM to generate `\color{hex}` inline — always use a named macro from the deck's macro file instead.
