from __future__ import annotations

import base64
import ctypes
import json
import struct
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Mapping, Protocol

from ..palette import parse_hex_color
from ..plan import Plan
from .base import AdapterResult

try:
    import winreg
except ImportError:  # pragma: no cover - the production target is Windows.
    winreg = None


PERSONALIZE_KEY = r"Software\Microsoft\Windows\CurrentVersion\Themes\Personalize"
CURRENT_VERSION_KEY = r"SOFTWARE\Microsoft\Windows NT\CurrentVersion"
DESKTOP_KEY = r"Control Panel\Desktop"
EXPLORER_ACCENT_KEY = r"Software\Microsoft\Windows\CurrentVersion\Explorer\Accent"
DWM_KEY = r"Software\Microsoft\Windows\DWM"
THEME_VALUES = (
    "AutoColorization",
    "AppsUseLightTheme",
    "SystemUsesLightTheme",
    "StartTaskbarColorPrevalence",
    "TitleBarColorPrevalence",
    "AccentColorMenu",
    "StartColorMenu",
    "AccentPalette",
    "AccentColor",
    "ColorizationColor",
    "ColorizationAfterglow",
)
_BYTES_MARKER = "__one_tone_bytes__"
REGISTRY_PATHS = {
    "AutoColorization": DESKTOP_KEY,
    "AppsUseLightTheme": PERSONALIZE_KEY,
    "SystemUsesLightTheme": PERSONALIZE_KEY,
    "StartTaskbarColorPrevalence": PERSONALIZE_KEY,
    "TitleBarColorPrevalence": DWM_KEY,
    "AccentColorMenu": EXPLORER_ACCENT_KEY,
    "StartColorMenu": EXPLORER_ACCENT_KEY,
    "AccentPalette": EXPLORER_ACCENT_KEY,
    "AccentColor": DWM_KEY,
    "ColorizationColor": DWM_KEY,
    "ColorizationAfterglow": DWM_KEY,
}
REGISTRY_VALUE_NAMES = {
    "StartTaskbarColorPrevalence": "ColorPrevalence",
    "TitleBarColorPrevalence": "ColorPrevalence",
}


class RegistryBackend(Protocol):
    def get_value(self, name: str, default: Any = None) -> Any: ...

    def set_value(self, name: str, value: Any) -> None: ...

    def delete_value(self, name: str) -> None: ...

    def snapshot_values(self, names: tuple[str, ...]) -> dict[str, Any]: ...

    def restore_values(self, values: Mapping[str, Any]) -> None: ...


class DesktopBackend(Protocol):
    def get_wallpaper(self) -> str: ...

    def set_wallpaper(self, path: str) -> bool: ...

    def refresh_theme(self) -> None: ...


class InMemoryRegistryBackend:
    def __init__(self, values: Mapping[str, Any] | None = None) -> None:
        self.values = dict(values or {})

    def get_value(self, name: str, default: Any = None) -> Any:
        return self.values.get(name, default)

    def set_value(self, name: str, value: Any) -> None:
        self.values[name] = value

    def delete_value(self, name: str) -> None:
        self.values.pop(name, None)

    def snapshot_values(self, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self.values.get(name) for name in names}

    def restore_values(self, values: Mapping[str, Any]) -> None:
        for name, value in values.items():
            if value is None:
                self.values.pop(name, None)
            else:
                self.values[name] = value


class InMemoryDesktopBackend:
    def __init__(self, wallpaper: str = "") -> None:
        self.wallpaper = wallpaper

    def get_wallpaper(self) -> str:
        return self.wallpaper

    def set_wallpaper(self, path: str) -> bool:
        self.wallpaper = path
        return True

    def refresh_theme(self) -> None:
        return None


class WindowsRegistryBackend:
    @staticmethod
    def _registry_value_name(name: str) -> str:
        return REGISTRY_VALUE_NAMES.get(name, name)

    def _key_for(self, name: str):
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        path = CURRENT_VERSION_KEY if name in {"CurrentBuild", "ProductName"} else REGISTRY_PATHS.get(name, PERSONALIZE_KEY)
        return winreg.HKEY_LOCAL_MACHINE if path == CURRENT_VERSION_KEY else winreg.HKEY_CURRENT_USER, path

    def get_value(self, name: str, default: Any = None) -> Any:
        root, path = self._key_for(name)
        registry_name = self._registry_value_name(name)
        try:
            with winreg.OpenKey(root, path) as key:
                return winreg.QueryValueEx(key, registry_name)[0]
        except FileNotFoundError:
            return default

    def set_value(self, name: str, value: Any) -> None:
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        root, path = self._key_for(name)
        registry_name = self._registry_value_name(name)
        with winreg.CreateKey(root, path) as key:
            value_type = winreg.REG_BINARY if isinstance(value, (bytes, bytearray)) else winreg.REG_DWORD
            winreg.SetValueEx(key, registry_name, 0, value_type, value if isinstance(value, (bytes, bytearray)) else int(value))

    def snapshot_values(self, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self.get_value(name) for name in names}

    def restore_values(self, values: Mapping[str, Any]) -> None:
        for name, value in values.items():
            if value is None:
                self.delete_value(name)
            else:
                self.set_value(name, value)

    def delete_value(self, name: str) -> None:
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        root, path = self._key_for(name)
        registry_name = self._registry_value_name(name)
        try:
            with winreg.OpenKey(root, path, 0, winreg.KEY_SET_VALUE) as key:
                winreg.DeleteValue(key, registry_name)
        except FileNotFoundError:
            return


