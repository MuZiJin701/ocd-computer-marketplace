from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import apply, preview, rollback, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="desktop-zero")
    sub = parser.add_subparsers(dest="command", required=True)
    for name in ("preview", "verify"):
        p = sub.add_parser(name)
        p.add_argument("plan_id", nargs="?")
        p.add_argument("--plans-dir", type=Path, default=Path(".desktop-zero/plans"))
        p.add_argument("--output", choices=("human", "json"), default="human")
    p = sub.choices["preview"]
    p.set_defaults(_preview=True)
    a = sub.add_parser("apply")
    a.add_argument("plan_id")
    a.add_argument("--confirm", action="store_true", required=True)
    a.add_argument("--plans-dir", type=Path, default=Path(".desktop-zero/plans"))
    a.add_argument("--transactions-dir", type=Path, default=Path(".desktop-zero/transactions"))
    a.add_argument("--output", choices=("human", "json"), default="human")
    r = sub.add_parser("rollback")
    r.add_argument("transaction_id")
    r.add_argument("--transactions-dir", type=Path, default=Path(".desktop-zero/transactions"))
    r.add_argument("--output", choices=("human", "json"), default="human")
    args = parser.parse_args(argv)
    if args.command == "preview":
        result = preview(plans_dir=args.plans_dir)
    elif args.command == "apply":
        result = apply(args.plan_id, args.confirm, args.plans_dir, args.transactions_dir)
    elif args.command == "verify":
        result = verify(args.plan_id, args.plans_dir)
    else:
        result = rollback(args.transaction_id, args.transactions_dir)
    if args.output == "json":
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['command']}: {result['status']}")
        if result.get("plan_id"): print(f"plan_id={result['plan_id']}")
        if result.get("transaction_id"): print(f"transaction_id={result['transaction_id']}")
        for item in result.get("operations", result.get("results", [])):
            print(item)
    return 0 if result["status"] in {"ok", "partial", "skipped"} else 1
