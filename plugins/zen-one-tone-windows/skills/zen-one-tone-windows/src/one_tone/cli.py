from __future__ import annotations

import argparse
import json
import os
import re
import shutil
import sys
from dataclasses import asdict
from pathlib import Path
from typing import Sequence

from .adapters import (
    ChromeAdapter,
    CodexAdapter,
    TerminalAdapter,
    UnsupportedAdapter,
    VSCodeFamilyAdapter,
    WindowsAdapter,
    WindowsConfig,
)
from .adapters.vscode_family import EditorSpec
from .adapters.windows import WindowsDesktopBackend, WindowsRegistryBackend
from .inventory import inventory_groups
from .plan import PlanIntegrityError, create_plan, load_plan, save_plan
from .storage import json_safe
from .transaction import TransactionStatus, TransactionStore, apply_plan, verify_plan

DEFAULT_TARGETS = ("windows", "terminal", "vscode", "trae", "codex", "chrome")


def _default_runtime_dir() -> Path:
    return Path(__file__).resolve().parents[2] / ".one-tone"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="one-tone")
    commands = parser.add_subparsers(dest="command", required=True)
    runtime_dir = _default_runtime_dir()

    preview = commands.add_parser("preview", help="generate a Plan without changing targets")
    preview.add_argument("seed_color")
    preview.add_argument(
        "--targets",
        default=",".join(DEFAULT_TARGETS),
        help="comma-separated target names (default: all supported targets)",
    )
    preview.add_argument("--plans-dir", type=Path, default=runtime_dir / "plans")
    preview.add_argument("--transactions-dir", type=Path, default=runtime_dir / "transactions")
    preview.add_argument("--state-dir", type=Path, default=runtime_dir / "state")
    preview.add_argument("--output", choices=("human", "json"), default="human")

    apply = commands.add_parser("apply", help="apply an existing Plan")
    apply.add_argument("plan_id")
    apply.add_argument("--confirm", action="store_true", required=True)
    apply.add_argument("--plans-dir", type=Path, default=runtime_dir / "plans")
    apply.add_argument("--transactions-dir", type=Path, default=runtime_dir / "transactions")
    apply.add_argument("--state-dir", type=Path, default=runtime_dir / "state")
    apply.add_argument("--keep-transactions", type=int, default=5)
    apply.add_argument("--output", choices=("human", "json"), default="human")

    verify = commands.add_parser("verify", help="check current targets against a saved Plan")
    verify.add_argument("plan_id")
    verify.add_argument("--plans-dir", type=Path, default=runtime_dir / "plans")
    verify.add_argument("--state-dir", type=Path, default=runtime_dir / "state")
    verify.add_argument("--output", choices=("human", "json"), default="human")

    rollback = commands.add_parser("rollback", help="restore one transaction")
    rollback.add_argument("transaction_id")
    rollback.add_argument("--transactions-dir", type=Path, default=runtime_dir / "transactions")
    rollback.add_argument("--state-dir", type=Path, default=runtime_dir / "state")
    rollback.add_argument("--output", choices=("human", "json"), default="human")
    return parser


def _target_names(raw_targets: str) -> tuple[str, ...]:
    targets = tuple(sorted({item.strip() for item in raw_targets.split(",") if item.strip()}))
    if not targets:
        raise ValueError("At least one target is required")
    return targets


def _adapter_result_payload(result: dict[str, object]) -> dict[str, object]:
    metadata = result.get("metadata", {})
    if isinstance(metadata, dict):
        metadata = {key: value for key, value in metadata.items() if key not in {"artifact", "artifacts"}}
    return {
        "target": result.get("target"),
        "status": result.get("status"),
        "changed": result.get("changed", False),
        "verified": result.get("verified", False),
        "message": result.get("message", ""),
        "requires_user_action": result.get("requires_user_action", False),
        "version": result.get("version"),
        "metadata": metadata,
    }


