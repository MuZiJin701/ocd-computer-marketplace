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
        "background", "background_foreground", "surface", "foreground", "muted_foreground",
        "accent", "accent_foreground", "selection_background",
        "selection_foreground", "border", "error", "warning", "success",
    }
    assert validate_palette(palette) == []
    assert palette["surface"] == "#7C3AED"
    assert contrast_ratio(palette["background_foreground"], palette["background"]) >= 7
    assert contrast_ratio(palette["foreground"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["muted_foreground"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["accent_foreground"], palette["accent"]) >= 4.5


def test_palette_validation_reports_contrast_failure():
    palette = generate_palette("#7C3AED")
    palette["foreground"] = palette["background"]

    palette["background_foreground"] = palette["background"]

    assert "background_foreground/background" in validate_palette(palette)[0]


def test_green_seed_tints_background_and_surface():
    palette = generate_palette("#00A86B")

    assert palette["background"] != "#111318"
    assert palette["surface"] == "#00A86B"
    assert contrast_ratio(palette["foreground"], palette["surface"]) >= 4.5
    assert palette["foreground"] not in {"#000000", "#FFFFFF"}
    assert int(palette["background"][3:5], 16) > int(palette["background"][5:7], 16)
