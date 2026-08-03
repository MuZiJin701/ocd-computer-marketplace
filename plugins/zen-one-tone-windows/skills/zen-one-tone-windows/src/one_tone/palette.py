from __future__ import annotations

import colorsys
import math
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
    ("foreground", "surface", 4.5),
    ("muted_foreground", "surface", 4.5),
    ("prediction_foreground", "surface", 4.5),
    ("accent_text", "surface", 4.5),
    ("error_text", "surface", 4.5),
    ("warning_text", "surface", 4.5),
    ("success_text", "surface", 4.5),
    ("accent_foreground", "accent", 4.5),
    ("selection_foreground", "selection_background", 4.5),
)

REGION_SEPARATION_PAIRS = (
    ("surface_subtle", "surface", 1.2),
    ("surface_raised", "surface", 1.2),
    ("surface", "background", 1.2),
)

INTERACTIVE_SEPARATION_PAIRS = (
    ("accent", "surface", 3),
    ("selection_background", "surface", 3),
    ("border", "surface", 3),
)

MODE_ACCENT_HUE_TOLERANCE = 0.04
MODE_ACCENT_MIN_LIGHTNESS = 0.08
MODE_ACCENT_MAX_LIGHTNESS = 0.92
MODE_ACCENT_LIGHTNESS_DELTA = 0.55
MODE_TONAL_LIGHTNESS_DELTA = 0.35
MODE_LIGHT_SURFACE_MAX_LUMINANCE = 0.90
MODE_DARK_SURFACE_MIN_LUMINANCE = 0.005
PREDICTION_MIN_CONTRAST = 4.5
PREDICTION_MIN_DISTANCE = 0.08
PREDICTION_MAX_CHROMA = 0.04
PREDICTION_HUE = 0.58


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


def _srgb_to_linear(channel: float) -> float:
    return channel / 12.92 if channel <= 0.04045 else ((channel + 0.055) / 1.055) ** 2.4


def _linear_to_srgb(channel: float) -> float:
    return 12.92 * channel if channel <= 0.0031308 else 1.055 * (max(0.0, channel) ** (1 / 2.4)) - 0.055


def _cbrt(value: float) -> float:
    return math.copysign(abs(value) ** (1 / 3), value)


def _oklch_components(color: str) -> tuple[float, float, float]:
    red, green, blue = ( _srgb_to_linear(channel / 255) for channel in parse_hex_color(color))
    l = _cbrt(0.4122214708 * red + 0.5363325363 * green + 0.0514459929 * blue)
    m = _cbrt(0.2119034982 * red + 0.6806995451 * green + 0.1073969566 * blue)
    s = _cbrt(0.0883024619 * red + 0.2817188376 * green + 0.6299787005 * blue)
    lightness = 0.2104542553 * l + 0.7936177850 * m - 0.0040720468 * s
    a = 1.9779984951 * l - 2.4285922050 * m + 0.4505937099 * s
    b = 0.0259040371 * l + 0.7827717662 * m - 0.8086757660 * s
    return lightness, math.hypot(a, b), math.atan2(b, a) / (2 * math.pi) % 1


def _oklab_components(color: str) -> tuple[float, float, float]:
    lightness, chroma, hue = _oklch_components(color)
    angle = hue * 2 * math.pi
    return lightness, chroma * math.cos(angle), chroma * math.sin(angle)


def _oklab_delta_e(first: str, second: str) -> float:
    return math.dist(_oklab_components(first), _oklab_components(second))


def _oklch_color(hue: float, lightness: float, chroma: float) -> str:
    angle = hue * 2 * math.pi
    a = chroma * math.cos(angle)
    b = chroma * math.sin(angle)
    l = lightness + 0.3963377774 * a + 0.2158037573 * b
    m = lightness - 0.1055613458 * a - 0.0638541728 * b
    s = lightness - 0.0894841775 * a - 1.2914855480 * b
    l, m, s = l**3, m**3, s**3
    red = 4.0767416621 * l - 3.3077115913 * m + 0.2309699292 * s
    green = -1.2684380046 * l + 2.6097574011 * m - 0.3413193965 * s
    blue = -0.0041960863 * l - 0.7034186147 * m + 1.7076147010 * s
    return _to_hex(tuple(round(max(0.0, min(1.0, _linear_to_srgb(channel))) * 255) for channel in (red, green, blue)))


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


