"""Tile-size suggestion heuristics.

Default convention: a 16-pixel-per-unit (PPU) base grid, the common
baseline for 2D pixel-art tilesets. Categories map to a bounding box in
PPU multiples; screen-resolution input is used to pick a PPU multiple
that divides the target resolution evenly.
"""
from __future__ import annotations

from typing import Optional

BASE_PPU = 16

# category -> (width_multiplier, height_multiplier) of BASE_PPU
CATEGORY_BOXES: dict[str, tuple[int, int]] = {
    "small_prop": (1, 1),     # rocks, flowers, items -> 16x16
    "character": (1, 2),      # -> 16x32
    "large_character": (2, 2),  # bosses/big creatures -> 32x32
    "structure": (3, 3),      # houses, big trees -> 48x48
    "large_structure": (4, 4),  # castles, landmarks -> 64x64
}


def suggest_tile_size(
    category: Optional[str] = None,
    screen_width: Optional[int] = None,
    screen_height: Optional[int] = None,
) -> dict:
    """Suggest a tile size in pixels plus the reasoning behind it.

    Priority: explicit `category` first, then `screen_width`/`screen_height`
    (picks the largest PPU multiple <= 64 that evenly divides both
    dimensions), otherwise falls back to the 16x16 base default.
    """
    if category:
        key = category.lower().replace(" ", "_")
        if key not in CATEGORY_BOXES:
            valid = ", ".join(sorted(CATEGORY_BOXES))
            raise ValueError(f"Unknown category '{category}'. Valid options: {valid}")
        w_mult, h_mult = CATEGORY_BOXES[key]
        tile_w, tile_h = w_mult * BASE_PPU, h_mult * BASE_PPU
        return {
            "tile_width": tile_w,
            "tile_height": tile_h,
            "ppu": BASE_PPU,
            "reasoning": (
                f"Category '{category}' conventionally fits a "
                f"{w_mult}x{h_mult} grid of {BASE_PPU}px units -> {tile_w}x{tile_h}px."
            ),
        }

    if screen_width and screen_height:
        best = BASE_PPU
        for candidate in (64, 48, 32, 24, 16, 8):
            if screen_width % candidate == 0 and screen_height % candidate == 0:
                best = candidate
                break
        return {
            "tile_width": best,
            "tile_height": best,
            "ppu": best,
            "reasoning": (
                f"{best}px tiles divide the {screen_width}x{screen_height} screen "
                f"evenly ({screen_width // best}x{screen_height // best} tiles)."
            ),
        }

    return {
        "tile_width": BASE_PPU,
        "tile_height": BASE_PPU,
        "ppu": BASE_PPU,
        "reasoning": (
            f"No category or screen size given; defaulting to the standard "
            f"{BASE_PPU}x{BASE_PPU} pixel-art base grid."
        ),
    }
