from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any

from .storage import atomic_write_json, read_json, safe_component

CATEGORIES = ("文档", "图片", "视频", "音频", "压缩包", "安装包", "代码", "未分类")
SHORTCUT_EXTENSIONS = {".lnk", ".url", ".website", ".scf", ".pif"}


def _hash_payload(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class Operation:
    source: str
    kind: str
    category: str | None = None
    destination: str | None = None
    final_destination: str | None = None
    collision: str = "none"
    status: str = "planned"
    message: str = ""


@dataclass
class Plan:
    plan_id: str
    desktop: str
    data_root: str
    operations: list[Operation]
    warnings: list[str] = field(default_factory=list)
    hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {"plan_id": self.plan_id, "desktop": self.desktop, "data_root": self.data_root,
                "operations": [asdict(item) for item in self.operations], "warnings": self.warnings}

    def seal(self) -> "Plan":
        self.hash = _hash_payload(self.payload())
        return self

    def to_dict(self) -> dict[str, Any]:
        payload = self.payload()
        payload["hash"] = self.hash
        return payload

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Plan":
        plan = cls(value["plan_id"], value["desktop"], value["data_root"],
                   [Operation(**item) for item in value.get("operations", [])], value.get("warnings", []), value.get("hash", ""))
        if plan.hash != _hash_payload(plan.payload()):
            raise ValueError("Plan hash mismatch")
        safe_component(plan.plan_id)
        return plan


def create_plan(desktop: Path, data_root: Path, operations: list[Operation], warnings: list[str] | None = None,
                plan_id: str | None = None) -> Plan:
    return Plan(plan_id or f"plan-{uuid.uuid4().hex[:12]}", str(desktop), str(data_root), operations, warnings or []).seal()


def save_plan(plan: Plan, plans_dir: Path) -> Path:
    safe_component(plan.plan_id)
    path = plans_dir / plan.plan_id / "plan.json"
    atomic_write_json(path, plan.to_dict())
    return path


def load_plan(plan_id: str, plans_dir: Path) -> Plan:
    safe_component(plan_id)
    return Plan.from_dict(read_json(plans_dir / plan_id / "plan.json"))
