from __future__ import annotations

import ctypes
import os
import shutil
from pathlib import Path
from typing import Callable

from .model import CATEGORIES, Operation, SHORTCUT_EXTENSIONS

EXTENSIONS = {
    "文档": {".doc", ".docx", ".docm", ".odt", ".pdf", ".rtf", ".txt", ".md", ".csv", ".xls", ".xlsx", ".ppt", ".pptx"},
    "图片": {".png", ".jpg", ".jpeg", ".gif", ".bmp", ".webp", ".svg", ".ico", ".tif", ".tiff"},
    "视频": {".mp4", ".mkv", ".mov", ".avi", ".wmv", ".webm", ".m4v"},
    "音频": {".mp3", ".wav", ".flac", ".aac", ".m4a", ".ogg", ".wma"},
    "压缩包": {".zip", ".7z", ".rar", ".tar", ".gz", ".bz2", ".xz"},
    "安装包": {".exe", ".msi", ".msix", ".appx", ".iso"},
    "代码": {".py", ".js", ".ts", ".tsx", ".jsx", ".java", ".c", ".h", ".cpp", ".cs", ".go", ".rs", ".rb", ".php", ".html", ".css", ".json", ".yaml", ".yml", ".toml", ".sql", ".sh", ".ps1"},
}


def resolve_desktop() -> Path:
    if os.name == "nt":
        try:
            buffer = ctypes.create_unicode_buffer(260)
            if ctypes.windll.shell32.SHGetFolderPathW(None, 0x10, None, 0, buffer) == 0:
                return Path(buffer.value).resolve()
        except (AttributeError, OSError):
            pass
    return (Path.home() / "Desktop").resolve()


def classify(path: Path) -> str:
    suffix = path.suffix.lower()
    for category, extensions in EXTENSIONS.items():
        if suffix in extensions:
            return category
    return "未分类"


def choose_destination(source: Path, category: str, data_root: Path) -> tuple[Path, str]:
    candidate = data_root / category / source.name
    if not candidate.exists():
        return candidate, "none"
    stem, suffix = source.stem, source.suffix
    index = 1
    while True:
        name = f"{stem} ({index}){suffix}"
        candidate = data_root / category / name
        if not candidate.exists():
            return candidate, f"renamed to {name}"
        index += 1


def preflight_data_root(data_root: Path) -> list[str]:
    warnings: list[str] = []
    root = data_root.anchor or data_root.parent
    if not root:
        return ["data root has no usable drive"]
    try:
        if data_root.exists() and not data_root.is_dir():
            return [f"data root is not a directory: {data_root}"]
        probe = data_root if data_root.exists() else data_root.parent
        if not probe.exists():
            return [f"destination drive is unavailable: {data_root}"]
        if not os.access(probe, os.W_OK):
            return [f"destination is not writable: {data_root}"]
    except OSError as exc:
        warnings.append(f"destination preflight failed: {exc}")
    return warnings


def build_operations(desktop: Path, data_root: Path) -> tuple[list[Operation], list[str]]:
    warnings = preflight_data_root(data_root)
    if warnings:
        return [], warnings
    try:
        entries = sorted(desktop.iterdir(), key=lambda item: item.name.casefold())
    except OSError as exc:
        return [], [f"cannot read resolved desktop: {exc}"]
    operations: list[Operation] = []
    for entry in entries:
        if entry.is_file() and entry.suffix.lower() in SHORTCUT_EXTENSIONS:
            operations.append(Operation(str(entry), "delete_shortcut"))
            continue
        category = classify(entry)
        destination, collision = choose_destination(entry, category, data_root)
        operations.append(Operation(str(entry), "move", category, str(destination), str(destination), collision))
    return operations, warnings
