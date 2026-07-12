import pytest

from one_tone.palette import (
    contrast_ratio,
    generate_palette,
    parse_hex_color,
    validate_palette,
)


def test_parse_hex_color_normalizes_three_and_six_digit_values():
    assert parse_hex_color("#abc") == (170, 187, 204)
    assert parse_hex_color("7C3AED") == (124, 58, 237)


def test_parse_hex_color_rejects_invalid_value():
    with pytest.raises(ValueError, match="HEX"):
        parse_hex_color("purple")


def test_generate_palette_contains_required_semantic_colors_and_passes_contrast():
    palette = generate_palette("#7C3AED")

    assert set(palette) == {
        "background", "surface", "foreground", "muted_foreground",
        "accent", "accent_foreground", "selection_background",
        "selection_foreground", "border", "error", "warning", "success",
    }
    assert validate_palette(palette) == []
    assert contrast_ratio(palette["foreground"], palette["background"]) >= 7


def test_palette_validation_reports_contrast_failure():
    palette = generate_palette("#7C3AED")
    palette["foreground"] = palette["background"]

    assert "foreground/background" in validate_palette(palette)[0]


def test_green_seed_tints_background_and_surface():
    palette = generate_palette("#00A86B")

    assert palette["background"] != "#111318"
    assert palette["surface"] != "#1B1D24"
    assert int(palette["background"][3:5], 16) > int(palette["background"][5:7], 16)
