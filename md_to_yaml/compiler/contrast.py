"""WCAG 2.1 contrast ratio utilities.

Implements the W3C relative luminance formula and contrast ratio calculation
for accessibility validation of slide deck color choices.
"""


def hex_to_relative_luminance(hex_color: str) -> float:
    """Compute WCAG 2.1 relative luminance of a hex color string.

    Args:
        hex_color: CSS hex color, e.g. '#f0a500' or 'f0a500'.

    Returns:
        Relative luminance in range [0.0, 1.0].
    """
    color = hex_color.lstrip('#')
    r_int = int(color[0:2], 16)
    g_int = int(color[2:4], 16)
    b_int = int(color[4:6], 16)

    def linearize(c_int: int) -> float:
        c = c_int / 255.0
        if c <= 0.04045:
            return c / 12.92
        return ((c + 0.055) / 1.055) ** 2.4

    r = linearize(r_int)
    g = linearize(g_int)
    b = linearize(b_int)
    return 0.2126 * r + 0.7152 * g + 0.0722 * b


def contrast_ratio(fg: str, bg: str) -> float:
    """Compute WCAG 2.1 contrast ratio between two hex colors.

    Args:
        fg: Foreground hex color.
        bg: Background hex color.

    Returns:
        Contrast ratio >= 1.0 (lighter+0.05)/(darker+0.05).
    """
    lum_fg = hex_to_relative_luminance(fg)
    lum_bg = hex_to_relative_luminance(bg)
    lighter = max(lum_fg, lum_bg)
    darker = min(lum_fg, lum_bg)
    return (lighter + 0.05) / (darker + 0.05)


def passes_wcag_aa(fg: str, bg: str, large_text: bool = False) -> bool:
    """Return True if the fg/bg pair meets WCAG 2.1 AA contrast requirements.

    Args:
        fg: Foreground hex color.
        bg: Background hex color.
        large_text: Use 3.0 threshold instead of 4.5 for large text.

    Returns:
        True if contrast ratio meets the AA threshold.
    """
    threshold = 3.0 if large_text else 4.5
    return contrast_ratio(fg, bg) >= threshold