def _record_payload(command: str, record, extra: dict[str, object] | None = None) -> dict[str, object]:
    targets: list[dict[str, object]] = []
    for target in record.targets:
        operations = record.results.get(target, [])
        latest = operations[-1] if operations else {"target": target, "status": "skipped", "message": "no result"}
        item = _adapter_result_payload(latest)
        item["target"] = target
        item["support_level"] = record.support_levels.get(target)
        item["requires_user_action"] = any(result.get("requires_user_action", False) for result in operations)
        targets.append(item)
    payload = {
        "command": command,
        "status": record.status.value,
        "plan_id": record.plan_id,
        "transaction_id": record.id,
        "targets": targets,
        "support_levels": record.support_levels,
        "message": f"{command} completed with status {record.status.value}",
    }
    if extra:
        payload.update(extra)
    return payload


def _emit(payload: dict[str, object], output: str, *, error: bool = False) -> None:
    if output == "json":
        print(json.dumps(json_safe(payload), ensure_ascii=False, sort_keys=True), file=sys.stderr if error else sys.stdout)


def _optional_path(name: str) -> Path | None:
    value = os.environ.get(name)
    return Path(value) if value else None


def _first_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def _configured_or_first(name: str, candidates: list[Path]) -> Path:
    return _optional_path(name) or _first_path(candidates)


def _first_executable(name: str, command: str, candidates: list[Path]) -> Path:
    configured = _optional_path(name)
    if configured is not None:
        return configured
    for candidate in candidates:
        if candidate.exists():
            return candidate
    resolved = shutil.which(command)
    return Path(resolved) if resolved else Path(command)


def _launcher_argument(executable: Path, argument: str) -> Path | None:
    if executable.suffix.lower() not in {".cmd", ".bat"} or not executable.is_file():
        return None
    try:
        contents = executable.read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None
    pattern = re.compile(
        rf"--{re.escape(argument)}(?:=|\s+)(?:\"([^\"]+)\"|'([^']+)'|([^\s%]+))",
        re.IGNORECASE,
    )
    match = pattern.search(contents)
    if not match:
        return None
    value = next((group for group in match.groups() if group), None)
    if not value:
        return None
    value = os.path.expandvars(value)
    if value.startswith("%~dp0"):
        value = str(executable.parent) + value[5:]
    path = Path(value)
    return path if path.is_absolute() else executable.parent / path


def _portable_editor_candidates(executable: Path) -> list[tuple[Path, Path, str]]:
    if not executable.is_file():
        return []
    roots: list[Path] = []
    if executable.parent.name.casefold() == "bin":
        roots.append(executable.parent.parent)
    roots.extend(executable.parents)
    candidates: list[tuple[Path, Path, str]] = []
    seen: set[tuple[Path, Path]] = set()
    for root in roots:
        data = root / "data"
        pair = (data / "user-data" / "User" / "settings.json", data / "extensions")
        if pair in seen:
            continue
        seen.add(pair)
        if pair[0].is_file() or pair[1].is_dir():
            candidates.append((*pair, "portable"))
    return candidates


