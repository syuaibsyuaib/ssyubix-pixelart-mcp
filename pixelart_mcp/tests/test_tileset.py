import json
import os

import pytest

from pixelart_mcp.canvas import PixelCanvas
from pixelart_mcp.tileset import Tileset, TilesetError


def test_create_tileset_sheet_size():
    ts = Tileset(tile_width=16, tile_height=16, columns=3, rows=2)
    assert ts.sheet.size == (48, 32)


def test_set_tile_places_pixels_at_correct_slot():
    ts = Tileset(tile_width=4, tile_height=4, columns=2, rows=1)
    tile = PixelCanvas(4, 4, background=(255, 0, 0, 255))
    ts.set_tile(1, tile)  # second slot -> offset x=4
    assert ts.sheet.getpixel((5, 1)) == (255, 0, 0, 255)
    assert ts.sheet.getpixel((1, 1)) == (0, 0, 0, 0)  # first slot untouched


def test_set_tile_size_mismatch_raises():
    ts = Tileset(tile_width=16, tile_height=16, columns=2, rows=2)
    wrong_size_tile = PixelCanvas(8, 8)
    with pytest.raises(TilesetError):
        ts.set_tile(0, wrong_size_tile)


def test_set_tile_out_of_range_raises():
    ts = Tileset(tile_width=4, tile_height=4, columns=2, rows=2)
    tile = PixelCanvas(4, 4)
    with pytest.raises(TilesetError):
        ts.set_tile(99, tile)


def test_grid_too_large_raises():
    with pytest.raises(TilesetError):
        Tileset(tile_width=16, tile_height=16, columns=1000, rows=1000)


def test_export_writes_png_and_json(tmp_path):
    ts = Tileset(tile_width=4, tile_height=4, columns=2, rows=1, ppu=16)
    tile = PixelCanvas(4, 4, background=(0, 255, 0, 255))
    ts.set_tile(0, tile)

    result = ts.export(str(tmp_path), "my_tileset", palette=["#00ff00"])

    assert os.path.exists(result["png_path"])
    assert os.path.exists(result["json_path"])

    with open(result["json_path"]) as f:
        meta = json.load(f)
    assert meta["tile_width"] == 4
    assert meta["columns"] == 2
    assert meta["filled_tiles"] == [0]
    assert meta["palette"] == ["#00ff00"]
    assert meta["sheet_width"] == 8
