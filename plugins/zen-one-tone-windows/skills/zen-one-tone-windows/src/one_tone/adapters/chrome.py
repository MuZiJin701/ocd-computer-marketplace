from __future__ import annotations

import colorsys
import json
import shutil
import zipfile
from pathlib import Path
from typing import Any, Mapping

from ..inventory import inventory_groups, inventory_report
from ..palette import parse_hex_color
from ..plan import Plan
from ..storage import atomic_write_text, validate_safe_component
from .base import AdapterResult, field_capabilities


def _rgb(color: str) -> list[int]:
    return list(parse_hex_color(color))


def _tint(color: str) -> list[float]:
    red, green, blue = (channel / 255 for channel in parse_hex_color(color))
    hue, lightness, saturation = colorsys.rgb_to_hls(red, green, blue)
    return [round(hue, 4), round(saturation, 4), round(lightness, 4)]


def _manifest(plan: Plan, mode: str | None = None) -> dict[str, Any]:
    mode = mode or plan.mode
    palette = plan.palette_for(mode)
    light_mode_surface = palette["surface"] if mode == "light" else palette["background"]
    inactive_text = palette["muted_foreground"] if mode == "light" else palette["background_foreground"]
    return {
        "manifest_version": 3,
        "version": "1.0.0",
        "name": f"One Tone {plan.id}",
        "description": "Palette-generated One-Tone Chrome theme",
        "theme": {
            "colors": {
                "frame": _rgb(palette["surface"]),
                "frame_inactive": _rgb(light_mode_surface),
                "toolbar": _rgb(palette["surface"] if mode == "light" else palette["surface_subtle"]),
                "toolbar_text": _rgb(palette["foreground"]),
                "toolbar_button_icon": _rgb(palette["foreground"]),
                "tab_background_text": _rgb(palette["foreground"]),
                "tab_background_text_inactive": _rgb(inactive_text),
                "tab_text": _rgb(palette["foreground"]),
                "bookmark_text": _rgb(palette["foreground"]),
                "ntp_background": _rgb(light_mode_surface),
                "ntp_header": _rgb(palette["foreground"]),
                "ntp_link": _rgb(palette["accent_text"]),
                "ntp_text": _rgb(palette["foreground"]),
                "omnibox_background": _rgb(palette["surface_raised"]),
                "omnibox_text": _rgb(palette["foreground"]),
                "omnibox_background_tint": _rgb(palette["surface_subtle"]),
                "omnibox_background_tab_switcher": _rgb(palette["surface_raised"]),
                "incognito_tab": _rgb(palette["surface_raised"]),
                "incognito_background": _rgb(light_mode_surface),
                "button_background": _rgb(palette["accent"]),
                "button_background_hover": _rgb(palette["selection_background"]),
                "separator": _rgb(palette["border"]),
            },
            "tints": {
                "buttons": _tint(palette["accent"]),
                "frame": _tint(palette["surface"]),
                "background_tab": _tint(palette["surface_subtle"]),
            },
            "display_properties": {
                "control_style": 1,
                "theme_supports_hidpi": True,
            },
        },
    }


def build_chrome_theme(plan: Plan, output_path: Path, mode: str | None = None) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(_manifest(plan, mode), ensure_ascii=False, indent=2))
    return output_path


def build_chrome_theme_directory(plan: Plan, output_dir: Path, mode: str | None = None) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    atomic_write_text(
        output_dir / "manifest.json",
        json.dumps(_manifest(plan, mode), ensure_ascii=False, indent=2) + "\n",
    )
    return output_dir


def build_chrome_themes(plan: Plan, output_dir: Path) -> dict[str, tuple[Path, Path]]:
    output_dir.mkdir(parents=True, exist_ok=True)
    return {
        mode: (
            build_chrome_theme_directory(plan, output_dir / f"one-tone-{plan.id}-{mode}", mode),
            build_chrome_theme(plan, output_dir / f"one-tone-{plan.id}-{mode}.zip", mode),
        )
        for mode in ("light", "dark")
    }


