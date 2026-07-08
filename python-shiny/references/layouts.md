# Shiny for Python — Layout Patterns

## Page sidebar (most common)

```python
app_ui = ui.page_sidebar(
    ui.sidebar(
        ui.h5("Controls"),
        ui.input_slider("k", "K", 1, 50, 5),
        ui.hr(),
        ui.input_action_button("go", "Run", class_="btn-primary w-100"),
        width=260,
        open="always",   # "always", "desktop", "closed"
    ),
    # Main area content
    ui.output_plot("main_plot", height="600px"),
    title="My App",
    fillable=True,
)
```

## Multi-panel (two plots side by side)

```python
ui.layout_columns(
    ui.card(
        ui.card_header("Graph"),
        ui.output_plot("graph_panel", height="500px"),
        full_screen=True,
    ),
    ui.card(
        ui.card_header("Details"),
        ui.output_plot("detail_panel", height="500px"),
        full_screen=True,
    ),
    col_widths=[7, 5],   # out of 12
)
```

## Auto-wrapping grid

```python
ui.layout_column_wrap(
    ui.card(...),
    ui.card(...),
    ui.card(...),
    width=1/2,       # each card takes ~50% width, wraps to next row
    fill=False,      # don't stretch to fill height
)
```

## Tabbed content

```python
ui.navset_card_underline(
    ui.nav_panel("Plot", ui.output_plot("p")),
    ui.nav_panel("Table", ui.output_table("t")),
    ui.nav_panel("Info", ui.markdown("Some **text**")),
    id="tabs",
)
```

Read active tab: `input.tabs()` in server.

## Accordion in sidebar (grouped controls)

```python
ui.sidebar(
    ui.accordion(
        ui.accordion_panel("Data", ui.input_slider("n", "N", 10, 500, 100)),
        ui.accordion_panel("Display", ui.input_checkbox("show_labels", "Labels")),
        open="Data",   # open panel by default
        multiple=False,
    )
)
```

## Value boxes row

```python
ui.layout_column_wrap(
    ui.value_box("RC Score", ui.output_text("rc"), theme="primary"),
    ui.value_box("Edges", ui.output_text("n_edges"), theme="secondary"),
    ui.value_box("k", ui.output_text("k_val"), theme="info"),
    width=1/3,
    fill=False,
)
```

## Conditional panel

Show/hide based on input without a round-trip to server:

```python
ui.panel_conditional(
    "input.method === 'custom'",   # JavaScript expression
    ui.input_numeric("custom_k", "Custom k", value=5),
)
```

## Full-screen expandable cards

```python
ui.card(
    ui.card_header("My Plot"),
    ui.output_plot("p"),
    full_screen=True,    # adds expand icon in corner
    height="400px",
)
```

## Notification and progress (server-side)

```python
# Temporary notification
ui.notification_show("Done!", type="message", duration=3)

# Progress bar during long computation
with ui.Progress(min=0, max=100) as p:
    for i, item in enumerate(items):
        p.set(i, message=f"Processing {i}/{len(items)}")
        process(item)
```

## Dynamic height for plots

Match plot height to viewport:

```python
# UI
ui.output_plot("plot", height="100%")   # fill container

# Wrap in a fillable card
ui.card(
    ui.output_plot("plot"),
    fill=True,
    height="500px",
)
```

## Converting matplotlib widget apps

When migrating from `matplotlib.widgets` (Slider, Button, RadioButtons):

| matplotlib.widgets | Shiny equivalent |
|---|---|
| `Slider(ax, label, min, max, valinit)` | `ui.input_slider(id, label, min, max, value)` |
| `Button(ax, label)` | `ui.input_action_button(id, label)` |
| `RadioButtons(ax, labels, active)` | `ui.input_radio_buttons(id, label, choices, selected)` |
| `TextBox(ax, label, initial)` | `ui.input_text(id, label, value)` |
| `slider.on_changed(fn)` | `@reactive.effect` depending on `input.slider_id()` |
| `btn.on_clicked(fn)` + `fig.canvas.draw_idle()` | `@reactive.effect` + `@reactive.event(input.btn_id)` |
| `state` dict | `reactive.Value({...})` |
| `plt.show()` | `return fig` inside `@render.plot` |

Key difference: in Shiny there is no explicit "redraw" — outputs automatically re-render when their reactive inputs change.
