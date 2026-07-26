import pytest

from pixelart_mcp.canvas import CanvasError, PixelCanvas


def test_create_canvas_defaults_transparent():
    c = PixelCanvas(4, 4)
    assert c.get_pixel(0, 0) == (0, 0, 0, 0)


def test_set_and_get_pixel():
    c = PixelCanvas(4, 4)
    c.set_pixel(1, 2, (255, 0, 0, 255))
    assert c.get_pixel(1, 2) == (255, 0, 0, 255)


def test_out_of_bounds_raises():
    c = PixelCanvas(4, 4)
    with pytest.raises(CanvasError):
        c.set_pixel(10, 10, (255, 0, 0, 255))
    with pytest.raises(CanvasError):
        c.get_pixel(-1, 0)


def test_invalid_dimensions_raise():
    with pytest.raises(CanvasError):
        PixelCanvas(0, 4)
    with pytest.raises(CanvasError):
        PixelCanvas(4, 9999)


def test_draw_rect_filled_vs_outline():
    filled = PixelCanvas(5, 5)
    filled.draw_rect(0, 0, 4, 4, (255, 255, 255, 255), fill=True)
    assert filled.get_pixel(2, 2) == (255, 255, 255, 255)

    outline = PixelCanvas(5, 5)
    outline.draw_rect(0, 0, 4, 4, (255, 255, 255, 255), fill=False)
    assert outline.get_pixel(2, 2) == (0, 0, 0, 0)
    assert outline.get_pixel(0, 0) == (255, 255, 255, 255)


def test_draw_line():
    c = PixelCanvas(5, 5)
    c.draw_line(0, 0, 4, 0, (0, 255, 0, 255))
    assert c.get_pixel(2, 0) == (0, 255, 0, 255)


def test_draw_circle_filled():
    c = PixelCanvas(9, 9)
    c.draw_circle(4, 4, 3, (0, 0, 255, 255), fill=True)
    assert c.get_pixel(4, 4) == (0, 0, 255, 255)


def test_flood_fill():
    c = PixelCanvas(5, 5, background=(0, 0, 0, 255))
    c.draw_rect(0, 0, 4, 4, (255, 0, 0, 255), fill=False)  # border only
    c.flood_fill(2, 2, (0, 255, 0, 255))
    assert c.get_pixel(2, 2) == (0, 255, 0, 255)
    assert c.get_pixel(0, 0) == (255, 0, 0, 255)  # border untouched


def test_clear_resets_canvas():
    c = PixelCanvas(3, 3)
    c.set_pixel(1, 1, (255, 0, 0, 255))
    c.clear()
    assert c.get_pixel(1, 1) == (0, 0, 0, 0)


def test_preview_upscale_dimensions():
    c = PixelCanvas(4, 4)
    preview = c.preview_image(scale=8)
    assert preview.size == (32, 32)


def test_preview_invalid_scale_raises():
    c = PixelCanvas(4, 4)
    with pytest.raises(CanvasError):
        c.preview_image(scale=0)


def test_to_png_bytes_is_valid_png():
    c = PixelCanvas(4, 4)
    data = c.to_png_bytes()
    assert data[:8] == b"\x89PNG\r\n\x1a\n"


def test_extract_palette_returns_hex_colors():
    c = PixelCanvas(4, 4, background=(255, 0, 0, 255))
    colors = c.extract_palette(n_colors=2)
    assert all(col.startswith("#") and len(col) == 7 for col in colors)


def test_flip_horizontal_moves_pixel_to_mirrored_column():
    c = PixelCanvas(4, 4)
    c.set_pixel(0, 0, (255, 0, 0, 255))
    c.flip(horizontal=True)
    assert c.get_pixel(3, 0) == (255, 0, 0, 255)
    assert c.get_pixel(0, 0) == (0, 0, 0, 0)


def test_flip_vertical_moves_pixel_to_mirrored_row():
    c = PixelCanvas(4, 4)
    c.set_pixel(0, 0, (255, 0, 0, 255))
    c.flip(horizontal=False)
    assert c.get_pixel(0, 3) == (255, 0, 0, 255)


def test_draw_polygon_filled():
    c = PixelCanvas(6, 6)
    c.draw_polygon([(0, 0), (5, 0), (5, 5), (0, 5)], (0, 0, 255, 255), fill=True)
    assert c.get_pixel(2, 2) == (0, 0, 255, 255)


def test_draw_polygon_requires_min_three_points():
    c = PixelCanvas(6, 6)
    with pytest.raises(CanvasError):
        c.draw_polygon([(0, 0), (1, 1)], (255, 0, 0, 255))


def test_duplicate_creates_independent_copy():
    c = PixelCanvas(4, 4)
    c.set_pixel(1, 1, (255, 0, 0, 255))
    clone = c.duplicate()
    clone.set_pixel(2, 2, (0, 255, 0, 255))
    assert c.get_pixel(2, 2) == (0, 0, 0, 0)  # original untouched
    assert clone.get_pixel(1, 1) == (255, 0, 0, 255)  # copied pixel present


def test_info_counts_non_transparent_pixels():
    c = PixelCanvas(4, 4)
    c.set_pixel(0, 0, (255, 0, 0, 255))
    c.set_pixel(1, 1, (255, 0, 0, 255))
    info = c.info()
    assert info["width"] == 4
    assert info["height"] == 4
    assert info["non_transparent_pixels"] == 2
    assert info["total_pixels"] == 16


def test_from_file_loads_existing_png(tmp_path):
    original = PixelCanvas(3, 3, background=(1, 2, 3, 255))
    original.set_pixel(1, 1, (9, 9, 9, 255))
    path = tmp_path / "sprite.png"
    with open(path, "wb") as f:
        f.write(original.to_png_bytes())

    loaded = PixelCanvas.from_file(str(path))
    assert loaded.width == 3
    assert loaded.height == 3
    assert loaded.get_pixel(0, 0) == (1, 2, 3, 255)
    assert loaded.get_pixel(1, 1) == (9, 9, 9, 255)


def test_from_file_missing_path_raises():
    with pytest.raises(CanvasError, match="No image file found"):
        PixelCanvas.from_file("/nonexistent/path/sprite.png")


def test_from_file_invalid_image_raises(tmp_path):
    bogus = tmp_path / "not_an_image.png"
    bogus.write_text("this is not image data")
    with pytest.raises(CanvasError, match="Could not open"):
        PixelCanvas.from_file(str(bogus))