class ChromeAdapter:
    target = "chrome"

    def __init__(self, output_dir: Path, preferences_path: Path | None = None) -> None:
        self.output_dir = output_dir
        self.preferences_path = preferences_path
        self._artifact: Path | None = None
        self._unpacked_dir: Path | None = None
        self._artifacts: list[Path] = []
        self._unpacked_dirs: list[Path] = []
        self._preferences_backup: Path | None = None

    def detect(self) -> AdapterResult:
        return AdapterResult(self.target, "ok", False, True, "Chrome theme package generation is available")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if self.preferences_path is None or not self.preferences_path.is_file():
            return AdapterResult(self.target, "partial", False, True, "Chrome Preferences path not supplied; theme restore remains a user action", True)
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            self._preferences_backup = backup_dir / "chrome-preferences.json"
            shutil.copy2(self.preferences_path, self._preferences_backup)
            return AdapterResult(self.target, "ok", False, True, "Chrome Preferences snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            paired = build_chrome_themes(plan, self.output_dir)
            self._unpacked_dir = paired[plan.mode][0]
            self._artifact = paired[plan.mode][1]
            self._unpacked_dirs = [path for path, _ in paired.values()]
            self._artifacts = [path for _, path in paired.values()]
            unpacked_names = [path.name for path, _ in paired.values()]
            artifact_names = [path.name for _, path in paired.values()]
            return AdapterResult(
                self.target,
                "partial",
                True,
                False,
                f"Chrome Light/Dark themes generated; load {self._unpacked_dir} in Chrome and confirm activation",
                True,
                metadata={
                    "artifact": self._artifact.name,
                    "unpacked_dir": self._unpacked_dir.name,
                    "artifacts": artifact_names,
                    "unpacked_dirs": unpacked_names,
                    "canonical_unpacked_dirs": unpacked_names,
                    "user_facing_choices": unpacked_names,
                    "field_capabilities": field_capabilities(self.target),
                    "field_inventory": inventory_report(self.target),
                    "field_groups": inventory_groups(self.target),
                },
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome theme generation failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            candidates = []
            for mode in ("light", "dark"):
                paired_dir = self.output_dir / f"one-tone-{plan.id}-{mode}" / "manifest.json"
                paired_zip = self.output_dir / f"one-tone-{plan.id}-{mode}.zip"
                if paired_dir.is_file():
                    candidates.append(json.loads(paired_dir.read_text(encoding="utf-8")))
                if paired_zip.is_file():
                    with zipfile.ZipFile(paired_zip) as archive:
                        candidates.append(json.loads(archive.read("manifest.json")))
            expected_frames = {tuple(_rgb(plan.palette_for(mode)["surface"])) for mode in ("light", "dark")}
            frames = {tuple(manifest.get("theme", {}).get("colors", {}).get("frame", ())) for manifest in candidates}
            verified = bool(candidates) and expected_frames.issubset(frames)
            return AdapterResult(
                self.target, "partial" if verified else "failed", False, verified,
                "Chrome theme package verified; user activation is still required" if verified else "Chrome theme package mismatch", True,
                metadata={
                    "field_capabilities": field_capabilities(self.target),
                    "field_inventory": inventory_report(self.target),
                    "field_groups": inventory_groups(self.target),
                    "canonical_unpacked_dirs": [f"one-tone-{plan.id}-light", f"one-tone-{plan.id}-dark"],
                    "user_facing_choices": [f"one-tone-{plan.id}-light", f"one-tone-{plan.id}-dark"],
                },
            )
        except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome verify failed: {error}")

    def rollback(self, backup_dir: Path, metadata: Mapping[str, Any] | None = None) -> AdapterResult:
        try:
            artifact = self._artifact
            unpacked_dir = self._unpacked_dir
            if metadata:
                artifact_names = metadata.get("artifacts", [])
                unpacked_names = metadata.get("unpacked_dirs", [])
                if isinstance(artifact_names, list):
                    for name in artifact_names:
                        if isinstance(name, str):
                            validate_safe_component(name, "Chrome artifact")
                            candidate = self.output_dir / name
                            if candidate.exists():
                                candidate.unlink()
                if isinstance(unpacked_names, list):
                    for name in unpacked_names:
                        if isinstance(name, str):
                            validate_safe_component(name, "Chrome unpacked directory")
                            candidate = self.output_dir / name
                            if candidate.exists():
                                shutil.rmtree(candidate)
                artifact_name = metadata.get("artifact")
                unpacked_name = metadata.get("unpacked_dir")
                if isinstance(artifact_name, str):
                    validate_safe_component(artifact_name, "Chrome artifact")
                    artifact = self.output_dir / artifact_name
                if isinstance(unpacked_name, str):
                    validate_safe_component(unpacked_name, "Chrome unpacked directory")
                    unpacked_dir = self.output_dir / unpacked_name
            else:
                for candidate in self._artifacts:
                    if candidate.exists():
                        candidate.unlink()
                for candidate in self._unpacked_dirs:
                    if candidate.exists():
                        shutil.rmtree(candidate)
            if artifact is None and unpacked_dir is None:
                return AdapterResult(self.target, "failed", False, False, "Chrome artifact metadata not found")
            if artifact is not None and artifact.exists():
                artifact.unlink()
            if unpacked_dir is not None and unpacked_dir.exists():
                shutil.rmtree(unpacked_dir)
            if self.preferences_path is not None and self._preferences_backup is not None and self._preferences_backup.is_file():
                shutil.copy2(self._preferences_backup, self.preferences_path)
            return AdapterResult(self.target, "partial", True, True, "Generated Chrome theme removed; restoring a previously activated Chrome theme requires user action", True)
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome rollback failed: {error}")
