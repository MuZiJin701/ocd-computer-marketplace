from __future__ import annotations

import json
import shutil
import uuid
from dataclasses import asdict, dataclass, field
from datetime import datetime, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Mapping

from .adapters import AdapterResult, ThemeAdapter, UnsupportedAdapter
from .plan import Plan

SupportLevel = str


class TransactionStatus(str, Enum):
    PENDING = "PENDING"
    APPLIED = "APPLIED"
    PARTIAL = "PARTIAL"
    FAILED = "FAILED"
    ROLLED_BACK = "ROLLED_BACK"


@dataclass
class TransactionRecord:
    id: str
    plan_id: str
    status: TransactionStatus
    created_at: str
    targets: tuple[str, ...]
    results: dict[str, list[dict[str, Any]]] = field(default_factory=dict)
    support_levels: dict[str, str] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "targets": list(self.targets),
            "results": self.results,
            "support_levels": self.support_levels,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> TransactionRecord:
        return cls(
            id=payload["id"],
            plan_id=payload["plan_id"],
            status=TransactionStatus(payload["status"]),
            created_at=payload["created_at"],
            targets=tuple(payload["targets"]),
            results={key: list(value) for key, value in payload.get("results", {}).items()},
            support_levels=dict(payload.get("support_levels", {})),
        )


def _transaction_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"tx-{timestamp}-{uuid.uuid4().hex[:6]}"


class TransactionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, transaction_id: str) -> Path:
        return self.root / transaction_id

    def backup_path_for(self, transaction_id: str, target: str) -> Path:
        path = self.path_for(transaction_id) / target / "snapshot"
        path.mkdir(parents=True, exist_ok=True)
        return path

    def create(self, plan: Plan) -> TransactionRecord:
        record = TransactionRecord(
            id=_transaction_id(),
            plan_id=plan.id,
            status=TransactionStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
            targets=plan.targets,
        )
        self.save(record)
        return record

    def save(self, record: TransactionRecord) -> None:
        path = self.path_for(record.id)
        path.mkdir(parents=True, exist_ok=True)
        (path / "transaction.json").write_text(
            json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
            encoding="utf-8",
        )

    def append_operation(self, record: TransactionRecord, target: str, operation: str, result: AdapterResult) -> None:
        _append_result(record, target, operation, result)

    def load(self, transaction_id: str) -> TransactionRecord:
        path = self.path_for(transaction_id) / "transaction.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Transaction not found: {transaction_id}") from error
        return TransactionRecord.from_dict(payload)

    def prune(self, keep: int = 5, preserve: set[str] | None = None) -> list[str]:
        if keep < 1:
            raise ValueError("keep must be at least 1")
        preserved = set(preserve or ())
        candidates: list[tuple[str, str, Path]] = []
        if not self.root.is_dir():
            return []
        for path in self.root.iterdir():
            if not path.is_dir() or path.name in preserved:
                continue
            try:
                record = self.load(path.name)
            except (FileNotFoundError, OSError, json.JSONDecodeError, KeyError, ValueError):
                continue
            if record.status == TransactionStatus.PENDING:
                continue
            candidates.append((record.created_at, record.id, path))
        candidates.sort(key=lambda item: item[0], reverse=True)
        removed: list[str] = []
        for _, transaction_id, path in candidates[keep:]:
            shutil.rmtree(path)
            removed.append(transaction_id)
        return removed

    def rollback(self, transaction_id: str, adapters: Mapping[str, ThemeAdapter]) -> TransactionRecord:
        record = self.load(transaction_id)
        failed = False
        for target in record.targets:
            operation_results = record.results.get(target, [])
            has_snapshot = any(
                item.get("operation") == "snapshot" and item.get("status") == "ok"
                for item in operation_results
            )
            if not has_snapshot:
                continue
            adapter = adapters.get(target, UnsupportedAdapter(target))
            result = adapter.rollback(self.backup_path_for(transaction_id, target))
            _append_result(record, target, "rollback", result)
            if result.status not in {"ok", "partial"} or not result.verified:
                failed = True
        record.status = TransactionStatus.FAILED if failed else TransactionStatus.ROLLED_BACK
        self.save(record)
        return record


def _append_result(record: TransactionRecord, target: str, operation: str, result: AdapterResult) -> None:
    payload = asdict(result)
    payload["operation"] = operation
    record.results.setdefault(target, []).append(payload)


def apply_plan(
    plan: Plan,
    adapters: Mapping[str, ThemeAdapter],
    store: TransactionStore,
    confirm: bool = False,
) -> TransactionRecord:
    if not confirm:
        raise ValueError("Apply requires confirm=True")
    record = store.create(plan)
    partial = False

    for target in plan.targets:
        adapter = adapters.get(target, UnsupportedAdapter(target))
        target_backup = store.backup_path_for(record.id, target)
        detected = adapter.detect()
        _append_result(record, target, "detect", detected)
        if detected.status == "skipped":
            partial = True
            continue
        if detected.status == "partial":
            partial = True
        if detected.status not in {"ok", "partial"}:
            partial = True
            continue

        snapshot = adapter.snapshot(target_backup)
        _append_result(record, target, "snapshot", snapshot)
        if snapshot.status == "partial":
            partial = True
        if snapshot.status not in {"ok", "partial"}:
            partial = True
            continue

        applied = adapter.apply(plan)
        _append_result(record, target, "apply", applied)
        if applied.status == "partial" or applied.requires_user_action:
            partial = True
        if applied.status not in {"ok", "partial"}:
            restored = adapter.rollback(target_backup)
            _append_result(record, target, "auto_rollback", restored)
            partial = True
            continue

        verified = adapter.verify(plan)
        _append_result(record, target, "verify", verified)
        if verified.status == "partial" or verified.requires_user_action:
            partial = True
        if verified.status not in {"ok", "partial"} or not verified.verified:
            restored = adapter.rollback(target_backup)
            _append_result(record, target, "auto_rollback", restored)
            partial = True

    record.status = TransactionStatus.PARTIAL if partial else TransactionStatus.APPLIED
    store.save(record)
    return record


def verify_plan(plan: Plan, adapters: Mapping[str, ThemeAdapter]) -> dict[str, AdapterResult]:
    """Read current target state and compare it with the saved Plan."""
    return {
        target: adapters.get(target, UnsupportedAdapter(target)).verify(plan)
        for target in plan.targets
    }
