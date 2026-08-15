Based on current presentation design best practices and your 12 layout templates, here's a comprehensive rulebook for effective presentation design:

***

# Presentation Layout Design Rules

## I. Foundation Principles

### 1. **One Message Per Slide Rule**
- Each slide must communicate a single, clear message
- The layout choice should reinforce that message
- If you need two messages, create two slides

### 2. **Visual Hierarchy Triangle**
- **Primary**: The main message (largest, highest contrast)
- **Secondary**: Supporting details (medium size, medium contrast)
- **Tertiary**: Metadata/context (smallest, lowest contrast)

### 3. **Cognitive Load Management**
- Maximum 5-7 bullet points per content slide
- Maximum 3-4 cards/sections per two-column or comparison slide
- One complex visual (diagram/figure) per slide unless comparison is the point

***

## II. Layout-Specific Usage Rules

### **title.html.j2**
**Purpose**: Opening slide, section breaks, major transitions

**Rules**:
- Use at presentation start (always)
- Use for major section transitions (2-4 times in a 20-slide deck)
- Title: 1-7 words maximum
- Subtitle: 1-2 short lines, optional
- Keep visual elements minimal (logo, date, author only)

**When to use**:
- ✅ Presentation opening
- ✅ New major section (after 4-6 content slides)
- ❌ Minor topic changes (use divider instead)

***

### **hero.html.j2**
**Purpose**: High-impact statement, key takeaway, emotional hook

**Rules**:
- Use sparingly: 1-3 times per presentation
- Content: Single powerful statement (5-15 words)
- Optional: One supporting visual or large number/statistic
- No bullets, no paragraphs

**When to use**:
- ✅ Mission statement or main thesis
- ✅ Dramatic reveal of key insight
- ✅ Call to action at end
- ❌ Routine information delivery

**Example content**: "AI will reshape how we teach within 3 years"

***

### **content.html.j2**
**Purpose**: Primary workhorse for text-based information

**Rules**:
- Heading: Clear, specific (not generic like "Overview")
- Bullets: 3-5 points maximum, each 1-2 lines
- Use parallel structure (all bullets start with verbs, or all nouns, etc.)
- No sub-bullets unless absolutely necessary
- Line length: Maximum 15-20 words per bullet

**Content density limits**:
- With short description paragraph: Max 3-4 bullets
- Bullets only: Max 5 bullets
- If you need more, split into multiple content slides

**When to use**:
- ✅ Listing features, benefits, requirements
- ✅ Explaining processes step-by-step (use **steps.html.j2** if sequential)
- ✅ Key takeaways or recommendations
- ❌ Dense explanations (use **two-column.html.j2** with visual)

### **transcribe.html.j2**
**Purpose**: Document-fidelity text (translation, PDF transcription), not presentation pacing.

**Rules**:
- Use **`layout: transcribe`** in YAML (same body rules as **content** slides: Markdown below `---`).
- Prefer **`transcribe`** for multi-paragraph blocks and long lists that mirror a source document.
- For **`md_to_yaml`** teaching decks, keep **`layout: content`** unless the user explicitly wants transcription styling.

***

### **two-column.html.j2**
**Purpose**: Pairing visual + text, showing relationships, before/after

**Rules**:
- Always pair complementary content types:
  - **Figure + bullets**: Image/diagram illustrates the points
  - **Mermaid + content**: Flowchart/architecture + explanation
  - **Content + content**: Contrasting perspectives (less common)
- Left-right ratio: Usually 50/50 or 40/60
- Each column: Follow same density rules as individual layouts
- Visual column: One primary element, labeled if needed

**Column content limits**:
- Bullet column: Max 4 bullets (less than standalone content slide)
- Paragraph column: Max 6-8 lines
- Visual column: One diagram/figure with optional title

