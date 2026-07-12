from __future__ import annotations

from collections.abc import Mapping

REQUIRED_KEYS = (
    "background",
    "surface",
    "foreground",
    "muted_foreground",
    "accent",
    "accent_foreground",
    "selection_background",
    "selection_foreground",
    "border",
    "error",
    "warning",
    "success",
)

_CONTRAST_PAIRS = (
    ("foreground", "background"),
    ("accent_foreground", "accent"),
    ("selection_foreground", "selection_background"),
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


def _best_contrast_foreground(background: str) -> str:
    black_ratio = contrast_ratio("#000000", background)
    white_ratio = contrast_ratio("#FFFFFF", background)
    return "#000000" if black_ratio >= white_ratio else "#FFFFFF"


def _contrast_safe_accent(seed_color: str, background: str) -> str:
    candidates = [seed_color]
    candidates.extend(_blend(seed_color, "#000000", amount) for amount in (0.2, 0.35, 0.5, 0.65, 0.8))
    candidates.extend(_blend(seed_color, "#FFFFFF", amount) for amount in (0.2, 0.35, 0.5, 0.65, 0.8))
    for candidate in candidates:
        if max(contrast_ratio("#000000", candidate), contrast_ratio("#FFFFFF", candidate)) >= 7:
            return candidate
    return "#000000" if contrast_ratio("#000000", background) >= 7 else "#FFFFFF"


def generate_palette(seed_color: str, mode: str = "dark") -> dict[str, str]:
    if mode != "dark":
        raise ValueError("Only dark mode is supported in this phase")
    seed = _to_hex(parse_hex_color(seed_color))
    background = _blend("#000000", seed, 0.12)
    surface = _blend("#000000", seed, 0.18)
    foreground = "#F7F7FA"
    accent = _contrast_safe_accent(seed, background)
    selection_background = _blend(accent, background, 0.8)
    palette = {
        "background": background,
        "surface": surface,
        "foreground": foreground,
        "muted_foreground": "#A7A9B4",
        "accent": accent,
        "accent_foreground": _best_contrast_foreground(accent),
        "selection_background": selection_background,
        "selection_foreground": _best_contrast_foreground(selection_background),
        "border": "#4A4D59",
        "error": "#F05252",
        "warning": "#F3B95F",
        "success": "#42D392",
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
    for foreground, background in _CONTRAST_PAIRS:
        if foreground in palette and background in palette:
            ratio = contrast_ratio(palette[foreground], palette[background])
            if ratio < 7:
                errors.append(f"{foreground}/{background} contrast is {ratio:.2f}:1, required >= 7:1")
    return errors
