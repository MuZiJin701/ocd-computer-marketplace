from .base import AdapterResult, AdapterStatus, ThemeAdapter, UnsupportedAdapter
from .chrome import ChromeAdapter
from .codex import CodexAdapter
from .terminal import TerminalAdapter
from .vscode_family import EditorSpec, VSCodeFamilyAdapter
from .windows import WindowsAdapter, WindowsConfig

__all__ = [
    "AdapterResult",
    "AdapterStatus",
    "ChromeAdapter",
    "CodexAdapter",
    "EditorSpec",
    "TerminalAdapter",
    "ThemeAdapter",
    "UnsupportedAdapter",
    "VSCodeFamilyAdapter",
    "WindowsAdapter",
    "WindowsConfig",
]
