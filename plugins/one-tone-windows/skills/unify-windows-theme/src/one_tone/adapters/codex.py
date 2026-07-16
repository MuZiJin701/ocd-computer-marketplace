from __future__ import annotations

import json
import os
import re
import shutil
import tomllib
from pathlib import Path
from typing import Any, Mapping

from ..plan import Plan
from ..storage import atomic_write_text
from .base import AdapterResult

CODEX_CONFIG_SCHEMA_V1 = "codex-config-v1"
_THEME_TABLES = (
    "desktop.appearanceLightChromeTheme",
    "desktop.appearanceDarkChromeTheme",
)
_THEME_FIELDS = ("accent", "ink", "surface")
_SEMANTIC_FIELDS = ("diffAdded", "diffRemoved", "skill")


def default_codex_config_path() -> Path:
    codex_home = os.environ.get("CODEX_HOME")
    if codex_home:
        return Path(codex_home) / "config.toml"
    userprofile = os.environ.get("USERPROFILE")
    home = Path(userprofile) if userprofile else Path.home()
    return home / ".codex" / "config.toml"


def _read_text(path: Path) -> str:
    with path.open("r", encoding="utf-8", newline="") as handle:
        return handle.read()


def _load_payload(path: Path) -> tuple[str, dict[str, Any]] | None:
    try:
        text = _read_text(path)
        payload = tomllib.loads(text)
    except (OSError, tomllib.TOMLDecodeError):
        return None
    return text, payload


def _is_v1_payload(payload: object) -> bool:
    if not isinstance(payload, dict):
        return False
    desktop = payload.get("desktop")
    if not isinstance(desktop, dict) or desktop.get("appearanceTheme") not in {"dark", "light", "system"}:
        return False
    for table_name in ("appearanceLightChromeTheme", "appearanceDarkChromeTheme"):
        theme = desktop.get(table_name)
        if not isinstance(theme, dict):
            return False
        if any(not isinstance(theme.get(key), str) for key in _THEME_FIELDS):
            return False
        if not isinstance(theme.get("contrast"), (int, float)) or isinstance(theme.get("contrast"), bool):
            return False
        if not isinstance(theme.get("opaqueWindows"), bool):
            return False
        for optional_table in ("fonts", "semanticColors"):
            value = theme.get(optional_table)
            if value is not None and not isinstance(value, dict):
                return False
        semantic = theme.get("semanticColors")
        if isinstance(semantic, dict) and any(
            key in semantic and not isinstance(semantic[key], str) for key in _SEMANTIC_FIELDS
        ):
            return False
    return True


def locate_verified_codex_config(explicit_path: Path | None = None) -> Path | None:
    path = explicit_path or default_codex_config_path()
    loaded = _load_payload(path) if path.is_file() else None
    if loaded is None or not _is_v1_payload(loaded[1]):
        return None
    return path


def _skip_result(message: str) -> AdapterResult:
    return AdapterResult("codex", "skipped", False, False, message)


def _theme_updates(palette: dict[str, str]) -> dict[str, dict[str, Any]]:
    base = {
        "accent": palette["accent"],
        "contrast": 100,
        "ink": palette["foreground"],
        "surface": palette["surface"],
    }
    semantic = {
        "diffAdded": palette["success_text"],
        "diffRemoved": palette["error_text"],
        "skill": palette["accent_text"],
    }
    return {
        _THEME_TABLES[0]: base,
        _THEME_TABLES[1]: base,
        f"{_THEME_TABLES[0]}.semanticColors": semantic,
        f"{_THEME_TABLES[1]}.semanticColors": semantic,
    }


def _replace_verified_values(text: str, palette: dict[str, str]) -> str:
    updates = _theme_updates(palette)
    section = ""
    output: list[str] = []
    header_pattern = re.compile(r"^\s*\[([^\]]+)\]\s*(?:\r?\n)?$")
    assignment_pattern = re.compile(r"^(\s*)([A-Za-z0-9_-]+)(\s*=\s*)(.*?)(\r?\n)?$")
    for line in text.splitlines(keepends=True):
        header = header_pattern.match(line)
        if header:
            section = header.group(1)
            output.append(line)
            continue
        assignment = assignment_pattern.match(line)
        replacement = updates.get(section, {}).get(assignment.group(2)) if assignment else None
        if replacement is None:
            output.append(line)
            continue
        newline = assignment.group(5) or ""
        output.append(f"{assignment.group(1)}{assignment.group(2)}{assignment.group(3)}{json.dumps(replacement)}{newline}")
    return "".join(output)


