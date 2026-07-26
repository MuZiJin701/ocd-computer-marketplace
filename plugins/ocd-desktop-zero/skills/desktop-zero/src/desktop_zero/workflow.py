from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable

from .desktop import build_operations, resolve_desktop
from .model import Operation, Plan, create_plan, load_plan, save_plan
from .repair import LockHolder, repair_locked_target
from .storage import atomic_write_json, read_json, safe_component


def _result(status: str, **extra: Any) -> dict[str, Any]:
    return {"status": status, **extra}


def _status(results: list[str]) -> str:
    good = sum(item == "ok" for item in results)
    bad = sum(item in {"failed", "skipped"} for item in results)
    if not results or good == 0:
        return "failed" if bad or not results else "skipped"
    return "partial" if bad else "ok"


def preview(desktop: Path | None = None, data_root: Path = Path("D:/data"), plans_dir: Path = Path(".desktop-zero/plans"), **_: Any) -> dict[str, Any]:
    desktop = (desktop or resolve_desktop()).resolve()
    data_root = Path(data_root)
    operations, warnings = build_operations(desktop, data_root)
    plan = create_plan(desktop, data_root, operations, warnings)
    save_plan(plan, Path(plans_dir))
    return _result("failed" if warnings else "ok", command="preview", plan_id=plan.plan_id,
                   plan_hash=plan.hash, desktop=str(desktop), data_root=str(data_root),
                   operations=[operation.__dict__ for operation in operations], warnings=warnings,
                   changed=False)


def _ledger_path(transactions_dir: Path, transaction_id: str) -> Path:
    safe_component(transaction_id)
    return transactions_dir / transaction_id / "transaction.json"


def apply(plan_id: str, confirm: bool = False, plans_dir: Path = Path(".desktop-zero/plans"),
          transactions_dir: Path = Path(".desktop-zero/transactions"),
          lock_holders: dict[str, list[LockHolder]] | Callable[[Path], list[LockHolder]] | None = None,
          close_process: Callable[[int], bool] | None = None,
          confirm_repair: Callable[[LockHolder, Path], bool] | None = None, **_: Any) -> dict[str, Any]:
    if not confirm:
        raise ValueError("explicit confirmation is required")
    plan = load_plan(plan_id, Path(plans_dir))
    tx_id = f"tx-{uuid.uuid4().hex[:12]}"
    ledger = {"transaction_id": tx_id, "plan_id": plan.plan_id, "desktop": plan.desktop, "snapshots": [], "moves": [], "deleted_shortcuts": [], "results": []}
    path = _ledger_path(Path(transactions_dir), tx_id)
    atomic_write_json(path, ledger)
    statuses: list[str] = []
    for operation in plan.operations:
        source = Path(operation.source)
        ledger["snapshots"].append({"source": str(source), "exists": source.exists(), "is_dir": source.is_dir()})
        atomic_write_json(path, ledger)
        try:
            if operation.kind == "delete_shortcut":
                source.unlink()
                ledger["deleted_shortcuts"].append(str(source))
                result = {"source": str(source), "status": "ok", "message": "shortcut deleted; not restorable"}
            else:
                destination = Path(operation.final_destination or operation.destination or "")
                destination.parent.mkdir(parents=True, exist_ok=True)
                if destination.exists():
                    result = {"source": str(source), "status": "failed", "message": "destination collision changed after Preview"}
                else:
                    shutil.move(str(source), str(destination))
                    ledger["moves"].append({"source": str(source), "destination": str(destination)})
                    result = {"source": str(source), "destination": str(destination), "status": "ok"}
            statuses.append(result["status"])
        except (OSError, shutil.Error) as exc:
            repaired = False
            if operation.kind == "move" and lock_holders and close_process and confirm_repair:
                holders = lock_holders(source) if callable(lock_holders) else lock_holders.get(str(source), [])
                repair_locked_target(source, holders, close_process, confirm_repair)
                try:
                    destination = Path(operation.final_destination or operation.destination or "")
                    destination.parent.mkdir(parents=True, exist_ok=True)
                    if not destination.exists():
                        shutil.move(str(source), str(destination))
                        ledger["moves"].append({"source": str(source), "destination": str(destination)})
                        result = {"source": str(source), "destination": str(destination), "status": "ok", "message": "moved after constrained repair"}
                        repaired = True
                except (OSError, shutil.Error):
                    pass
            if not repaired:
                result = {"source": str(source), "status": "failed", "message": str(exc)}
            statuses.append(result["status"])
        ledger["results"].append(result)
        atomic_write_json(path, ledger)
    ledger["status"] = _status(statuses)
    atomic_write_json(path, ledger)
    return _result(ledger["status"], command="apply", plan_id=plan.plan_id, transaction_id=tx_id,
                   results=ledger["results"], changed=any(item == "ok" for item in statuses))


def verify(plan_id: str, plans_dir: Path = Path(".desktop-zero/plans"), **_: Any) -> dict[str, Any]:
    plan = load_plan(plan_id, Path(plans_dir))
    desktop = Path(plan.desktop)
    failures: list[dict[str, str]] = []
    for operation in plan.operations:
        source = Path(operation.source)
        if operation.kind == "delete_shortcut" and source.exists():
            failures.append({"source": str(source), "message": "shortcut still exists"})
        elif operation.kind == "move" and source.exists():
            failures.append({"source": str(source), "message": "item remains on desktop"})
        elif operation.kind == "move" and not Path(operation.final_destination or operation.destination or "").exists():
            failures.append({"source": str(source), "message": "destination evidence missing"})
    remaining = []
    if desktop.exists():
        remaining = [str(item) for item in desktop.iterdir()]
    status = "partial" if failures or remaining else "ok"
    return _result(status, command="verify", plan_id=plan.plan_id,
                   verified=not failures and not remaining, failures=failures, remaining=remaining, changed=False)


def rollback(transaction_id: str, transactions_dir: Path = Path(".desktop-zero/transactions"), **_: Any) -> dict[str, Any]:
    path = _ledger_path(Path(transactions_dir), transaction_id)
    ledger = read_json(path)
    results = []
    for move in reversed(ledger.get("moves", [])):
        source, destination = Path(move["source"]), Path(move["destination"])
        try:
            if source.exists():
                raise FileExistsError(f"rollback source already exists: {source}")
            if not destination.exists():
                raise FileNotFoundError(destination)
            source.parent.mkdir(parents=True, exist_ok=True)
            shutil.move(str(destination), str(source))
            results.append({"source": str(source), "destination": str(destination), "status": "ok"})
        except OSError as exc:
            results.append({"source": str(source), "destination": str(destination), "status": "failed", "message": str(exc)})
    status = _status([item["status"] for item in results]) if results else "skipped"
    ledger["rollback"] = results
    ledger["rollback_status"] = status
    atomic_write_json(path, ledger)
    return _result(status, command="rollback", transaction_id=transaction_id, results=results, changed=bool(results))
