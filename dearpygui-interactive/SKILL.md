---
name: dearpygui-interactive
description: Build interactive Dear PyGui (DPG) applications with ImPlot visualizations and drawlist graphics driven by sliders, text inputs, and other widgets. Use this skill whenever the user wants to create or modify a DearPyGui app, add interactive controls to plots, style markers/lines dynamically, or debug DPG theme/rendering issues. Also use it when the user mentions dearpygui, dpg, ImPlot scatter/line/bar styling, or interactive Python visualization demos.
---

# Dear PyGui Interactive Visualizations

This skill helps you build Dear PyGui applications where widgets (sliders, text boxes, checkboxes) drive visual properties of plots and drawn shapes in real time. DearPyGui wraps two distinct rendering subsystems — **drawlist primitives** and **ImPlot series** — and they require different update strategies. Getting this wrong produces silent failures (sliders move, nothing changes on screen).

Read `references/mwe_scatter_style.py` (in-repo: `mwe_dpg_scatter_style.py`) for the canonical working example before writing any DPG code. It demonstrates both subsystems side by side.

## Two subsystems, two update paths

### Drawlist primitives (`draw_circle`, `draw_line`, `draw_triangle`, etc.)

These support direct property mutation via `configure_item`:

```python
dpg.configure_item(tag, fill=(r, g, b, a), radius=new_radius, color=(0, 0, 0, a))
```

This is the simpler path. Tag each primitive at creation, then call `configure_item` in slider callbacks. No themes needed.

### ImPlot series (`add_scatter_series`, `add_line_series`, `add_bar_series`, etc.)

ImPlot series do **not** support `configure_item(..., fill=...)`. All styling goes through **themes**. The update pattern has three parts that must all be present:

1. **Tagged theme children** — give explicit `tag=` to every `add_theme_color` and `add_theme_style` inside the theme so you can address them later with `set_value`.

2. **`set_value` on theme children** — update colors, sizes, and style vars by calling `dpg.set_value("tag_name", [values])`.

3. **Touch the series data** — after updating theme values, call `dpg.set_value("series_tag", [xs, ys])` with the same data. This forces ImPlot to invalidate its cache and redraw with the new style. Without this step, the plot will not update.

Skip any of these three and the update silently fails.

## Theme setup pattern

Always use `category=dpg.mvThemeCat_Plots` for ImPlot theme entries. Without it, DPG may apply the style in the wrong category and nothing changes.

```python
with dpg.theme(tag="my_theme"):
    with dpg.theme_component(dpg.mvScatterSeries):  # match your series type
        dpg.add_theme_color(
            dpg.mvPlotCol_MarkerFill, [r, g, b, alpha],
            category=dpg.mvThemeCat_Plots, tag="tc_fill"
        )
        dpg.add_theme_color(
            dpg.mvPlotCol_MarkerOutline, [0, 0, 0, alpha],
            category=dpg.mvThemeCat_Plots, tag="tc_outline"
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_MarkerSize, 14.0,
            category=dpg.mvThemeCat_Plots, tag="ts_size"
        )
        dpg.add_theme_style(
            dpg.mvPlotStyleVar_FillAlpha, 0.5,
            category=dpg.mvThemeCat_Plots, tag="ts_alpha"
        )
```

Bind it once after creating the series:

```python
dpg.bind_item_theme("series_tag", "my_theme")
```

## Opacity: use RGBA, not just FillAlpha

Many DPG/ImPlot backends ignore `mvPlotStyleVar_FillAlpha` for scatter markers. Encode opacity in the **A channel** of `mvPlotCol_MarkerFill` and `mvPlotCol_MarkerOutline` directly. Set `FillAlpha` too as a belt-and-suspenders measure, but rely on the RGBA values:

```python
def alpha_u8(fraction: float) -> int:
    return int(max(0, min(255, round(255.0 * fraction))))

a = alpha_u8(slider_value)
dpg.set_value("tc_fill", [r, g, b, a])
dpg.set_value("tc_outline", [0, 0, 0, a])
dpg.set_value("ts_alpha", [float(slider_value), float(slider_value)])
```

## Slider callback pattern