**When to use**:
- ✅ Explaining architecture with diagram + key points
- ✅ Process flow (mermaid) + explanation
- ✅ Photo/screenshot + feature bullets
- ✅ Before/after comparison
- ❌ When visual doesn't directly support text

**Layout patterns**:
```
[Figure | Content]  - Visual first when it's the hook
[Content | Figure]  - Text first when explaining what's coming
[Mermaid | Content] - Always diagram left, explanation right
[Content | Mermaid] - Less common, use when building to reveal
```

***

### **figure.html.j2**
**Purpose**: Showcasing visual evidence, screenshots, photos, architecture

**Rules**:
- One primary visual per slide
- Heading: Descriptive caption (not "Screenshot" or "Diagram")
- Optional: 1-2 line explanation below figure
- Visual must be high resolution and clearly visible
- Annotations/callouts directly on image if needed

**When to use**:
- ✅ Showing user interface or product
- ✅ Displaying data visualization that speaks for itself
- ✅ Presenting architecture diagram or system overview
- ✅ Photo evidence or real-world example
- ❌ When the visual needs significant text explanation (use **two-column.html.j2**)

### Figure layout selection by aspect ratio

When a slide centres on a single figure, choose layout from figure geometry:

| Figure aspect ratio (width ÷ height) | Layout |
|--------------------------------------|--------|
| 1.35 – 2.1 (near slide-shaped, 16:9) | `figure` |
| > 2.1 (wide banner / landscape pipeline) | `figure-wide` |
| < 1.35 (portrait / tall diagram) | `two-column` (figure + side text) |

**Fallback rules:**
- Wide figure (`> 2.1`) with almost no supporting text → use plain `figure`.
- Tall figure (`< 1.35`) with short explanation → `figure` still works.
- When text volume is substantial and figure is wide → prefer `figure-wide`.

**`figure-wide` YAML shape:**

Front matter: `src`, `alt_text`, `caption` (optional), `proportion` (optional, default `50/50`).
Body: up to three `## Heading` sections — `## Summary` (optional, shown above figure),
then two headings for left and right columns.

***

### **diagram.html.j2**
**Purpose**: Complex technical diagrams, network graphs, system architecture

**Rules**:
- One diagram per slide (complexity budget)
- Heading: What the diagram shows
- Diagram should be understandable in 10 seconds
- Use progressive disclosure: build diagram across 2-3 slides if complex
- Label all components clearly within diagram
- Optional: Brief 1-line context above diagram

**Complexity limits**:
- Max 7-9 nodes/components (cognitive limit)
- If more complex, split into multiple slides showing different aspects
- Use color/grouping to reduce perceived complexity

**When to use**:
- ✅ Network topology or system architecture
- ✅ Data flow or process diagrams
- ✅ Relationship maps (mind maps, org charts)
- ❌ Simple flowcharts (use **steps.html.j2** or **two-column.html.j2** with mermaid)

### Diagram variety rule

Do NOT use `graph TD` for every diagram slide. Before writing Mermaid source, ask:

1. **Is this a 2×2 outcome grid?** → use `quadrantChart`
2. **Is this an ordered sequence of steps or interactions?** → use `sequenceDiagram`
3. **Is this a proportion or composition?** → use `pie`
4. **Is this a state machine (stages, transitions)?** → use `stateDiagram-v2`
5. **Is this a concept map or topic cluster?** → use `mindmap`
6. **Is this a ranked numeric comparison?** → use `xychart-beta`
7. **Is this a causal chain or decision tree?** → use `graph TD` or `graph LR`

A deck with 4+ diagram slides must use at least 3 different Mermaid diagram types.

### Color usage rule for diagrams

Before adding any `style NodeId fill:` directive, ask:
- **Does the color tell the audience something the label does not?**
- **Does it distinguish two semantically different outcomes?**

If yes → use a color from the approved pairs in `mermaid-best-practices.md`, and always pair `fill:` with `color:`.
If no → omit the `style` directive entirely. Leave the node default.

