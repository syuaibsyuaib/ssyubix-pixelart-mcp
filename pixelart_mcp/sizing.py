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
    TILE_NOTE = (
        "This is the size of ONE tile, not a full tilemap/level image. A "
        "playable tilemap is a grid of many tiles at this size -- use "
        "pixelart_suggest_tilemap_layout to work out how many, then "
        "pixelart_create_tileset to build the full grid. Do not hand back "
        "a single canvas of this size as 'the tilemap'."
    )

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
            "note": TILE_NOTE,
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
            "note": TILE_NOTE,
        }

    return {
        "tile_width": BASE_PPU,
        "tile_height": BASE_PPU,
        "ppu": BASE_PPU,
        "reasoning": (
            f"No category or screen size given; defaulting to the standard "
            f"{BASE_PPU}x{BASE_PPU} pixel-art base grid."
        ),
        "note": TILE_NOTE,
    }


MAX_TILEMAP_CELLS = 4096  # keep in sync with tileset.MAX_GRID_CELLS


def suggest_tilemap_layout(
    tile_width: int,
    tile_height: int,
    columns: Optional[int] = None,
    rows: Optional[int] = None,
    screen_width: Optional[int] = None,
    screen_height: Optional[int] = None,
) -> dict:
    """Work out the full grid (and total pixel size) needed for an actual tilemap.

    A tilemap is many tiles arranged in a grid -- never a single small
    canvas. Provide either an explicit columns+rows, or a target
    screen/level size in pixels to derive columns+rows from the tile size.
    """
    if columns and rows:
        pass
    elif screen_width and screen_height:
        columns = max(1, round(screen_width / tile_width))
        rows = max(1, round(screen_height / tile_height))
    else:
        raise ValueError(
            "Provide either columns+rows, or screen_width+screen_height, "
            "to compute a tilemap layout."
        )

    if columns < 1 or rows < 1:
        raise ValueError("columns and rows must each be at least 1.")
    if columns * rows > MAX_TILEMAP_CELLS:
        raise ValueError(
            f"{columns}x{rows} = {columns * rows} tiles exceeds the "
            f"{MAX_TILEMAP_CELLS}-cell limit for a single tileset sheet."
        )

    total_w = columns * tile_width
    total_h = rows * tile_height
    return {
        "tile_width": tile_width,
        "tile_height": tile_height,
        "columns": columns,
        "rows": rows,
        "total_tiles": columns * rows,
        "total_map_width_px": total_w,
        "total_map_height_px": total_h,
        "reasoning": (
            f"A full tilemap here needs {columns}x{rows} = {columns * rows} "
            f"individual {tile_width}x{tile_height}px tiles arranged in a grid, "
            f"producing a {total_w}x{total_h}px image overall -- build it with "
            f"pixelart_create_tileset(tile_width={tile_width}, tile_height={tile_height}, "
            f"columns={columns}, rows={rows}), then pixelart_set_tile for each "
            f"position, then pixelart_export_tileset."
        ),
    }