Wire sliders to a single callback that reads all control values and pushes them to both subsystems:

```python
dpg.add_slider_float(
    label="MarkerSize", tag="slider_size",
    default_value=14.0, min_value=4.0, max_value=40.0,
    callback=lambda *_: on_slider_change()
)

def on_slider_change() -> None:
    sz = float(dpg.get_value("slider_size"))
    op = float(dpg.get_value("slider_opacity"))
    apply_drawlist(sz, op)      # configure_item on tagged primitives
    apply_implot(sz, op)        # set_value on theme children + touch series
```

Using `lambda *_:` avoids issues with DPG passing sender/app_data args you don't need.

## Reset view (fit data) — required control

Every Dear PyGui + ImPlot teaching or demo app **must** include a **Reset view** (aka **fit data**) button in the control panel. It re-applies axis limits so all current series are visible again after the user has panned or zoomed.

**Why:** Calling `dpg.set_axis_limits` inside every data refresh (especially when **data-generation sliders** change `X`) resets ImPlot's pan/zoom and feels broken. **Style-only** sliders (marker size, alpha) must not touch axis limits either if they share the same callback pattern—only push themes/series.

**Policy:**
- **First** time the app has real data, compute limits once so the data bbox fills ~**90%** of each axis span (symmetric margin), then `set_axis_limits` on every plot axis. That matches "whole cloud visible" defaults.
- On later **data** slider moves, **do not** call `set_axis_limits`; keep min/max fixed so the user can pan/zoom freely. Re-apply limits **only** when the user clicks **Reset view** (recompute from current `X` with the same ~90% rule).
- Track this with a boolean (e.g. `_initial_implot_axis_fit_done`) set after the first fit; **Reset view** always calls your refit helper regardless.

**Pattern:**
- One function, e.g. `refit_implot_axes_to_current_data()`, reads current point arrays, computes `(xmin, xmax, ymin, ymax)` (90% fill or your margin policy), then `dpg.set_axis_limits` per axis tag.
- A full-width button wired to that function:

```python
dpg.add_button(
    label="Reset view (fit all data)",
    tag="btn_reset_view",
    callback=lambda *_: refit_implot_axes_to_current_data(),
    width=-1,
)
```

Place **Reset view** directly under the **Global** header (after any Global sliders). If the control column is taller than the plot stack, put the **entire Global block (and optionally Metrics) at the top** of the panel so it stays visible without relying on scrollbars. For the remaining controls inside a **fixed-height** cell, use a ``child_window`` with ``no_scrollbar=False`` (vertical scrollbar when content is taller than the cell), ``horizontal_scrollbar=True`` (so long labels or wide widgets stay reachable in a narrow column), and ``flattened_navigation=False``. Prefer Dear PyGui's native scrollbars here instead of custom ``set_item_pos`` / drag-to-pan logic unless the user explicitly asks for it.

## Layout: controls left, plots side by side