Maximum 4 colored nodes per diagram. Prefer 0–2. See `mermaid-best-practices.md` for the full color budget table.

***

### **steps.html.j2**
**Purpose**: Sequential processes, numbered procedures, timelines

**Rules**:
- 3-6 steps maximum (optimal: 4-5)
- Each step: Number + title + 1-2 line description
- Steps must be sequential and dependent
- Use visual indicators (arrows, timeline, numbers)
- All steps visible simultaneously (not progressive reveal unless presenting live)

**When to use**:
- ✅ Workflow or process (sign-up flow, algorithm steps)
- ✅ Timeline of events
- ✅ Implementation phases
- ✅ Decision tree with clear sequential logic
- ❌ Non-sequential lists (use **content.html.j2**)
- ❌ More than 6 steps (split into phases)

***

### **comparison.html.j2**
**Purpose**: Side-by-side comparison, A vs B, pros/cons

**Rules**:
- Exactly 2-3 items being compared (optimal: 2)
- Parallel structure: same attributes for each item
- 3-5 attributes compared
- Use visual distinction (color, icons, borders)
- Header clearly states what's being compared

**Layout patterns**:
```
[Option A | Option B]           - Two-way comparison
[Before | After]                - Transformation
[Current | Proposed]            - Change advocacy
[Approach 1 | Approach 2 | 3]   - Max 3 options
```

**When to use**:
- ✅ Comparing tools, approaches, methodologies
- ✅ Before/after results
- ✅ Current state vs. future state
- ❌ More than 3 items (use **table.html.j2**)

***

### **table.html.j2**
**Purpose**: Structured data, feature matrices, multi-item comparison

**Rules**:
- Maximum dimensions: 6 columns × 8 rows (including header)
- Optimal: 4 columns × 5 rows
- Header row always visible and clearly distinguished
- Highlight key cells/rows with subtle color
- Keep cell content brief (1-5 words, or ✓/✗/numbers)
- Left-align text, right-align numbers

**When to use**:
- ✅ Feature comparison across multiple products
- ✅ Requirements matrix or specification sheet
- ✅ Schedule or agenda (time-based rows)
- ✅ Results summary with multiple dimensions
- ❌ Complex nested data (simplify first)
- ❌ More than 10 rows (split or use appendix)

**Data density rule**: If cells need full sentences, you need a different layout

***

### **code.html.j2**
**Purpose**: Showing code snippets, configuration, command examples

**Rules**:
- 8-15 lines maximum (visible without scrolling)
- Syntax highlighting required
- Line numbers optional (use for reference in explanation)
- Heading: What the code does (not "Code Example")
- Optional: 1-2 line explanation before or after
- Focus: Highlight the 2-3 most important lines

**When to use**:
- ✅ Demonstrating API usage
- ✅ Showing configuration examples
- ✅ Teaching programming concepts
- ✅ Terminal commands or scripts
- ❌ Full program listings (link to repo instead)
- ❌ More than one code block per slide (use **two-column.html.j2** if comparing)

**Code clarity rules**:
- Omit boilerplate (imports, closing brackets) if not essential
- Use comments sparingly (1-2 per slide)
- Increase font size: minimum 20pt for code

***

### **quote.html.j2**
**Purpose**: Expert testimony, user feedback, memorable statements

**Rules**:
- Quote length: 1-4 sentences maximum (optimal: 1-2)
- Always attribute: Name + title/affiliation
- Quote must be relevant and support your argument
- Use large, readable font (24-32pt)
- Optional: Photo of person quoted

