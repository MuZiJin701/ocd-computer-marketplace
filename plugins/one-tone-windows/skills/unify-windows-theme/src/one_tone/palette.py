from __future__ import annotations

import colorsys
from collections.abc import Mapping

REQUIRED_KEYS = (
    "background",
    "background_foreground",
    "surface",
    "foreground",
    "muted_foreground",
    "accent",
    "accent_text",
    "accent_foreground",
    "selection_background",
    "selection_foreground",
    "border",
    "error",
    "error_text",
    "warning",
    "warning_text",
    "success",
    "success_text",
)

_CONTRAST_PAIRS = (
    ("background_foreground", "background", 7),
    ("foreground", "surface", 5.5),
    ("muted_foreground", "surface", 4.5),
    ("accent_text", "surface", 5.5),
    ("error_text", "surface", 5.5),
    ("warning_text", "surface", 5.5),
    ("success_text", "surface", 5.5),
    ("accent_foreground", "accent", 5.5),
    ("selection_foreground", "selection_background", 5.5),
)


def parse_hex_color(value: str) -> tuple[int, int, int]:
    if not isinstance(value, str):
        raise ValueError("HEX color must be a string")
    normalized = value.strip().removeprefix("#")
    if len(normalized) == 3:
        normalized = "".join(char * 2 for char in normalized)
    if len(normalized) != 6 or any(char not in "0123456789abcdefABCDEF" for char in normalized):
        raise ValueError(f"Invalid HEX color: {value!r}")
    return tuple(int(normalized[index:index + 2], 16) for index in (0, 2, 4))


def _to_hex(rgb: tuple[int, int, int]) -> str:
    return "#" + "".join(f"{max(0, min(255, channel)):02X}" for channel in rgb)


def _blend(first: str, second: str, second_weight: float) -> str:
    first_rgb = parse_hex_color(first)
    second_rgb = parse_hex_color(second)
    return _to_hex(
        tuple(
            round(left * (1 - second_weight) + right * second_weight)
            for left, right in zip(first_rgb, second_rgb)
        )
    )


def _channel_luminance(channel: int) -> float:
    value = channel / 255
    return value / 12.92 if value <= 0.03928 else ((value + 0.055) / 1.055) ** 2.4


def relative_luminance(color: str) -> float:
    red, green, blue = parse_hex_color(color)
    return (
        0.2126 * _channel_luminance(red)
        + 0.7152 * _channel_luminance(green)
        + 0.0722 * _channel_luminance(blue)
    )


def contrast_ratio(foreground: str, background: str) -> float:
    first = relative_luminance(foreground)
    second = relative_luminance(background)
    return (max(first, second) + 0.05) / (min(first, second) + 0.05)


def _hls_color(hue: float, lightness: float, saturation: float) -> str:
    rgb = colorsys.hls_to_rgb(
        hue % 1.0,
        max(0.01, min(0.99, lightness)),
        max(0.08, min(0.95, saturation)),
    )
    return _to_hex(tuple(round(channel * 255) for channel in rgb))


def _chromatic_candidates(color: str) -> list[str]:
    red, green, blue = parse_hex_color(color)
    hue, _lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    candidates: list[str] = []
    for lightness_step in range(1, 100):
        lightness = lightness_step / 100
        for candidate_saturation in (
            max(0.08, saturation),
            max(0.08, saturation * 0.88),
            max(0.08, saturation * 0.72),
            max(0.08, saturation * 0.45),
            max(0.08, saturation * 0.25),
            0.12,
            0.2,
            0.35,
            0.5,
        ):
            candidate = _hls_color(hue, lightness, candidate_saturation)
            if candidate not in candidates and candidate not in {"#000000", "#FFFFFF"}:
                candidates.append(candidate)
    return candidates