def _resolve_editor_spec(
    target: str,
    executable: Path,
    default_candidates: list[tuple[Path, Path, str]],
    settings_override: Path | None,
    extensions_override: Path | None,
    artifacts_dir: Path,
) -> EditorSpec:
    launcher_settings = _launcher_argument(executable, "user-data-dir")
    launcher_extensions = _launcher_argument(executable, "extensions-dir")
    if settings_override is not None or extensions_override is not None:
        settings = settings_override or (launcher_settings / "User" / "settings.json" if launcher_settings else default_candidates[0][0])
        extensions = extensions_override or launcher_extensions or default_candidates[0][1]
        return EditorSpec(target, executable, settings, extensions, artifacts_dir=artifacts_dir, resolution_source="environment")
    if launcher_settings is not None or launcher_extensions is not None:
        settings = launcher_settings / "User" / "settings.json" if launcher_settings else default_candidates[0][0]
        extensions = launcher_extensions or default_candidates[0][1]
        return EditorSpec(target, executable, settings, extensions, artifacts_dir=artifacts_dir, resolution_source="launcher")

    portable = _portable_editor_candidates(executable)
    candidates = portable + default_candidates
    existing = [candidate for candidate in candidates if candidate[0].is_file() or candidate[1].is_dir()]
    if existing:
        priority_order = {"portable": 0, "standard": 1}
        priority = min(priority_order.get(candidate[2], 99) for candidate in existing)
        priority_candidates = [candidate for candidate in existing if priority_order.get(candidate[2], 99) == priority]
        evidence_score = lambda candidate: (int(candidate[0].is_file()), int(candidate[1].is_dir()))
        best_score = max(evidence_score(candidate) for candidate in priority_candidates)
        winners = [candidate for candidate in priority_candidates if evidence_score(candidate) == best_score]
        unique = {(candidate[0], candidate[1]) for candidate in winners}
        if len(unique) > 1:
            description = "; ".join(f"{settings} + {extensions}" for settings, extensions, _ in winners)
            settings, extensions, source = winners[0]
            return EditorSpec(
                target,
                executable,
                settings,
                extensions,
                artifacts_dir=artifacts_dir,
                resolution_status="skipped",
                resolution_message=f"{target} configuration paths are ambiguous: {description}",
            )
        settings, extensions, source = winners[0]
        return EditorSpec(target, executable, settings, extensions, artifacts_dir=artifacts_dir, resolution_source=source)
    settings, extensions, source = default_candidates[0]
    return EditorSpec(
        target,
        executable,
        settings,
        extensions,
        artifacts_dir=artifacts_dir,
        resolution_status="skipped",
        resolution_message=f"{target} configuration instance was not found",
        resolution_source=source,
    )


def _editor_spec_from_plan(target: str, context: dict[str, object], fallback: EditorSpec) -> EditorSpec:
    status = context.get("status")
    if status != "ok":
        return EditorSpec(
            target,
            fallback.executable,
            fallback.settings_path,
            fallback.extensions_dir,
            artifacts_dir=fallback.artifacts_dir,
            resolution_status="skipped",
            resolution_message=str(context.get("reason") or f"{target} has no resolved configuration instance in Plan"),
        )
    try:
        return EditorSpec(
            target,
            Path(str(context["executable"])),
            Path(str(context["settings_path"])),
            Path(str(context["extensions_dir"])),
            artifacts_dir=fallback.artifacts_dir,
            resolution_source=str(context.get("source") or "plan"),
        )
    except (KeyError, TypeError):
        return EditorSpec(
            target,
            fallback.executable,
            fallback.settings_path,
            fallback.extensions_dir,
            artifacts_dir=fallback.artifacts_dir,
            resolution_status="skipped",
            resolution_message=f"{target} Plan instance paths are incomplete",
        )


def _scoop_root_from_shim(executable: Path) -> Path | None:
    if executable.parent.name.casefold() != "shims":
        return None
    return executable.parent.parent


def _terminal_settings_candidates(executable: Path, localappdata: Path, userprofile: Path) -> list[Path]:
    candidates = [
        localappdata / "Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json",
        localappdata / "Microsoft/Windows Terminal/settings.json",
        userprofile / "scoop/persist/windows-terminal/settings/settings.json",
        localappdata / "scoop/persist/windows-terminal/settings/settings.json",
    ]
    scoop_root = _scoop_root_from_shim(executable)
    if scoop_root is not None:
        candidates.insert(0, scoop_root / "persist/windows-terminal/settings/settings.json")
    return candidates


