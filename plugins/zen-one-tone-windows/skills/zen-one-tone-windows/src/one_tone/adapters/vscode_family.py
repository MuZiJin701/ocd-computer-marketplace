from __future__ import annotations

import json
import shutil
import subprocess
import zipfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Callable, Mapping

from ..plan import Plan
from ..inventory import inventory_groups, inventory_report
from ..storage import atomic_write_text
from .base import AdapterResult, field_capabilities


@dataclass(frozen=True)
class EditorSpec:
    target: str
    executable: str | Path
    settings_path: Path
    extensions_dir: Path
    ai_panel_supported: bool = False
    artifacts_dir: Path | None = None
    resolution_status: str = "ok"
    resolution_message: str = ""
    resolution_source: str = ""


def build_theme_json(plan: Plan, theme_name: str, mode: str | None = None) -> dict[str, Any]:
    mode = mode or plan.mode
    palette = plan.palette_for(mode)
    background_foreground = palette["background_foreground"]
    return {
        "name": theme_name,
        "type": mode,
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
            "editorGroupHeader.tabsBackground": palette["surface_subtle"],
            "editorGroupHeader.tabsBorder": palette["border"],
            "sideBar.background": palette["surface_subtle"],
            "sideBar.foreground": palette["foreground"],
            "sideBar.border": palette["border"],
            "sideBarTitle.background": palette["surface_subtle"],
            "sideBarTitle.foreground": palette["foreground"],
            "sideBarTitle.border": palette["border"],
            "sideBarSectionHeader.background": palette["background"],
            "sideBarSectionHeader.foreground": background_foreground,
            "sideBarSectionHeader.border": palette["border"],
            "activityBar.background": palette["background"],
            "activityBar.foreground": palette["foreground"],
            "activityBar.inactiveForeground": palette["muted_foreground"],
            "activityBar.activeBorder": palette["accent"],
            "activityBar.border": palette["border"],
            "activityBarBadge.background": palette["accent"],
            "activityBarBadge.foreground": palette["accent_foreground"],
            "activityBarTop.background": palette["background"],
            "activityBarTop.foreground": palette["foreground"],
            "activityBarTop.inactiveForeground": palette["muted_foreground"],
            "activityBarTop.activeBorder": palette["accent"],
            "titleBar.activeBackground": palette["surface_raised"],
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
            "statusBar.background": palette["surface_raised"],
            "statusBar.foreground": palette["foreground"],
            "statusBar.border": palette["border"],
            "input.background": palette["surface_raised"],
            "input.foreground": background_foreground,
            "input.border": palette["border"],
            "input.placeholderForeground": palette["muted_foreground"],
            "dropdown.background": palette["surface_raised"],
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
            "editorWidget.background": palette["surface_raised"],
            "editorWidget.border": palette["border"],
            "settings.headerForeground": palette["foreground"],
            "settings.modifiedItemIndicator": palette["accent"],
            "breadcrumb.background": palette["background"],
            "breadcrumb.foreground": background_foreground,
            "breadcrumb.focusForeground": palette["foreground"],
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
    dark_label = f"{theme_name} Dark"
    light_label = f"{theme_name} Light"
    package = {
        "name": f"one-tone-{spec.target}",
        "displayName": theme_name,
        "description": "Palette-generated One-Tone theme",
        "version": "0.1.0",
        "publisher": "one-tone",
        "engines": {"vscode": ">=1.80.0"},
        "contributes": {"themes": [
            {"label": f"{theme_name} Dark", "uiTheme": "vs-dark", "path": "./themes/one-tone-color-theme.json"},
            {"label": f"{theme_name} Light", "uiTheme": "vs", "path": "./themes/one-tone-light-color-theme.json"},
        ]},
    }
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(output_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr("extension/package.json", json.dumps(package, ensure_ascii=False, indent=2))
        archive.writestr("extension/themes/one-tone-color-theme.json", json.dumps(build_theme_json(plan, dark_label, "dark"), ensure_ascii=False, indent=2))
        archive.writestr("extension/themes/one-tone-light-color-theme.json", json.dumps(build_theme_json(plan, light_label, "light"), ensure_ascii=False, indent=2))
    return output_path


class VSCodeFamilyAdapter:
    def __init__(self, spec: EditorSpec, command_runner: Callable[..., Any] | None = None) -> None:
        self.spec = spec
        self.target = spec.target
        self.command_runner = command_runner
        self._extension_dir: Path | None = None
        self._theme_name = f"One Tone {spec.target}"

    def target_instance(self) -> dict[str, Any]:
        instance: dict[str, Any] = {
            "status": self.spec.resolution_status,
        }
        if self.spec.resolution_status == "ok":
            instance.update({
                "executable": str(self.spec.executable),
                "settings_path": str(self.spec.settings_path),
                "extensions_dir": str(self.spec.extensions_dir),
            })
            if self.spec.resolution_source:
                instance["source"] = self.spec.resolution_source
        elif self.spec.resolution_message:
            instance["reason"] = self.spec.resolution_message
        return instance

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

    def _theme_label(self, mode: str) -> str:
        return f"{self._theme_name} {'Light' if mode == 'light' else 'Dark'}"

    def _theme_labels(self) -> tuple[str, str]:
        return self._theme_label("dark"), self._theme_label("light")

    def _contributed_labels(self, extension_dir: Path) -> set[str] | None:
        package_path = extension_dir / "package.json"
        if not package_path.is_file():
            return None
        try:
            package = json.loads(package_path.read_text(encoding="utf-8"))
            themes = package.get("contributes", {}).get("themes", [])
            return {item["label"] for item in themes if isinstance(item, dict) and isinstance(item.get("label"), str)}
        except (OSError, TypeError, AttributeError, json.JSONDecodeError):
            return set()

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

    def _registered_extension_dirs(self) -> list[Path]:
        index = self.spec.extensions_dir / "extensions.json"
        if not index.is_file():
            return []
        try:
            entries = json.loads(index.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            return []
        normalized_entries = entries if isinstance(entries, list) else [entries] if isinstance(entries, dict) else []
        registered: list[Path] = []
        for entry in normalized_entries:
            if not isinstance(entry, dict) or entry.get("identifier", {}).get("id") != self._extension_id():
                continue
            relative = entry.get("relativeLocation")
            if isinstance(relative, str):
                candidate = self.spec.extensions_dir / relative
                if candidate.is_dir():
                    registered.append(candidate)
        return list(dict.fromkeys(registered))

    def _theme_file(self, extension_dir: Path) -> Path | None:
        for candidate in (
            extension_dir / "themes" / "one-tone-color-theme.json",
            extension_dir / "extension" / "themes" / "one-tone-color-theme.json",
        ):
            if candidate.is_file():
                return candidate
        return None

    def _theme_files(self, extension_dir: Path) -> tuple[Path, Path] | None:
        dark = extension_dir / "themes" / "one-tone-color-theme.json"
        light = extension_dir / "themes" / "one-tone-light-color-theme.json"
        if dark.is_file() and light.is_file():
            return dark, light
        return None

    def _registration_candidate(self) -> tuple[Path | None, str | None]:
        for extension_dir in self._registered_extension_dirs():
            if self._theme_files(extension_dir) is None:
                continue
            labels = self._contributed_labels(extension_dir)
            if labels is not None and set(self._theme_labels()) <= labels:
                return extension_dir, None
        return None, "registered extension, theme files or contributed labels are incomplete"

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

    def _cli_requires_restart(self, completed: Any) -> bool:
        output = b"\n".join(
            value if isinstance(value, bytes) else str(value or "").encode("utf-8", errors="replace")
            for value in (getattr(completed, "stdout", b""), getattr(completed, "stderr", b""))
        ).lower()
        restart_markers = (
            b"please restart vscode before reinstalling",
            b"please restart vs code before reinstalling",
            b"please restart trae before reinstalling",
            b"restart trae before reinstalling",
        )
        return any(marker in output for marker in restart_markers)

    def _cli_diagnostic(self, completed: Any) -> str:
        values = []
        for value in (getattr(completed, "stdout", b""), getattr(completed, "stderr", b"")):
            if isinstance(value, bytes):
                value = value.decode("utf-8", errors="replace")
            if value:
                values.append(str(value).strip())
        return " ".join(values)[:1000]

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
                elif isinstance(loaded, dict):
                    entries = [loaded]
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
            atomic_write_text(index, json.dumps(entries, ensure_ascii=False, separators=(",", ":")))
            return True
        except (OSError, KeyError, TypeError, ValueError, json.JSONDecodeError, zipfile.BadZipFile):
            return False
        finally:
            if staging.exists():
                shutil.rmtree(staging, ignore_errors=True)

    def detect(self) -> AdapterResult:
        if self.spec.resolution_status != "ok":
            return AdapterResult(self.target, "skipped", False, False, self.spec.resolution_message or f"{self.target} configuration path is ambiguous")
        if not self.spec.settings_path.is_file():
            return AdapterResult(self.target, "skipped", False, False, f"{self.target} settings not found: {self.spec.settings_path}")
        if not self._executable_available():
            return AdapterResult(self.target, "skipped", False, False, f"{self.target} executable not found: {self.spec.executable}")
        return AdapterResult(
            self.target,
            "ok",
            False,
            True,
            f"{self.target} detected at {self.spec.settings_path}",
            metadata={"target_instance": self.target_instance()},
        )

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if not self.spec.settings_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "editor settings not found")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.spec.settings_path, backup_dir / f"{self.target}-settings.json")
            self._snapshot_extension_state(backup_dir)
            return AdapterResult(
                self.target,
                "ok",
                False,
                True,
                f"{self.target} settings snapshot saved",
                metadata={"target_instance": self.target_instance()},
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            artifacts_dir = self.spec.artifacts_dir or self.spec.extensions_dir.parent / ".one-tone-artifacts"
            vsix_path = build_vsix(plan, artifacts_dir / f"{self.target}-{plan.id}.vsix", self.spec)
            self.spec.extensions_dir.mkdir(parents=True, exist_ok=True)
            self._remove_installed_extension_state()
            settings["workbench.colorTheme"] = self._theme_label(plan.mode)
            settings["workbench.preferredDarkColorTheme"] = self._theme_label("dark")
            settings["workbench.preferredLightColorTheme"] = self._theme_label("light")
            settings["window.autoDetectColorScheme"] = True
            atomic_write_text(
                self.spec.settings_path,
                json.dumps(settings, ensure_ascii=False, indent=2) + "\n",
            )
            command = [str(self.spec.executable), "--install-extension", str(vsix_path), "--force"]
            if self.command_runner is None:
                completed = subprocess.run(command, check=False, capture_output=True, timeout=30)
            else:
                completed = self.command_runner(command, check=False, capture_output=True)
            cli_returncode = getattr(completed, "returncode", 0) if completed is not None else 0
            cli_warning = ""
            cli_diagnostic = ""
            if completed is not None and cli_returncode not in (0, None):
                cli_diagnostic = self._cli_diagnostic(completed)
                if self._cli_requires_restart(completed):
                    if not self._manual_install_vsix(vsix_path):
                        cli_warning = f" CLI returned {cli_returncode}; manual installation fallback failed."
                    else:
                        cli_warning = f" CLI returned {cli_returncode}; manual installation fallback completed."
                else:
                    cli_warning = f" CLI returned {cli_returncode}; final installation evidence was used."
            extension_dir, evidence_error = self._registration_candidate()
            if extension_dir is None:
                return AdapterResult(self.target, "failed", True, False, f"{self.target} extension installation evidence failed: {evidence_error}{cli_warning}")
            self._extension_dir = extension_dir
            status = "partial" if cli_returncode not in (0, None) else "ok"
            return AdapterResult(
                self.target, status, True, False, f"{self.target} VSIX installed and theme selected.{cli_warning}",
                metadata={
                    "field_capabilities": field_capabilities(self.target),
                    "field_inventory": inventory_report(self.target),
                    "field_groups": inventory_groups(self.target),
                    "theme_registration": "applied",
                    "theme_activation": "applied",
                    "theme_labels": list(self._theme_labels()),
                    "auto_detect_enabled": settings.get("window.autoDetectColorScheme") is True,
                    "target_instance": self.target_instance(),
                    "cli_returncode": cli_returncode,
                    "cli_diagnostic": cli_diagnostic,
                },
            )
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile, subprocess.TimeoutExpired) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            candidates = self._registered_extension_dirs()
            extension_dir = self._extension_dir if self._extension_dir in candidates else (
                max(candidates, key=lambda path: path.stat().st_mtime) if candidates else None
            )
            contributed_labels = self._contributed_labels(extension_dir) if extension_dir else None
            labels_ok = contributed_labels is not None and set(self._theme_labels()) <= contributed_labels
            verified = (
                settings.get("workbench.colorTheme") in self._theme_labels()
                and settings.get("workbench.preferredDarkColorTheme") == self._theme_label("dark")
                and settings.get("workbench.preferredLightColorTheme") == self._theme_label("light")
                and settings.get("window.autoDetectColorScheme") is True
                and extension_dir is not None
                and self._theme_files(extension_dir) is not None
                and labels_ok
            )
            if not verified:
                return AdapterResult(self.target, "failed", False, False, f"{self.target} theme verification failed")
            if self.spec.ai_panel_supported:
                status = "ok"
                message = f"{self.target} registration and active theme verified"
            else:
                status = "partial"
                message = f"{self.target} registration and active theme verified; AI-specific panels are outside standard theme fields"
            return AdapterResult(
                self.target,
                status,
                False,
                True,
                message,
                metadata={
                    "field_capabilities": field_capabilities(self.target),
                    "field_inventory": inventory_report(self.target),
                    "field_groups": inventory_groups(self.target),
                    "theme_registration": "verified",
                    "theme_activation": "verified",
                    "theme_labels": list(self._theme_labels()),
                    "auto_detect_enabled": settings.get("window.autoDetectColorScheme") is True,
                },
            )
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
