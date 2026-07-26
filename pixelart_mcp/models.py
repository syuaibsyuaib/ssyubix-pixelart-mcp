"""Pydantic input models for pixelart_mcp tools."""
from __future__ import annotations

from typing import List, Literal, Optional

from pydantic import BaseModel, ConfigDict, Field, field_validator

RGBA_DESC = "Color as [R, G, B, A], each 0-255 (e.g. [255, 0, 0, 255] for opaque red)."


class CreateCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str = Field(..., min_length=1, max_length=64, description="Unique name for this canvas, e.g. 'tree_tile'.")
    width: int = Field(..., ge=1, le=512, description="Canvas width in pixels.")
    height: int = Field(..., ge=1, le=512, description="Canvas height in pixels.")
    background: List[int] = Field(default=[0, 0, 0, 0], min_length=4, max_length=4, description=RGBA_DESC)


class SetPixelInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str = Field(..., description="Target canvas id.")
    x: int = Field(..., ge=0, description="X coordinate (0 = left).")
    y: int = Field(..., ge=0, description="Y coordinate (0 = top).")
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)


class DrawLineInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    x0: int = Field(..., ge=0)
    y0: int = Field(..., ge=0)
    x1: int = Field(..., ge=0)
    y1: int = Field(..., ge=0)
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)
    line_width: int = Field(default=1, ge=1, le=32)


class DrawRectInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    x0: int = Field(..., ge=0)
    y0: int = Field(..., ge=0)
    x1: int = Field(..., ge=0)
    y1: int = Field(..., ge=0)
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)
    fill: bool = Field(default=False, description="True = filled rectangle, False = outline only.")


class DrawCircleInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    center_x: int = Field(..., ge=0)
    center_y: int = Field(..., ge=0)
    radius: int = Field(..., ge=1, le=256)
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)
    fill: bool = Field(default=False)


class FloodFillInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    x: int = Field(..., ge=0)
    y: int = Field(..., ge=0)
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)


class CanvasPreviewInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    scale: int = Field(default=8, ge=1, le=32, description="Nearest-neighbor upscale factor for visibility.")


class ExtractPaletteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    n_colors: int = Field(default=8, ge=1, le=64)


class ClearCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    background: List[int] = Field(default=[0, 0, 0, 0], min_length=4, max_length=4, description=RGBA_DESC)


class ImportCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str = Field(..., min_length=1, max_length=64, description="Unique id to store the imported image under.")
    file_path: str = Field(..., description="Local path to an existing PNG (or other image) file to load.")


class GetCanvasInfoInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str = Field(..., description="Canvas to inspect.")


class DeleteCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str


class DeleteTilesetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tileset_id: str


class DuplicateCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    source_canvas_id: str = Field(..., description="Canvas to copy from.")
    new_canvas_id: str = Field(..., min_length=1, max_length=64, description="Unique id for the new copy.")


class FlipCanvasInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    direction: Literal["horizontal", "vertical"] = Field(
        default="horizontal", description="'horizontal' mirrors left-right, 'vertical' mirrors top-bottom."
    )


class DrawPolygonInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    canvas_id: str
    points: List[List[int]] = Field(
        ..., min_length=3, description="List of [x, y] vertex points, at least 3, in drawing order."
    )
    color: List[int] = Field(..., min_length=4, max_length=4, description=RGBA_DESC)
    fill: bool = Field(default=False)

    @field_validator("points")
    @classmethod
    def validate_points(cls, v: List[List[int]]) -> List[List[int]]:
        for point in v:
            if len(point) != 2:
                raise ValueError("Each polygon point must be exactly [x, y].")
        return v


class SuggestTileSizeInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    category: Optional[str] = Field(
        default=None,
        description="Object category: 'small_prop', 'character', 'large_character', 'structure', or 'large_structure'.",
    )
    screen_width: Optional[int] = Field(default=None, ge=1, description="Target game screen width in pixels.")
    screen_height: Optional[int] = Field(default=None, ge=1, description="Target game screen height in pixels.")


class SuggestTilemapLayoutInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tile_width: int = Field(..., ge=1, le=512, description="Width of a single tile in pixels.")
    tile_height: int = Field(..., ge=1, le=512, description="Height of a single tile in pixels.")
    columns: Optional[int] = Field(default=None, ge=1, description="Explicit number of tile columns in the map.")
    rows: Optional[int] = Field(default=None, ge=1, description="Explicit number of tile rows in the map.")
    screen_width: Optional[int] = Field(default=None, ge=1, description="Target full map/screen width in pixels (used to derive columns if not given).")
    screen_height: Optional[int] = Field(default=None, ge=1, description="Target full map/screen height in pixels (used to derive rows if not given).")


class GeneratePaletteInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    n_colors: int = Field(default=8, ge=1, le=64)
    style: Optional[str] = Field(
        default=None,
        description="Optional mood/style: 'forest', 'desert', 'ocean', 'retro', 'pastel', 'night', 'lava', 'candy'. Omit for a balanced default spread.",
    )


class CreateTilesetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tileset_id: str = Field(..., min_length=1, max_length=64)
    tile_width: int = Field(..., ge=1, le=512)
    tile_height: int = Field(..., ge=1, le=512)
    columns: int = Field(..., ge=1, le=64)
    rows: int = Field(..., ge=1, le=64)
    ppu: int = Field(default=16, ge=1, le=256)


class SetTileInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tileset_id: str
    index: int = Field(..., ge=0, description="Zero-based slot index (row-major: index = row*columns + col).")
    canvas_id: str = Field(..., description="Canvas whose current drawing will be placed into this slot.")


class ExportTilesetInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    tileset_id: str
    output_dir: str = Field(..., description="Local directory to write the PNG + metadata JSON into.")
    name: str = Field(..., min_length=1, max_length=100, description="Base filename (without extension).")
    palette: Optional[List[str]] = Field(default=None, description="Hex color list to record in the metadata for reference.")
