"""Minimal Dear PyGui demo: marker **size** and **opacity** from sliders.

Two panels side by side:

1. **Drawlist + ``configure_item``** (panel A): tagged ``draw_circle`` items;
   the slider callback updates ``fill`` / outline ``color`` and ``radius``
   directly.

2. **ImPlot scatter + theme** (panel B): series ``sc_reb`` uses theme
   ``th_rebuild`` (``bind_item_theme``). On each slider change,
   ``apply_rebuild`` runs ``set_value`` on **tagged** theme children
   (fill/outline RGBA, marker size, fill-alpha style) and then ``set_value``
   on ``sc_reb`` with the same ``x``/``y`` to nudge ImPlot to redraw.

Run::

    uv run --project ../../ python mwe_dpg_scatter_style.py

"""

from __future__ import annotations

import dearpygui.dearpygui as dpg

# ---------------------------------------------------------------------------
# Shared data
# ---------------------------------------------------------------------------
XS: list[float] = [0.0, 1.0, 2.0, 0.5, 1.5]
YS: list[float] = [0.0, 1.0, 0.0, 1.2, 0.3]

# ---------------------------------------------------------------------------
# Layout constants
# ---------------------------------------------------------------------------
DRAW_W: int = 420
DRAW_H: int = 320
PAD: float = 36.0

X_MIN, X_MAX = -0.25, 2.25
Y_MIN, Y_MAX = -0.15, 1.35

# ---------------------------------------------------------------------------
# Color constants (RGB; alpha comes from slider)
# ---------------------------------------------------------------------------
MUT_FILL_RGB = (200, 60, 60)   # left panel (drawlist)
REB_FILL_RGB = (60, 200, 60)   # right panel (ImPlot)

MUT_CIRC_TAGS = [f"mut_circ_{i}" for i in range(len(XS))]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def alpha_u8(fraction: float) -> int:
    """Clamp fraction to [0,1] and return 8-bit alpha."""
    return int(max(0, min(255, round(255.0 * fraction))))


def data_to_canvas(x: float, y: float) -> tuple[float, float]:
    """Map data coords to drawlist pixel coords (y-up -> y-down)."""
    u = (x - X_MIN) / (X_MAX - X_MIN)
    v = (y - Y_MIN) / (Y_MAX - Y_MIN)
    px = PAD + u * (DRAW_W - 2.0 * PAD)
    py = DRAW_H - PAD - v * (DRAW_H - 2.0 * PAD)
    return (px, py)


# ---------------------------------------------------------------------------
# Panel A: drawlist
# ---------------------------------------------------------------------------
def add_left_drawlist_with_markers() -> None:
    dpg.add_text("A: drawlist + configure_item")
    with dpg.drawlist(width=DRAW_W, height=DRAW_H):
        dpg.draw_line((PAD, DRAW_H - PAD), (DRAW_W - PAD, DRAW_H - PAD),
                       color=(140, 140, 140, 200), thickness=1.0)
        dpg.draw_line((PAD, PAD), (PAD, DRAW_H - PAD),
                       color=(140, 140, 140, 200), thickness=1.0)
        for i in range(len(XS)):
            cx, cy = data_to_canvas(XS[i], YS[i])
            dpg.draw_circle((cx, cy), 7.0, tag=MUT_CIRC_TAGS[i],
                            color=(0, 0, 0, 128), fill=(200, 60, 60, 128),
                            thickness=1.0)


def apply_drawlist_circles(size: float, opacity: float) -> None:
    r, g, b = MUT_FILL_RGB
    a = alpha_u8(opacity)
    rad = max(1.0, float(size) * 0.5)
    for i, tag in enumerate(MUT_CIRC_TAGS):
        cx, cy = data_to_canvas(XS[i], YS[i])
        dpg.configure_item(tag, center=(cx, cy), radius=rad,
                           fill=(r, g, b, a), color=(0, 0, 0, a),
                           thickness=1.0)


