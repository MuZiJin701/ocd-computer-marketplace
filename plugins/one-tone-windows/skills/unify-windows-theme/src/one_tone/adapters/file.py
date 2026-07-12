from __future__ import annotations

import json
import shutil
from pathlib import Path

from ..plan import Plan
from .base import AdapterResult, ThemeAdapter, write_json


class FileAdapter:
    """A local JSON target used to exercise the transactional workflow."""

    def __init__(self, target: str, config_path: Path) -> None:
        self.target = target
        self.config_path = config_path

    @property
    def backup_name(self) -> str:
        return self.target.replace("\\", "_").replace("/", "_") + ".json"

    def detect(self) -> AdapterResult:
        if not self.config_path.is_file():
            return AdapterResult(self.target, "skipped", False, False, f"config not found: {self.config_path}")
        return AdapterResult(self.target, "ok", False, True, "config detected")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if not self.config_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "cannot snapshot missing config")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.config_path, backup_dir / self.backup_name)
            return AdapterResult(self.target, "ok", False, True, "snapshot saved")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"snapshot failed: {error}")

    def apply(self, plan: Plan) -> AdapterResult:
        try:
            write_json(self.config_path, {"plan_id": plan.id, "palette": plan.palette})
            return AdapterResult(self.target, "ok", True, False, "palette written")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"apply failed: {error}")

    def verify(self, plan: Plan) -> AdapterResult:
        try:
            payload = json.loads(self.config_path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as error:
            return AdapterResult(self.target, "failed", False, False, f"verify failed: {error}")
        expected = {"plan_id": plan.id, "palette": plan.palette}
        verified = payload == expected
        return AdapterResult(
            self.target,
            "ok" if verified else "failed",
            False,
            verified,
            "configuration verified" if verified else "configuration does not match Plan",
        )

    def rollback(self, backup_dir: Path) -> AdapterResult:
        backup_path = backup_dir / self.backup_name
        if not backup_path.is_file():
            return AdapterResult(self.target, "failed", False, False, "backup not found")
        try:
            self.config_path.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(backup_path, self.config_path)
            restored = self.config_path.read_bytes() == backup_path.read_bytes()
            return AdapterResult(self.target, "ok" if restored else "failed", True, restored, "configuration restored")
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"rollback failed: {error}")
