from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any, Mapping

from ..plan import Plan
from ..storage import atomic_write_text
from .base import AdapterResult

_SCHEME_NAME = "One Tone"
_THEME_NAME = "One Tone"


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
    default = settings.get("defaultProfile")
    if default is not None:
        for index, profile in enumerate(profile_list):
            if str(profile.get("guid")) == str(default) or profile.get("name") == default:
                return index, "defaultProfile resolved by GUID/name"
    for index, profile in enumerate(profile_list):
        if not profile.get("source"):
            return index, "profiles.default is null; first local profile selected"
    return None


def _palette_colors(plan: Plan) -> dict[str, str]:
    palette = plan.palette
    return {
        "background": palette["surface"],
        "foreground": palette["foreground"],
        "selectionBackground": palette["selection_background"],
        "selectionForeground": palette["selection_foreground"],
        "black": palette["foreground"],
        "red": palette["error_text"],
        "green": palette["success_text"],
        "yellow": palette["warning_text"],
        "blue": palette["accent_text"],
        "purple": palette["accent_text"],
        "cyan": palette["accent_text"],
        "white": palette["foreground"],
        "brightBlack": palette["foreground"],
        "brightRed": palette["error_text"],
        "brightGreen": palette["success_text"],
        "brightYellow": palette["warning_text"],
        "brightBlue": palette["accent_text"],
        "brightPurple": palette["accent_text"],
        "brightCyan": palette["accent_text"],
        "brightWhite": palette["foreground"],
    }


def _scheme_colors(plan: Plan) -> dict[str, str]:
    colors = _palette_colors(plan)
    return {"name": _SCHEME_NAME, "cursorColor": plan.palette["accent_text"], **colors}


def _theme_colors(plan: Plan) -> dict[str, Any]:
    palette = plan.palette
    return {
        "name": _THEME_NAME,
        "window": {
            "applicationTheme": "system",
            "frame": palette["accent"],
            "unfocusedFrame": palette["muted_foreground"],
        },
        "tabRow": {
            "background": palette["surface"],
            "unfocusedBackground": palette["background"],
        },
        "tab": {
            "background": palette["accent"],
            "unfocusedBackground": palette["surface"],
        },
    }


class TerminalAdapter:
    target = "terminal"

    def __init__(self, settings_path: Path) -> None:
        self.settings_path = settings_path
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
            for profile in profile_list:
                if not isinstance(profile, dict):
                    continue
                profile.update(self._expected_colors)
                profile["colorScheme"] = _SCHEME_NAME
                profile["tabColor"] = plan.palette["accent"]
            settings["profiles"].setdefault("defaults", {})["colorScheme"] = _SCHEME_NAME
            schemes = [item for item in settings.get("schemes", []) if item.get("name") != _SCHEME_NAME]
            schemes.append(_scheme_colors(plan))
            settings["schemes"] = schemes
            themes = [item for item in settings.get("themes", []) if isinstance(item, dict) and item.get("name") != _THEME_NAME]
            themes.append(_theme_colors(plan))
            settings["themes"] = themes
            settings["theme"] = _THEME_NAME
            atomic_write_text(
                self.settings_path,
                json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            )
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
            profile_list = settings["profiles"]["list"]
            scheme = next((item for item in settings.get("schemes", []) if item.get("name") == _SCHEME_NAME), None)
            scheme_expected = _scheme_colors(plan)
            theme = next((item for item in settings.get("themes", []) if item.get("name") == _THEME_NAME), None)
            verified = (
                all(
                    isinstance(profile, dict)
                    and all(profile.get(key) == value for key, value in expected.items())
                    and profile.get("colorScheme") == _SCHEME_NAME
                    and profile.get("tabColor") == plan.palette["accent"]
                    for profile in profile_list
                )
                and settings.get("profiles", {}).get("defaults", {}).get("colorScheme") == _SCHEME_NAME
                and isinstance(scheme, dict)
                and all(scheme.get(key) == value for key, value in scheme_expected.items())
                and settings.get("theme") == _THEME_NAME
                and theme == _theme_colors(plan)
            )
            return AdapterResult(self.target, "ok" if verified else "failed", False, verified, f"Terminal Profile verified; {message}" if verified else "Terminal Profile colors do not match Plan")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal verify failed: {error}")

    def rollback(self, backup_dir: Path, metadata: Mapping[str, Any] | None = None) -> AdapterResult:
        backup = backup_dir / "terminal-settings.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, "Terminal backup not found")
        try:
            shutil.copy2(backup, self.settings_path)
            restored = self.settings_path.read_bytes() == backup.read_bytes()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Terminal settings restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Terminal rollback failed: {error}")
