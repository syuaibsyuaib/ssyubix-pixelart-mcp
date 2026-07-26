import re

from pixelart_mcp.palette import available_styles, generate_palette

HEX_RE = re.compile(r"^#[0-9a-f]{6}$")


def test_generate_palette_default_count():
    colors = generate_palette(n_colors=8)
    assert len(colors) == 8
    assert all(HEX_RE.match(c) for c in colors)


def test_generate_palette_clamps_range():
    assert len(generate_palette(n_colors=0)) == 1
    assert len(generate_palette(n_colors=1000)) == 64


def test_generate_palette_with_known_style():
    colors = generate_palette(n_colors=5, style="forest")
    assert len(colors) == 5
    assert all(HEX_RE.match(c) for c in colors)


def test_generate_palette_unknown_style_falls_back():
    colors = generate_palette(n_colors=5, style="not-a-real-style")
    assert len(colors) == 5
    assert all(HEX_RE.match(c) for c in colors)


def test_generate_palette_is_deterministic_for_style():
    a = generate_palette(n_colors=6, style="retro")
    b = generate_palette(n_colors=6, style="retro")
    assert a == b


def test_available_styles_nonempty():
    styles = available_styles()
    assert "forest" in styles
    assert "retro" in styles
