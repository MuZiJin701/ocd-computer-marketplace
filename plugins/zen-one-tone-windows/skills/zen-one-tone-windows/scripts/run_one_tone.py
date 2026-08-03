from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--output" not in args:
        args.extend(["--output", "json"])
    skill_root = Path(__file__).resolve().parents[1]
    return subprocess.run(
        ["uv", "run", "--project", str(skill_root), "one-tone", *args],
        check=False,
    ).returncode


if __name__ == "__main__":
    raise SystemExit(main())
