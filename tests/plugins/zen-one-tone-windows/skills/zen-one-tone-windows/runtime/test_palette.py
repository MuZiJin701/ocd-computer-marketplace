import colorsys

import pytest

from one_tone.palette import (
    _oklch_components,
    contrast_ratio,
    generate_palette,
    parse_hex_color,
    relative_luminance,
    validate_mode_coherence,
    validate_palette,
)


def _hue(color: str) -> float:
    red, green, blue = parse_hex_color(color)
    return colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)[0]


def _circular_hue_distance(first: str, second: str) -> float:
    distance = abs(_hue(first) - _hue(second))
    return min(distance, 1 - distance)


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
        "accent", "accent_text", "accent_foreground", "selection_background",
        "selection_foreground", "border", "error", "error_text", "warning", "warning_text",
        "success", "success_text",
    }
    assert validate_palette(palette) == []
    assert palette["surface"] == "#7C3AED"
    assert contrast_ratio(palette["background_foreground"], palette["background"]) >= 7
    assert contrast_ratio(palette["foreground"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["muted_foreground"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["accent_foreground"], palette["accent"]) >= 4.5
    assert contrast_ratio(palette["accent_text"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["error_text"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["warning_text"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["success_text"], palette["surface"]) >= 4.5
    assert contrast_ratio(palette["selection_foreground"], palette["selection_background"]) >= 4.5


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
    assert contrast_ratio(palette["accent_text"], palette["surface"]) >= 4.5
    assert int(palette["background"][3:5], 16) > int(palette["background"][5:7], 16)


def test_legacy_single_palette_keeps_original_accent_selection():
    assert generate_palette("#7C3AED")["accent"] == "#E8D1FF"


def test_surface_text_uses_the_4_5_minimum_to_preserve_more_seed_colors():
    palette = generate_palette("#10B981")

    ratio = contrast_ratio(palette["foreground"], palette["surface"])
    assert 4.5 <= ratio < 5.5


def test_explicit_modes_keep_seed_anchor_and_separate_tonal_surface_roles():
    for mode in ("light", "dark"):
        palette = generate_palette("#7C3AED", mode)
        assert palette["surface"] != "#7C3AED"
        assert len({palette["surface"], palette["surface_subtle"], palette["surface_raised"]}) == 3
        assert contrast_ratio(palette["surface_subtle"], palette["surface"]) >= 1.2
        assert contrast_ratio(palette["surface_raised"], palette["surface"]) >= 1.2


def test_explicit_modes_preserve_coherent_tones_and_accent_identity():
    light = generate_palette("#7C3AED", "light")
    dark = generate_palette("#7C3AED", "dark")

    assert relative_luminance(light["surface_raised"]) < 0.90
    assert relative_luminance(dark["surface_subtle"]) > 0.005
    assert _circular_hue_distance(light["accent"], dark["accent"]) <= 0.04
    assert validate_mode_coherence("#7C3AED", {"light": light, "dark": dark}) == []


def test_explicit_modes_keep_large_area_roles_within_coherence_lightness_limit():
    for seed in ("#7C3AED", "#00A86B", "#FF0000", "#FAFAFA"):
        light = generate_palette(seed, "light")
        dark = generate_palette(seed, "dark")
        for role in ("background", "surface_subtle", "surface", "surface_raised"):
            lightness_delta = abs(_oklch_components(light[role])[0] - _oklch_components(dark[role])[0])
            assert lightness_delta <= 0.35


def test_validate_mode_coherence_rejects_large_cross_mode_tone_delta():
    light = generate_palette("#7C3AED", "light")
    dark = generate_palette("#7C3AED", "dark")
    light["background"] = light["surface_raised"]

    errors = validate_mode_coherence("#7C3AED", {"light": light, "dark": dark})

    assert any("lightness" in error for error in errors)


def test_explicit_modes_validate_coherence_for_representative_seed_colors():
    for seed in ("#FF0000", "#00A86B", "#00FFFF", "#010101", "#FAFAFA"):
        palettes = {mode: generate_palette(seed, mode) for mode in ("light", "dark")}
        assert validate_mode_coherence(seed, palettes) == []


def test_extreme_seed_colors_keep_tonal_surfaces_and_readable_interactions():
    for seed in ("#FF0000", "#FFFF00", "#00FFFF", "#800080", "#010101", "#FAFAFA"):
        for mode in ("light", "dark"):
            palette = generate_palette(seed, mode)
            assert palette["surface"] != seed
            assert all(palette[role] not in {"#000000", "#FFFFFF"} for role in (
                "background", "surface", "surface_subtle", "surface_raised", "accent", "border",
                "selection_background",
            ))
            assert contrast_ratio(palette["accent"], palette["surface"]) >= 3
            assert validate_palette(palette) == []
