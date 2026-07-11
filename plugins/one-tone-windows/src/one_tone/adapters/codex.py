from __future__ import annotations

import json
import shutil
from pathlib import Path
from typing import Any

from ..plan import Plan
from .base import AdapterResult


def _is_verified_schema(path: Path) -> bool:
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return False
    theme = payload.get("theme") if isinstance(payload, dict) else None
    return isinstance(theme, dict) and isinstance(theme.get("name"), str) and isinstance(theme.get("colors"), dict)


def locate_verified_codex_config(explicit_path: Path | None = None) -> Path | None:
    if explicit_path is None or not explicit_path.is_file() or not _is_verified_schema(explicit_path):
        return None
    return explicit_path


class CodexAdapter:
    target = "codex"

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = locate_verified_codex_config(config_path)

    def _read(self) -> dict[str, Any]:
        if self.config_path is None:
            raise FileNotFoundError("Codex theme configuration format is not verified")
        payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        if not _is_verified_schema(self.config_path):
            raise ValueError("Codex configuration does not match the verified theme schema")
        return payload

    def detect(self) -> AdapterResult:
        if self.config_path is None:
            return AdapterResult(self.target, "skipped", False, False, "Codex theme configuration format is not verified")
        return AdapterResult(self.target, "ok", False, True, f"verified Codex theme configuration: {self.config_path}")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if self.config_path is None:
            return AdapterResult(self.target, "skipped", False, False, "Codex theme configuration format is not verified")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.config_path, backup_dir / "codex-theme.json")
            return AdapterResult(self.target, "ok", False, True, "Codex theme snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        if self.config_path is None:
            return AdapterResult(self.target, "skipped", False, False, "Codex theme configuration format is not verified")
        try:
            payload = self._read()
            payload["theme"]["name"] = "One Tone Codex"
            payload["theme"]["colors"] = dict(plan.palette)
            self.config_path.write_text(json.dumps(payload, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
            return AdapterResult(self.target, "ok", True, False, "Codex theme configuration written")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        if self.config_path is None:
            return AdapterResult(self.target, "skipped", False, False, "Codex theme configuration format is not verified")
        try:
            payload = self._read()
            verified = payload["theme"]["name"] == "One Tone Codex" and payload["theme"]["colors"] == plan.palette
            return AdapterResult(self.target, "ok" if verified else "failed", False, verified, "Codex theme verified" if verified else "Codex theme does not match Plan")
        except (OSError, ValueError, KeyError, TypeError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex verify failed: {error}")

    def restart(self) -> AdapterResult:
        return AdapterResult(self.target, "skipped", False, False, "Codex restart is unavailable without a verified process/configuration contract")

    def verify_again(self, plan: Plan) -> AdapterResult:
        return self.verify(plan)

    def rollback(self, backup_dir: Path) -> AdapterResult:
        if self.config_path is None:
            return AdapterResult(self.target, "skipped", False, False, "Codex theme configuration format is not verified")
        backup = backup_dir / "codex-theme.json"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, "Codex backup not found")
        try:
            shutil.copy2(backup, self.config_path)
            restored = self.config_path.read_bytes() == backup.read_bytes()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "Codex theme restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex rollback failed: {error}")