def _readable_foreground(
    backgrounds: tuple[str, ...],
    minimum_ratio: float,
    hue: float = 0.58,
    minimum_lightness: int = 4,
) -> str:
    candidates = [
        _hls_color(hue, lightness / 100, saturation)
        for lightness in range(minimum_lightness, 100)
        for saturation in (0.08, 0.12, 0.18)
    ]
    valid = [
        candidate
        for candidate in candidates
        if min(contrast_ratio(candidate, background) for background in backgrounds) >= minimum_ratio
    ]
    if not valid:
        return max(candidates, key=lambda candidate: min(contrast_ratio(candidate, background) for background in backgrounds))
    desired_lightness = 0.14 if max(relative_luminance(background) for background in backgrounds) > 0.179 else 0.88
    return min(
        valid,
        key=lambda candidate: abs(colorsys.rgb_to_hls(*(channel / 255 for channel in parse_hex_color(candidate)))[1] - desired_lightness),
    )


def _prediction_foreground(surface: str, foreground: str) -> str | None:
    candidates = [
        (_hls_color(PREDICTION_HUE, lightness / 100, saturation), lightness / 100, saturation)
        for lightness in range(4, 97)
        for saturation in (0.08, 0.12, 0.18)
    ]
    valid = [
        candidate
        for candidate in candidates
        if contrast_ratio(candidate[0], surface) >= PREDICTION_MIN_CONTRAST
        and _oklch_components(candidate[0])[1] <= PREDICTION_MAX_CHROMA
        and _oklab_delta_e(candidate[0], foreground) >= PREDICTION_MIN_DISTANCE
    ]
    if not valid:
        return None
    desired_lightness = 0.20 if relative_luminance(surface) > 0.179 else 0.72
    return min(
        valid,
        key=lambda candidate: (
            abs(candidate[1] - desired_lightness),
            candidate[2],
        ),
    )[0]


def _chromatic_saturation(color: str) -> float:
    red, green, blue = parse_hex_color(color)
    return colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)[2]


def _circular_hue_distance(first: float, second: float) -> float:
    distance = abs(first - second)
    return min(distance, 1 - distance)


def _contrast_safe_accent(
    seed_color: str,
    background: str,
    preserve_identity: bool = False,
    allow_low_chroma: bool = False,
) -> str:
    seed_lightness, seed_chroma, hue = _oklch_components(seed_color)
    target_chroma = min(0.16, max(0.035, seed_chroma))
    factors = (1.0, 0.8, 0.6, 0.4, 0.25) if allow_low_chroma else (1.0, 0.8, 0.6)
    candidates = [
        _oklch_color(hue, candidate_lightness / 100, min(0.16, max(0.035, seed_chroma * factor)))
        for candidate_lightness in range(8, 93)
        for factor in factors
    ]
    candidates = [candidate for candidate in candidates if candidate not in {"#000000", "#FFFFFF"}]
    valid = [candidate for candidate in candidates if contrast_ratio(candidate, background) >= 3]

    def theme_distance(candidate: str) -> tuple[float, float, float]:
        lightness, chroma, _ = _oklch_components(candidate)
        return (
            abs(lightness - seed_lightness),
            abs(chroma - target_chroma),
            -contrast_ratio(candidate, background),
        )

    if preserve_identity:
        return min(valid or candidates, key=theme_distance)
    return max(valid or candidates, key=lambda candidate: contrast_ratio(candidate, background))


def _ensure_contrast(color: str, background: str, minimum_ratio: float) -> str:
    if contrast_ratio(color, background) >= minimum_ratio:
        return color
    _lightness, chroma, hue = _oklch_components(color)
    candidates = [
        _oklch_color(hue, lightness / 100, min(0.16, max(0.02, chroma * factor)))
        for lightness in range(4, 98)
        for factor in (1.0, 0.8, 0.6, 0.35)
    ]
    candidates = [candidate for candidate in candidates if candidate not in {"#000000", "#FFFFFF"}]
    return max(candidates, key=lambda candidate: contrast_ratio(candidate, background))