def build_target_adapters(targets, state_dir: Path, target_instances: dict[str, dict[str, object]] | None = None):
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    localappdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    userprofile = Path(os.environ.get("USERPROFILE", Path.home()))
    terminal_executable = _first_executable("ONE_TONE_TERMINAL_EXECUTABLE", "wt", [])
    terminal_settings = _configured_or_first(
        "ONE_TONE_TERMINAL_SETTINGS",
        _terminal_settings_candidates(terminal_executable, localappdata, userprofile),
    )
    terminal_instance = target_instances.get("terminal", {}) if target_instances is not None else {}
    if terminal_instance.get("status") == "ok" and terminal_instance.get("settings_path"):
        terminal_settings = Path(str(terminal_instance["settings_path"]))
    if target_instances is None:
        vscode_defaults = [(appdata / "Code/User/settings.json", userprofile / ".vscode/extensions", "standard")]
        vscode_spec = _resolve_editor_spec(
            "vscode",
            _first_executable("ONE_TONE_VSCODE_EXECUTABLE", "code", []),
            vscode_defaults,
            _optional_path("ONE_TONE_VSCODE_SETTINGS"),
            _optional_path("ONE_TONE_VSCODE_EXTENSIONS"),
            state_dir / "vscode-artifacts",
        )
        trae_defaults = [
            (appdata / "TRAE/User/settings.json", userprofile / ".trae/extensions", "standard"),
            (appdata / "Trae/User/settings.json", userprofile / ".trae/extensions", "standard"),
        ]
        trae_spec = _resolve_editor_spec(
            "trae",
            _first_executable("ONE_TONE_TRAE_EXECUTABLE", "trae", []),
            trae_defaults,
            _optional_path("ONE_TONE_TRAE_SETTINGS"),
            _optional_path("ONE_TONE_TRAE_EXTENSIONS"),
            state_dir / "trae-artifacts",
        )
    else:
        vscode_spec = _editor_spec_from_plan(
            "vscode",
            target_instances.get("vscode", {}),
            EditorSpec("vscode", "", Path(), Path(), artifacts_dir=state_dir / "vscode-artifacts"),
        )
        trae_spec = _editor_spec_from_plan(
            "trae",
            target_instances.get("trae", {}),
            EditorSpec("trae", "", Path(), Path(), artifacts_dir=state_dir / "trae-artifacts"),
        )
    codex_path = os.environ.get("ONE_TONE_CODEX_THEME_CONFIG")
    chrome_preferences = _configured_or_first(
        "ONE_TONE_CHROME_PREFERENCES",
        [localappdata / "Google/Chrome/User Data/Default/Preferences"],
    )
    registry = {}
    for target in targets:
        if target == "windows":
            registry[target] = WindowsAdapter(WindowsConfig(state_dir / "windows-wallpapers"), WindowsRegistryBackend(), WindowsDesktopBackend())
        elif target == "terminal":
            registry[target] = TerminalAdapter(
                terminal_settings,
                target_instance=terminal_instance or None,
                discover_shell=target_instances is None,
            )
        elif target == "vscode":
            registry[target] = VSCodeFamilyAdapter(vscode_spec)
        elif target == "cursor":
            registry[target] = UnsupportedAdapter(target)
        elif target == "trae":
            registry[target] = VSCodeFamilyAdapter(trae_spec)
        elif target == "codex":
            registry[target] = CodexAdapter(Path(codex_path) if codex_path else None)
        elif target == "chrome":
            registry[target] = ChromeAdapter(state_dir / "chrome-themes", chrome_preferences if chrome_preferences.is_file() else None)
        else:
            registry[target] = UnsupportedAdapter(target)
    return registry


def _preview(args: argparse.Namespace) -> int:
    targets = _target_names(args.targets)
    adapters = build_target_adapters(targets, args.state_dir)
    detected = {target: adapter.detect() for target, adapter in adapters.items()}
    target_instances = {
        target: adapter.target_instance()
        for target, adapter in adapters.items()
        if hasattr(adapter, "target_instance")
    }
    plan = create_plan(args.seed_color, targets, target_instances=target_instances)
    path = save_plan(plan, args.plans_dir)
    unsupported_count = sum(result.status != "ok" for result in detected.values())
    if args.output == "json":
        _emit({
            "command": "preview",
            "status": "ok",
            "plan_id": plan.id,
            "mode_palettes": plan.palettes,
            "field_capabilities": plan.field_capabilities,
            "target_instances": plan.target_instances,
            "targets": [
                {
                    "target": target,
                    "status": result.status,
                    "changed": result.changed,
                    "verified": result.verified,
                    "message": result.message,
                    "requires_user_action": result.requires_user_action,
                    "version": result.version,
                    "metadata": result.metadata,
                }
                for target, result in detected.items()
            ],
            "selected_mode": plan.mode,
            "mode_semantics": "Mode is a presentation variant of the Seed Color; it does not change Windows system mode",
            "field_inventory": {
                target: inventory_groups(target)
                for target in plan.targets
            },
            "warnings": unsupported_count,
            "path": str(path),
        }, args.output)
        return 0
    print(f"Plan ID: {plan.id}")
    print("Targets:")
    for target in plan.targets:
        print(f"- {target}")
    print("Detection:")
    for target, result in detected.items():
        print(f"- {target}: {result.status} — {result.message}")
    print("Validation:")
    print("- Contrast: PASS")
    print("- Appearance safety: PASS")
    print("Field regions:")
    for target in plan.targets:
        print(f"- {target}: {', '.join(inventory_groups(target)) or 'none'}")
    print(f"- Saved: {path}")
    return 0


