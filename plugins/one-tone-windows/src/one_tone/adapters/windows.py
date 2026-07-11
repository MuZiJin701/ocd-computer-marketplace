from __future__ import annotations

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
    "AppsUseLightTheme",
    "SystemUsesLightTheme",
    "ColorPrevalence",
    "AccentColorMenu",
    "StartColorMenu",
    "AccentColor",
    "ColorizationColor",
    "ColorizationAfterglow",
)
REGISTRY_PATHS = {
    "AppsUseLightTheme": PERSONALIZE_KEY,
    "SystemUsesLightTheme": PERSONALIZE_KEY,
    "ColorPrevalence": PERSONALIZE_KEY,
    "AccentColorMenu": EXPLORER_ACCENT_KEY,
    "StartColorMenu": EXPLORER_ACCENT_KEY,
    "AccentColor": DWM_KEY,
    "ColorizationColor": DWM_KEY,
    "ColorizationAfterglow": DWM_KEY,
}


class RegistryBackend(Protocol):
    def get_value(self, name: str, default: Any = None) -> Any: ...

    def set_value(self, name: str, value: Any) -> None: ...

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
    def _key_for(self, name: str):
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        path = CURRENT_VERSION_KEY if name in {"CurrentBuild", "ProductName"} else REGISTRY_PATHS.get(name, PERSONALIZE_KEY)
        return winreg.HKEY_LOCAL_MACHINE if path == CURRENT_VERSION_KEY else winreg.HKEY_CURRENT_USER, path

    def get_value(self, name: str, default: Any = None) -> Any:
        root, path = self._key_for(name)
        try:
            with winreg.OpenKey(root, path) as key:
                return winreg.QueryValueEx(key, name)[0]
        except FileNotFoundError:
            return default

    def set_value(self, name: str, value: Any) -> None:
        if winreg is None:
            raise OSError("Windows registry is only available on Windows")
        root, path = self._key_for(name)
        with winreg.CreateKey(root, path) as key:
            winreg.SetValueEx(key, name, 0, winreg.REG_DWORD, int(value))

    def snapshot_values(self, names: tuple[str, ...]) -> dict[str, Any]:
        return {name: self.get_value(name) for name in names}

    def restore_values(self, values: Mapping[str, Any]) -> None:
        for name, value in values.items():
            if value is not None:
                self.set_value(name, value)


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
    background = parse_hex_color(palette["background"])
    surface = parse_hex_color(palette["surface"])
    accent = parse_hex_color(palette["accent"])
    rows = bytearray()
    for y in range(height):
        row = bytearray([0])
        for x in range(width):
            diagonal = (x + y) / max(1, width + height - 2)
            first = tuple(round(left * (1 - diagonal) + right * diagonal) for left, right in zip(background, accent))
            glow = max(0.0, 1.0 - (((x / max(1, width - 1) - 0.72) ** 2) + ((y / max(1, height - 1) - 0.28) ** 2)) * 3.0)
            pixel = tuple(round(channel * (1 - glow * 0.18) + base * glow * 0.18) for channel, base in zip(first, surface))
            row.extend(pixel)
        rows.extend(row)
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


def _theme_registry_values(plan: Plan) -> dict[str, int]:
    accent = windows_color_value(plan.palette["accent"])
    return {
        "AppsUseLightTheme": 0,
        "SystemUsesLightTheme": 0,
        "ColorPrevalence": 1,
        "AccentColorMenu": accent,
        "StartColorMenu": accent,
        "AccentColor": accent,
        "ColorizationColor": windows_colorization_value(plan.palette["accent"]),
        "ColorizationAfterglow": windows_colorization_value(plan.palette["accent"]),
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
            metadata = {"registry": self.registry.snapshot_values(THEME_VALUES), "wallpaper": old_path}
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
            for name, value in _theme_registry_values(plan).items():
                self.registry.set_value(name, value)
            if not self.desktop.set_wallpaper(str(self._wallpaper_path)):
                return AdapterResult(self.target, "failed", True, False, "Windows wallpaper API rejected the generated wallpaper")
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

    def restart(self) -> AdapterResult:
        return AdapterResult(self.target, "ok", False, True, "Windows theme changes are live; desktop restart not required", version=self._version)

    def verify_again(self, plan: Plan) -> AdapterResult:
        return self.verify(plan)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        try:
            metadata = json.loads((backup_dir / "windows.json").read_text(encoding="utf-8"))
            self.registry.restore_values(metadata["registry"])
            old_path = str(metadata.get("wallpaper", ""))
            original_backup = backup_dir / "original-wallpaper"
            if old_path and original_backup.is_file():
                import shutil

                shutil.copy2(original_backup, old_path)
            if not self.desktop.set_wallpaper(old_path):
                return AdapterResult(self.target, "failed", True, False, "Windows wallpaper restore was rejected")
            restored = all(self.registry.get_value(name) == metadata["registry"].get(name) for name in THEME_VALUES)
            restored = restored and self.desktop.get_wallpaper() == old_path
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Windows theme and wallpaper restored" if restored else "Windows restore verification failed", version=self._version)
        except (OSError, KeyError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Windows rollback failed: {error}")
