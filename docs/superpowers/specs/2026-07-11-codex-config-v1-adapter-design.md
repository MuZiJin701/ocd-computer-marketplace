# Codex `config.toml` v1 Adapter Design

## Goal

Make the Codex target use the real desktop theme configuration at `%USERPROFILE%\\.codex\\config.toml`, while refusing unknown TOML shapes instead of guessing.

## Scope

The first verified schema is `codex-config-v1`. It recognizes the current configuration shape:

- `desktop.appearanceTheme`
- `desktop.appearanceLightChromeTheme`
- `desktop.appearanceDarkChromeTheme`
- `accent`, `contrast`, `ink`, `opaqueWindows`, and `surface` in both theme tables
- optional nested `semanticColors` and `fonts` tables

The adapter will discover `%USERPROFILE%\\.codex\\config.toml` by default and accept `ONE_TONE_CODEX_THEME_CONFIG` as an explicit override. A valid override must still match the v1 schema.

## Field mapping

Both Light and Dark theme tables are updated so switching appearance mode does not undo the unified theme:

| Codex field | Palette value | Policy |
| --- | --- | --- |
| `accent` | `accent` | update |
| `ink` | `foreground` | update |
| `surface` | `surface` | update |
| `semanticColors.diffAdded` | `success` | update when the table exists |
| `semanticColors.diffRemoved` | `error` | update when the table exists |
| `semanticColors.skill` | `accent` | update when the table exists |
| `contrast` | none | preserve |
| `opaqueWindows` | none | preserve |
| `fonts` and unknown keys | none | preserve |

`AdapterResult.version` reports `codex-config-v1`; this is the verified configuration schema version, not an invented Codex application version.

## Safety and lifecycle

1. Parse and validate the complete TOML before writing.
2. Snapshot the original file into the transaction backup directory.
3. Apply only the mapped fields, preserving comments, unknown keys, and unrelated Codex settings through a targeted line-preserving TOML update.
4. Verify both theme tables against the Plan Palette.
5. Return `partial` with `requires_user_action=true` for restart because this project has no verified Codex process/restart contract.
6. Rollback copies the transaction's original file and verifies byte equality.

Malformed TOML, missing required v1 tables, or wrong value types return `skipped` during Detect. Apply must never run against an unverified schema.

## Testing

Tests use fixture TOML only. They cover v1 detection, field mapping, preservation of unrelated content, malformed/unknown schema rejection, snapshot/apply/verify/rollback, and CLI auto-discovery through an injected home/config path. No test writes to the user's actual Codex directory.