def _chromatic_foreground(
    backgrounds: tuple[str, ...],
    minimum_ratio: float,
    source_color: str | None = None,
) -> str:
    source = source_color or backgrounds[0]
    candidates = _chromatic_candidates(source)
    valid = [
        candidate
        for candidate in candidates
        if min(contrast_ratio(candidate, background) for background in backgrounds) >= minimum_ratio
    ]
    if valid:
        source_luminance = relative_luminance(source)
        source_hue = colorsys.rgb_to_hls(*(channel / 255 for channel in parse_hex_color(source)))[0]
        desired_lightness = 0.12 if source_luminance >= 0.179 else 0.88
        return max(
            valid,
            key=lambda candidate: (
                -abs(colorsys.rgb_to_hls(*(channel / 255 for channel in parse_hex_color(candidate)))[1] - desired_lightness),
                _chromatic_saturation(candidate),
                -abs(colorsys.rgb_to_hls(*(channel / 255 for channel in parse_hex_color(candidate)))[0] - source_hue),
            ),
        )
    return max(
        candidates,
        key=lambda candidate: (
            min(contrast_ratio(candidate, background) for background in backgrounds),
            _chromatic_saturation(candidate),
        ),
    )


def _chromatic_saturation(color: str) -> float:
    red, green, blue = parse_hex_color(color)
    return colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)[2]


def _contrast_safe_accent(seed_color: str, background: str) -> str:
    red, green, blue = parse_hex_color(seed_color)
    hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    candidates = [
        _hls_color(hue, lightness + delta, min(0.95, max(0.2, saturation * factor)))
        for delta in (0.28, -0.28, 0.18, -0.18, 0.38, -0.38)
        for factor in (1.0, 0.75)
    ]
    candidates = [candidate for candidate in candidates if candidate != seed_color]
    return max(candidates, key=lambda candidate: contrast_ratio(candidate, background))


def generate_palette(seed_color: str, mode: str = "dark") -> dict[str, str]:
    if mode != "dark":
        raise ValueError("Only dark mode is supported in this phase")
    seed = _to_hex(parse_hex_color(seed_color))
    red, green, blue = parse_hex_color(seed)
    _hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
    background = _hls_color(_hue, min(0.18, max(0.06, lightness * 0.38)), max(0.24, saturation * 0.72))
    surface = seed
    background_foreground = _chromatic_foreground((background,), 7)
    foreground = _chromatic_foreground((surface,), 5.5)
    muted_foreground = _chromatic_foreground((surface,), 4.5)
    accent = _contrast_safe_accent(seed, background)
    selection_background = _blend(accent, background, 0.8)
    error = "#F05252"
    warning = "#F3B95F"
    success = "#42D392"
    palette = {
        "background": background,
        "background_foreground": background_foreground,
        "surface": surface,
        "foreground": foreground,
        "muted_foreground": muted_foreground,
        "accent": accent,
        "accent_text": _chromatic_foreground((surface,), 5.5, source_color=accent),
        "accent_foreground": _chromatic_foreground((accent,), 5.5),
        "selection_background": selection_background,
        "selection_foreground": _chromatic_foreground((selection_background,), 5.5),
        "border": "#4A4D59",
        "error": error,
        "error_text": _chromatic_foreground((surface,), 5.5, source_color=error),
        "warning": warning,
        "warning_text": _chromatic_foreground((surface,), 5.5, source_color=warning),
        "success": success,
        "success_text": _chromatic_foreground((surface,), 5.5, source_color=success),
    }
    errors = validate_palette(palette)
    if errors:
        raise ValueError("Generated palette failed validation: " + "; ".join(errors))
    return palette


def validate_palette(palette: Mapping[str, str]) -> list[str]:
    errors: list[str] = []
    missing = [key for key in REQUIRED_KEYS if key not in palette]
    if missing:
        errors.append("missing keys: " + ", ".join(missing))
    for key in REQUIRED_KEYS:
        if key in palette:
            try:
                parse_hex_color(palette[key])
            except ValueError as error:
                errors.append(f"{key}: {error}")
    for foreground, background, minimum_ratio in _CONTRAST_PAIRS:
        if foreground in palette and background in palette:
            ratio = contrast_ratio(palette[foreground], palette[background])
            if ratio < minimum_ratio:
                errors.append(f"{foreground}/{background} contrast is {ratio:.2f}:1, required >= {minimum_ratio:g}:1")
    return errors
