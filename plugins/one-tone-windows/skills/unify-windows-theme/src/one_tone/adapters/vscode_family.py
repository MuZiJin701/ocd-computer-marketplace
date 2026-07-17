from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from ..plan import Plan
from ..storage import atomic_write_text
from .base import AdapterResult


@dataclass(frozen=True)
class EditorSpec:
    target: str
    executable: str | Path
    settings_path: Path
    extensions_dir: Path
    ai_panel_supported: bool = False
    artifacts_dir: Path | None = None


def build_theme_json(plan: Plan, theme_name: str) -> dict[str, Any]:
    palette = plan.palette
    background_foreground = palette["background_foreground"]
    return {
        "name": theme_name,
        "type": "dark",
        "colors": {
            "foreground": palette["foreground"],
            "disabledForeground": palette["muted_foreground"],
            "descriptionForeground": palette["muted_foreground"],
            "icon.foreground": palette["foreground"],
            "editor.background": palette["surface"],
            "editor.foreground": palette["foreground"],
            "editor.selectionBackground": palette["selection_background"],
            "editor.selectionForeground": palette["selection_foreground"],
            "editorLineNumber.foreground": palette["muted_foreground"],
            "editorLineNumber.activeForeground": palette["foreground"],
            "editorCursor.foreground": palette["accent_text"],
            "editorMultiCursor.primary.foreground": palette["accent_text"],
            "editorMultiCursor.secondary.foreground": palette["accent_text"],
            "editor.placeholder.foreground": palette["muted_foreground"],
            "editor.findMatchBackground": palette["selection_background"],
            "editor.findMatchForeground": palette["selection_foreground"],
            "editorError.foreground": palette["error_text"],
            "editorWarning.foreground": palette["warning_text"],
            "editorInfo.foreground": palette["accent_text"],
            "editorHint.foreground": palette["success_text"],
            "editorGroupHeader.tabsBackground": palette["surface"],
            "editorGroupHeader.tabsBorder": palette["border"],
            "sideBar.background": palette["surface"],
            "sideBar.foreground": palette["foreground"],
            "sideBar.border": palette["border"],
            "sideBarTitle.background": palette["surface"],
            "sideBarTitle.foreground": palette["foreground"],
            "sideBarTitle.border": palette["border"],
            "sideBarSectionHeader.background": palette["background"],
            "sideBarSectionHeader.foreground": background_foreground,
            "sideBarSectionHeader.border": palette["border"],
            "activityBar.background": palette["surface"],
            "activityBar.foreground": palette["foreground"],
            "activityBar.inactiveForeground": palette["muted_foreground"],
            "activityBar.activeBorder": palette["accent"],
            "activityBar.border": palette["border"],
            "activityBarBadge.background": palette["accent"],
            "activityBarBadge.foreground": palette["accent_foreground"],
            "activityBarTop.background": palette["surface"],
            "activityBarTop.foreground": palette["foreground"],
            "activityBarTop.inactiveForeground": palette["muted_foreground"],
            "activityBarTop.activeBorder": palette["accent"],
            "titleBar.activeBackground": palette["surface"],
            "titleBar.activeForeground": palette["foreground"],
            "titleBar.inactiveBackground": palette["background"],
            "titleBar.inactiveForeground": background_foreground,
            "titleBar.border": palette["border"],
            "tab.activeBackground": palette["surface"],
            "tab.activeForeground": palette["foreground"],
            "tab.inactiveBackground": palette["background"],
            "tab.inactiveForeground": background_foreground,
            "tab.activeBorderTop": palette["accent"],
            "panel.background": palette["background"],
            "panel.foreground": background_foreground,
            "panel.border": palette["border"],
            "panelTitle.activeBorder": palette["accent"],
            "panelTitle.activeForeground": background_foreground,
            "panelTitle.inactiveForeground": palette["muted_foreground"],
            "statusBar.background": palette["surface"],
            "statusBar.foreground": palette["foreground"],
            "statusBar.border": palette["border"],
            "input.background": palette["background"],
            "input.foreground": background_foreground,
            "input.border": palette["border"],
            "input.placeholderForeground": palette["muted_foreground"],
            "dropdown.background": palette["background"],
            "dropdown.foreground": background_foreground,
            "list.activeSelectionBackground": palette["selection_background"],
            "list.activeSelectionForeground": palette["selection_foreground"],
            "list.inactiveSelectionForeground": palette["selection_foreground"],
            "list.focusForeground": palette["selection_foreground"],
            "list.highlightForeground": palette["accent_text"],
            "list.focusHighlightForeground": palette["accent_text"],
            "list.hoverBackground": palette["selection_background"],
            "badge.background": palette["accent"],
            "badge.foreground": palette["accent_foreground"],
            "terminal.background": palette["surface"],
            "terminal.foreground": palette["foreground"],
            "terminalCursor.foreground": palette["accent_text"],
            "terminal.ansiBlack": palette["foreground"],
            "terminal.ansiRed": palette["error_text"],
            "terminal.ansiGreen": palette["success_text"],
            "terminal.ansiYellow": palette["warning_text"],
            "terminal.ansiBlue": palette["accent_text"],
            "terminal.ansiMagenta": palette["accent_text"],
            "terminal.ansiCyan": palette["accent_text"],
            "terminal.ansiWhite": palette["foreground"],
            "terminal.ansiBrightBlack": palette["foreground"],
            "terminal.ansiBrightRed": palette["error_text"],
            "terminal.ansiBrightGreen": palette["success_text"],
            "terminal.ansiBrightYellow": palette["warning_text"],
            "terminal.ansiBrightBlue": palette["accent_text"],
            "terminal.ansiBrightMagenta": palette["accent_text"],
            "terminal.ansiBrightCyan": palette["accent_text"],
            "terminal.ansiBrightWhite": palette["foreground"],
            "textLink.foreground": palette["accent_text"],
            "textLink.activeForeground": palette["accent_text"],
            "errorForeground": palette["error_text"],
            "notifications.foreground": palette["foreground"],
            "notificationCenterHeader.foreground": background_foreground,
            "focusBorder": palette["accent"],
            "button.background": palette["accent"],
            "button.foreground": palette["accent_foreground"],
            "editorWidget.background": palette["surface"],
            "editorWidget.border": palette["border"],
        },
        "semanticHighlighting": True,
        "semanticTokenColors": {
            "namespace": palette["accent_text"],
            "type": palette["accent_text"],
            "class": palette["accent_text"],
            "interface": palette["accent_text"],
            "enum": palette["accent_text"],
            "struct": palette["accent_text"],
            "typeParameter": palette["accent_text"],
            "function": palette["success_text"],
            "method": palette["success_text"],
            "variable": palette["foreground"],
            "parameter": palette["foreground"],
            "property": palette["foreground"],
            "enumMember": palette["accent_text"],
            "constant": palette["warning_text"],
            "number": palette["warning_text"],
            "regexp": palette["warning_text"],
            "operator": palette["accent_text"],
            "keyword": palette["accent_text"],
            "macro": palette["warning_text"],
            "decorator": palette["warning_text"],
            "comment": palette["muted_foreground"],
            "string": palette["success_text"],
        },
        "tokenColors": [
            {"scope": ["comment"], "settings": {"foreground": palette["muted_foreground"]}},
            {"scope": ["string"], "settings": {"foreground": palette["success_text"]}},
            {"scope": ["keyword"], "settings": {"foreground": palette["accent_text"]}},
            {"scope": ["invalid"], "settings": {"foreground": palette["error_text"]}},
            {"scope": ["entity.name.function", "support.function"], "settings": {"foreground": palette["success_text"]}},
            {"scope": ["entity.name.type", "support.type", "storage.type"], "settings": {"foreground": palette["accent_text"]}},
            {"scope": ["variable", "variable.parameter"], "settings": {"foreground": palette["foreground"]}},
            {"scope": ["constant.numeric", "constant.language"], "settings": {"foreground": palette["warning_text"]}},
        ],
    }


