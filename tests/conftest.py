"""Shared pytest configuration for the one-tone test suite."""

import os
import sys
from pathlib import Path


def pytest_sessionstart(session):
    """Keep repository-relative fixture paths stable from either project root."""
    del session
    root = Path(__file__).resolve().parents[1]
    os.chdir(root)
    for relative in (
        "plugins/zen-desktop-zero/skills/zen-desktop-zero/src",
        "plugins/zen-scoop-toolchain/skills/zen-scoop-toolchain/src",
    ):
        sys.path.insert(0, str(root / relative))
