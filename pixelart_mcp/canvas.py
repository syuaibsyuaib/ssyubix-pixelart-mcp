"""Pixel canvas primitives for pixel-art drawing.

Wraps a Pillow RGBA image and exposes pixel-level drawing operations
(set/get pixel, line, rect, circle, flood fill) plus PNG/base64 export
and an upscaled preview for easy visual inspection by an AI agent.
"""
from __future__ import annotations

import base64
import io
from typing import Tuple

from PIL import Image as PILImage
from PIL import ImageDraw

RGBA = Tuple[int, int, int, int]

MAX_CANVAS_DIMENSION = 512  # sane upper bound for a single tile/canvas


class CanvasError(ValueError):
    """Raised for invalid canvas operations (out-of-bounds, bad size, etc.)."""


class PixelCanvas:
    """A single pixel-art canvas (e.g. one tile) backed by an RGBA PIL image."""

    def __init__(self, width: int, height: int, background: RGBA = (0, 0, 0, 0)):
        if not (1 <= width <= MAX_CANVAS_DIMENSION and 1 <= height <= MAX_CANVAS_DIMENSION):
            raise CanvasError(
                f"Canvas dimensions must be between 1 and {MAX_CANVAS_DIMENSION} pixels."
            )
        self.width = width
        self.height = height
        self.image = PILImage.new("RGBA", (width, height), background)
        self._draw = ImageDraw.Draw(self.image)

    @classmethod
    def from_file(cls, path: str) -> "PixelCanvas":
        """Load an existing PNG (or other Pillow-supported image) from disk into a new canvas.

        Lets an agent continue editing an existing sprite instead of
        always drawing from a blank canvas.
        """
        try:
            source_image = PILImage.open(path)
        except FileNotFoundError as exc:
            raise CanvasError(f"No image file found at '{path}'.") from exc
        except Exception as exc:  # Pillow raises various format-specific errors
            raise CanvasError(f"Could not open '{path}' as an image: {exc}") from exc

        rgba_image = source_image.convert("RGBA")
        width, height = rgba_image.size
        if not (1 <= width <= MAX_CANVAS_DIMENSION and 1 <= height <= MAX_CANVAS_DIMENSION):
            raise CanvasError(
                f"Image at '{path}' is {width}x{height}, outside the supported "
                f"1-{MAX_CANVAS_DIMENSION}px range."
            )
        canvas = cls(width, height)
        canvas.image = rgba_image
        canvas._draw = ImageDraw.Draw(canvas.image)
        return canvas

    def _check_bounds(self, x: int, y: int) -> None:
        if not (0 <= x < self.width and 0 <= y < self.height):
            raise CanvasError(
                f"Point ({x}, {y}) is outside the canvas ({self.width}x{self.height})."
            )

    def set_pixel(self, x: int, y: int, color: RGBA) -> None:
        self._check_bounds(x, y)
        self.image.putpixel((x, y), color)

    def get_pixel(self, x: int, y: int) -> RGBA:
        self._check_bounds(x, y)
        return self.image.getpixel((x, y))

    def draw_line(self, x0: int, y0: int, x1: int, y1: int, color: RGBA, width: int = 1) -> None:
        self._draw.line([(x0, y0), (x1, y1)], fill=color, width=width)

    def draw_rect(self, x0: int, y0: int, x1: int, y1: int, color: RGBA, fill: bool = False) -> None:
        if fill:
            self._draw.rectangle([x0, y0, x1, y1], fill=color)
        else:
            self._draw.rectangle([x0, y0, x1, y1], outline=color)

    def draw_circle(self, cx: int, cy: int, radius: int, color: RGBA, fill: bool = False) -> None:
        bbox = [cx - radius, cy - radius, cx + radius, cy + radius]
        if fill:
            self._draw.ellipse(bbox, fill=color)
        else:
            self._draw.ellipse(bbox, outline=color)

    def flood_fill(self, x: int, y: int, color: RGBA) -> None:
        self._check_bounds(x, y)
        ImageDraw.floodfill(self.image, (x, y), color)

    def clear(self, background: RGBA = (0, 0, 0, 0)) -> None:
        self.image = PILImage.new("RGBA", (self.width, self.height), background)
        self._draw = ImageDraw.Draw(self.image)

    def to_png_bytes(self) -> bytes:
        buf = io.BytesIO()
        self.image.save(buf, format="PNG")
        return buf.getvalue()

    def to_base64(self) -> str:
        return base64.b64encode(self.to_png_bytes()).decode("ascii")

    def preview_image(self, scale: int = 8) -> PILImage.Image:
        """Nearest-neighbor upscale so tiny pixel art is visible/inspectable."""
        if scale < 1:
            raise CanvasError("scale must be >= 1")
        return self.image.resize(
            (self.width * scale, self.height * scale), PILImage.NEAREST
        )

    def flip(self, horizontal: bool = True) -> None:
        """Mirror the canvas. horizontal=True flips left-right, False flips top-bottom."""
        mode = PILImage.FLIP_LEFT_RIGHT if horizontal else PILImage.FLIP_TOP_BOTTOM
        self.image = self.image.transpose(mode)
        self._draw = ImageDraw.Draw(self.image)

    def draw_polygon(self, points: list[tuple[int, int]], color: RGBA, fill: bool = False) -> None:
        if len(points) < 3:
            raise CanvasError("A polygon needs at least 3 points.")
        if fill:
            self._draw.polygon(points, fill=color)
        else:
            self._draw.polygon(points, outline=color)

    def duplicate(self) -> "PixelCanvas":
        """Return a new independent PixelCanvas with the same size and pixels."""
        clone = PixelCanvas(self.width, self.height)
        clone.image = self.image.copy()
        clone._draw = ImageDraw.Draw(clone.image)
        return clone

    def info(self) -> dict:
        """Lightweight summary (dimensions + non-transparent pixel count) without a full preview."""
        alpha_channel = self.image.split()[-1]
        if hasattr(alpha_channel, "get_flattened_data"):
            pixel_values = alpha_channel.get_flattened_data()
        else:  # pragma: no cover - fallback for older Pillow versions
            pixel_values = alpha_channel.getdata()
        non_transparent = sum(1 for a in pixel_values if a > 0)
        return {
            "width": self.width,
            "height": self.height,
            "non_transparent_pixels": non_transparent,
            "total_pixels": self.width * self.height,
        }

    def extract_palette(self, n_colors: int = 8) -> list[str]:
        """Return the top-N dominant colors in the canvas as hex strings."""
        n_colors = max(1, min(n_colors, 256))
        rgb_image = self.image.convert("RGB")
        quantized = rgb_image.quantize(colors=n_colors, method=PILImage.MEDIANCUT)
        palette = quantized.getpalette()[: n_colors * 3]
        hex_colors = []
        for i in range(0, len(palette), 3):
            r, g, b = palette[i], palette[i + 1], palette[i + 2]
            hex_colors.append(f"#{r:02x}{g:02x}{b:02x}")
        return hex_colors