def _matches_plan(payload: dict[str, Any], plan: Plan) -> bool:
    desktop = payload["desktop"]
    for table_name in ("appearanceLightChromeTheme", "appearanceDarkChromeTheme"):
        theme = desktop[table_name]
        expected = {
            "accent": plan.palette["accent"],
            "contrast": 100,
            "ink": plan.palette["foreground"],
            "surface": plan.palette["surface"],
        }
        if any(theme.get(key) != value for key, value in expected.items()):
            return False
        semantic = theme.get("semanticColors")
        if isinstance(semantic, dict):
            expected_semantic = {
                "diffAdded": plan.palette["success_text"],
                "diffRemoved": plan.palette["error_text"],
                "skill": plan.palette["accent_text"],
            }
            if any(key in semantic and semantic[key] != value for key, value in expected_semantic.items()):
                return False
    return True


class CodexAdapter:
    target = "codex"

    def __init__(self, config_path: Path | None = None) -> None:
        self.config_path = locate_verified_codex_config(config_path)

    def _document(self) -> tuple[str, dict[str, Any]] | None:
        if self.config_path is None:
            return None
        loaded = _load_payload(self.config_path)
        if loaded is None or not _is_v1_payload(loaded[1]):
            return None
        return loaded

    def detect(self) -> AdapterResult:
        if self.config_path is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        if self._document() is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        return AdapterResult(
            self.target,
            "ok",
            False,
            True,
            f"verified Codex config.toml: {self.config_path}",
            version=CODEX_CONFIG_SCHEMA_V1,
        )

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        if self._document() is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        try:
            backup_dir.mkdir(parents=True, exist_ok=True)
            shutil.copy2(self.config_path, backup_dir / "codex-config.toml")
            return AdapterResult(self.target, "ok", False, True, "Codex config.toml snapshot saved", version=CODEX_CONFIG_SCHEMA_V1)
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex snapshot failed: {error}", version=CODEX_CONFIG_SCHEMA_V1)

    def apply(self, plan: Plan) -> AdapterResult:
        document = self._document()
        if document is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        original, _ = document
        updated = _replace_verified_values(original, plan.palette)
        try:
            atomic_write_text(self.config_path, updated, newline="")
            return AdapterResult(self.target, "ok", updated != original, False, "Codex config.toml theme written", version=CODEX_CONFIG_SCHEMA_V1)
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex apply failed: {error}", version=CODEX_CONFIG_SCHEMA_V1)

    def verify(self, plan: Plan) -> AdapterResult:
        document = self._document()
        if document is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        verified = _matches_plan(document[1], plan)
        return AdapterResult(
            self.target,
            "ok" if verified else "failed",
            False,
            verified,
            "Codex config.toml theme verified" if verified else "Codex config.toml theme does not match Plan",
            version=CODEX_CONFIG_SCHEMA_V1,
        )

    def rollback(self, backup_dir: Path, metadata: Mapping[str, Any] | None = None) -> AdapterResult:
        if self.config_path is None:
            return _skip_result(f"Codex config.toml does not match {CODEX_CONFIG_SCHEMA_V1}")
        backup = backup_dir / "codex-config.toml"
        if not backup.is_file():
            return AdapterResult(self.target, "failed", False, False, "Codex config.toml backup not found", version=CODEX_CONFIG_SCHEMA_V1)
        try:
            shutil.copy2(backup, self.config_path)
            restored = self.config_path.read_bytes() == backup.read_bytes()
            return AdapterResult(
                self.target,
                "ok" if restored else "failed",
                True,
                restored,
                "Codex config.toml restored" if restored else "Codex config.toml restore verification failed",
                version=CODEX_CONFIG_SCHEMA_V1,
            )
        except OSError as error:
            return AdapterResult(self.target, "failed", False, False, f"Codex rollback failed: {error}", version=CODEX_CONFIG_SCHEMA_V1)
