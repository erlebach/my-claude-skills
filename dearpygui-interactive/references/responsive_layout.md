# Responsive Layout in Dear PyGui

DearPyGui is an immediate-mode GUI — it has no CSS flexbox or grid. Responsive
behavior requires explicit wiring. This reference documents the patterns that
work and the pitfalls that don't.

## Core principles

1. **Plots and colormaps use `width=-1, height=-1`** to fill their parent
   container. Never hardcode pixel dimensions on `dpg.plot()` or
   `add_colormap_scale` unless you want a fixed, non-resizable layout.

2. **Only the control panel gets a fixed width.** Everything else should derive
   its size from the viewport or from `-1` (fill remaining).

3. **The last sibling in a horizontal group gets `width=-1`.** DPG allocates
   fixed-width siblings first, then gives the remainder to `-1`. This is how
   you make the right-most column fill available space.

4. **Recalculate proportional columns in the render loop.** DPG does not
   re-layout fixed-width children when the viewport resizes. Poll
   `get_viewport_client_width()` each frame and call `configure_item` on
   children whose width should change.

5. **Compute viewport height from content, not round numbers.** Add up the
   actual heights of your content (plot + title + axis labels + chrome) and
   use that as `VIEWPORT_H`. No padding "just in case."

## Recommended column structure

```
viewport
└── primary window (set_primary_window)
    └── group(horizontal=True)                    ← top-level row
        ├── child_window(width=CONTROL_W)         ← fixed
        └── group(horizontal=True)                ← plot area
            ├── child_window(width=computed)       ← left plot col (resized on viewport change)
            │   └── group(horizontal=True)
            │       ├── plot(width=-1, height=-1)
            │       └── colormap_scale(width=50, height=-1)
            └── child_window(width=-1)             ← right plot col (fills remaining)
                └── plot(width=-1, height=-1)
```

## Viewport resize handler

```python
def _on_viewport_resize(self) -> None:
    vw = dpg.get_viewport_client_width()
    rest = vw - PAD - CONTROL_W - 3 * GAP
    new_left = max(280, rest // 2)
    dpg.configure_item("child_plot_left", width=new_left)

def run(self) -> None:
    dpg.show_viewport()
    dpg.set_primary_window("win", True)
    last_vw = dpg.get_viewport_client_width()
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
        vw = dpg.get_viewport_client_width()
        if vw != last_vw:
            last_vw = vw
            self._on_viewport_resize()
        # ... other per-frame work
    dpg.destroy_context()
```

Only the left column needs `configure_item` — the right column has `width=-1`
so DPG automatically gives it whatever is left. The plots inside both columns
have `width=-1, height=-1` so they expand to fill their child_window.

## Vertical sizing

- `autosize_y=True` on plot child windows so they match the tallest content.
- `VIEWPORT_H = PLOT_H + chrome_overhead` — compute, don't guess.
- Move status/info text into the control panel rather than adding a row below
  the plots, which wastes vertical space.

## What doesn't work

| Approach | Why it fails |
|----------|-------------|
| Two `child_window(width=-1)` siblings | First one takes 100% of remaining; second gets 0 |
| `dpg.plot(width=PLOT_W)` with fixed px | Plot doesn't resize when viewport changes |
| Negative width like `width=-300` on child_window | Means "remaining minus 300px", not "300px from right" — confusing and fragile |
| Relying on `autosize_x=True` for plots | Plot may collapse to minimum width or expand unpredictably |

## Horizontal scaling limitations

DPG's layout engine does not support proportional column splits natively.
The render-loop polling pattern handles most resize cases, but rapid or
extreme horizontal resizing may show one frame of stale layout before the
`configure_item` call catches up. This is acceptable for teaching demos;
production dashboards may want to debounce or set a minimum viewport width.

## Asymmetric columns (one plot has a colormap)

When one plot column includes a colormap scale beside it, that column is
wider overall but the plot itself is narrower. Account for the colormap width
when computing the split:

```python
COLORMAP_W = 50
rest = viewport_w - PAD - CONTROL_W - 3 * GAP
left_col = rest // 2              # contains plot + colormap
right_col = rest - left_col        # contains plot only
# The plot inside the left column gets: left_col - COLORMAP_W - frame_pad
# The plot inside the right column gets: right_col - frame_pad
# But with width=-1 on the plots, this happens automatically.
```

With `width=-1` on both plots, DPG handles the internal split — the left
plot shares its child_window with the colormap, so it gets less space
automatically.
