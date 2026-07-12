from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from ..palette import parse_hex_color
from ..plan import Plan
from .base import AdapterResult


def _rgb(color: str) -> list[int]:
    return list(parse_hex_color(color))


def _manifest(plan: Plan) -> dict[str, Any]:
    palette = plan.palette
    return {
        "manifest_version": 2,
        "version": "1.0.0",
        "name": f"One Tone {plan.id}",
        "description": "Palette-generated One-Tone Chrome theme",
        "theme": {
            "colors": {
                "frame": _rgb(palette["surface"]),
                "toolbar": _rgb(palette["surface"]),
                "tab_background_text": _rgb(palette["foreground"]),
                "ntp_background": _rgb(palette["surface"]),
                "ntp_text": _rgb(palette["foreground"]),
                "omnibox_background": _rgb(palette["surface"]),
                "omnibox_text": _rgb(palette["foreground"]),
            },
        },
    }


def build_chrome_theme(plan: Plan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(_manifest(plan), ensure_ascii=False, indent=2))
    return output_path


def build_chrome_theme_directory(plan: Plan, output_dir: Path) -> Path:
    output_dir.mkdir(parents=True, exist_ok=True)
    (output_dir / "manifest.json").write_text(
        json.dumps(_manifest(plan), ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    return output_dir


class ChromeAdapter:
    target = "chrome"

    def __init__(self, output_dir: Path, preferences_path: Path | None = None) -> None:
        self.output_dir = output_dir
        self.preferences_path = preferences_path
        self._artifact: Path | None = None
        self._unpacked_dir: Path | None = None
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
            self._unpacked_dir = build_chrome_theme_directory(plan, self.output_dir / f"one-tone-{plan.id}")
            self._artifact = build_chrome_theme(plan, self.output_dir / f"one-tone-{plan.id}.zip")
            return AdapterResult(
                self.target,
                "partial",
                True,
                False,
                f"Chrome theme generated at {self._unpacked_dir}; load it in Chrome and confirm activation",
                True,
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome theme generation failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            candidates = []
            unpacked = self._unpacked_dir or self.output_dir / f"one-tone-{plan.id}"
            artifact = self._artifact or self.output_dir / f"one-tone-{plan.id}.zip"
            if (unpacked / "manifest.json").is_file():
                candidates.append(json.loads((unpacked / "manifest.json").read_text(encoding="utf-8")))
            if artifact.is_file():
                with zipfile.ZipFile(artifact) as archive:
                    candidates.append(json.loads(archive.read("manifest.json")))
            verified = bool(candidates) and all(
                manifest.get("theme", {}).get("colors", {}).get("frame") == _rgb(plan.palette["surface"])
                for manifest in candidates
            )
            return AdapterResult(self.target, "partial" if verified else "failed", False, verified, "Chrome theme package verified; user activation is still required" if verified else "Chrome theme package mismatch", True)
        except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome verify failed: {error}")

    def rollback(self, backup_dir: Path) -> AdapterResult:
        try:
            if self._artifact is not None and self._artifact.exists():
                self._artifact.unlink()
            if self._unpacked_dir is not None and self._unpacked_dir.exists():
                shutil.rmtree(self._unpacked_dir)
            if self.preferences_path is not None and self._preferences_backup is not None and self._preferences_backup.is_file():
                shutil.copy2(self._preferences_backup, self.preferences_path)
            return AdapterResult(self.target, "partial", True, True, "Generated Chrome theme removed; restoring a previously activated Chrome theme requires user action", True)
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome rollback failed: {error}")
