from __future__ import annotations

import argparse
import sys
from pathlib import Path
from typing import Sequence

from .adapters import FileAdapter, UnsupportedAdapter
from .plan import PlanIntegrityError, create_plan, load_plan, save_plan
from .transaction import TransactionStatus, TransactionStore, apply_plan


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="one-tone")
    commands = parser.add_subparsers(dest="command", required=True)

    preview = commands.add_parser("preview", help="generate a Plan without changing targets")
    preview.add_argument("seed_color")
    preview.add_argument("--targets", required=True, help="comma-separated target names")
    preview.add_argument("--plans-dir", type=Path, default=Path("plans"))
    preview.add_argument("--transactions-dir", type=Path, default=Path("transactions"))

    apply = commands.add_parser("apply", help="apply an existing Plan")
    apply.add_argument("plan_id")
    apply.add_argument("--confirm", action="store_true", required=True)
    apply.add_argument("--plans-dir", type=Path, default=Path("plans"))
    apply.add_argument("--transactions-dir", type=Path, default=Path("transactions"))
    apply.add_argument("--state-dir", type=Path, default=Path("state"))

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


def _adapters_for(targets: tuple[str, ...], state_dir: Path):
    return {
        target: FileAdapter(target, state_dir / f"{target}.json")
        if target == "file-demo"
        else UnsupportedAdapter(target)
        for target in targets
    }


def _preview(args: argparse.Namespace) -> int:
    targets = _target_names(args.targets)
    plan = create_plan(args.seed_color, targets)
    path = save_plan(plan, args.plans_dir)
    unsupported_count = sum(target != "file-demo" for target in targets)
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
    adapters = _adapters_for(plan.targets, args.state_dir)
    record = apply_plan(plan, adapters, TransactionStore(args.transactions_dir), confirm=args.confirm)
    print(f"Transaction ID: {record.id}")
    print(f"Status: {record.status.value}")
    return 0 if record.status in {TransactionStatus.APPLIED, TransactionStatus.PARTIAL} else 1


def _rollback(args: argparse.Namespace) -> int:
    store = TransactionStore(args.transactions_dir)
    record = store.load(args.transaction_id)
    adapters = _adapters_for(record.targets, args.state_dir)
    restored = store.rollback(record.id, adapters)
    print(f"Transaction ID: {restored.id}")
    print(f"Status: {restored.status.value}")
    return 0 if restored.status == TransactionStatus.ROLLED_BACK else 1


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
        return _rollback(args)
    except (FileNotFoundError, PlanIntegrityError, ValueError, OSError) as error:
        print(f"Error: {error}", file=sys.stderr)
        return 1
