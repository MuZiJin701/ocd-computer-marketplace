from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable


@dataclass(frozen=True)
class LockHolder:
    pid: int | None
    name: str | None
    system: bool = False
    confirmed: bool = False


def repair_locked_target(target: Path, holders: list[LockHolder], close: Callable[[int], bool], confirm: Callable[[LockHolder, Path], bool]) -> list[dict[str, object]]:
    results = []
    for holder in holders:
        if holder.system or holder.pid is None or not holder.name or not holder.confirmed:
            results.append({"target": str(target), "process": holder.name, "status": "skipped", "message": "unknown, system, or unconfirmed process"})
            continue
        if not confirm(holder, target):
            results.append({"target": str(target), "process": holder.name, "status": "skipped", "message": "user declined constrained repair"})
            continue
        results.append({"target": str(target), "process": holder.name, "status": "ok" if close(holder.pid) else "failed"})
    return results