# ---------------------------------------------------------------------------
# Panel B: ImPlot scatter + theme
# ---------------------------------------------------------------------------
def create_initial_rebuild_theme() -> None:
    r, g, b = REB_FILL_RGB
    a0 = alpha_u8(0.5)
    with dpg.theme(tag="th_rebuild"):
        with dpg.theme_component(dpg.mvScatterSeries):
            dpg.add_theme_color(dpg.mvPlotCol_MarkerFill, [r, g, b, a0],
                                category=dpg.mvThemeCat_Plots, tag="tc_fill")
            dpg.add_theme_color(dpg.mvPlotCol_MarkerOutline, [0, 0, 0, a0],
                                category=dpg.mvThemeCat_Plots, tag="tc_outline")
            dpg.add_theme_style(dpg.mvPlotStyleVar_MarkerSize, 14.0,
                                category=dpg.mvThemeCat_Plots, tag="ts_size")
            dpg.add_theme_style(dpg.mvPlotStyleVar_FillAlpha, 0.5,
                                category=dpg.mvThemeCat_Plots, tag="ts_alpha")


def add_right_implot_panel() -> None:
    with dpg.plot(label="B: ImPlot + theme", tag="plot_reb",
                  width=DRAW_W, height=DRAW_H, equal_aspects=True):
        dpg.add_plot_legend()
        dpg.add_plot_axis(dpg.mvXAxis, label="x")
        with dpg.plot_axis(dpg.mvYAxis, label="y", tag="yb"):
            dpg.add_scatter_series(list(XS), list(YS),
                                   label="rebuild", tag="sc_reb")
            dpg.bind_item_theme("sc_reb", "th_rebuild")


def apply_rebuild(size: float, opacity: float) -> None:
    r, g, b = REB_FILL_RGB
    oa = alpha_u8(opacity)
    dpg.set_value("tc_fill", [r, g, b, oa])
    dpg.set_value("tc_outline", [0, 0, 0, oa])
    dpg.set_value("ts_size", [float(size), float(size)])
    dpg.set_value("ts_alpha", [float(opacity), float(opacity)])
    # Touch series data so ImPlot redraws with the updated theme
    dpg.set_value("sc_reb", [list(XS), list(YS)])


# ---------------------------------------------------------------------------
# Controls + wiring
# ---------------------------------------------------------------------------
def on_slider_change() -> None:
    sz = float(dpg.get_value("slider_size"))
    op = float(dpg.get_value("slider_opacity"))
    apply_drawlist_circles(sz, op)
    apply_rebuild(sz, op)
    dpg.set_value("status",
                  f"size={sz:.1f}  opacity={op:.2f}")


def build_controls_window() -> None:
    with dpg.window(label="Controls", tag="win", width=900, height=500):
        dpg.add_text(
            "Drag sliders to change marker size and opacity in both panels.",
            wrap=880)
        dpg.add_slider_float(label="MarkerSize (px)", tag="slider_size",
                             default_value=14.0, min_value=4.0,
                             max_value=40.0, format="%.1f",
                             callback=lambda *_: on_slider_change())
        dpg.add_slider_float(label="FillAlpha", tag="slider_opacity",
                             default_value=0.5, min_value=0.05,
                             max_value=1.0, format="%.2f",
                             callback=lambda *_: on_slider_change())
        dpg.add_text("", tag="status", color=(40, 40, 40, 255))
        with dpg.group(horizontal=True):
            with dpg.group():
                add_left_drawlist_with_markers()
            add_right_implot_panel()


def main() -> None:
    dpg.create_context()
    create_initial_rebuild_theme()
    dpg.create_viewport(title="MWE: scatter style", width=900, height=520)
    build_controls_window()
    dpg.setup_dearpygui()
    on_slider_change()
    dpg.show_viewport()
    dpg.set_primary_window("win", True)
    while dpg.is_dearpygui_running():
        dpg.render_dearpygui_frame()
    dpg.destroy_context()


if __name__ == "__main__":
    main()
