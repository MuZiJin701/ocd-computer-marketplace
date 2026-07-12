from __future__ import annotations

import json
import os
import re
import uuid
from pathlib import Path
from typing import Any, Mapping


_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")


def validate_safe_component(value: str, label: str) -> str:
    if not isinstance(value, str) or value in {"", ".", ".."} or not _SAFE_COMPONENT.fullmatch(value):
        raise ValueError(f"{label} must be a safe path component")
    return value


def atomic_write_text(path: Path, text: str, *, encoding: str = "utf-8", newline: str | None = None) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    try:
        with temporary.open("w", encoding=encoding, newline=newline) as handle:
            handle.write(text)
            handle.flush()
            os.fsync(handle.fileno())
        os.replace(temporary, path)
    finally:
        try:
            temporary.unlink()
        except FileNotFoundError:
            pass


def atomic_write_json(path: Path, payload: Mapping[str, Any], *, sort_keys: bool = True) -> None:
    atomic_write_text(
        path,
        json.dumps(payload, ensure_ascii=False, sort_keys=sort_keys, separators=(",", ":")) + "\n",
    )