class WindowsDesktopBackend:
    def get_wallpaper(self) -> str:
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        try:
            with winreg.OpenKey(winreg.HKEY_CURRENT_USER, DESKTOP_KEY) as key:
                return str(winreg.QueryValueEx(key, "Wallpaper")[0])
        except FileNotFoundError:
            return ""

    def set_wallpaper(self, path: str) -> bool:
        if not hasattr(ctypes, "windll"):
            raise OSError("System wallpaper API is only available on Windows")
        result = ctypes.windll.user32.SystemParametersInfoW(20, 0, path, 3)
        return bool(result)

    def refresh_theme(self) -> None:
        if not hasattr(ctypes, "windll"):
            raise OSError("Windows theme API is only available on Windows")
        result = ctypes.c_ulong()
        ctypes.windll.user32.SendMessageTimeoutW(
            0xFFFF,
            0x001A,
            0,
            "ImmersiveColorSet",
            0x0002,
            1000,
            ctypes.byref(result),
        )


def _json_safe_registry_value(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return {_BYTES_MARKER: base64.b64encode(bytes(value)).decode("ascii")}
    return value


def _registry_value_from_json(value: Any) -> Any:
    if isinstance(value, dict) and set(value) == {_BYTES_MARKER}:
        return base64.b64decode(value[_BYTES_MARKER])
    return value


@dataclass(frozen=True)
class WindowsConfig:
    wallpaper_dir: Path
    min_windows_10_build: int = 19045
    min_windows_11_build: int = 22621


def detect_windows_version(registry: RegistryBackend) -> tuple[str, int] | None:
    raw_build = registry.get_value("CurrentBuild")
    try:
        build = int(str(raw_build))
    except (TypeError, ValueError):
        return None
    if build >= 22621:
        return "windows-11", build
    if 19045 <= build < 22000:
        return "windows-10", build
    return None


def _png_chunk(kind: bytes, payload: bytes) -> bytes:
    return struct.pack(">I", len(payload)) + kind + payload + struct.pack(">I", zlib.crc32(kind + payload) & 0xFFFFFFFF)


def generate_wallpaper(palette: Mapping[str, str], path: Path, width: int = 1920, height: int = 1080) -> Path:
    if width < 1 or height < 1:
        raise ValueError("Wallpaper dimensions must be positive")
    surface = bytes(parse_hex_color(palette["surface"]))
    row = b"\x00" + surface * width
    rows = row * height
    raw = b"\x89PNG\r\n\x1a\n"
    raw += _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
    raw += _png_chunk(b"IDAT", zlib.compress(bytes(rows), level=9))
    raw += _png_chunk(b"IEND", b"")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(raw)
    return path


def windows_color_value(color: str, alpha: int = 0xFF) -> int:
    red, green, blue = parse_hex_color(color)
    return (alpha << 24) | (blue << 16) | (green << 8) | red


def windows_colorization_value(color: str, alpha: int = 0xC4) -> int:
    red, green, blue = parse_hex_color(color)
    return (alpha << 24) | (red << 16) | (green << 8) | blue


def _blend_color(first: str, second: str, second_weight: float) -> str:
    first_rgb = parse_hex_color(first)
    second_rgb = parse_hex_color(second)
    return "#" + "".join(
        f"{round(left * (1 - second_weight) + right * second_weight):02X}"
        for left, right in zip(first_rgb, second_rgb)
    )


def generate_accent_palette(accent: str) -> bytes:
    colors = [
        accent,
        _blend_color(accent, "#FFFFFF", 0.2),
        _blend_color(accent, "#FFFFFF", 0.4),
        _blend_color(accent, "#FFFFFF", 0.6),
        _blend_color(accent, "#FFFFFF", 0.8),
        _blend_color(accent, "#000000", 0.2),
        _blend_color(accent, "#000000", 0.4),
        _blend_color(accent, "#000000", 0.6),
    ]
    return b"".join(bytes((*reversed(parse_hex_color(color)), 0)) for color in colors)


def _theme_registry_values(plan: Plan) -> dict[str, int | bytes]:
    surface = windows_color_value(plan.palette["surface"])
    return {
        "AutoColorization": 0,
        "AppsUseLightTheme": 0,
        "SystemUsesLightTheme": 0,
        "StartTaskbarColorPrevalence": 1,
        "TitleBarColorPrevalence": 1,
        "AccentColorMenu": surface,
        "StartColorMenu": surface,
        "AccentPalette": generate_accent_palette(plan.palette["surface"]),
        "AccentColor": surface,
        "ColorizationColor": windows_colorization_value(plan.palette["surface"]),
        "ColorizationAfterglow": windows_colorization_value(plan.palette["surface"]),
    }


class WindowsAdapter:
    target = "windows"

    def __init__(
        self,
        config: WindowsConfig,
        registry: RegistryBackend | None = None,
        desktop: DesktopBackend | None = None,
    ) -> None:
        self.config = config
        self.registry = registry or WindowsRegistryBackend()
        self.desktop = desktop or WindowsDesktopBackend()
        self._wallpaper_path: Path | None = None
        self._version: str | None = None

    def detect(self) -> AdapterResult:
        detected = detect_windows_version(self.registry)
        if detected is None:
            return AdapterResult(self.target, "skipped", False, False, "Windows 10 22H2+ or Windows 11 22H2+ not detected")
        family, build = detected
        self._version = f"{family} build {build}"
        return AdapterResult(self.target, "ok", False, True, f"detected {self._version}", version=self._version)

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            old_path = self.desktop.get_wallpaper()
            registry_values = self.registry.snapshot_values(THEME_VALUES)
            metadata = {
                "registry": {name: _json_safe_registry_value(value) for name, value in registry_values.items()},
                "wallpaper": old_path,
            }
            (backup_dir / "windows.json").write_text(json.dumps(metadata, sort_keys=True), encoding="utf-8")
            if old_path and Path(old_path).is_file():
                import shutil

                shutil.copy2(old_path, backup_dir / "original-wallpaper")
            return AdapterResult(self.target, "ok", False, True, "Windows theme and wallpaper snapshot saved", version=self._version)
        except (OSError, TypeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Windows snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            self.config.wallpaper_dir.mkdir(parents=True, exist_ok=True)
            wallpaper_path = (self.config.wallpaper_dir / f"{plan.id}.png").resolve()
            self._wallpaper_path = generate_wallpaper(plan.palette, wallpaper_path)
            if not self.desktop.set_wallpaper(str(self._wallpaper_path)):
                return AdapterResult(self.target, "failed", True, False, "Windows wallpaper API rejected the generated wallpaper")
            for name, value in _theme_registry_values(plan).items():
                self.registry.set_value(name, value)
            self.desktop.refresh_theme()
            return AdapterResult(self.target, "ok", True, False, "dark theme and generated wallpaper applied", version=self._version)
        except (OSError, KeyError, ValueError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Windows apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        expected_path = self._wallpaper_path
        expected_registry = _theme_registry_values(plan)
        colors_ok = all(self.registry.get_value(name) == value for name, value in expected_registry.items())
        wallpaper_ok = expected_path is not None and Path(expected_path).is_file() and self.desktop.get_wallpaper() == str(expected_path)
        verified = colors_ok and wallpaper_ok
        return AdapterResult(self.target, "ok" if verified else "failed", False, verified, "Windows theme and wallpaper verified" if verified else "Windows theme or wallpaper mismatch", version=self._version)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        try:
            metadata = json.loads((backup_dir / "windows.json").read_text(encoding="utf-8"))
            registry_values = {name: _registry_value_from_json(value) for name, value in metadata["registry"].items()}
            auto_colorization = registry_values.pop("AutoColorization", None)
            if auto_colorization:
                self.registry.set_value("AutoColorization", 0)
            self.registry.restore_values(registry_values)
            old_path = str(metadata.get("wallpaper", ""))
            original_backup = backup_dir / "original-wallpaper"
            if old_path and original_backup.is_file():
                import shutil

                shutil.copy2(original_backup, old_path)
            try:
                if not self.desktop.set_wallpaper(old_path):
                    return AdapterResult(self.target, "failed", True, False, "Windows wallpaper restore was rejected")
                self.registry.restore_values(registry_values)
            finally:
                if auto_colorization is None:
                    self.registry.delete_value("AutoColorization")
                else:
                    self.registry.set_value("AutoColorization", auto_colorization)
            restored = all(
                self.registry.get_value(name) == registry_values.get(name)
                for name in THEME_VALUES
                if name != "AutoColorization"
            )
            restored = restored and self.registry.get_value("AutoColorization") == auto_colorization
            restored = restored and self.desktop.get_wallpaper() == old_path
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Windows theme and wallpaper restored" if restored else "Windows restore verification failed", version=self._version)
        except (OSError, KeyError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Windows rollback failed: {error}")
