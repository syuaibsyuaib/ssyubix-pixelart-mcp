import json

import pytest

from pixelart_mcp import server
from pixelart_mcp.models import (
    CanvasPreviewInput,
    CreateCanvasInput,
    CreateTilesetInput,
    DrawRectInput,
    ExportTilesetInput,
    GeneratePaletteInput,
    SetPixelInput,
    SetTileInput,
    SuggestTileSizeInput,
)


@pytest.fixture(autouse=True)
def _reset_state():
    server._canvases.clear()
    server._tilesets.clear()
    yield
    server._canvases.clear()
    server._tilesets.clear()


def test_create_canvas_then_draw_and_preview():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="t1", width=8, height=8))
    server.pixelart_set_pixel(SetPixelInput(canvas_id="t1", x=0, y=0, color=[255, 0, 0, 255]))
    server.pixelart_draw_rect(DrawRectInput(canvas_id="t1", x0=1, y0=1, x1=3, y1=3, color=[0, 255, 0, 255], fill=True))

    preview = server.pixelart_get_canvas_preview(CanvasPreviewInput(canvas_id="t1", scale=4))
    assert preview.data[:8] == b"\x89PNG\r\n\x1a\n"


def test_missing_canvas_raises_clear_error():
    with pytest.raises(ValueError, match="No canvas named"):
        server.pixelart_set_pixel(SetPixelInput(canvas_id="ghost", x=0, y=0, color=[0, 0, 0, 255]))


def test_suggest_tile_size_tool_returns_json():
    result = json.loads(server.pixelart_suggest_tile_size(SuggestTileSizeInput(category="character")))
    assert result["tile_width"] == 16
    assert result["tile_height"] == 32


def test_generate_palette_tool_returns_json_colors():
    result = json.loads(server.pixelart_generate_palette(GeneratePaletteInput(n_colors=4, style="ocean")))
    assert len(result["colors"]) == 4


def test_full_tileset_workflow_to_export(tmp_path):
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="tile_a", width=4, height=4, background=[10, 20, 30, 255]))
    server.pixelart_create_tileset(CreateTilesetInput(tileset_id="ts1", tile_width=4, tile_height=4, columns=2, rows=1, ppu=16))
    server.pixelart_set_tile(SetTileInput(tileset_id="ts1", index=0, canvas_id="tile_a"))

    export_result = json.loads(
        server.pixelart_export_tileset(
            ExportTilesetInput(tileset_id="ts1", output_dir=str(tmp_path), name="demo")
        )
    )
    assert export_result["metadata"]["filled_tiles"] == [0]
    assert export_result["metadata"]["tile_width"] == 4


def test_missing_tileset_raises_clear_error(tmp_path):
    with pytest.raises(ValueError, match="No tileset named"):
        server.pixelart_export_tileset(ExportTilesetInput(tileset_id="ghost", output_dir=str(tmp_path), name="x"))
