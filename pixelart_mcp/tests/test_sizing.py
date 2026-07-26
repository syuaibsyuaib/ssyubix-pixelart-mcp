import pytest

from pixelart_mcp.sizing import suggest_tile_size, suggest_tilemap_layout


def test_default_fallback_is_16x16():
    result = suggest_tile_size()
    assert result["tile_width"] == 16
    assert result["tile_height"] == 16
    assert result["ppu"] == 16


def test_suggest_tile_size_includes_tilemap_warning_note():
    result = suggest_tile_size()
    assert "note" in result
    assert "ONE tile" in result["note"] or "one tile" in result["note"].lower()


def test_category_small_prop():
    result = suggest_tile_size(category="small_prop")
    assert (result["tile_width"], result["tile_height"]) == (16, 16)


def test_category_character():
    result = suggest_tile_size(category="character")
    assert (result["tile_width"], result["tile_height"]) == (16, 32)


def test_category_structure():
    result = suggest_tile_size(category="structure")
    assert (result["tile_width"], result["tile_height"]) == (48, 48)


def test_unknown_category_raises():
    with pytest.raises(ValueError):
        suggest_tile_size(category="spaceship")


def test_screen_resolution_picks_dividing_ppu():
    result = suggest_tile_size(screen_width=1920, screen_height=1080)
    assert 1920 % result["tile_width"] == 0
    assert 1080 % result["tile_height"] == 0


def test_category_takes_priority_over_screen_size():
    result = suggest_tile_size(category="character", screen_width=1920, screen_height=1080)
    assert (result["tile_width"], result["tile_height"]) == (16, 32)


def test_tilemap_layout_from_explicit_columns_rows():
    result = suggest_tilemap_layout(tile_width=16, tile_height=16, columns=20, rows=15)
    assert result["total_tiles"] == 300
    assert result["total_map_width_px"] == 320
    assert result["total_map_height_px"] == 240


def test_tilemap_layout_from_screen_size_derives_grid():
    result = suggest_tilemap_layout(tile_width=16, tile_height=16, screen_width=320, screen_height=240)
    assert result["columns"] == 20
    assert result["rows"] == 15


def test_tilemap_layout_rejects_single_tile_confusion():
    # A "tilemap" the size of one tile should never be returned as valid:
    # asking for 1x1 is technically allowed, but must be explicit, not a default.
    result = suggest_tilemap_layout(tile_width=32, tile_height=32, columns=1, rows=1)
    assert result["total_map_width_px"] == 32
    assert result["total_tiles"] == 1


def test_tilemap_layout_requires_columns_rows_or_screen_size():
    with pytest.raises(ValueError, match="Provide either"):
        suggest_tilemap_layout(tile_width=16, tile_height=16)


def test_tilemap_layout_rejects_oversized_grid():
    with pytest.raises(ValueError, match="exceeds"):
        suggest_tilemap_layout(tile_width=16, tile_height=16, columns=1000, rows=1000)
