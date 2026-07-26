"""Tileset assembly and export.

A Tileset is a grid of equally-sized tile slots composited into one PNG
sheet. Export writes the PNG plus a sidecar JSON metadata file (tile
size, grid, PPU, palette) so a downstream tool -- e.g. an agent driving
unity-mcp-server -- can slice/import the sheet without guessing values.
"""
from __future__ import annotations

import json
import os
from typing import Optional

from PIL import Image as PILImage

from .canvas import PixelCanvas, CanvasError

MAX_GRID_CELLS = 4096  # guard against pathological columns*rows


class TilesetError(ValueError):
    pass


class Tileset:
    def __init__(self, tile_width: int, tile_height: int, columns: int, rows: int, ppu: int = 16):
        if columns * rows > MAX_GRID_CELLS or columns < 1 or rows < 1:
            raise TilesetError(f"Grid must be between 1 and {MAX_GRID_CELLS} cells.")
        self.tile_width = tile_width
        self.tile_height = tile_height
        self.columns = columns
        self.rows = rows
        self.ppu = ppu
        self.sheet = PILImage.new(
            "RGBA", (tile_width * columns, tile_height * rows), (0, 0, 0, 0)
        )
        self.filled: dict[int, bool] = {}

    def _slot_bounds(self, index: int) -> tuple[int, int]:
        total = self.columns * self.rows
        if not (0 <= index < total):
            raise TilesetError(f"Tile index {index} out of range (0-{total - 1}).")
        col = index % self.columns
        row = index // self.columns
        return col * self.tile_width, row * self.tile_height

    def set_tile(self, index: int, canvas: PixelCanvas) -> None:
        if canvas.width != self.tile_width or canvas.height != self.tile_height:
            raise TilesetError(
                f"Canvas size {canvas.width}x{canvas.height} does not match "
                f"tile size {self.tile_width}x{self.tile_height}."
            )
        x, y = self._slot_bounds(index)
        self.sheet.paste(canvas.image, (x, y), canvas.image)
        self.filled[index] = True

    def export(self, output_dir: str, name: str, palette: Optional[list[str]] = None) -> dict:
        os.makedirs(output_dir, exist_ok=True)
        png_path = os.path.join(output_dir, f"{name}.png")
        json_path = os.path.join(output_dir, f"{name}.json")

        self.sheet.save(png_path, format="PNG")

        metadata = {
            "sheet_file": f"{name}.png",
            "tile_width": self.tile_width,
            "tile_height": self.tile_height,
            "columns": self.columns,
            "rows": self.rows,
            "ppu": self.ppu,
            "sheet_width": self.tile_width * self.columns,
            "sheet_height": self.tile_height * self.rows,
            "filled_tiles": sorted(self.filled.keys()),
            "total_tiles": self.columns * self.rows,
            "palette": palette or [],
        }
        with open(json_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

        return {"png_path": png_path, "json_path": json_path, "metadata": metadata}
