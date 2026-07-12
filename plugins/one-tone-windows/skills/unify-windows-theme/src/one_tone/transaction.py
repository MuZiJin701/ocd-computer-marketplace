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
from .storage import atomic_write_text, validate_safe_component

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
    target_metadata: dict[str, dict[str, Any]] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "plan_id": self.plan_id,
            "status": self.status.value,
            "created_at": self.created_at,
            "targets": list(self.targets),
            "results": self.results,
            "support_levels": self.support_levels,
            "target_metadata": self.target_metadata,
        }

    @classmethod
    def from_dict(cls, payload: Mapping[str, Any]) -> TransactionRecord:
        validate_safe_component(payload["id"], "transaction_id")
        validate_safe_component(payload["plan_id"], "plan_id")
        for target in payload["targets"]:
            validate_safe_component(target, "target")
        return cls(
            id=payload["id"],
            plan_id=payload["plan_id"],
            status=TransactionStatus(payload["status"]),
            created_at=payload["created_at"],
            targets=tuple(payload["targets"]),
            results={key: list(value) for key, value in payload.get("results", {}).items()},
            support_levels=dict(payload.get("support_levels", {})),
            target_metadata={key: dict(value) for key, value in payload.get("target_metadata", {}).items()},
        )


def _transaction_id() -> str:
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"tx-{timestamp}-{uuid.uuid4().hex[:6]}"


class TransactionStore:
    def __init__(self, root: Path) -> None:
        self.root = root

    def path_for(self, transaction_id: str) -> Path:
        validate_safe_component(transaction_id, "transaction_id")
        return self.root / transaction_id

    def backup_path_for(self, transaction_id: str, target: str) -> Path:
        validate_safe_component(target, "target")
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
        atomic_write_text(
            path / "transaction.json",
            json.dumps(record.to_dict(), ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n",
        )

    def append_operation(self, record: TransactionRecord, target: str, operation: str, result: AdapterResult) -> None:
        _append_result(record, target, operation, result)
        if result.metadata:
            record.target_metadata.setdefault(target, {}).update(result.metadata)
        self.save(record)

    def load(self, transaction_id: str) -> TransactionRecord:
        path = self.path_for(transaction_id) / "transaction.json"
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except FileNotFoundError as error:
            raise FileNotFoundError(f"Transaction not found: {transaction_id}") from error
        record = TransactionRecord.from_dict(payload)
        if record.id != transaction_id:
            raise ValueError(f"Transaction ID mismatch for {transaction_id}")
        return record

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
                item.get("operation") == "snapshot" and item.get("status") in {"ok", "partial"}
                for item in operation_results
            )
            if not has_snapshot:
                self.append_operation(
                    record,
                    target,
                    "rollback",
                    AdapterResult(target, "failed", False, False, "no restorable snapshot recorded"),
                )
                failed = True
                continue
            adapter = adapters.get(target, UnsupportedAdapter(target))
            result = adapter.rollback(
                self.backup_path_for(transaction_id, target),
                record.target_metadata.get(target),
            )
            self.append_operation(record, target, "rollback", result)
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
    successful_targets = 0
    unsuccessful_targets = False
    compensation_failed = False

    for target in plan.targets:
        adapter = adapters.get(target, UnsupportedAdapter(target))
        target_backup = store.backup_path_for(record.id, target)
        detected = adapter.detect()
        store.append_operation(record, target, "detect", detected)
        if detected.status == "skipped":
            partial = True
            unsuccessful_targets = True
            continue
        if detected.status == "partial":
            partial = True
        if detected.status not in {"ok", "partial"}:
            partial = True
            unsuccessful_targets = True
            continue

        snapshot = adapter.snapshot(target_backup)
        store.append_operation(record, target, "snapshot", snapshot)
        if snapshot.status == "partial":
            partial = True
        if snapshot.status not in {"ok", "partial"}:
            partial = True
            unsuccessful_targets = True
            continue

        applied = adapter.apply(plan)
        store.append_operation(record, target, "apply", applied)
        if applied.status == "partial" or applied.requires_user_action:
            partial = True
        if applied.status not in {"ok", "partial"}:
            restored = adapter.rollback(target_backup, record.target_metadata.get(target))
            store.append_operation(record, target, "auto_rollback", restored)
            partial = True
            unsuccessful_targets = True
            if restored.status not in {"ok", "partial"} or not restored.verified:
                compensation_failed = True
            continue

        verified = adapter.verify(plan)
        store.append_operation(record, target, "verify", verified)
        if verified.status == "partial" or verified.requires_user_action:
            partial = True
        if verified.status not in {"ok", "partial"} or not verified.verified:
            restored = adapter.rollback(target_backup, record.target_metadata.get(target))
            store.append_operation(record, target, "auto_rollback", restored)
            partial = True
            unsuccessful_targets = True
            if restored.status not in {"ok", "partial"} or not restored.verified:
                compensation_failed = True
            continue
        successful_targets += 1

    if compensation_failed or successful_targets == 0:
        record.status = TransactionStatus.FAILED
    elif unsuccessful_targets or partial:
        record.status = TransactionStatus.PARTIAL
    else:
        record.status = TransactionStatus.APPLIED
    store.save(record)
    return record


def verify_plan(plan: Plan, adapters: Mapping[str, ThemeAdapter]) -> dict[str, AdapterResult]:
    """Read current target state and compare it with the saved Plan."""
    return {
        target: adapters.get(target, UnsupportedAdapter(target)).verify(plan)
        for target in plan.targets
    }
