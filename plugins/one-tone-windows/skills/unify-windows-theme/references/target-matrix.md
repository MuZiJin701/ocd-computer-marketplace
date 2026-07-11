# Supported target matrix

| Target | Scope | Expected limitation | Real `FULL` gate |
| --- | --- | --- | --- |
| `windows` | Windows 10/11 desktop theme and generated wallpaper | Requires the Windows registry and desktop backend; wallpaper is transaction-owned | Detect, snapshot, apply, verify, restart, verify again, rollback, verify restore on the target machine |
| `terminal` | Windows Terminal current/default profile in `settings.json` | Requires the actual settings path and a restart for all UI surfaces | Same eight-step cycle with the installed Terminal version recorded |
| `vscode` | VS Code user settings and generated theme artifact | Standard theme fields do not control every extension or AI panel | Same cycle with the installed VS Code version recorded |
| `cursor` | Cursor user settings and generated theme artifact | Standard theme fields do not control every Cursor surface | Same cycle with the installed Cursor version recorded |
| `trae` | TRAE user settings and generated theme artifact | Path and version are installation-specific | Same cycle with the installed TRAE version recorded |
| `codex` | Independent Codex adapter | Unknown or unverified configuration is `SKIPPED`; never treat it as VS Code-compatible | A real, versioned Codex configuration must be verified independently |
| `chrome` | Generated Chrome theme ZIP and user load instructions | Loading/confirming the theme is a user action, so automated flow is normally `PARTIAL` | Only after the user loads and confirms the generated theme and the rollback path is documented |

Explicitly out of scope: JetBrains, Edge, Office, contrast themes, and other unverified targets.
