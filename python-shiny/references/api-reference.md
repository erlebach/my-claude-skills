# Shiny for Python — API Reference

## Inputs (ui.input_*)

| Function | Key args | Returns |
|---|---|---|
| `input_slider(id, label, min, max, value, step)` | `step=1`, `ticks=False` | int/float |
| `input_numeric(id, label, value, min, max, step)` | | int/float |
| `input_text(id, label, value, placeholder)` | | str |
| `input_text_area(id, label, value, rows)` | | str |
| `input_select(id, label, choices, selected, multiple)` | `choices` can be list or dict | str/list |
| `input_selectize(id, label, choices, selected, multiple)` | searchable dropdown | str/list |
| `input_radio_buttons(id, label, choices, selected)` | | str |
| `input_checkbox(id, label, value)` | | bool |
| `input_checkbox_group(id, label, choices, selected)` | | list[str] |
| `input_switch(id, label, value)` | modern toggle | bool |
| `input_action_button(id, label, class_)` | `class_="btn-primary"` | int (click count) |
| `input_action_link(id, label)` | | int |
| `input_date(id, label, value, min, max)` | value as "YYYY-MM-DD" | date str |
| `input_date_range(id, label, start, end)` | | dict with start/end |
| `input_file(id, label, accept, multiple)` | | list of file dicts |
| `input_password(id, label, value)` | | str |

## Outputs (ui.output_*)

| Function | Paired render decorator |
|---|---|
| `output_plot(id, width, height)` | `@render.plot` |
| `output_text(id)` | `@render.text` |
| `output_text_verbatim(id)` | `@render.text` |
| `output_ui(id)` | `@render.ui` |
| `output_table(id)` | `@render.table` (returns DataFrame) |
| `output_data_frame(id)` | `@render.data_frame` (returns DataFrame, sortable) |
| `output_image(id)` | `@render.image` (returns dict with src) |

## Render decorators (server-side)

```python
@render.plot(alt="description")   # optional alt text for accessibility
def my_plot():
    fig, ax = plt.subplots()
    return fig

@render.text
def my_text():
    return "hello"

@render.ui
def dynamic_ui():
    return ui.div(ui.p("content"), class_="my-class")

@render.table
def my_table():
    return pd.DataFrame({"a": [1, 2], "b": [3, 4]})

@render.data_frame
def my_df():
    return render.DataGrid(df, filters=True, editable=False)

@render.image
def my_image():
    return {"src": "/path/to/img.png", "alt": "description"}
```

## Reactive primitives

```python
# Mutable state
v = reactive.Value(initial)
v()          # read
v.set(new)   # write
v.get()      # same as v()

# Computed (cached, lazy)
@reactive.calc
def computed():
    return expensive(input.x())

computed()   # returns cached result, recomputes when deps change

# Side effects
@reactive.effect
def effect():
    x = input.x()   # runs whenever x changes

@reactive.effect
@reactive.event(input.btn)   # only runs when btn clicked
def on_click():
    ...

# Isolate a read (prevent dependency tracking)
with reactive.isolate():
    val = some_reactive()

# Invalidate / trigger manually
reactive.invalidate_later(5)   # re-run context after 5 seconds
```

## Session utilities

```python
# In server(input, output, session):
session.close()                        # close the session
await session.send_custom_message(...)  # send JS message
session.on_ended(callback)             # cleanup callback

# Notifications
ui.notification_show("message", type="message")  # "message","warning","error"
ui.notification_remove(id)

# Modals
ui.modal_show(ui.modal("content", title="Title"))
ui.modal_remove()
```

## Module pattern (for reusable components)

```python
# Define
def my_module_ui(id):
    return ui.TagList(
        ui.input_slider(f"{id}-k", "K", 1, 50, 5),
        ui.output_plot(f"{id}-plot"),
    )

def my_module_server(id, data):
    def server(input, output, session):
        @render.plot
        def plot():
            return make_plot(data(), input.k())
    return server

# Use
# ui side
my_module_ui("mod1")

# server side  
module_server = my_module_server("mod1", reactive_data)
```

For cleaner module syntax use `@module.ui` / `@module.server` decorators (shiny >= 0.6).

## Theming

```python
from shiny import ui
from shiny.ui import Theme  # shiny >= 0.10

app_ui = ui.page_sidebar(
    ...,
    theme=ui.Theme("bootstrap"),          # default Bootstrap
    # theme=ui.Theme("cosmo"),            # Bootswatch themes
)
```

Or use `shinyswatch` package for Bootswatch:
```python
import shinyswatch
theme=shinyswatch.theme.darkly()
```
