from __future__ import annotations

import json
import shutil
import zipfile
from pathlib import Path
from typing import Any

from ..plan import Plan
from .base import AdapterResult


def _manifest(plan: Plan) -> dict[str, Any]:
    palette = plan.palette
    return {
        "manifest_version": 2,
        "version": "1.0.0",
        "name": f"One Tone {plan.id}",
        "description": "Palette-generated One-Tone Chrome theme",
        "theme": {
            "colors": {
                "frame": palette["surface"],
                "toolbar": palette["background"],
                "tab_background_text": palette["foreground"],
                "ntp_background": palette["background"],
                "ntp_text": palette["foreground"],
                "omnibox_background": palette["surface"],
                "omnibox_text": palette["foreground"],
            },
        },
    }


def build_chrome_theme(plan: Plan, output_path: Path) -> Path:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("manifest.json", json.dumps(_manifest(plan), ensure_ascii=False, indent=2))
    return output_path


class ChromeAdapter:
    target = "chrome"

    def __init__(self, output_dir: Path, preferences_path: Path | None = None) -> None:
        self.output_dir = output_dir
        self.preferences_path = preferences_path
        self._artifact: Path | None = None
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
            self._artifact = build_chrome_theme(plan, self.output_dir / f"one-tone-{plan.id}.zip")
            return AdapterResult(
                self.target,
                "partial",
                True,
                False,
                f"Chrome theme generated at {self._artifact}; load it in Chrome and confirm activation",
                True,
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome theme generation failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        if self._artifact is None:
            candidate = self.output_dir / f"one-tone-{plan.id}.zip"
        else:
            candidate = self._artifact
        try:
            with zipfile.ZipFile(candidate) as archive:
                manifest = json.loads(archive.read("manifest.json"))
            verified = manifest.get("theme", {}).get("colors", {}).get("frame") == plan.palette["surface"]
            return AdapterResult(self.target, "partial" if verified else "failed", False, verified, "Chrome theme package verified; user activation is still required" if verified else "Chrome theme package mismatch", True)
        except (OSError, KeyError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome verify failed: {error}")

    def restart(self) -> AdapterResult:
        return AdapterResult(self.target, "partial", False, False, "Chrome activation requires user confirmation; automatic restart is not used", True)

    def verify_again(self, plan: Plan) -> AdapterResult:
        return self.verify(plan)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        try:
            if self._artifact is not None and self._artifact.exists():
                self._artifact.unlink()
            if self.preferences_path is not None and self._preferences_backup is not None and self._preferences_backup.is_file():
                shutil.copy2(self._preferences_backup, self.preferences_path)
            return AdapterResult(self.target, "partial", True, True, "Generated Chrome theme removed; restoring a previously activated Chrome theme requires user action", True)
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Chrome rollback failed: {error}")
