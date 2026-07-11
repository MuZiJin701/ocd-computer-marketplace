from __future__ import annotations

import json
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

    def create(self, plan: Plan) -> TransactionRecord:
        record = TransactionRecord(
            id=_transaction_id(),
            plan_id=plan.id,
            status=TransactionStatus.PENDING,
            created_at=datetime.now(timezone.utc).isoformat(),
            targets=plan.targets,
        )
        self.save(record)
        (self.path_for(record.id) / "backup").mkdir(parents=True, exist_ok=True)
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

    def rollback(self, transaction_id: str, adapters: Mapping[str, ThemeAdapter]) -> TransactionRecord:
        record = self.load(transaction_id)
        backup_dir = self.path_for(transaction_id) / "backup"
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
            result = adapter.rollback(backup_dir)
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
    backup_dir = store.path_for(record.id) / "backup"
    modified_targets: list[str] = []
    skipped = False
    partial = False
    failed = False

    for target in plan.targets:
        adapter = adapters.get(target, UnsupportedAdapter(target))
        detected = adapter.detect()
        _append_result(record, target, "detect", detected)
        if detected.status == "skipped":
            skipped = True
            continue
        if detected.status == "partial":
            partial = True
        if detected.status not in {"ok", "partial"}:
            failed = True
            break

        snapshot = adapter.snapshot(backup_dir)
        _append_result(record, target, "snapshot", snapshot)
        if snapshot.status == "partial":
            partial = True
        if snapshot.status not in {"ok", "partial"}:
            failed = True
            break

        applied = adapter.apply(plan)
        _append_result(record, target, "apply", applied)
        if applied.changed and target not in modified_targets:
            modified_targets.append(target)
        if applied.status == "partial" or applied.requires_user_action:
            partial = True
        if applied.status not in {"ok", "partial"}:
            failed = True
            break

        verified = adapter.verify(plan)
        _append_result(record, target, "verify", verified)
        if verified.status == "partial" or verified.requires_user_action:
            partial = True
        if verified.status not in {"ok", "partial"} or not verified.verified:
            failed = True
            break

    if failed:
        for target in reversed(modified_targets):
            adapter = adapters.get(target, UnsupportedAdapter(target))
            restored = adapter.rollback(backup_dir)
            _append_result(record, target, "auto_rollback", restored)
        record.status = TransactionStatus.FAILED
    elif skipped or partial:
        record.status = TransactionStatus.PARTIAL
    else:
        record.status = TransactionStatus.APPLIED
    store.save(record)
    return record


def _operation_results(record: TransactionRecord, target: str) -> list[dict[str, Any]]:
    return record.results.get(target, [])


def _record_support_level(record: TransactionRecord, target: str) -> str:
    operations = _operation_results(record, target)
    if not operations or any(item.get("status") == "skipped" for item in operations):
        return "SKIPPED"
    if any(item.get("status") == "failed" or item.get("requires_user_action") for item in operations):
        return "PARTIAL"
    detected = next((item for item in operations if item.get("operation") == "detect"), {})
    if not detected.get("version"):
        return "PARTIAL"
    if not all(item.get("verified") for item in operations if item.get("operation") != "apply"):
        return "PARTIAL"
    return "FULL"


def run_full_cycle(
    plan: Plan,
    adapters: Mapping[str, ThemeAdapter],
    store: TransactionStore,
    confirm: bool,
    restart_apps: bool,
) -> TransactionRecord:
    """Run the eight-step validation flow and leave the target restored."""
    record = apply_plan(plan, adapters, store, confirm=confirm)
    if record.status == TransactionStatus.FAILED:
        for target in plan.targets:
            record.support_levels[target] = "PARTIAL"
        store.save(record)
        return record

    backup_dir = store.path_for(record.id) / "backup"
    for target in plan.targets:
        operation_results = _operation_results(record, target)
        if any(item.get("status") == "skipped" for item in operation_results):
            record.support_levels[target] = "SKIPPED"
            continue
        adapter = adapters.get(target, UnsupportedAdapter(target))
        restarted = adapter.restart()
        _append_result(record, target, "restart", restarted)
        verified_again = adapter.verify_again(plan)
        _append_result(record, target, "verify_again", verified_again)
        restored = adapter.rollback(backup_dir)
        _append_result(record, target, "rollback", restored)
        verify_restore = AdapterResult(
            target,
            restored.status,
            False,
            restored.verified,
            "restore verification reused Adapter rollback verification",
            restored.requires_user_action,
            restored.version,
        )
        _append_result(record, target, "verify_restore", verify_restore)
        record.support_levels[target] = _record_support_level(record, target)
        if not restart_apps and restarted.status == "partial":
            record.support_levels[target] = "PARTIAL"

    record.status = TransactionStatus.ROLLED_BACK if all(level != "SKIPPED" for level in record.support_levels.values()) else TransactionStatus.PARTIAL
    store.save(record)
    return record