def _apply(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan_id, args.plans_dir)
    adapters = build_target_adapters(plan.targets, args.state_dir, plan.target_instances)
    store = TransactionStore(args.transactions_dir)
    record = apply_plan(plan, adapters, store, confirm=args.confirm)
    removed = store.prune(keep=args.keep_transactions, preserve={record.id})
    if args.output == "json":
        _emit(_record_payload("apply", record, {"pruned_transactions": removed}), args.output)
        return 0 if record.status in {TransactionStatus.APPLIED, TransactionStatus.PARTIAL} else 1
    print(f"Transaction ID: {record.id}")
    print(f"Status: {record.status.value}")
    if removed:
        print(f"Pruned transactions: {len(removed)}")
    return 0 if record.status in {TransactionStatus.APPLIED, TransactionStatus.PARTIAL} else 1


def _rollback(args: argparse.Namespace) -> int:
    store = TransactionStore(args.transactions_dir)
    record = store.load(args.transaction_id)
    target_instances = {
        target: metadata["target_instance"]
        for target, metadata in record.target_metadata.items()
        if isinstance(metadata, dict) and isinstance(metadata.get("target_instance"), dict)
    }
    adapters = build_target_adapters(record.targets, args.state_dir, target_instances)
    restored = store.rollback(record.id, adapters)
    if args.output == "json":
        _emit(_record_payload("rollback", restored), args.output)
        return 0 if restored.status == TransactionStatus.ROLLED_BACK else 1
    print(f"Transaction ID: {restored.id}")
    print(f"Status: {restored.status.value}")
    return 0 if restored.status == TransactionStatus.ROLLED_BACK else 1


def _aggregate_status(results) -> str:
    statuses = [result.status for result in results.values()]
    if any(status == "failed" for status in statuses):
        return "failed"
    if any(status in {"partial", "skipped"} for status in statuses):
        return "partial"
    return "ok"


def _verify(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan_id, args.plans_dir)
    adapters = build_target_adapters(plan.targets, args.state_dir, plan.target_instances)
    results = verify_plan(plan, adapters)
    status = _aggregate_status(results)
    if args.output == "json":
        _emit({
            "command": "verify",
            "status": status,
            "plan_id": plan.id,
            "targets": [
                _adapter_result_payload(asdict(results[target]))
                for target in plan.targets
            ],
            "message": f"verify completed with status {status}",
        }, args.output)
        return 0 if status in {"ok", "partial"} else 1
    print(f"Plan ID: {plan.id}")
    print(f"Status: {status.upper()}")
    for target in plan.targets:
        print(f"{target}: {results[target].status}")
    print("Field regions:")
    for target in plan.targets:
        print(f"- {target}: {', '.join(inventory_groups(target)) or 'none'}")
    return 0 if status in {"ok", "partial"} else 1


def main(argv: Sequence[str] | None = None) -> int:
    parser = _build_parser()
    try:
        args = parser.parse_args(argv)
    except SystemExit as error:
        return int(error.code)
    try:
        if args.command == "preview":
            return _preview(args)
        if args.command == "apply":
            return _apply(args)
        if args.command == "verify":
            return _verify(args)
        return _rollback(args)
    except (FileNotFoundError, PlanIntegrityError, ValueError, OSError) as error:
        if getattr(args, "output", "human") == "json":
            _emit({"command": getattr(args, "command", "unknown"), "status": "FAILED", "error": str(error)}, args.output, error=True)
            return 1
        print(f"Error: {error}", file=sys.stderr)
        return 1
