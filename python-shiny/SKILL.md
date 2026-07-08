---
name: python-shiny
description: Build interactive Python web apps using the Shiny for Python framework (shiny package). Use this skill when creating or converting Python apps to Shiny, working with reactive inputs/outputs, building dashboards with matplotlib/plotly/networkx visualizations, structuring ui/server patterns, handling reactive state, or using shiny's page_sidebar, layout_columns, cards, or input widgets. Also use when the user mentions `shiny run`, `App()`, `@render.plot`, `reactive.Value`, or is converting a matplotlib-widget or ipywidgets app to a web UI. Trigger even if the user just says "shiny" in a Python project context.
---

# Shiny for Python

Build interactive web apps in Python with the `shiny` package. The API mirrors R Shiny but uses Python idioms — decorators instead of `render*()` calls, `reactive.Value` instead of `reactiveVal`, etc.

## Quick start

```python
from shiny import App, ui, render, reactive

app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.input_slider("n", "N", min=1, max=100, value=50),
    ),
    ui.output_plot("hist"),
    title="My App",
)

def server(input, output, session):
    @render.plot
    def hist():
        import matplotlib.pyplot as plt
        import numpy as np
        fig, ax = plt.subplots()
        ax.hist(np.random.randn(input.n()))
        return fig

app = App(app_ui, server)
```

Run with: `shiny run app.py`  
Auto-reload: `shiny run --reload app.py`

## UI layout

### Page types

```python
ui.page_sidebar(sidebar=..., *args, title="...")   # sidebar + main area
ui.page_navbar(*nav_panels, title="...")            # top nav bar
ui.page_fillable(*args)                             # fills viewport
ui.page_fluid(*args)                               # scrolling layout
```

### Columns and cards

```python
ui.layout_columns(col1, col2, col_widths=[6, 6])   # 12-col Bootstrap grid
ui.layout_column_wrap(width=1/2, *items)            # auto-wrapping grid

ui.card(
    ui.card_header("Title"),
    ui.output_plot("my_plot"),
    full_screen=True,
)
```

### Sidebar

```python
ui.sidebar(
    ui.input_slider(...),
    ui.input_select(...),
    ui.input_action_button("go", "Run", class_="btn-primary w-100"),
    width=250,
)
```

### Common inputs

```python
ui.input_slider("k", "K neighbors", min=1, max=50, value=5, step=1)
ui.input_select("method", "Method", choices=["kmeans", "dbscan"])
ui.input_radio_buttons("pair", "Pair", choices=["A vs B", "A vs C"])
ui.input_checkbox("show", "Show labels", value=True)
ui.input_numeric("n", "N points", value=100, min=10, max=1000)
ui.input_action_button("regen", "Regenerate")
ui.input_text("query", "Search", placeholder="enter text")
```

### Common outputs

```python
ui.output_plot("plot_id")
ui.output_text("text_id")
ui.output_text_verbatim("text_id")
ui.output_table("table_id")
ui.output_ui("dynamic_ui_id")
```

## Server and reactivity

### Reading inputs

Access inputs by calling them — they are callables, not attributes:

```python
k = input.k()          # current slider value
pair = input.pair()    # current radio selection
```

### Render decorators

```python
@render.plot
def my_plot():
    fig, ax = plt.subplots()
    ax.plot([1, 2, 3], [input.n(), 2, 3])
    return fig          # return the figure object

@render.text
def my_text():
    return f"Selected: {input.pair()}"

@render.table
def my_table():
    return pd.DataFrame(...)

@render.ui
def dynamic():
    return ui.p(f"Value is {input.k()}")
```

The function name must match the `output_*("id")` id in the UI.

### Reactive state

```python
# Mutable reactive value (like R's reactiveVal)
count = reactive.Value(0)

@reactive.effect
@reactive.event(input.btn)   # only fires when btn is clicked
def _increment():
    count.set(count() + 1)

# Computed reactive (like R's reactive({}))
@reactive.calc
def filtered_data():
    return df[df["k"] == input.k()]
```

`reactive.Value` holds mutable state. Read it by calling `val()`, write it with `val.set(new)`.

`@reactive.calc` caches a derived computation; re-runs only when dependencies change.

`@reactive.event(input.x)` isolates a reactive from running until `input.x` changes — essential for action buttons.

### Isolating reads

```python
with reactive.isolate():
    current = some_value()   # read without creating a dependency
```

## Matplotlib in Shiny

**Always set a non-interactive backend** at the top of the file:

```python
import matplotlib
matplotlib.use("Agg")   # must come before pyplot import
import matplotlib.pyplot as plt
```

Return the `Figure` object from `@render.plot`, not `plt.show()`:

```python
@render.plot
def plot():
    fig, ax = plt.subplots(figsize=(10, 6))
    ax.scatter(x, y)
    fig.tight_layout()
    return fig          # correct — return figure
    # plt.show()        # wrong — do not call this
```

Close figures you don't return to avoid memory leaks in long-running apps:
```python
plt.close("all")   # if rebuilding figures on each render
```

## Plotly and other renderers

```python
from shiny import render as shiny_render
from shinywidgets import output_widget, render_widget   # pip install shinywidgets
import plotly.express as px

# UI
ui.output_widget("plotly_chart")   # not output_plot

# Server
@render_widget
def plotly_chart():
    return px.scatter(df, x="x", y="y")
```

For plain plotly (no shinywidgets), render as an image or use `render.ui` with `plotly.io.to_html`.

## Patterns

### Button-triggered regeneration

```python
_data = reactive.Value(generate_data(seed=42))

@reactive.effect
@reactive.event(input.regen)
def _regen():
    _data.set(generate_data(seed=None))

@render.plot
def plot():
    X = _data()          # reactive dependency on the data
    k = input.k()
    ...
```

### Shared computed graph

```python
@reactive.calc
def graph():
    X = _data()
    P = create_proximity_matrix(X)
    k = _clamp_k(input.k(), len(X))
    return create_graph_from_matrix(X, sparsify_knn(P, k))

@render.plot
def left_panel():
    G = graph()   # cached — not recomputed for right panel
    ...

@render.plot
def right_panel():
    G = graph()   # same cached value
    ...
```

### Dynamic UI based on input

```python
@render.ui
def cluster_controls():
    n = input.n_clusters()
    return ui.TagList(*[
        ui.input_color(f"color_{i}", f"Cluster {i} color")
        for i in range(n)
    ])
```

## Value boxes (metrics display)

```python
from shiny import ui

ui.value_box(
    title="RC Score",
    value=ui.output_text("rc_val"),
    theme="primary",
)
```

## File structure for multi-file apps

```
app/
├── app.py          # App(app_ui, server) entry point
├── ui.py           # ui definition
├── server.py       # server function
└── utils.py        # computation helpers
```

Import cleanly:
```python
# app.py
from ui import app_ui
from server import server
from shiny import App
app = App(app_ui, server)
```

## Common mistakes

| Mistake | Fix |
|---|---|
| `input.k` (missing `()`) | `input.k()` — inputs are callables |
| `plt.show()` in render | Return `fig` instead |
| Missing `matplotlib.use("Agg")` | Add before `import matplotlib.pyplot` |
| `reactive.Value` read without `()` | `val()` not `val` |
| `@render.plot` id mismatch | Function name must equal `output_plot("id")` string |
| Modifying `reactive.Value` in a `@reactive.calc` | Use `@reactive.effect` for side effects |

## Reference files

- [api-reference.md](references/api-reference.md) — Full input/output/render API reference
- [layouts.md](references/layouts.md) — Detailed layout patterns and examples
