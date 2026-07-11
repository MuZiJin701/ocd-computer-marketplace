from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..plan import Plan
from .base import AdapterResult


def resolve_default_profile(settings: dict[str, Any]) -> tuple[int, str] | None:
    profiles = settings.get("profiles", {})
    profile_list = profiles.get("list", [])
    if not isinstance(profile_list, list):
        return None
    default = profiles.get("default")
    if default is not None:
        for index, profile in enumerate(profile_list):
            if str(profile.get("guid")) == str(default) or profile.get("name") == default:
                return index, "profiles.default resolved by GUID/name"
        return None
    for index, profile in enumerate(profile_list):
        if not profile.get("source"):
            return index, "profiles.default is null; first local profile selected"
    return None


def _palette_colors(plan: Plan) -> dict[str, str]:
    palette = plan.palette
    return {
        "background": palette["background"],
        "foreground": palette["foreground"],
        "selectionBackground": palette["selection_background"],
        "selectionForeground": palette["selection_foreground"],
        "black": palette["background"],
        "red": palette["error"],
        "green": palette["success"],
        "yellow": palette["warning"],
        "blue": palette["accent"],
        "purple": palette["accent"],
        "cyan": palette["accent"],
        "white": palette["foreground"],
        "brightBlack": palette["surface"],
        "brightRed": palette["error"],
        "brightGreen": palette["success"],
        "brightYellow": palette["warning"],
        "brightBlue": palette["accent"],
        "brightPurple": palette["accent"],
        "brightCyan": palette["accent"],
        "brightWhite": palette["foreground"],
    }


class TerminalAdapter:
    target = "terminal"

    def __init__(self, settings_path: Path, allow_restart: bool = False) -> None:
        self.settings_path = settings_path
        self.allow_restart = allow_restart
        self._profile_index: int | None = None
        self._resolution_message = ""
        self._expected_colors: dict[str, str] = {}

    def _read(self) -> dict[str, Any]:
        payload = json.loads(self.settings_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("Terminal settings must be a JSON object")
        return payload

    def detect(self) -> AdapterResult:
        if not self.settings_path.is_file():
            return AdapterResult(self.target, "skipped", False, False, f"Terminal settings not found: {self.settings_path}")
        try:
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "skipped", False, False, "Terminal default Profile could not be resolved")
            self._profile_index, self._resolution_message = resolved
            return AdapterResult(self.target, "ok", False, True, f"Terminal Profile detected; {self._resolution_message}")
        except (OSError, ValueError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal detect failed: {error}")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if not self.settings_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "Terminal settings not found")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.settings_path, backup_dir / "terminal-settings.json")
            return AdapterResult(self.target, "ok", False, True, "Terminal settings snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "failed", False, False, "Terminal default Profile could not be resolved")
            self._profile_index, self._resolution_message = resolved
            profile_list = settings["profiles"]["list"]
            self._expected_colors = _palette_colors(plan)
            profile_list[self._profile_index].update(self._expected_colors)
            self.settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return AdapterResult(self.target, "ok", True, False, f"Terminal Profile updated; {self._resolution_message}")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read()
            resolved = resolve_default_profile(settings)
            if resolved is None:
                return AdapterResult(self.target, "failed", False, False, "Terminal default Profile could not be resolved")
            index, message = resolved
            expected = _palette_colors(plan)
            profile = settings["profiles"]["list"][index]
            verified = all(profile.get(key) == value for key, value in expected.items())
            return AdapterResult(self.target, "ok" if verified else "failed", False, verified, f"Terminal Profile verified; {message}" if verified else "Terminal Profile colors do not match Plan")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal verify failed: {error}")

    def restart(self) -> AdapterResult:
        if not self.allow_restart:
            return AdapterResult(self.target, "partial", False, False, "Terminal restart requires --restart-apps")
        try:
            subprocess.run(["taskkill", "/IM", "WindowsTerminal.exe", "/T", "/F"], check=False, capture_output=True)
            subprocess.Popen(["wt"], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return AdapterResult(self.target, "ok", False, True, "Windows Terminal restarted")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal restart failed: {error}")

    def verify_again(self, plan: Plan) -> AdapterResult:
        return self.verify(plan)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        backup = backup_dir / "terminal-settings.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, "Terminal backup not found")
        try:
            shutil.copy2(backup, self.settings_path)
            restored = self.settings_path.read_bytes() == backup.read_bytes()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Terminal settings restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal rollback failed: {error}")
