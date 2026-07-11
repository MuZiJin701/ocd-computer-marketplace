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
    allow_restart: bool = False
    artifacts_dir: Path | None = None


def build_theme_json(plan: Plan, theme_name: str) -> dict[str, Any]:
    palette = plan.palette
    return {
        "name": theme_name,
        "type": "dark",
        "colors": {
            "editor.background": palette["background"],
            "editor.foreground": palette["foreground"],
            "editor.selectionBackground": palette["selection_background"],
            "editorLineNumber.foreground": palette["muted_foreground"],
            "sideBar.background": palette["surface"],
            "sideBar.foreground": palette["foreground"],
            "activityBar.background": palette["surface"],
            "statusBar.background": palette["surface"],
            "terminal.background": palette["background"],
            "terminal.foreground": palette["foreground"],
            "focusBorder": palette["accent"],
            "button.background": palette["accent"],
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
            return AdapterResult(self.target, "ok", False, True, f"{self.target} settings snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            artifacts_dir = self.spec.artifacts_dir or self.spec.extensions_dir.parent / ".one-tone-artifacts"
            vsix_path = build_vsix(plan, artifacts_dir / f"{self.target}-{plan.id}.vsix", self.spec)
            self.spec.extensions_dir.mkdir(parents=True, exist_ok=True)
            self._extension_dir = self.spec.extensions_dir / f"one-tone-{self.target}"
            self._extension_dir.mkdir(parents=True, exist_ok=True)
            with zipfile.ZipFile(vsix_path) as archive:
                for member in ("extension/package.json", "extension/themes/one-tone-color-theme.json"):
                    destination = self._extension_dir / Path(member).name
                    destination.write_bytes(archive.read(member))
            settings["workbench.colorTheme"] = self._theme_name
            self.spec.settings_path.write_text(json.dumps(settings, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            command = [str(self.spec.executable), "--install-extension", str(vsix_path), "--force"]
            if self.command_runner is None:
                completed = subprocess.run(command, check=False, capture_output=True)
            else:
                completed = self.command_runner(command, check=False, capture_output=True)
            if completed is not None and getattr(completed, "returncode", 0) not in (0, None):
                return AdapterResult(self.target, "failed", True, False, f"{self.target} extension install failed")
            return AdapterResult(self.target, "ok", True, False, f"{self.target} VSIX installed and theme selected")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError, zipfile.BadZipFile) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            settings = self._read_settings()
            extension_dir = self._extension_dir or self.spec.extensions_dir / f"one-tone-{self.target}"
            verified = settings.get("workbench.colorTheme") == self._theme_name and (extension_dir / "one-tone-color-theme.json").is_file()
            if not verified:
                return AdapterResult(self.target, "failed", False, False, f"{self.target} theme verification failed")
            if self.spec.ai_panel_supported:
                return AdapterResult(self.target, "ok", False, True, f"{self.target} common workbench verified")
            return AdapterResult(self.target, "partial", False, True, f"{self.target} common workbench verified; AI-specific panels are outside standard theme fields")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} verify failed: {error}")

    def restart(self) -> AdapterResult:
        if not self.spec.allow_restart:
            return AdapterResult(self.target, "partial", False, False, f"{self.target} restart requires --restart-apps")
        try:
            subprocess.run(["taskkill", "/IM", f"{self.target}.exe", "/T", "/F"], check=False, capture_output=True)
            subprocess.Popen([str(self.spec.executable)], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            return AdapterResult(self.target, "ok", False, True, f"{self.target} restarted")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} restart failed: {error}")

    def verify_again(self, plan: Plan) -> AdapterResult:
        return self.verify(plan)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        backup = backup_dir / f"{self.target}-settings.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, f"{self.target} settings backup not found")
        try:
            shutil.copy2(backup, self.spec.settings_path)
            extension_dir = self._extension_dir or self.spec.extensions_dir / f"one-tone-{self.target}"
            if extension_dir.exists():
                shutil.rmtree(extension_dir)
            restored = self.spec.settings_path.read_bytes() == backup.read_bytes() and not extension_dir.exists()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, f"{self.target} settings and extension restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"{self.target} rollback failed: {error}")
