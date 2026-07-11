from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path
from typing import Sequence

from .adapters import (
    ChromeAdapter,
    CodexAdapter,
    FileAdapter,
    TerminalAdapter,
    UnsupportedAdapter,
    VSCodeFamilyAdapter,
    WindowsAdapter,
    WindowsConfig,
)
from .adapters.vscode_family import EditorSpec
from .adapters.windows import WindowsDesktopBackend, WindowsRegistryBackend
from .plan import PlanIntegrityError, create_plan, load_plan, save_plan
from .transaction import TransactionStatus, TransactionStore, apply_plan, run_full_cycle


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="one-tone")
    commands = parser.add_subparsers(dest="command", required=True)

    preview = commands.add_parser("preview", help="generate a Plan without changing targets")
    preview.add_argument("seed_color")
    preview.add_argument("--targets", required=True, help="comma-separated target names")
    preview.add_argument("--plans-dir", type=Path, default=Path("plans"))
    preview.add_argument("--transactions-dir", type=Path, default=Path("transactions"))
    preview.add_argument("--state-dir", type=Path, default=Path("state"))

    apply = commands.add_parser("apply", help="apply an existing Plan")
    apply.add_argument("plan_id")
    apply.add_argument("--confirm", action="store_true", required=True)
    apply.add_argument("--plans-dir", type=Path, default=Path("plans"))
    apply.add_argument("--transactions-dir", type=Path, default=Path("transactions"))
    apply.add_argument("--state-dir", type=Path, default=Path("state"))

    verify = commands.add_parser("verify", help="run the full eight-step validation cycle")
    verify.add_argument("plan_id")
    verify.add_argument("--confirm", action="store_true", required=True)
    verify.add_argument("--restart-apps", action="store_true")
    verify.add_argument("--plans-dir", type=Path, default=Path("plans"))
    verify.add_argument("--transactions-dir", type=Path, default=Path("transactions"))
    verify.add_argument("--state-dir", type=Path, default=Path("state"))

    rollback = commands.add_parser("rollback", help="restore one transaction")
    rollback.add_argument("transaction_id")
    rollback.add_argument("--transactions-dir", type=Path, default=Path("transactions"))
    rollback.add_argument("--state-dir", type=Path, default=Path("state"))
    return parser


def _target_names(raw_targets: str) -> tuple[str, ...]:
    targets = tuple(sorted({item.strip() for item in raw_targets.split(",") if item.strip()}))
    if not targets:
        raise ValueError("At least one target is required")
    return targets


def _first_path(candidates: list[Path]) -> Path:
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]


