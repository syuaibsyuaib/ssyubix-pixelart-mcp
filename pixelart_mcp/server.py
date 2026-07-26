"""pixelart_mcp: an MCP server for drawing pixel-art tiles/tilesets.

Runs over stdio for local use (e.g. Claude Desktop/Code), designed to
sit alongside engine-integration servers (such as unity-mcp-server):
this server produces pixel art + a PNG/JSON handoff, other servers
take it from there.

Any ValueError raised by the domain modules (canvas/tileset/sizing) is
caught by FastMCP and surfaced to the calling agent as a tool error
result with the exception message -- so error messages in those
modules are written to be directly useful to the agent.
"""
from __future__ import annotations

import json
from typing import Dict

from mcp.server.fastmcp import FastMCP, Image

from .canvas import PixelCanvas
from .models import (
    CanvasPreviewInput,
    ClearCanvasInput,
    CreateCanvasInput,
    CreateTilesetInput,
    DeleteCanvasInput,
    DeleteTilesetInput,
    DrawCircleInput,
    DrawLineInput,
    DrawPolygonInput,
    DrawRectInput,
    DuplicateCanvasInput,
    ExportTilesetInput,
    ExtractPaletteInput,
    FlipCanvasInput,
    FloodFillInput,
    GeneratePaletteInput,
    GetCanvasInfoInput,
    ImportCanvasInput,
    SetPixelInput,
    SetTileInput,
    SuggestTileSizeInput,
)
from .palette import generate_palette
from .sizing import suggest_tile_size
from .tileset import Tileset

mcp = FastMCP("ssyubix-pixelart-mcp")

_canvases: Dict[str, PixelCanvas] = {}
_tilesets: Dict[str, Tileset] = {}


def _get_canvas(canvas_id: str) -> PixelCanvas:
    if canvas_id not in _canvases:
        raise ValueError(f"No canvas named '{canvas_id}'. Create it first with pixelart_create_canvas.")
    return _canvases[canvas_id]


def _get_tileset(tileset_id: str) -> Tileset:
    if tileset_id not in _tilesets:
        raise ValueError(f"No tileset named '{tileset_id}'. Create it first with pixelart_create_tileset.")
    return _tilesets[tileset_id]


def _rgba(values: list[int]) -> tuple[int, int, int, int]:
    return tuple(values)  # type: ignore[return-value]