**When to use**:
- ✅ Expert endorsement of your approach
- ✅ User testimonial or feedback
- ✅ Defining concept with authoritative source
- ✅ Problem statement from stakeholder
- ❌ Your own words (that's not a quote)
- ❌ Generic motivational quotes

***

### **summary.html.j2**
**Purpose**: Recap, key takeaways, conclusion slide

**Rules**:
- Use near end of presentation or end of major section
- 3-5 bullet points maximum
- Each bullet: One core takeaway (not details)
- Bullets should echo slides in the section
- Heading: "Key Takeaways" or "Summary" or section-specific

**When to use**:
- ✅ End of presentation (required)
- ✅ End of major section (optional, if section >8 slides)
- ✅ Transition before Q&A
- ❌ Beginning of presentation (use **title.html.j2** or **hero.html.j2**)

**Content rule**: Takeaways should be actionable or memorable, not just repetition

***

### **divider.html.j2**
**Purpose**: Visual break, breath, section transition (lighter than title slide)

**Rules**:
- Text: 1-5 words maximum (section name or transition phrase)
- Minimal visual elements
- Use sparingly: Only when needed for pacing
- Distinct visual treatment (color, graphic, white space)

**When to use**:
- ✅ Brief pause between related topics
- ✅ Signaling shift in perspective or approach
- ✅ "Questions?" slide before Q&A
- ✅ Humor break or palate cleanser
- ❌ Major section transitions (use **title.html.j2**)

**Timing rule**: Use every 6-10 slides to give audience mental break

***

## III. Presentation Structure Rules

### **Opening Sequence** (3-4 slides)
1. **title.html.j2**: Presentation title
2. **hero.html.j2** or **content.html.j2**: Agenda or hook
3. **content.html.j2** or **figure.html.j2**: Problem/context

### **Body Structure** (per major section)
- **title.html.j2**: Section opener
- 4-8 content slides using appropriate layouts
- **summary.html.j2**: Section recap (if section >8 slides)
- Optional **divider.html.j2** before next section

### **Closing Sequence** (2-3 slides)
1. **summary.html.j2**: Key takeaways
2. **hero.html.j2**: Call to action or final message
3. Optional **content.html.j2**: Contact/resources/next steps

***

## IV. Layout Selection Decision Tree

```
START: What is the primary purpose of this slide?

├─ Opening/Transition?
│  ├─ Major section → title.html.j2
│  └─ Minor break → divider.html.j2
│
├─ Making emotional impact?
│  └─ → hero.html.j2
│
├─ Presenting information?
│  ├─ Pure text list? → content.html.j2
│  ├─ Sequential process? → steps.html.j2
│  ├─ Comparing 2-3 things? → comparison.html.j2
│  ├─ Structured data grid? → table.html.j2
│  └─ Text + visual needed?
│     └─ → two-column.html.j2
│
├─ Showing visual evidence?
│  ├─ Simple image/screenshot → figure.html.j2
│  ├─ Wide figure with supporting text → figure-wide.html.j2
│  └─ Complex diagram → diagram.html.j2
│
├─ Demonstrating code/commands?
│  └─ → code.html.j2
│
├─ Supporting with authority?
│  └─ → quote.html.j2
│
└─ Summarizing/concluding?
   └─ → summary.html.j2
```

***

## V. Advanced Layout Usage Rules

### **The 3-Slide Rule**
Never use the same layout for more than 3 consecutive slides (except during dense technical sections where consistency aids comprehension)

### **The Variety Principle**
In a 20-slide deck:
- **content.html.j2**: 6-8 slides (most common)
- **two-column.html.j2**: 3-5 slides
- **figure.html.j2 / figure-wide.html.j2 / diagram.html.j2**: 2-4 slides combined
- **title.html.j2**: 2-3 slides
- **Other layouts**: 1-2 each as needed

### **The Transition Signal**
Changing layout = signaling change in content type or importance
- Same layout = "more of the same"
- Different layout = "pay attention, shift happening"

### **The Simplification Test**
Before choosing a complex layout (diagram, table, comparison):
1. Can this be simplified to content + bullets? → Use simpler layout
2. Does the complexity serve the message? → Proceed with complex layout
3. Will the audience understand in <10 seconds? → Adjust or split

### **The Progressive Disclosure Pattern**
For complex topics, use this sequence:
1. **hero.html.j2**: State the problem/question
2. **content.html.j2**: List the key aspects
3. **two-column.html.j2** or **diagram.html.j2**: Show the solution
4. **summary.html.j2**: Reinforce takeaway

***

## VI. Content-Layout Mapping Rules

| Content Type | Primary Layout | Secondary Option | Avoid |
|--------------|----------------|------------------|-------|
| Features list | content.html.j2 | two-column.html.j2 (with icon/image) | table.html.j2 |
| Architecture | diagram.html.j2 | two-column.html.j2 (mermaid + bullets) | content.html.j2 |
| Process/workflow | steps.html.j2 | two-column.html.j2 (mermaid + content) | content.html.j2 |
| Before/after | comparison.html.j2 | two-column.html.j2 | content.html.j2 |
| Product demo | figure.html.j2 | figure-wide.html.j2 (wide layout), two-column.html.j2 (figure + bullets) | content.html.j2 |
| Data results | table.html.j2 | figure.html.j2 (chart) | content.html.j2 |
| API example | code.html.j2 | two-column.html.j2 (code + explanation) | content.html.j2 |
| User feedback | quote.html.j2 | content.html.j2 (multiple quotes as bullets) | hero.html.j2 |
| Call to action | hero.html.j2 | summary.html.j2 | content.html.j2 |

***

## VII. Accessibility & Readability Rules

**Apply to ALL layouts:**

1. **Minimum font sizes**:
   - Heading: 36pt
   - Body/bullets: 24pt
   - Code: 20pt
   - Captions: 18pt

2. **Color contrast**: Minimum 4.5:1 ratio (text to background)

3. **Alt text**: All figures, diagrams, and code blocks need descriptive alt text

4. **Reading order**: Left-to-right, top-to-bottom (for two-column, left column first)

5. **Maximum line length**: 80 characters (~15-20 words)

***

## VIII. Error Prevention Checklist

Before finalizing any slide, check:

- [ ] Does this slide have ONE clear message?
- [ ] Is the layout the simplest one that works?
- [ ] Are there fewer than 5-7 items/bullets/rows?
- [ ] Can someone understand this in 10 seconds?
- [ ] Does the heading describe the content specifically?
- [ ] Is the text large enough (24pt minimum for body)?
- [ ] Would a visual make this clearer? (If yes, use two-column or figure)
- [ ] Am I using the same layout 4+ times in a row? (If yes, vary)

***

## IX. Meta-Rules for Effective Presentations

1. **Start with content, then choose layout** (not the other way around)
2. **When in doubt, use two-column.html.j2** (most flexible)
3. **Fewer slides with clear messages > more slides with clutter**
4. **Every layout change should be intentional** (signals importance or shift)
5. **Test readability from 10 feet away** (if you can't read it, font too small)
6. **Use templates consistently** (don't customize individual slides)
7. **Respect the 10-second rule** (audience should grasp main point in 10s)

***

## X. Slide copy hygiene (citations, math, Mermaid)

1. **No bracket citations on-slide** — avoid `[23]`, `[42–45]` in bullets, table cells, figure titles, captions, `alt_text`, or hero descriptions. Cite in the paper or speaker notes; on-slide text should be **self-explanatory**.
2. **Math in table cells** — use `$...$` / `$$...$$` in `headers:` / `rows:` strings; the compiler renders them to MathML (same pipeline as slide bodies).
3. **Mermaid labels** — characters like `|` and raw ket notation inside `[square brackets]` confuse Mermaid. Prefer **double-quoted** node text, e.g. `["PQC prepares q, k, v registers"]`.
4. **Markdown bold** — `**word**` only; spaces immediately inside the asterisks break rendering (`** word**` fails).

***

This rulebook ensures your 12 templates work together as a coherent system, guiding you to create presentations that are clear, engaging, and effective for academic and professional contexts.
