from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable

from ..plan import Plan
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
            "editorLineNumber.foreground": palette["muted_foreground"],
            "editorLineNumber.activeForeground": palette["foreground"],
            "editorCursor.foreground": palette["accent"],
            "editorGroupHeader.tabsBackground": palette["surface"],
            "editorGroupHeader.tabsBorder": palette["border"],
            "sideBar.background": palette["surface"],
            "sideBar.foreground": palette["foreground"],
            "sideBar.border": palette["border"],
            "sideBarTitle.background": palette["surface"],
            "sideBarTitle.foreground": palette["foreground"],
            "sideBarTitle.border": palette["border"],
            "sideBarSectionHeader.background": palette["background"],
            "sideBarSectionHeader.foreground": palette["foreground"],
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
            "titleBar.inactiveForeground": palette["muted_foreground"],
            "titleBar.border": palette["border"],
            "tab.activeBackground": palette["surface"],
            "tab.activeForeground": palette["foreground"],
            "tab.inactiveBackground": palette["background"],
            "tab.inactiveForeground": palette["muted_foreground"],
            "tab.activeBorderTop": palette["accent"],
            "panel.background": palette["background"],
            "panel.border": palette["border"],
            "panelTitle.activeBorder": palette["accent"],
            "statusBar.background": palette["surface"],
            "statusBar.foreground": palette["foreground"],
            "statusBar.border": palette["border"],
            "input.background": palette["background"],
            "input.foreground": palette["foreground"],
            "input.border": palette["border"],
            "dropdown.background": palette["background"],
            "dropdown.foreground": palette["foreground"],
            "list.activeSelectionBackground": palette["selection_background"],
            "list.activeSelectionForeground": palette["selection_foreground"],
            "list.hoverBackground": palette["selection_background"],
            "badge.background": palette["accent"],
            "badge.foreground": palette["accent_foreground"],
            "terminal.background": palette["surface"],
            "terminal.foreground": palette["foreground"],
            "focusBorder": palette["accent"],
            "button.background": palette["accent"],
            "button.foreground": palette["accent_foreground"],
            "editorWidget.background": palette["surface"],
            "editorWidget.border": palette["border"],
        },
        "tokenColors": [
            {"scope": ["comment"], "settings": {"foreground": palette["muted_foreground"]}},
            {"scope": ["string"], "settings": {"foreground": palette["success"]}},
            {"scope": ["keyword"], "settings": {"foreground": palette["accent"]}},
            {"scope": ["invalid"], "settings": {"foreground": palette["error"]}},
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
            return self.spec.executable.exists()
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
            for entry in entries if isinstance(entries, list) else []:
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
        if not isinstance(entries, list):
            return
        filtered = [
            entry
            for entry in entries
            if entry.get("identifier", {}).get("id") != self._extension_id()
            or entry.get("relativeLocation") not in removable_names
        ]
        if filtered != entries:
            index.write_text(json.dumps(filtered, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")

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
            if index.is_file():
                loaded = json.loads(index.read_text(encoding="utf-8"))
                if isinstance(loaded, list):
                    entries = loaded
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
            index.write_text(json.dumps(entries, ensure_ascii=False, separators=(",", ":")), encoding="utf-8")
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
            artifacts_dir = self.spec.artifacts_dir or self.spec.extensions_dir.parent / ".one-tone-artifacts"
            vsix_path = build_vsix(plan, artifacts_dir / f"{self.target}-{plan.id}.vsix", self.spec)
            self.spec.extensions_dir.mkdir(parents=True, exist_ok=True)
            self._remove_installed_extension_state()
            settings["workbench.colorTheme"] = self._theme_name
            settings["workbench.preferredDarkColorTheme"] = self._theme_name
            settings["workbench.preferredLightColorTheme"] = self._theme_name
            self.spec.settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            command = [str(self.spec.executable), "--install-extension", str(vsix_path), "--force"]
            if self.command_runner is None:
                completed = subprocess.run(command, check=False, capture_output=True)
            else:
                completed = self.command_runner(command, check=False, capture_output=True)
            if completed is not None and getattr(completed, "returncode", 0) not in (0, None):
                if not self._cli_requires_restart(completed) or not self._manual_install_vsix(vsix_path):
                    return AdapterResult(self.target, "failed", True, False, f"{self.target} extension install failed")
            installed_dirs = self._installed_extension_dirs()
            if not installed_dirs:
                return AdapterResult(self.target, "failed", True, False, f"{self.target} extension install produced no registered extension")
            self._extension_dir = max(installed_dirs, key=lambda path: path.stat().st_mtime)
            return AdapterResult(self.target, "ok", True, False, f"{self.target} VSIX installed and theme selected")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            extension_dir = self._extension_dir or self.spec.extensions_dir / f"one-tone-{self.target}"
            verified = (
                settings.get("workbench.colorTheme") == self._theme_name
                and settings.get("workbench.preferredDarkColorTheme") == self._theme_name
                and settings.get("workbench.preferredLightColorTheme") == self._theme_name
                and self._theme_file(extension_dir) is not None
            )
            if not verified:
                return AdapterResult(self.target, "failed", False, False, f"{self.target} theme verification failed")
            if self.spec.ai_panel_supported:
                return AdapterResult(self.target, "ok", False, True, f"{self.target} common workbench verified")
            return AdapterResult(self.target, "partial", False, True, f"{self.target} common workbench verified; AI-specific panels are outside standard theme fields")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} verify failed: {error}")

    def rollback(self, backup_dir: Path) -> AdapterResult:
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
