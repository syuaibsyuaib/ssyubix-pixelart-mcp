import pytest

from pixelart_mcp.sizing import suggest_tile_size


def test_default_fallback_is_16x16():
    result = suggest_tile_size()
    assert result["tile_width"] == 16
    assert result["tile_height"] == 16
    assert result["ppu"] == 16


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
