from __future__ import annotations

import os
import shutil
import uuid
from pathlib import Path
from typing import Any, Callable

from .storage import Plan, Tool, atomic_write_json, load_plan, plan_hash, read_json, save_plan
from .tools import ScoopInstaller, WingetInstaller, detect, preflight_root, scoop_available


def _status(values: list[str]) -> str:
    good = sum(value == "ok" for value in values)
    degraded = any(value == "partial" for value in values)
    bad = sum(value in {"failed", "skipped"} for value in values)
    if good == 0: return "failed" if bad else ("ok" if values else "failed")
    return "partial" if bad or degraded else "ok"


def _result(status: str, **extra: Any) -> dict[str, Any]: return {"status": status, **extra}


def _build_plan(root: Path, current: list[Tool], warnings: list[str], scoop: bool | None = None) -> Plan:
    tools = []
    scoop = scoop_available() if scoop is None else scoop
    for item in current:
        if item.executable:
            tools.append(item)
        else:
            tools.append(Tool(item.name, None, source="scoop" if scoop and not warnings else "winget", path_conforms=scoop and not warnings))
    return Plan(f"plan-{uuid.uuid4().hex[:12]}", str(root), tools, warnings).seal()


def detect_tools(which: Callable[[str], str | None] | None = None) -> list[Tool]:
    return detect(which) if which else detect()


def preview(scoop_root: Path = Path("D:/software/scoop"), plans_dir: Path = Path(".scoop-toolchain/plans"), which: Callable[[str], str | None] | None = None, **_: Any) -> dict[str, Any]:
    root = Path(scoop_root)
    warnings = preflight_root(root)
    current = detect_tools(which)
    scoop = bool((which or shutil.which)("scoop"))
    plan = _build_plan(root, current, warnings, scoop)
    save_plan(plan, Path(plans_dir))
    return _result("partial" if warnings and any(not item.executable for item in current) else "ok", command="preview", plan_id=plan.plan_id,
                   scoop_root=str(root), tools=[item.__dict__ for item in plan.tools], warnings=warnings, changed=False)


def apply(plan_id: str, confirm: bool = False, plans_dir: Path = Path(".scoop-toolchain/plans"),
          scoop_installer: ScoopInstaller | None = None, winget_installer: WingetInstaller | None = None,
          which: Callable[[str], str | None] | None = None, **_: Any) -> dict[str, Any]:
    if not confirm: raise ValueError("explicit confirmation is required")
    plan = load_plan(plan_id, Path(plans_dir))
    root = Path(plan.scoop_root)
    results = []
    scoop = scoop_installer or ScoopInstaller()
    winget = winget_installer or WingetInstaller()
    root_warnings = preflight_root(root)
    scoop_ready = not root_warnings and scoop_available()
    bootstrap_message = ""
    if not root_warnings and not scoop_ready:
        try:
            bootstrap_ok, bootstrap_message = scoop.bootstrap(root)
            scoop_ready = bootstrap_ok
        except AttributeError:
            bootstrap_message = "Scoop bootstrap is unavailable"
        if scoop_ready and not root.exists():
            root.mkdir(parents=True)
    for item in plan.tools:
        if item.executable:
            results.append({"tool": item.name, "status": "skipped", "source": "existing", "path": item.executable, "message": "preserved existing installation"})
            continue
        success = False
        message = ""
        source = item.source
        if root_warnings:
            message = "; ".join(root_warnings)
        elif scoop_ready:
            success, message = scoop.install(item.name, root)
            source = "scoop"
        if not success and not root_warnings:
            success, message = winget.install(item.name, root)
            source = "winget"
        actual = {tool.name: tool for tool in detect_tools(which)}.get(item.name)
        path = actual.executable if actual else None
        result_status = "partial" if success and source == "winget" else ("ok" if success else "failed")
        results.append({"tool": item.name, "status": result_status, "source": source, "path": path,
                        "path_conforms": source == "scoop", "message": message or bootstrap_message or ("winget path is controlled by Windows" if source == "winget" else "")})
    status = _status([item["status"] for item in results])
    return _result(status, command="apply", plan_id=plan.plan_id, results=results, changed=any(item["status"] == "ok" and item["source"] != "existing" for item in results))


def verify(plan_id: str, plans_dir: Path = Path(".scoop-toolchain/plans"), which: Callable[[str], str | None] | None = None, **_: Any) -> dict[str, Any]:
    plan = load_plan(plan_id, Path(plans_dir))
    current = {item.name: item for item in detect_tools(which)}
    failures = []
    for expected in plan.tools:
        actual = current[expected.name]
        if not actual.executable:
            failures.append({"tool": expected.name, "message": "tool is missing"})
        elif expected.source == "scoop" and not str(actual.executable).lower().startswith(str(Path(plan.scoop_root)).lower()):
            failures.append({"tool": expected.name, "message": "tool exists but is outside the Scoop root", "path": actual.executable})
    return _result("partial" if failures else "ok", command="verify", plan_id=plan.plan_id, verified=not failures,
                   tools=[item.__dict__ for item in current.values()], failures=failures, changed=False)