@mcp.tool(
    name="pixelart_create_canvas",
    annotations={"title": "Create pixel canvas", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_create_canvas(params: CreateCanvasInput) -> str:
    """Create a new blank pixel-art canvas (a single tile/sprite surface).

    Args:
        params: canvas_id, width, height, background RGBA.
    Returns:
        JSON string confirming creation with canvas_id, width, height.
    """
    canvas = PixelCanvas(params.width, params.height, _rgba(params.background))
    _canvases[params.canvas_id] = canvas
    return json.dumps({"canvas_id": params.canvas_id, "width": params.width, "height": params.height})


@mcp.tool(
    name="pixelart_import_canvas",
    annotations={"title": "Import existing PNG into canvas", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_import_canvas(params: ImportCanvasInput) -> str:
    """Load an existing PNG (or other image) file from disk into a new canvas.

    Use this to continue editing a sprite that already exists (e.g. a
    tile already in the user's Unity project) instead of redrawing it
    from a blank canvas.

    Args:
        params: canvas_id (new id to store it under), file_path (local path to the image).
    Returns:
        JSON string: {"canvas_id", "width", "height"}.
    """
    if params.canvas_id in _canvases:
        raise ValueError(
            f"Canvas '{params.canvas_id}' already exists. Choose a different id or delete it first."
        )
    canvas = PixelCanvas.from_file(params.file_path)
    _canvases[params.canvas_id] = canvas
    return json.dumps({"canvas_id": params.canvas_id, "width": canvas.width, "height": canvas.height})


@mcp.tool(
    name="pixelart_set_pixel",
    annotations={"title": "Set a pixel", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_set_pixel(params: SetPixelInput) -> str:
    """Set a single pixel's color on a canvas.

    Args:
        params: canvas_id, x, y, RGBA color.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).set_pixel(params.x, params.y, _rgba(params.color))
    return f"Pixel ({params.x},{params.y}) set on '{params.canvas_id}'."


@mcp.tool(
    name="pixelart_draw_line",
    annotations={"title": "Draw a line", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_draw_line(params: DrawLineInput) -> str:
    """Draw a straight line on a canvas between two points.

    Args:
        params: canvas_id, x0, y0, x1, y1, color, line_width.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).draw_line(
        params.x0, params.y0, params.x1, params.y1, _rgba(params.color), params.line_width
    )
    return f"Line drawn on '{params.canvas_id}'."


@mcp.tool(
    name="pixelart_draw_rect",
    annotations={"title": "Draw a rectangle", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_draw_rect(params: DrawRectInput) -> str:
    """Draw a rectangle (outline or filled) on a canvas.

    Args:
        params: canvas_id, x0, y0, x1, y1, color, fill.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).draw_rect(
        params.x0, params.y0, params.x1, params.y1, _rgba(params.color), params.fill
    )
    return f"Rectangle drawn on '{params.canvas_id}'."


@mcp.tool(
    name="pixelart_draw_circle",
    annotations={"title": "Draw a circle", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_draw_circle(params: DrawCircleInput) -> str:
    """Draw a circle/ellipse (outline or filled) on a canvas.

    Args:
        params: canvas_id, center_x, center_y, radius, color, fill.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).draw_circle(
        params.center_x, params.center_y, params.radius, _rgba(params.color), params.fill
    )
    return f"Circle drawn on '{params.canvas_id}'."


@mcp.tool(
    name="pixelart_flood_fill",
    annotations={"title": "Flood fill an area", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_flood_fill(params: FloodFillInput) -> str:
    """Flood-fill the contiguous region containing (x, y) with a color.

    Args:
        params: canvas_id, x, y, color.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).flood_fill(params.x, params.y, _rgba(params.color))
    return f"Flood fill applied on '{params.canvas_id}' from ({params.x},{params.y})."


@mcp.tool(
    name="pixelart_draw_polygon",
    annotations={"title": "Draw a polygon", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_draw_polygon(params: DrawPolygonInput) -> str:
    """Draw a polygon (outline or filled) from a list of vertex points.

    Use this for shapes that draw_rect/draw_circle can't express (roof
    slopes, tree silhouettes, diagonal terrain edges, etc).

    Args:
        params: canvas_id, points (>=3 [x,y] pairs), color, fill.
    Returns:
        Confirmation string.
    """
    points = [tuple(p) for p in params.points]
    _get_canvas(params.canvas_id).draw_polygon(points, _rgba(params.color), params.fill)
    return f"Polygon drawn on '{params.canvas_id}'."


@mcp.tool(
    name="pixelart_clear_canvas",
    annotations={"title": "Clear canvas", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_clear_canvas(params: ClearCanvasInput) -> str:
    """Erase all drawing on a canvas back to a flat background color.

    Args:
        params: canvas_id, background RGBA (default fully transparent).
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).clear(_rgba(params.background))
    return f"Canvas '{params.canvas_id}' cleared."


@mcp.tool(
    name="pixelart_flip_canvas",
    annotations={"title": "Flip/mirror canvas", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_flip_canvas(params: FlipCanvasInput) -> str:
    """Mirror a canvas horizontally or vertically in place.

    Common for pixel-art symmetry: draw one half of a character/object
    and flip instead of hand-drawing the mirrored half.

    Args:
        params: canvas_id, direction ('horizontal' or 'vertical').
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id).flip(horizontal=(params.direction == "horizontal"))
    return f"Canvas '{params.canvas_id}' flipped {params.direction}ly."


@mcp.tool(
    name="pixelart_duplicate_canvas",
    annotations={"title": "Duplicate canvas", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_duplicate_canvas(params: DuplicateCanvasInput) -> str:
    """Copy an existing canvas into a new canvas id.

    Useful for repeated/near-identical tiles (grass variants, floor
    tiles) without redrawing from scratch.

    Args:
        params: source_canvas_id, new_canvas_id.
    Returns:
        Confirmation string.
    """
    if params.new_canvas_id in _canvases:
        raise ValueError(f"Canvas '{params.new_canvas_id}' already exists. Choose a different id or delete it first.")
    source = _get_canvas(params.source_canvas_id)
    _canvases[params.new_canvas_id] = source.duplicate()
    return f"Canvas '{params.source_canvas_id}' duplicated as '{params.new_canvas_id}'."


@mcp.tool(
    name="pixelart_get_canvas_info",
    annotations={"title": "Get canvas info", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_get_canvas_info(params: GetCanvasInfoInput) -> str:
    """Get lightweight metadata about a canvas without rendering a preview image.

    Cheaper than pixelart_get_canvas_preview when the agent only needs
    to check dimensions or whether anything has been drawn yet.

    Args:
        params: canvas_id.
    Returns:
        JSON string: {"width", "height", "non_transparent_pixels", "total_pixels"}.
    """
    return json.dumps(_get_canvas(params.canvas_id).info())


@mcp.tool(
    name="pixelart_delete_canvas",
    annotations={"title": "Delete canvas", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_delete_canvas(params: DeleteCanvasInput) -> str:
    """Remove a canvas from memory once it's no longer needed.

    Args:
        params: canvas_id.
    Returns:
        Confirmation string.
    """
    _get_canvas(params.canvas_id)  # raises a clear error if missing
    del _canvases[params.canvas_id]
    return f"Canvas '{params.canvas_id}' deleted."


@mcp.tool(
    name="pixelart_list_canvases",
    annotations={"title": "List canvases", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_list_canvases() -> str:
    """List every canvas currently held in memory for this server session.

    Use this to recover canvas_id/size context in a long session instead
    of relying on conversation memory of what was created earlier.

    Returns:
        JSON string: {"canvases": [{"canvas_id", "width", "height"}, ...]}.
    """
    return json.dumps({
        "canvases": [
            {"canvas_id": cid, "width": c.width, "height": c.height} for cid, c in _canvases.items()
        ]
    })


@mcp.tool(
    name="pixelart_get_canvas_preview",
    annotations={"title": "Preview canvas", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_get_canvas_preview(params: CanvasPreviewInput) -> Image:
    """Return the current canvas as an upscaled PNG image for visual inspection.

    Args:
        params: canvas_id, scale (nearest-neighbor upscale factor).
    Returns:
        Image: PNG preview, upscaled by `scale` so small pixel art is visible.
    """
    canvas = _get_canvas(params.canvas_id)
    preview = canvas.preview_image(params.scale)
    import io as _io

    buf = _io.BytesIO()
    preview.save(buf, format="PNG")
    return Image(data=buf.getvalue(), format="png")


@mcp.tool(
    name="pixelart_extract_palette",
    annotations={"title": "Extract palette from canvas", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_extract_palette(params: ExtractPaletteInput) -> str:
    """Extract the dominant colors currently used on a canvas.

    Args:
        params: canvas_id, n_colors.
    Returns:
        JSON string: {"colors": ["#rrggbb", ...]}.
    """
    colors = _get_canvas(params.canvas_id).extract_palette(params.n_colors)
    return json.dumps({"colors": colors})


@mcp.tool(
    name="pixelart_suggest_tile_size",
    annotations={"title": "Suggest tile size", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_suggest_tile_size(params: SuggestTileSizeInput) -> str:
    """Suggest an ideal tile size in pixels for a game asset.

    Uses a 16-pixel-per-unit (PPU) base-grid convention by default. If
    `category` is given (small_prop, character, large_character,
    structure, large_structure) it takes priority. Otherwise, if a
    target screen resolution is given, picks a PPU that divides the
    screen evenly. Falls back to a 16x16 default.

    Args:
        params: category, screen_width, screen_height (all optional).
    Returns:
        JSON string: {"tile_width", "tile_height", "ppu", "reasoning"}.
    """
    result = suggest_tile_size(params.category, params.screen_width, params.screen_height)
    return json.dumps(result)


@mcp.tool(
    name="pixelart_generate_palette",
    annotations={"title": "Generate color palette", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_generate_palette(params: GeneratePaletteInput) -> str:
    """Generate a limited, cohesive color palette for pixel art.

    Args:
        params: n_colors, style (forest/desert/ocean/retro/pastel/night/lava/candy, optional).
    Returns:
        JSON string: {"colors": ["#rrggbb", ...]}.
    """
    colors = generate_palette(params.n_colors, params.style)
    return json.dumps({"colors": colors})


@mcp.tool(
    name="pixelart_create_tileset",
    annotations={"title": "Create tileset sheet", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_create_tileset(params: CreateTilesetInput) -> str:
    """Create a blank tileset sheet (grid of equally-sized tile slots).

    Args:
        params: tileset_id, tile_width, tile_height, columns, rows, ppu.
    Returns:
        JSON string confirming the grid dimensions.
    """
    tileset = Tileset(params.tile_width, params.tile_height, params.columns, params.rows, params.ppu)
    _tilesets[params.tileset_id] = tileset
    return json.dumps({
        "tileset_id": params.tileset_id,
        "columns": params.columns,
        "rows": params.rows,
        "tile_width": params.tile_width,
        "tile_height": params.tile_height,
        "total_slots": params.columns * params.rows,
    })


@mcp.tool(
    name="pixelart_set_tile",
    annotations={"title": "Place tile into tileset", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_set_tile(params: SetTileInput) -> str:
    """Place a drawn canvas into a tileset slot.

    Args:
        params: tileset_id, index (row-major slot), canvas_id.
    Returns:
        Confirmation string.
    """
    tileset = _get_tileset(params.tileset_id)
    canvas = _get_canvas(params.canvas_id)
    tileset.set_tile(params.index, canvas)
    return f"Canvas '{params.canvas_id}' placed at slot {params.index} in tileset '{params.tileset_id}'."


@mcp.tool(
    name="pixelart_export_tileset",
    annotations={"title": "Export tileset to disk", "readOnlyHint": False, "destructiveHint": False, "idempotentHint": False, "openWorldHint": False},
)
def pixelart_export_tileset(params: ExportTilesetInput) -> str:
    """Export a tileset to a PNG file plus a JSON metadata sidecar.

    The metadata (tile size, grid, PPU, filled slots, palette) is meant
    to be handed to a downstream engine-integration tool (e.g. an agent
    calling unity-mcp-server) so it can slice/import the sheet without
    re-deriving those values.

    Args:
        params: tileset_id, output_dir, name, palette (optional hex list to record).
    Returns:
        JSON string: {"png_path", "json_path", "metadata": {...}}.
    """
    tileset = _get_tileset(params.tileset_id)
    result = tileset.export(params.output_dir, params.name, params.palette)
    return json.dumps(result)


@mcp.tool(
    name="pixelart_delete_tileset",
    annotations={"title": "Delete tileset", "readOnlyHint": False, "destructiveHint": True, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_delete_tileset(params: DeleteTilesetInput) -> str:
    """Remove a tileset from memory once it's no longer needed.

    Args:
        params: tileset_id.
    Returns:
        Confirmation string.
    """
    _get_tileset(params.tileset_id)  # raises a clear error if missing
    del _tilesets[params.tileset_id]
    return f"Tileset '{params.tileset_id}' deleted."


@mcp.tool(
    name="pixelart_list_tilesets",
    annotations={"title": "List tilesets", "readOnlyHint": True, "destructiveHint": False, "idempotentHint": True, "openWorldHint": False},
)
def pixelart_list_tilesets() -> str:
    """List every tileset currently held in memory for this server session.

    Returns:
        JSON string: {"tilesets": [{"tileset_id", "columns", "rows", "tile_width", "tile_height", "filled_tiles"}, ...]}.
    """
    return json.dumps({
        "tilesets": [
            {
                "tileset_id": tid,
                "columns": t.columns,
                "rows": t.rows,
                "tile_width": t.tile_width,
                "tile_height": t.tile_height,
                "filled_tiles": sorted(t.filled.keys()),
            }
            for tid, t in _tilesets.items()
        ]
    })


def main() -> None:
    mcp.run()


if __name__ == "__main__":
    main()