def build_vsix(plan: Plan, output_path: Path, spec: EditorSpec) -> Path:
    theme_name = f"One Tone {spec.target}"
    package = {
        "name": f"one-tone-{spec.target}",
        "displayName": theme_name,
        "description": "Palette-generated One-Tone theme",
        "version": "0.1.0",
        "publisher": "one-tone",
        "engines": {"vscode": ">=1.80.0"},
        "contributes": {"themes": [{"label": theme_name, "uiTheme": "vs-dark", "path": "./themes/one-tone-color-theme.json"}]},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension/package.json", json.dumps(package, ensure_ascii=False, indent=2))
        archive.writestr("extension/themes/one-tone-color-theme.json", json.dumps(build_theme_json(plan, theme_name), ensure_ascii=False, indent=2))
    return output_path


class VSCodeFamilyAdapter:
    def __init__(self, spec: EditorSpec, command_runner: Callable[..., Any] | None = None) -> None:
        self.spec = spec
        self.target = spec.target
        self.command_runner = command_runner
        self._extension_dir: Path | None = None
        self._theme_name = f"One Tone {spec.target}"

    def _executable_available(self) -> bool:
        if isinstance(self.spec.executable, Path):
            if self.spec.executable.exists():
                return True
            # CLI fallbacks such as ``Path("code")`` should still resolve
            # through PATH when the executable is not a file in cwd.
            return shutil.which(str(self.spec.executable)) is not None
        return shutil.which(str(self.spec.executable)) is not None

    def _read_settings(self) -> dict[str, Any]:
        payload = json.loads(self.spec.settings_path.read_text(encoding="utf-8"))
        if not isinstance(payload, dict):
            raise ValueError("editor settings must be a JSON object")
        return payload

    def _extension_id(self) -> str:
        return f"one-tone.one-tone-{self.target}"

    def _installed_extension_dirs(self) -> list[Path]:
        prefix = f"{self._extension_id()}-"
        if not self.spec.extensions_dir.is_dir():
            return []
        candidates = [
            path
            for path in self.spec.extensions_dir.iterdir()
            if path.is_dir() and path.name.startswith(prefix)
        ]
        index = self.spec.extensions_dir / "extensions.json"
        if index.is_file():
            try:
                entries = json.loads(index.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                entries = []
            normalized_entries = entries if isinstance(entries, list) else [entries] if isinstance(entries, dict) else []
            for entry in normalized_entries:
                if not isinstance(entry, dict):
                    continue
                identifier = entry.get("identifier", {})
                if identifier.get("id") != self._extension_id():
                    continue
                relative = entry.get("relativeLocation")
                if isinstance(relative, str):
                    candidate = self.spec.extensions_dir / relative
                    if candidate.is_dir():
                        candidates.append(candidate)
        return list(dict.fromkeys(candidates))

    def _theme_file(self, extension_dir: Path) -> Path | None:
        for candidate in (
            extension_dir / "themes" / "one-tone-color-theme.json",
            extension_dir / "extension" / "themes" / "one-tone-color-theme.json",
        ):
            if candidate.is_file():
                return candidate
        return None

    def _snapshot_extension_state(self, backup_dir: Path) -> None:
        index = self.spec.extensions_dir / "extensions.json"
        if index.is_file():
            shutil.copy2(index, backup_dir / f"{self.target}-extensions.json")
        obsolete = self.spec.extensions_dir / ".obsolete"
        if obsolete.is_file():
            shutil.copy2(obsolete, backup_dir / f"{self.target}-extensions-obsolete")
        installed_backup = backup_dir / f"{self.target}-installed"
        for extension_dir in self._installed_extension_dirs():
            shutil.copytree(extension_dir, installed_backup / extension_dir.name)

    def _restore_extension_state(self, backup_dir: Path) -> bool:
        for extension_dir in self._installed_extension_dirs():
            shutil.rmtree(extension_dir)
        staging = self.spec.extensions_dir / f"one-tone-{self.target}"
        if staging.exists():
            shutil.rmtree(staging)

        installed_backup = backup_dir / f"{self.target}-installed"
        if installed_backup.is_dir():
            for extension_dir in installed_backup.iterdir():
                shutil.copytree(extension_dir, self.spec.extensions_dir / extension_dir.name)

        index = self.spec.extensions_dir / "extensions.json"
        index_backup = backup_dir / f"{self.target}-extensions.json"
        if index_backup.is_file():
            shutil.copy2(index_backup, index)
        elif index.exists():
            index.unlink()

        obsolete = self.spec.extensions_dir / ".obsolete"
        obsolete_backup = backup_dir / f"{self.target}-extensions-obsolete"
        if obsolete_backup.is_file():
            shutil.copy2(obsolete_backup, obsolete)
        elif obsolete.exists():
            obsolete.unlink()

        current_names = {path.name for path in self._installed_extension_dirs()}
        backup_names = {path.name for path in installed_backup.iterdir()} if installed_backup.is_dir() else set()
        index_restored = (not index_backup.is_file() and not index.exists()) or (
            index_backup.is_file() and index.read_bytes() == index_backup.read_bytes()
        )
        return current_names == backup_names and index_restored

    def _remove_installed_extension_state(self) -> None:
        installed_dirs = self._installed_extension_dirs()
        removable_dirs = [path for path in installed_dirs if self._theme_file(path) is None]
        removable_names = {path.name for path in removable_dirs}
        for extension_dir in removable_dirs:
            shutil.rmtree(extension_dir)
        staging = self.spec.extensions_dir / f"one-tone-{self.target}"
        if staging.exists():
            shutil.rmtree(staging)

        index = self.spec.extensions_dir / "extensions.json"
        if not index.is_file():
            return
        try:
            entries = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return
        if isinstance(entries, dict):
            entries = [entries]
        if not isinstance(entries, list):
            return
        filtered = [
            entry
            for entry in entries
            if entry.get("identifier", {}).get("id") != self._extension_id()
            or entry.get("relativeLocation") not in removable_names
        ]
        if filtered != entries:
            atomic_write_text(index, json.dumps(filtered, ensure_ascii=False, separators=(",", ":")))

    def _cursor_color_customizations(self, plan: Plan) -> dict[str, str]:
        return build_theme_json(plan, self._theme_name)["colors"]

    def _apply_cursor_settings_fallback(self, settings: dict[str, Any], plan: Plan) -> None:
        customizations = settings.get("workbench.colorCustomizations")
        if not isinstance(customizations, dict):
            customizations = {}
        customizations.update(self._cursor_color_customizations(plan))
        settings["workbench.colorCustomizations"] = customizations

    def _cursor_settings_match(self, settings: dict[str, Any], plan: Plan) -> bool:
        customizations = settings.get("workbench.colorCustomizations")
        if not isinstance(customizations, dict):
            return False
        expected = self._cursor_color_customizations(plan)
        return all(customizations.get(key) == value for key, value in expected.items())

    def _cli_requires_restart(self, completed: Any) -> bool:
        output = b"\n".join(
            value if isinstance(value, bytes) else str(value or "").encode("utf-8", errors="replace")
            for value in (getattr(completed, "stdout", b""), getattr(completed, "stderr", b""))
        ).lower()
        restart_markers = (
            b"please restart vscode before reinstalling",
            b"please restart vs code before reinstalling",
            b"please restart cursor before reinstalling",
            b"please restart trae before reinstalling",
            b"restart cursor before reinstalling",
            b"restart trae before reinstalling",
        )
        return any(marker in output for marker in restart_markers)

    def _manual_install_vsix(self, vsix_path: Path) -> bool:
        staging = self.spec.extensions_dir / f".one-tone-{self.target}-staging"
        try:
            if staging.exists():
                shutil.rmtree(staging)
            staging.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(vsix_path) as archive:
                members = [name for name in archive.namelist() if name == "extension" or name.startswith("extension/")]
                if not members:
                    return False
                archive.extractall(staging, members)

            package_dir = staging / "extension"
            package_path = package_dir / "package.json"
            package = json.loads(package_path.read_text(encoding="utf-8"))
            extension_id = f"{package['publisher']}.{package['name']}"
            version = str(package["version"])
            if extension_id != self._extension_id():
                return False
            installed_dir = self.spec.extensions_dir / f"{extension_id}-{version}"
            if installed_dir.exists():
                shutil.rmtree(installed_dir)
            shutil.move(str(package_dir), str(installed_dir))

            index = self.spec.extensions_dir / "extensions.json"
            entries = []
            index_was_single_object = False
            if index.is_file():
                loaded = json.loads(index.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    entries = loaded
                elif isinstance(loaded, dict):
                    index_was_single_object = True
            relative_location = installed_dir.name
            location = {
                "$mid": 1,
                "fsPath": str(installed_dir),
                "_sep": 1,
                "path": "/" + str(installed_dir).replace("\\", "/"),
                "scheme": "file",
            }
            replacement = {
                "identifier": {"id": extension_id},
                "version": version,
                "location": location,
                "relativeLocation": relative_location,
                "metadata": {"pinned": True, "source": "vsix"},
            }
            entries = [
                replacement if entry.get("identifier", {}).get("id") == extension_id else entry
                for entry in entries
                if isinstance(entry, dict)
            ]
            if not any(entry.get("identifier", {}).get("id") == extension_id for entry in entries):
                entries.append(replacement)
            if not index_was_single_object:
                atomic_write_text(index, json.dumps(entries, ensure_ascii=False, separators=(",", ":")))
            return True
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, zipfile.BadZipFile):
            return False
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def detect(self) -> AdapterResult:
        if not self.spec.settings_path.is_file():
            return AdapterResult(self.target, "skipped", False, False, f"{self.target} settings not found: {self.spec.settings_path}")
        if not self._executable_available():
            return AdapterResult(self.target, "skipped", False, False, f"{self.target} executable not found: {self.spec.executable}")
        return AdapterResult(self.target, "ok", False, True, f"{self.target} detected at {self.spec.settings_path}")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if not self.spec.settings_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "editor settings not found")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.spec.settings_path, backup_dir / f"{self.target}-settings.json")
            self._snapshot_extension_state(backup_dir)
            return AdapterResult(self.target, "ok", False, True, f"{self.target} settings snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            original_theme_values = {
                key: settings.get(key)
                for key in (
                    "workbench.colorTheme",
                    "workbench.preferredDarkColorTheme",
                    "workbench.preferredLightColorTheme",
                )
            }
            artifacts_dir = self.spec.artifacts_dir or self.spec.extensions_dir.parent / ".one-tone-artifacts"
            vsix_path = build_vsix(plan, artifacts_dir / f"{self.target}-{plan.id}.vsix", self.spec)
            self.spec.extensions_dir.mkdir(parents=True, exist_ok=True)
            self._remove_installed_extension_state()
            settings["workbench.colorTheme"] = self._theme_name
            settings["workbench.preferredDarkColorTheme"] = self._theme_name
            settings["workbench.preferredLightColorTheme"] = self._theme_name
            if self.target == "cursor":
                self._apply_cursor_settings_fallback(settings, plan)
            atomic_write_text(
                self.spec.settings_path,
                json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            )
            command = [str(self.spec.executable), "--install-extension", str(vsix_path), "--force"]
            try:
                if self.command_runner is None:
                    completed = subprocess.run(command, check=False, capture_output=True, timeout=30)
                else:
                    completed = self.command_runner(command, check=False, capture_output=True)
            except (OSError, subprocess.TimeoutExpired):
                if self.target != "cursor":
                    raise
                completed = None
            if completed is not None and getattr(completed, "returncode", 0) not in (0, None):
                if self._cli_requires_restart(completed):
                    self._manual_install_vsix(vsix_path)
                elif self.target != "cursor":
                    return AdapterResult(self.target, "failed", True, False, f"{self.target} extension install failed")
            installed_dirs = self._installed_extension_dirs()
            if not installed_dirs:
                if self.target == "cursor" and self._cursor_settings_match(self._read_settings(), plan):
                    fallback_settings = self._read_settings()
                    for key, value in original_theme_values.items():
                        if value is None:
                            fallback_settings.pop(key, None)
                        else:
                            fallback_settings[key] = value
                    atomic_write_text(
                        self.spec.settings_path,
                        json.dumps(fallback_settings, ensure_ascii=False, indent=2) + "\n",
                    )
                    return AdapterResult(
                        self.target,
                        "partial",
                        True,
                        False,
                        "Cursor color customizations applied; VSIX registration was unavailable, so restart Cursor to reload settings",
                        True,
                    )
                return AdapterResult(self.target, "failed", True, False, f"{self.target} extension install produced no registered extension")
            self._extension_dir = max(installed_dirs, key=lambda path: path.stat().st_mtime)
            return AdapterResult(self.target, "ok", True, False, f"{self.target} VSIX installed and theme selected")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            candidates = [
                path for path in self._installed_extension_dirs()
                if self._theme_file(path) is not None
            ]
            extension_dir = self._extension_dir if self._extension_dir and self._theme_file(self._extension_dir) else (
                max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None
            )
            verified = (
                settings.get("workbench.colorTheme") == self._theme_name
                and settings.get("workbench.preferredDarkColorTheme") == self._theme_name
                and settings.get("workbench.preferredLightColorTheme") == self._theme_name
                and extension_dir is not None
            )
            if self.target == "cursor" and not verified and self._cursor_settings_match(settings, plan):
                return AdapterResult(
                    self.target,
                    "partial",
                    False,
                    True,
                    "Cursor color customizations verified; VSIX registration is unavailable",
                    True,
                )
            if not verified:
                return AdapterResult(self.target, "failed", False, False, f"{self.target} theme verification failed")
            if self.spec.ai_panel_supported:
                return AdapterResult(self.target, "ok", False, True, f"{self.target} common workbench verified")
            return AdapterResult(self.target, "partial", False, True, f"{self.target} common workbench verified; AI-specific panels are outside standard theme fields")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} verify failed: {error}")

    def rollback(self, backup_dir: Path, metadata: Mapping[str, Any] | None = None) -> AdapterResult:
        backup = backup_dir / f"{self.target}-settings.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, f"{self.target} settings backup not found")
        try:
            shutil.copy2(backup, self.spec.settings_path)
            extensions_restored = self._restore_extension_state(backup_dir)
            restored = self.spec.settings_path.read_bytes() == backup.read_bytes() and extensions_restored
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, f"{self.target} settings and extension restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} rollback failed: {error}")