def _generate_palette(seed_color: str, mode: str) -> dict[str, str]:
    seed = _to_hex(parse_hex_color(seed_color))
    _lightness, seed_chroma, hue = _oklch_components(seed)
    tonal_chroma = min(0.045, max(0.018, seed_chroma * 0.22))
    if mode == "dark":
        background = _oklch_color(hue, 0.24, tonal_chroma)
        surface = _oklch_color(hue, 0.34, tonal_chroma)
        surface_subtle = _oklch_color(hue, 0.26, tonal_chroma)
        surface_raised = _oklch_color(hue, 0.42, tonal_chroma)
    else:
        background = _oklch_color(hue, 0.44, tonal_chroma)
        surface = _oklch_color(hue, 0.686, tonal_chroma)
        surface_subtle = _oklch_color(hue, 0.58, tonal_chroma)
        surface_raised = _oklch_color(hue, 0.75, tonal_chroma)
    background_foreground = _readable_foreground((background,), 7)
    foreground = _readable_foreground(
        (surface,), 7 if mode == "light" else 4.5, minimum_lightness=2 if mode == "light" else 4
    )
    muted_foreground = _readable_foreground((surface,), 4.5, hue=0.52)
    accent = _contrast_safe_accent(seed, surface, preserve_identity=True, allow_low_chroma=True)
    accent_lightness, accent_chroma, accent_hue = _oklch_components(accent)
    selection_background = _oklch_color(accent_hue, accent_lightness, accent_chroma * 0.72)
    if (
        contrast_ratio(selection_background, surface) < 3
        or contrast_ratio(_readable_foreground((selection_background,), 4.5), selection_background) < 4.5
    ):
        selection_background = accent
    border_lightness = accent_lightness - 0.12 if accent_lightness > 0.5 else accent_lightness + 0.12
    border = _oklch_color(accent_hue, max(0.04, min(0.96, border_lightness)), accent_chroma * 0.72)
    if contrast_ratio(border, surface) < 3:
        border = accent
    error = "#F05252"
    warning = "#F3B95F"
    success = "#42D392"
    palette = {
        "background": background,
        "background_foreground": background_foreground,
        "surface": surface,
        "surface_subtle": surface_subtle,
        "surface_raised": surface_raised,
        "foreground": foreground,
        "muted_foreground": muted_foreground,
        "accent": accent,
        "accent_text": _readable_foreground((surface,), 4.5),
        "accent_foreground": _readable_foreground((accent,), 4.5),
        "selection_background": selection_background,
        "selection_foreground": _readable_foreground((selection_background,), 4.5),
        "border": border,
        "error": error,
        "error_text": _readable_foreground((surface,), 4.5, hue=0.02),
        "warning": warning,
        "warning_text": _readable_foreground((surface,), 4.5, hue=0.12),
        "success": success,
        "success_text": _readable_foreground((surface,), 4.5, hue=0.40),
    }
    prediction_foreground = _prediction_foreground(surface, foreground)
    if prediction_foreground is not None:
        palette["prediction_foreground"] = prediction_foreground
    errors = validate_palette(palette, mode=mode)
    if errors:
        raise ValueError("Generated palette failed validation: " + "; ".join(errors))
    return palette


