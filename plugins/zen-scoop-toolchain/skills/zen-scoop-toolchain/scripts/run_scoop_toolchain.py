from pathlib import Path
import sys

SRC = Path(__file__).resolve().parents[1] / "src"
sys.path.insert(0, str(SRC))
from scoop_toolchain.cli import main

if __name__ == "__main__":
    raise SystemExit(main())
