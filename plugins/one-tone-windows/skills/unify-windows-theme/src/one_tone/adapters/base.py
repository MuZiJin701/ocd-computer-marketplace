from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Literal, Protocol

from ..plan import Plan

AdapterStatus = Literal["ok", "partial", "failed", "skipped"]


@dataclass(frozen=True)
class AdapterResult:
    target: str
    status: AdapterStatus
    changed: bool
    verified: bool
    message: str
    requires_user_action: bool = False
    version: str | None = None

    def __post_init__(self) -> None:
        if self.status not in {"ok", "partial", "failed", "skipped"}:
            raise ValueError(f"Invalid adapter status: {self.status}")


class ThemeAdapter(Protocol):
    target: str

    def detect(self) -> AdapterResult: ...

    def snapshot(self, backup_dir: Path) -> AdapterResult: ...

    def apply(self, plan: Plan) -> AdapterResult: ...

    def verify(self, plan: Plan) -> AdapterResult: ...

    def rollback(self, backup_dir: Path) -> AdapterResult: ...


class UnsupportedAdapter:
    def __init__(self, target: str) -> None:
        self.target = target

    def _skipped(self, operation: str) -> AdapterResult:
        return AdapterResult(self.target, "skipped", False, False, f"{operation}: target not verified")

    def detect(self) -> AdapterResult:
        return self._skipped("detect")

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        return self._skipped("snapshot")

    def apply(self, plan: Plan) -> AdapterResult:
        return self._skipped("apply")

    def verify(self, plan: Plan) -> AdapterResult:
        return self._skipped("verify")

    def rollback(self, backup_dir: Path) -> AdapterResult:
        return self._skipped("rollback")


def write_json(path: Path, payload: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n", encoding="utf-8")