For the full responsive layout reference (resize handling, what works and what
doesn't, asymmetric columns), read `references/responsive_layout.md`.

The default layout for apps with a control panel and two plots is:

```
┌──────────┬───────────────────────────────┐
│ Controls │  Plot A        │  Plot B      │
│ (narrow) │  (equal width) │  (equal w.)  │
│          │                │              │
└──────────┴───────────────────────────────┘
```

Achieve this with nested `dpg.group(horizontal=True)`:

```python
with dpg.window(label="Main", tag="win"):
    with dpg.group(horizontal=True):
        # Left column: controls (fixed width via child_window)
        with dpg.child_window(width=280, autosize_y=True):
            # radio buttons, sliders, combos, status text ...
            pass

        # Right area: plots side by side
        with dpg.group(horizontal=True):
            with dpg.plot(tag="plot_a", width=PLOT_W, height=PLOT_H):
                ...
            with dpg.plot(tag="plot_b", width=PLOT_W, height=PLOT_H):
                ...
```

Key rules:
- **Plots go in the same horizontal group.** If each plot is in its own vertical group or child_window without `horizontal=True` on the parent, DPG stacks them vertically.
- **Plots must fill all available width — zero dead space.** Divide the remaining width into two equal columns. If one column contains a colormap scale, subtract the colormap width from that column's plot, not from both. The other column's plot gets its full width:
  ```python
  COLORMAP_W = 50; GAP = 6; PAD = 24; FRAME_PAD = 18
  rest = VIEWPORT_W - PAD - CONTROL_PANEL_W - 3 * GAP
  COL_LEFT = rest // 2          # holds plot + colormap
  COL_RIGHT = rest - COL_LEFT   # holds plot only
  PLOT_W_LEFT  = COL_LEFT  - FRAME_PAD - COLORMAP_W
  PLOT_W_RIGHT = COL_RIGHT - FRAME_PAD
  PLOT_H = min(PLOT_W_LEFT, PLOT_W_RIGHT)  # square, matched height
  ```
  Verify: `CONTROL_PANEL_W + COL_LEFT + COL_RIGHT + 3*GAP + PAD == VIEWPORT_W`.
- **Tight viewport height — no dead space below.** Compute `VIEWPORT_H` from content, not a round number.
- **Responsive plots with `width=-1, height=-1`.** Fixed pixel sizes on `dpg.plot()` don't resize when the user drags the window. Use `width=-1` and `height=-1` so the plot fills its parent container. Also use `height=-1` on `add_colormap_scale` so it matches the plot height automatically.
- **Responsive column layout.** Give the last plot `child_window` `width=-1` (fill remaining). In the render loop, poll `get_viewport_client_width()` and recalculate the first plot column's width with `configure_item` when it changes:
  ```python
  last_vw = dpg.get_viewport_client_width()
  while dpg.is_dearpygui_running():
      dpg.render_dearpygui_frame()
      vw = dpg.get_viewport_client_width()
      if vw != last_vw:
          last_vw = vw
          rest = vw - PAD - CONTROL_W - 3 * GAP
          dpg.configure_item("child_plot_left", width=max(280, rest // 2))
  ```
- **Use `child_window` for the control column** with a fixed `width=` so it does not stretch. Let plots fill the remaining space. When the control stack may overflow, set `no_scrollbar=False` and `horizontal_scrollbar=True` on that `child_window` so users can scroll **vertically and horizontally** without clipping (aligns with `python-gui-design-review`).
- **Plot cells:** If each ImPlot is wrapped in its own `child_window`, set **`no_scroll_with_mouse=True`** on **plot** `child_window`s (not on the scrollable control column). Otherwise the child often **captures the mouse wheel** and **trackpad scroll never reaches ImPlot**, so zoom appears broken. Scroll wheel / two-finger scroll zooms when the plot receives the event.
- **Colormap scale beside the plot, not inside it.** `add_colormap_scale` placed inside a `dpg.plot()` context renders below the plot axes. Instead, place the plot and colormap scale as siblings in a `dpg.group(horizontal=True)`:
  ```python
  with dpg.group(horizontal=True):
      with dpg.plot(tag="plot_d", width=PLOT_W - 60, height=PLOT_H):
          ...  # axes, series
      dpg.add_colormap_scale(label="density", tag="cms",
                             width=50, height=PLOT_H, ...)
  ```
- **Plot legends go in a corner, not centered on an edge.** Use `location=dpg.mvPlot_Location_NorthWest` or `NorthEast`, not `East` or `West` alone — edge-centered legends span the full plot height and obscure data. Keep `outside=False` and `horizontal=False` for a compact box.

## Layout variant: three plots in a 2-by-2 grid

Some teaching apps need **three** ImPlot panels (e.g. true labels, K-means, DBSCAN). A workable pattern: **top row** — two plots side by side in one `horizontal=True` group, each inside a fixed-size `child_window`; **bottom row** — `horizontal=True` group with a **scrollable** control `child_window` (left) and the third plot `child_window` (right, `width=-1` to fill). Use the same scrollbar settings as above for the control cell.

---

## Coding conventions

- **Reset view (fit data) button** — every ImPlot app must include a full-width control that refits axis limits to current data without repushing style-only state; see section *Reset view (fit data) — required control*.
- **Tag everything you will update at runtime.** Unnamed items cannot be addressed later.
- **Keep theme container tags for `bind_item_theme`.** The string passed to `dpg.theme(tag=...)` is the second argument to `dpg.bind_item_theme(item, theme_tag)` (plot, line series, scatter series). Tagged *children* are only for `set_value`. Dropping the container tag from your code while still calling `bind_item_theme` raises `AttributeError` at startup — a wiring bug, not a Dear PyGui quirk.
- **Named constants for layout and color** (`DRAW_W`, `DRAW_H`, `FILL_RGB`, etc.) — no magic numbers.
- **Small, single-purpose functions** — one function to build each panel, one to apply updates per subsystem, one callback that reads controls and dispatches.
- **Single source of truth for shared data** — if both panels show the same points, define `XS`/`YS` once at module level.
- **Google-style docstrings** on functions with non-obvious contracts (coordinate transforms, alpha conversions).

## App skeleton

```python
import dearpygui.dearpygui as dpg

def main() -> None:
    dpg.create_context()
    create_themes()          # themes before any UI that references them
    dpg.create_viewport(title="My App", width=900, height=520)
    build_ui()               # windows, controls, plots
    dpg.setup_dearpygui()
    initialize_display()     # fire callbacks once to set initial state
    dpg.show_viewport()
    dpg.set_primary_window("win", True)
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    dpg.destroy_context()

if __name__ == "__main__":
    main()
```

Create themes **before** `build_ui` so `bind_item_theme` can reference them. Call the update functions once **after** `setup_dearpygui` so the initial display matches slider defaults.

## Application theming (UI + ImPlot together)

Real apps need **two coordinated layers**:

1. **Global Dear PyGui chrome** — one theme per visual preset using
   ``dpg.theme_component(dpg.mvAll)`` and ``dpg.add_theme_color`` for
   ``mvThemeCol_WindowBg``, ``ChildBg``, ``FrameBg``, ``Text``, ``TextDisabled``,
   ``SliderGrab``, ``SliderGrabActive``, ``CheckMark``, ``Border``, ``Separator``.
   Apply with ``dpg.bind_theme(theme_container_tag)``. Match the viewport with
   ``dpg.configure_viewport(0, clear_color=(r, g, b, a))`` (same RGB as window
   background) so letterboxing does not flash light gray.

2. **ImPlot** — unchanged rules: ``category=dpg.mvThemeCat_Plots``, tagged
   children, ``set_value`` + series data touch. Extend the plot-bound theme
   (``theme_component(dpg.mvPlot)``) beyond ``mvPlotCol_PlotBg`` to legend and
   axes when you want dark-mode legends and gridlines:
   ``mvPlotCol_LegendBg``, ``mvPlotCol_LegendText``, ``mvPlotCol_AxisText``,
   ``mvPlotCol_AxisGrid``, ``mvPlotCol_PlotBorder`` (all with explicit ``tag=``
   if you switch presets at runtime).

**Default preset (Modern Dark)** — good baseline for teaching / slides; example
hex anchors: window ``#1A1A1E``, accent ``#4A90E2``, primary text ``#D1D1D1``,
plot face a few steps darker than the window, edges/nodes from a small graph
palette (see ``example1_shared_neighbor_pygui.py``: ``Modern Dark``, plus
``Solarized Dark``, ``High Contrast``, ``Light`` for flexibility).

Implement presets as immutable bundles (e.g. dataclass: UI colors + graph
palette). On combo change: ``bind_theme`` → ``set_value`` on all tagged ImPlot
chrome + line theme colors → mark plot dirty / ``refresh`` so scatter markers
and series data pick up the new palette.

**Selecting a theme at launch:** The default theme is **Modern Dark**. Users can
request a different default via chat (e.g. “start in Light mode”) or pass
``--theme light`` on the command line. The app should also include an in-app
**Theme** combo/dropdown so the user can switch at runtime without restarting.

### Built-in theme presets

Both presets must meet **WCAG 2.1 AA contrast requirements** (4.5:1 for normal
text, 3:1 for large text and UI components like slider tracks/grabs).

**Modern Dark** (default):

| Element | Color | Hex |
|---------|-------|-----|
| Window / viewport background | near-black | `#1A1A1E` |
| Primary text | light gray | `#D1D1D1` |
| Disabled / secondary text | mid gray | `#8A8A8A` |
| Accent (slider grab, active) | muted blue | `#4A90E2` |
| Frame background (sliders, inputs) | dark gray | `#2D2D32` |
| Border / separator | subtle gray | `#3A3A40` |
| Plot background | slightly darker than window | `#141418` |
| Plot axis text / grid | `#8A8A8A` / `#2D2D32` | |
| Legend background | `#1E1E24` | |

Contrast check: `#D1D1D1` on `#1A1A1E` = ~11.5:1; `#8A8A8A` on `#1A1A1E` = ~4.7:1. Both pass AA.

**Light**:

| Element | Color | Hex |
|---------|-------|-----|
| Window / viewport background | off-white | `#F5F5F0` |
| Primary text | near-black | `#1A1A1E` |
| Disabled / secondary text | dark gray | `#5A5A5A` |
| Accent (slider grab, active) | deeper blue | `#2B6CB0` |
| Frame background (sliders, inputs) | light gray | `#E0E0DA` |
| Border / separator | medium gray | `#C0C0BA` |
| Plot background | white | `#FAFAF5` |
| Plot axis text / grid | `#5A5A5A` / `#E0E0DA` | |
| Legend background | `#EDEDEA` | |

Contrast check: `#1A1A1E` on `#F5F5F0` = ~15.6:1; `#5A5A5A` on `#F5F5F0` = ~5.5:1; `#2B6CB0` on `#E0E0DA` = ~4.6:1. All pass AA.

---

## Version sensitivity

DearPyGui's ImPlot integration is brittle across versions. The patterns in this skill are verified with the version currently in the project's `pyproject.toml`. If behavior breaks after a `dearpygui` upgrade (sliders move but plot doesn't change), compare against the reference MWE before debugging further — the API may have shifted underneath you.

## Common failure modes

| Symptom | Likely cause |
|---------|-------------|
| Slider moves, plot unchanged | Missing series data touch (`set_value` on series after theme update) |
| Pan/zoom resets when data sliders move | `set_axis_limits` runs inside every data rebuild; limit refit to first load + **Reset view** only |
| Theme has no effect | Missing `category=dpg.mvThemeCat_Plots` on theme entries |
| Opacity slider does nothing | Using only `FillAlpha` style var; encode alpha in RGBA instead |
| `configure_item` error on scatter | Scatter series don't support `configure_item` for style; use themes |
| Theme works initially but not on update | Theme children lack `tag=`; cannot be addressed by `set_value` |
| `AttributeError` for missing theme at startup | `bind_item_theme` still uses a removed variable; keep the **container** theme tag as a named constant or field |
| Two plots stacked vertically instead of side by side | Plots are not inside the same `dpg.group(horizontal=True)`; each plot in its own vertical group forces stacking |
| Control panel clips sliders or help text | `child_window` uses `no_scrollbar=True` or omits `horizontal_scrollbar=True` when content exceeds the cell |
| ImPlot zoom / scroll does nothing | Plot is inside a `child_window` that steals wheel events; set `no_scroll_with_mouse=True` on the **plot** cell only |
| Large empty space beside plots | Viewport wider than controls + plots; compute `PLOT_W` from available width or size viewport to fit |
| Colormap scale appears below plot | `add_colormap_scale` inside `dpg.plot()` context; move it outside as a sibling in a `horizontal=True` group |
| Legend covers data / spans full plot height | Using edge location (`East`/`West`); switch to corner (`NorthEast`/`NorthWest`) |

## Line series and bar series

The same tagged-theme + data-touch pattern applies. Change `dpg.mvScatterSeries` to `dpg.mvLineSeries` or `dpg.mvBarSeries` in `theme_component`, and use the corresponding style vars:

- **Line**: `mvPlotCol_Line`, `mvPlotStyleVar_LineWeight`
- **Bar**: `mvPlotCol_Fill`, `mvPlotCol_Line`

The data-touch step (`set_value` on the series) is needed for all ImPlot series types.