def generate_palette(seed_color: str, mode: str | None = None) -> dict[str, str]:
    """Generate a mode palette; omitted mode preserves the v1 palette shape."""
    if mode is None:
        # Keep the public v1 helper stable for callers that only need the original
        # semantic palette. Plans use the explicit mode form below.
        seed = _to_hex(parse_hex_color(seed_color))
        red, green, blue = parse_hex_color(seed)
        hue, lightness, saturation = colorsys.rgb_to_hls(red / 255, green / 255, blue / 255)
        background = _hls_color(hue, min(0.18, max(0.06, lightness * 0.38)), max(0.24, saturation * 0.72))
        background_foreground = _chromatic_foreground((background,), 7)
        foreground = _chromatic_foreground((seed,), 4.5)
        accent = _contrast_safe_accent(seed, background)
        palette = {
            "background": background,
            "background_foreground": background_foreground,
            "surface": seed,
            "foreground": foreground,
            "muted_foreground": foreground,
            "accent": accent,
            "accent_text": _chromatic_foreground((seed,), 4.5, source_color=accent),
            "accent_foreground": _chromatic_foreground((accent,), 4.5),
            "selection_background": _blend(accent, background, 0.8),
            "selection_foreground": _chromatic_foreground((_blend(accent, background, 0.8),), 4.5),
            "border": "#4A4D59",
            "error": "#F05252",
            "error_text": _chromatic_foreground((seed,), 4.5, source_color="#F05252"),
            "warning": "#F3B95F",
            "warning_text": _chromatic_foreground((seed,), 4.5, source_color="#F3B95F"),
            "success": "#42D392",
            "success_text": _chromatic_foreground((seed,), 4.5, source_color="#42D392"),
        }
        errors = validate_palette(palette)
        if errors:
            raise ValueError("Generated palette failed validation: " + "; ".join(errors))
        return palette
    if mode not in {"light", "dark"}:
        raise ValueError("mode must be 'light' or 'dark'")
    palette = _generate_palette(seed_color, mode)
    return palette


def validate_palette(palette: Mapping[str, str], *, mode: str | None = None) -> list[str]:
    errors: list[str] = []
    invalid_keys: set[str] = set()
    required_keys = REQUIRED_KEYS
    missing = [key for key in required_keys if key not in palette]
    if missing:
        errors.append("missing keys: " + ", ".join(missing))
    for key in required_keys:
        if key in palette:
            try:
                parse_hex_color(palette[key])
            except ValueError as error:
                invalid_keys.add(key)
                errors.append(f"{key}: {error}")
    if "prediction_foreground" in palette:
        try:
            parse_hex_color(palette["prediction_foreground"])
        except ValueError as error:
            invalid_keys.add("prediction_foreground")
            errors.append(f"prediction_foreground: {error}")
    for foreground, background, minimum_ratio in _CONTRAST_PAIRS:
        if mode == "light" and foreground == "foreground":
            minimum_ratio = 7
        if foreground in palette and background in palette and not ({foreground, background} & invalid_keys):
            ratio = contrast_ratio(palette[foreground], palette[background])
            if ratio < minimum_ratio:
                errors.append(f"contrast: {foreground}/{background} is {ratio:.2f}:1, required >= {minimum_ratio:g}:1")
    if "surface_subtle" in palette:
        tonal_roles = ("background", "surface", "surface_subtle", "surface_raised")
        interactive_roles = ("accent", "border", "selection_background")
        for role in tonal_roles + interactive_roles:
            if role not in palette:
                continue
            color = palette[role].upper()
            if color in {"#000000", "#FFFFFF"}:
                errors.append(f"appearance safety: {role} must not be pure black or white")
            if role in tonal_roles and _oklch_components(color)[1] > 0.06:
                errors.append(f"appearance safety: {role} chroma is too high for a large area")
        for foreground, background, minimum_ratio in REGION_SEPARATION_PAIRS + INTERACTIVE_SEPARATION_PAIRS:
            if foreground in palette and background in palette and not ({foreground, background} & invalid_keys):
                ratio = contrast_ratio(palette[foreground], palette[background])
                if ratio < minimum_ratio:
                    errors.append(f"separation: {foreground}/{background} is {ratio:.2f}:1, required >= {minimum_ratio:g}:1")
    if "prediction_foreground" in palette and "foreground" in palette:
        if "prediction_foreground" not in invalid_keys:
            distance = _oklab_delta_e(palette["prediction_foreground"], palette["foreground"])
            if distance < PREDICTION_MIN_DISTANCE:
                errors.append(
                    f"distance: prediction_foreground/foreground is {distance:.3f}, "
                    f"required >= {PREDICTION_MIN_DISTANCE:.2f}"
                )
            if _oklch_components(palette["prediction_foreground"])[1] > PREDICTION_MAX_CHROMA:
                errors.append(f"neutrality: prediction_foreground chroma exceeds {PREDICTION_MAX_CHROMA:.2f}")
    return errors


