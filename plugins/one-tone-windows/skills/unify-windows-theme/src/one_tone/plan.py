from __future__ import annotations

import hashlib
import json
import uuid
from dataclasses import dataclass, replace
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Iterable, Mapping

from .palette import generate_palette, parse_hex_color
from .storage import atomic_write_text, validate_safe_component


class PlanIntegrityError(ValueError):
    """Raised when a saved Plan no longer matches its recorded Hash."""


@dataclass(frozen=True)
class Plan:
    id: str
    seed_color: str
    mode: str
    targets: tuple[str, ...]
    palette: dict[str, str]
    created_at: str
    hash: str

    def to_dict(self, include_hash: bool = True) -> dict[str, Any]:
        payload: dict[str, Any] = {
            "id": self.id,
            "seed_color": self.seed_color,
            "mode": self.mode,
            "targets": list(self.targets),
            "palette": dict(self.palette),
            "created_at": self.created_at,
        }
        if include_hash:
            payload["hash"] = self.hash
        return payload


def _canonical_json(payload: Mapping[str, Any]) -> str:
    return json.dumps(payload, ensure_ascii=False, sort_keys=True, separators=(",", ":"))


def compute_plan_hash(payload: Mapping[str, Any]) -> str:
    without_hash = dict(payload)
    without_hash.pop("hash", None)
    return hashlib.sha256(_canonical_json(without_hash).encode("utf-8")).hexdigest()


def _new_id(prefix: str) -> str:
    now = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S")
    return f"{prefix}-{now}-{uuid.uuid4().hex[:6]}"


def create_plan(
    seed_color: str,
    targets: Iterable[str],
    plan_id: str | None = None,
    created_at: datetime | None = None,
) -> Plan:
    normalized_seed = "#" + "".join(f"{channel:02X}" for channel in parse_hex_color(seed_color))
    normalized_targets = tuple(sorted({
        validate_safe_component(target.strip(), "target")
        for target in targets
        if target.strip()
    }))
    if not normalized_targets:
        raise ValueError("At least one target is required")
    timestamp = (created_at or datetime.now(timezone.utc)).isoformat()
    safe_plan_id = validate_safe_component(plan_id, "plan_id") if plan_id else _new_id("plan")
    payload = {
        "id": safe_plan_id,
        "seed_color": normalized_seed,
        "mode": "dark",
        "targets": list(normalized_targets),
        "palette": generate_palette(normalized_seed),
        "created_at": timestamp,
    }
    return Plan(
        id=payload["id"],
        seed_color=payload["seed_color"],
        mode=payload["mode"],
        targets=normalized_targets,
        palette=payload["palette"],
        created_at=payload["created_at"],
        hash=compute_plan_hash(payload),
    )


def save_plan(plan: Plan, plans_dir: Path) -> Path:
    validate_safe_component(plan.id, "plan_id")
    payload = plan.to_dict(include_hash=False)
    computed_hash = compute_plan_hash(payload)
    if plan.hash and plan.hash != computed_hash:
        raise PlanIntegrityError(f"Plan Hash mismatch for {plan.id}")
    plan = replace(plan, hash=computed_hash)
    plans_dir.mkdir(parents=True, exist_ok=True)
    path = plans_dir / f"{plan.id}.json"
    atomic_write_text(path, _canonical_json(plan.to_dict()) + "\n")
    return path


def load_plan(plan_id: str, plans_dir: Path) -> Plan:
    validate_safe_component(plan_id, "plan_id")
    path = plans_dir / f"{plan_id}.json"
    try:
        payload = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise FileNotFoundError(f"Plan not found: {plan_id}") from error
    expected_hash = payload.get("hash", "")
    actual_hash = compute_plan_hash(payload)
    if expected_hash != actual_hash:
        raise PlanIntegrityError(f"Plan Hash mismatch for {plan_id}")
    if payload["id"] != plan_id:
        raise PlanIntegrityError(f"Plan ID mismatch for {plan_id}")
    validate_safe_component(payload["id"], "plan_id")
    for target in payload["targets"]:
        validate_safe_component(target, "target")
    payload["targets"] = tuple(payload["targets"])
    return Plan(**payload)