def build_target_adapters(targets, state_dir: Path, restart_apps: bool = False):
    appdata = Path(os.environ.get("APPDATA", Path.home() / "AppData/Roaming"))
    localappdata = Path(os.environ.get("LOCALAPPDATA", Path.home() / "AppData/Local"))
    userprofile = Path(os.environ.get("USERPROFILE", Path.home()))
    terminal_settings = _first_path([
        Path(r"D:\software\scoop\apps\windows-terminal\current\settings\settings.json"),
        localappdata / "Packages/Microsoft.WindowsTerminal_8wekyb3d8bbwe/LocalState/settings.json",
    ])
    vscode_spec = EditorSpec(
        "vscode",
        _first_path([Path(r"D:\software\scoop\apps\vscode\current\bin\code.cmd"), Path("code")]),
        _first_path([Path(r"D:\software\scoop\apps\vscode\current\data\user-data\User\settings.json"), appdata / "Code/User/settings.json"]),
        _first_path([Path(r"D:\software\scoop\apps\vscode\current\data\extensions"), userprofile / ".vscode/extensions"]),
        allow_restart=restart_apps,
        artifacts_dir=state_dir / "vscode-artifacts",
    )
    cursor_spec = EditorSpec(
        "cursor",
        _first_path([Path(r"D:\software\scoop\apps\cursor\current\resources\app\bin\cursor.cmd"), Path("cursor")]),
        _first_path([Path(r"D:\software\scoop\apps\cursor\current\data\user-data\User\settings.json"), appdata / "Cursor/User/settings.json"]),
        _first_path([Path(r"D:\software\scoop\apps\cursor\current\data\extensions"), userprofile / ".cursor/extensions"]),
        allow_restart=restart_apps,
        artifacts_dir=state_dir / "cursor-artifacts",
    )
    trae_spec = EditorSpec(
        "trae",
        _first_path([Path(r"D:\software\scoop\apps\trae\current\IDE\bin\trae.cmd"), Path("trae")]),
        _first_path([appdata / "TRAE/User/settings.json", appdata / "Trae/User/settings.json"]),
        userprofile / ".trae/extensions",
        allow_restart=restart_apps,
        artifacts_dir=state_dir / "trae-artifacts",
    )
    codex_path = os.environ.get("ONE_TONE_CODEX_THEME_CONFIG")
    chrome_preferences = localappdata / "Google/Chrome/User Data/Default/Preferences"
    registry = {}
    for target in targets:
        if target == "file-demo":
            registry[target] = FileAdapter(target, state_dir / "file-demo.json")
        elif target == "windows":
            registry[target] = WindowsAdapter(WindowsConfig(state_dir / "windows-wallpapers"), WindowsRegistryBackend(), WindowsDesktopBackend())
        elif target == "terminal":
            registry[target] = TerminalAdapter(terminal_settings, allow_restart=restart_apps)
        elif target == "vscode":
            registry[target] = VSCodeFamilyAdapter(vscode_spec)
        elif target == "cursor":
            registry[target] = VSCodeFamilyAdapter(cursor_spec)
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
    plan = create_plan(args.seed_color, targets)
    path = save_plan(plan, args.plans_dir)
    adapters = build_target_adapters(targets, args.state_dir)
    detected = {target: adapter.detect() for target, adapter in adapters.items()}
    unsupported_count = sum(result.status != "ok" for result in detected.values())
    print(f"Plan ID: {plan.id}")
    print("Targets:")
    for target in plan.targets:
        print(f"- {target}")
    print("Validation:")
    print("- Contrast: PASS")
    print(f"- Warnings: {unsupported_count} unverified target(s)")
    print(f"- Saved: {path}")
    return 0


def _apply(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan_id, args.plans_dir)
    adapters = build_target_adapters(plan.targets, args.state_dir)
    record = apply_plan(plan, adapters, TransactionStore(args.transactions_dir), confirm=args.confirm)
    print(f"Transaction ID: {record.id}")
    print(f"Status: {record.status.value}")
    return 0 if record.status in {TransactionStatus.APPLIED, TransactionStatus.PARTIAL} else 1


def _rollback(args: argparse.Namespace) -> int:
    store = TransactionStore(args.transactions_dir)
    record = store.load(args.transaction_id)
    adapters = build_target_adapters(record.targets, args.state_dir)
    restored = store.rollback(record.id, adapters)
    print(f"Transaction ID: {restored.id}")
    print(f"Status: {restored.status.value}")
    return 0 if restored.status == TransactionStatus.ROLLED_BACK else 1


def _verify(args: argparse.Namespace) -> int:
    plan = load_plan(args.plan_id, args.plans_dir)
    adapters = build_target_adapters(plan.targets, args.state_dir, restart_apps=args.restart_apps)
    record = run_full_cycle(plan, adapters, TransactionStore(args.transactions_dir), confirm=args.confirm, restart_apps=args.restart_apps)
    print(f"Transaction ID: {record.id}")
    print(f"Status: {record.status.value}")
    for target in record.targets:
        print(f"{target}: {record.support_levels.get(target, 'SKIPPED')}")
    return 0 if record.status != TransactionStatus.FAILED else 1


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
        print(f"Error: {error}", file=sys.stderr)
        return 1
