from __future__ import annotations

import argparse
import json
from pathlib import Path

from .workflow import apply, preview, verify


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="scoop-toolchain")
    sub = parser.add_subparsers(dest="command", required=True)
    p = sub.add_parser("preview"); p.add_argument("--plans-dir", type=Path, default=Path(".scoop-toolchain/plans")); p.add_argument("--output", choices=("human", "json"), default="human")
    for name in ("apply", "verify"):
        q = sub.add_parser(name); q.add_argument("plan_id"); q.add_argument("--plans-dir", type=Path, default=Path(".scoop-toolchain/plans")); q.add_argument("--output", choices=("human", "json"), default="human")
        if name == "apply": q.add_argument("--confirm", action="store_true", required=True)
    args = parser.parse_args(argv)
    if args.command == "preview": result = preview(plans_dir=args.plans_dir)
    elif args.command == "apply": result = apply(args.plan_id, args.confirm, args.plans_dir)
    else: result = verify(args.plan_id, args.plans_dir)
    if args.output == "json": print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"{result['command']}: {result['status']}")
        if result.get("plan_id"): print(f"plan_id={result['plan_id']}")
        for item in result.get("tools", result.get("results", [])): print(item)
    return 0 if result["status"] in {"ok", "partial", "skipped"} else 1
