from __future__ import annotations

import os
import shutil
import subprocess
from pathlib import Path
from typing import Callable, Iterable

from .storage import PACKAGES, TOOLS, Tool

DEFAULT_EXECUTABLES = {"python": ("python", "python3"), "git": ("git",), "uv": ("uv",), "node": ("node",)}


def detect(which: Callable[[str], str | None] = shutil.which) -> list[Tool]:
    result = []
    for name in TOOLS:
        path = next((candidate for item in DEFAULT_EXECUTABLES[name] if (candidate := which(item))), None)
        result.append(Tool(name, path, source="existing", path_conforms=True) if path else Tool(name, None))
    return result


def command_runner(command: list[str], env: dict[str, str] | None = None) -> tuple[int, str]:
    try:
        proc = subprocess.run(command, capture_output=True, text=True, env=env, check=False)
        return proc.returncode, (proc.stdout or proc.stderr).strip()
    except OSError as exc:
        return 1, str(exc)


class Installer:
    def __init__(self, runner: Callable[[list[str], dict[str, str] | None], tuple[int, str]] = command_runner):
        self.runner = runner

    def install(self, tool: str, root: Path) -> tuple[bool, str]:
        raise NotImplementedError


class ScoopInstaller(Installer):
    def bootstrap(self, root: Path) -> tuple[bool, str]:
        command = ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", "$env:SCOOP=$args[0]; irm get.scoop.sh | iex", str(root)]
        code, output = self.runner(command, {**os.environ, "SCOOP": str(root)})
        return code == 0, output

    def install(self, tool: str, root: Path) -> tuple[bool, str]:
        env = os.environ.copy()
        env["SCOOP"] = str(root)
        code, output = self.runner(["scoop", "install", PACKAGES[tool]], env)
        return code == 0, output


class WingetInstaller(Installer):
    def install(self, tool: str, root: Path) -> tuple[bool, str]:
        code, output = self.runner(["winget", "install", "--id", {"python": "Python.Python.3", "git": "Git.Git", "uv": "astral-sh.uv", "node": "OpenJS.NodeJS"}[tool], "--exact", "--accept-source-agreements", "--accept-package-agreements"], None)
        return code == 0, output


def scoop_available(which: Callable[[str], str | None] = shutil.which) -> bool:
    return bool(which("scoop"))


def preflight_root(root: Path) -> list[str]:
    try:
        if root.exists() and not root.is_dir(): return [f"Scoop root is not a directory: {root}"]
        parent = root if root.exists() else root.parent
        if not parent.exists(): return [f"Scoop drive is unavailable: {root}"]
        if not os.access(parent, os.W_OK): return [f"Scoop root is not writable: {root}"]
    except OSError as exc:
        return [f"Scoop root preflight failed: {exc}"]
    return []
