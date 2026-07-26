import json

import pytest

from pixelart_mcp import server
from pixelart_mcp.models import (
    ClearCanvasInput,
    CreateCanvasInput,
    CreateTilesetInput,
    DeleteCanvasInput,
    DeleteTilesetInput,
    DrawPolygonInput,
    DuplicateCanvasInput,
    FlipCanvasInput,
    GetCanvasInfoInput,
    ImportCanvasInput,
    SetPixelInput,
)


@pytest.fixture(autouse=True)
def _reset_state():
    server._canvases.clear()
    server._tilesets.clear()
    yield
    server._canvases.clear()
    server._tilesets.clear()


def test_clear_canvas_tool():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=4, height=4))
    server.pixelart_set_pixel(SetPixelInput(canvas_id="c1", x=0, y=0, color=[255, 0, 0, 255]))
    server.pixelart_clear_canvas(ClearCanvasInput(canvas_id="c1"))
    info = json.loads(server.pixelart_get_canvas_info(GetCanvasInfoInput(canvas_id="c1")))
    assert info["non_transparent_pixels"] == 0


def test_flip_canvas_tool():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=4, height=4))
    server.pixelart_set_pixel(SetPixelInput(canvas_id="c1", x=0, y=0, color=[255, 0, 0, 255]))
    server.pixelart_flip_canvas(FlipCanvasInput(canvas_id="c1", direction="horizontal"))
    assert server._canvases["c1"].get_pixel(3, 0) == (255, 0, 0, 255)


def test_duplicate_canvas_tool_rejects_existing_id():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=4, height=4))
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c2", width=4, height=4))
    with pytest.raises(ValueError, match="already exists"):
        server.pixelart_duplicate_canvas(DuplicateCanvasInput(source_canvas_id="c1", new_canvas_id="c2"))


def test_duplicate_canvas_tool_copies_pixels():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=4, height=4))
    server.pixelart_set_pixel(SetPixelInput(canvas_id="c1", x=0, y=0, color=[1, 2, 3, 255]))
    server.pixelart_duplicate_canvas(DuplicateCanvasInput(source_canvas_id="c1", new_canvas_id="c2"))
    assert server._canvases["c2"].get_pixel(0, 0) == (1, 2, 3, 255)


def test_draw_polygon_tool():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=6, height=6))
    server.pixelart_draw_polygon(
        DrawPolygonInput(canvas_id="c1", points=[[0, 0], [5, 0], [5, 5], [0, 5]], color=[10, 20, 30, 255], fill=True)
    )
    assert server._canvases["c1"].get_pixel(2, 2) == (10, 20, 30, 255)


def test_delete_canvas_tool_and_missing_error():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="c1", width=4, height=4))
    server.pixelart_delete_canvas(DeleteCanvasInput(canvas_id="c1"))
    assert "c1" not in server._canvases
    with pytest.raises(ValueError, match="No canvas named"):
        server.pixelart_delete_canvas(DeleteCanvasInput(canvas_id="c1"))


def test_list_canvases_tool():
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="a", width=4, height=4))
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="b", width=8, height=8))
    result = json.loads(server.pixelart_list_canvases())
    ids = {c["canvas_id"] for c in result["canvases"]}
    assert ids == {"a", "b"}


def test_list_tilesets_tool():
    server.pixelart_create_tileset(CreateTilesetInput(tileset_id="t1", tile_width=4, tile_height=4, columns=2, rows=1))
    result = json.loads(server.pixelart_list_tilesets())
    assert result["tilesets"][0]["tileset_id"] == "t1"


def test_delete_tileset_tool_and_missing_error():
    server.pixelart_create_tileset(CreateTilesetInput(tileset_id="t1", tile_width=4, tile_height=4, columns=2, rows=1))
    server.pixelart_delete_tileset(DeleteTilesetInput(tileset_id="t1"))
    assert "t1" not in server._tilesets
    with pytest.raises(ValueError, match="No tileset named"):
        server.pixelart_delete_tileset(DeleteTilesetInput(tileset_id="t1"))


def test_import_canvas_tool_loads_file(tmp_path):
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="source", width=4, height=4, background=[5, 6, 7, 255]))
    path = tmp_path / "sprite.png"
    with open(path, "wb") as f:
        f.write(server._canvases["source"].to_png_bytes())

    result = json.loads(server.pixelart_import_canvas(ImportCanvasInput(canvas_id="imported", file_path=str(path))))
    assert result == {"canvas_id": "imported", "width": 4, "height": 4}
    assert server._canvases["imported"].get_pixel(0, 0) == (5, 6, 7, 255)


def test_import_canvas_tool_rejects_existing_id(tmp_path):
    server.pixelart_create_canvas(CreateCanvasInput(canvas_id="dup", width=4, height=4))
    path = tmp_path / "sprite.png"
    with open(path, "wb") as f:
        f.write(server._canvases["dup"].to_png_bytes())
    with pytest.raises(ValueError, match="already exists"):
        server.pixelart_import_canvas(ImportCanvasInput(canvas_id="dup", file_path=str(path)))
