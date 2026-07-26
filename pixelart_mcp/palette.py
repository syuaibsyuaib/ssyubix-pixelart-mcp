"""Procedural color palette generation for pixel art.

Generates limited, cohesive palettes suitable for pixel-art tilesets,
either from a named style/mood or as a balanced default spread.
"""
from __future__ import annotations

import colorsys
from typing import Optional

# Base hue (0-1), saturation range, and lightness range per style keyword.
STYLE_PRESETS: dict[str, dict[str, tuple[float, float] | float]] = {
    "forest":   {"hue": 0.30, "sat": (0.35, 0.75), "light": (0.15, 0.75)},
    "desert":   {"hue": 0.10, "sat": (0.30, 0.70), "light": (0.25, 0.85)},
    "ocean":    {"hue": 0.55, "sat": (0.40, 0.80), "light": (0.15, 0.80)},
    "retro":    {"hue": 0.95, "sat": (0.55, 0.95), "light": (0.25, 0.70)},
    "pastel":   {"hue": 0.80, "sat": (0.20, 0.45), "light": (0.55, 0.90)},
    "night":    {"hue": 0.65, "sat": (0.30, 0.65), "light": (0.05, 0.45)},
    "lava":     {"hue": 0.02, "sat": (0.60, 1.00), "light": (0.20, 0.65)},
    "candy":    {"hue": 0.90, "sat": (0.55, 0.90), "light": (0.45, 0.85)},
}

GOLDEN_RATIO_CONJUGATE = 0.618033988749895


def _hex(r: float, g: float, b: float) -> str:
    return f"#{int(r * 255):02x}{int(g * 255):02x}{int(b * 255):02x}"


def generate_palette(n_colors: int = 8, style: Optional[str] = None, seed_hue: Optional[float] = None) -> list[str]:
    """Generate n_colors hex colors.

    If `style` matches a known preset, colors are sampled around that
    style's hue/saturation/lightness ranges. Otherwise colors are spread
    using golden-ratio hue stepping for a balanced, non-repeating look.
    """
    n_colors = max(1, min(n_colors, 64))
    preset = STYLE_PRESETS.get((style or "").lower())

    colors = []
    if preset:
        hue_base = preset["hue"]
        sat_lo, sat_hi = preset["sat"]
        light_lo, light_hi = preset["light"]
        for i in range(n_colors):
            frac = i / max(n_colors - 1, 1)
            hue = (hue_base + (frac - 0.5) * 0.08) % 1.0
            sat = sat_lo + (sat_hi - sat_lo) * frac
            light = light_lo + (light_hi - light_lo) * frac
            r, g, b = colorsys.hls_to_rgb(hue, light, sat)
            colors.append(_hex(r, g, b))
    else:
        hue = seed_hue if seed_hue is not None else 0.15
        for i in range(n_colors):
            hue = (hue + GOLDEN_RATIO_CONJUGATE) % 1.0
            light = 0.35 + 0.4 * ((i % 4) / 3)
            r, g, b = colorsys.hls_to_rgb(hue, light, 0.65)
            colors.append(_hex(r, g, b))
    return colors


def available_styles() -> list[str]:
    return sorted(STYLE_PRESETS.keys())