def validate_mode_coherence(
    seed_color: str,
    palettes: Mapping[str, Mapping[str, str]],
) -> list[str]:
    """Validate shared visual identity across the explicit Light/Dark Palettes."""
    errors: list[str] = []
    if set(palettes) != {"light", "dark"}:
        return ["mode coherence: palettes must contain exactly light and dark"]
    try:
        _seed_lightness, seed_chroma, seed_hue = _oklch_components(seed_color)
    except ValueError as error:
        return [f"mode coherence: invalid Seed Color: {error}"]

    light = palettes["light"]
    dark = palettes["dark"]
    tonal_roles = ("surface_subtle", "surface", "surface_raised")
    large_area_roles = ("background",) + tonal_roles
    for mode, palette in (("light", light), ("dark", dark)):
        for role in ("accent",) + large_area_roles:
            if role not in palette:
                errors.append(f"mode coherence: {mode} Palette is missing {role}")
        if all(role in palette for role in tonal_roles):
            tonal_luminances = tuple(relative_luminance(palette[role]) for role in tonal_roles)
            if not tonal_luminances[0] < tonal_luminances[1] < tonal_luminances[2]:
                errors.append(f"mode coherence: {mode} Tonal surface ordering is invalid")
        if all(role in palette for role in large_area_roles):
            large_area_luminances = tuple(relative_luminance(palette[role]) for role in large_area_roles)
            if mode == "light" and any(luminance >= MODE_LIGHT_SURFACE_MAX_LUMINANCE for luminance in large_area_luminances):
                errors.append("mode coherence: Light Tonal surface is too close to white")
            if mode == "dark" and any(luminance <= MODE_DARK_SURFACE_MIN_LUMINANCE for luminance in large_area_luminances):
                errors.append("mode coherence: Dark Tonal surface is too close to black")

    for role in large_area_roles:
        if role in light and role in dark:
            lightness_delta = abs(_oklch_components(light[role])[0] - _oklch_components(dark[role])[0])
            if lightness_delta > MODE_TONAL_LIGHTNESS_DELTA:
                errors.append(
                    f"mode coherence: {role} Light/Dark lightness changed by {lightness_delta:.2f}, "
                    f"maximum is {MODE_TONAL_LIGHTNESS_DELTA:g}"
                )

    if "accent" not in light or "accent" not in dark:
        return errors
    light_accent = _oklch_components(light["accent"])
    dark_accent = _oklch_components(dark["accent"])
    if seed_chroma >= 0.035:
        for mode, accent in (("light", light_accent), ("dark", dark_accent)):
            if _circular_hue_distance(accent[2], seed_hue) > MODE_ACCENT_HUE_TOLERANCE:
                errors.append(f"mode coherence: {mode} Accent lost the Seed Color hue")
            if not MODE_ACCENT_MIN_LIGHTNESS <= accent[0] <= MODE_ACCENT_MAX_LIGHTNESS:
                errors.append(f"mode coherence: {mode} Accent lightness is out of bounds")
        if _circular_hue_distance(light_accent[2], dark_accent[2]) > MODE_ACCENT_HUE_TOLERANCE:
            errors.append("mode coherence: Light and Dark Accents use different hue families")
        if abs(light_accent[0] - dark_accent[0]) > MODE_ACCENT_LIGHTNESS_DELTA:
            errors.append("mode coherence: Light and Dark Accent lightness changed too much")
        for role in tonal_roles:
            if role in light and role in dark:
                for mode, color in (("light", light[role]), ("dark", dark[role])):
                    if _circular_hue_distance(_oklch_components(color)[2], seed_hue) > MODE_ACCENT_HUE_TOLERANCE:
                        errors.append(f"mode coherence: {mode} {role} lost the Seed Color hue")
    if abs(light_accent[1] - dark_accent[1]) > 0.12:
        errors.append("mode coherence: Light and Dark Accent chroma changed too much")
    return errors
