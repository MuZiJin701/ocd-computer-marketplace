"""Shared pytest configuration for the one-tone test suite."""

import os
from pathlib import Path


def pytest_sessionstart(session):
    """Keep repository-relative fixture paths stable from either project root."""
    del session
    os.chdir(Path(__file__).resolve().parents[1])
