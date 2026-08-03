from __future__ import annotations

import base64
import os
import re
import uuid
from pathlib import Path
from typing import Any


_SAFE_COMPONENT = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]*$")
BYTES_MARKER = "__one_tone_bytes__"


def json_safe(value: Any) -> Any:
    if isinstance(value, (bytes, bytearray)):
        return {BYTES_MARKER: base64.b64encode(bytes(value)).decode("ascii")}
    if isinstance(value, dict):
        return {key: json_safe(item) for key, item in value.items()}
    if isinstance(value, (list, tuple)):
        return [json_safe(item) for item in value]
    return value


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
