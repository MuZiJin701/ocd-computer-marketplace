from __future__ import annotations

import hashlib
import json
import os
import re
import uuid
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Callable

_SAFE = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
TOOLS = ("python", "git", "uv", "node")
PACKAGES = {"python": "python", "git": "git", "uv": "main/uv", "node": "nodejs"}
WINGET = {"python": "Python.Python.3", "git": "Git.Git", "uv": "astral-sh.uv", "node": "OpenJS.NodeJS"}


def safe_component(value: str) -> str:
    if not isinstance(value, str) or not _SAFE.fullmatch(value):
        raise ValueError(f"unsafe path component: {value!r}")
    return value


def atomic_write_json(path: Path, payload: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_name(path.name + ".tmp")
    tmp.write_text(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def read_json(path: Path) -> dict[str, Any]:
    for candidate in (path, path.with_name(path.name + ".tmp")):
        try:
            value = json.loads(candidate.read_text(encoding="utf-8"))
            if isinstance(value, dict): return value
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            pass
    raise FileNotFoundError(path)


def plan_hash(payload: dict[str, Any]) -> str:
    raw = json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(raw).hexdigest()


@dataclass
class Tool:
    name: str
    executable: str | None
    version: str | None = None
    source: str = "missing"
    path_conforms: bool | None = None


@dataclass
class Plan:
    plan_id: str
    scoop_root: str
    tools: list[Tool]
    warnings: list[str] = field(default_factory=list)
    hash: str = ""

    def payload(self) -> dict[str, Any]:
        return {"plan_id": self.plan_id, "scoop_root": self.scoop_root,
                "tools": [asdict(item) for item in self.tools], "warnings": self.warnings}

    def seal(self) -> "Plan":
        self.hash = plan_hash(self.payload()); return self

    def to_dict(self) -> dict[str, Any]:
        value = self.payload(); value["hash"] = self.hash; return value

    @classmethod
    def from_dict(cls, value: dict[str, Any]) -> "Plan":
        plan = cls(value["plan_id"], value["scoop_root"], [Tool(**item) for item in value.get("tools", [])], value.get("warnings", []), value.get("hash", ""))
        if plan.hash != plan_hash(plan.payload()): raise ValueError("Plan hash mismatch")
        safe_component(plan.plan_id); return plan


def save_plan(plan: Plan, plans_dir: Path) -> Path:
    safe_component(plan.plan_id); path = plans_dir / plan.plan_id / "plan.json"; atomic_write_json(path, plan.to_dict()); return path


def load_plan(plan_id: str, plans_dir: Path) -> Plan:
    safe_component(plan_id); return Plan.from_dict(read_json(plans_dir / plan_id / "plan.json"))
