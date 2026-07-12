# Theme Surface Coverage Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Extend the Skill's verified configuration coverage across Windows accents, Windows Terminal window chrome, VS Code-family workbenches, and locally loadable Chrome themes.

**Architecture:** Keep target-specific behavior inside the existing adapters. Use explicit registry aliases for the two Windows `ColorPrevalence` values, a named Windows Terminal window theme, standard VS Code theme color IDs, and both ZIP/unpacked Chrome theme artifacts. Cursor, TRAE, and Chrome remain `partial` where live application or proprietary UI cannot be verified by fixtures.

**Tech Stack:** Python 3.11+, `uv`, pytest, Windows Registry/JSON adapters, Chrome Manifest V2 theme format for local development.

## Global Constraints

- Preview never mutates target configuration.
- Apply snapshots each target before mutation and rolls back only the failing target.
- Verify is read-only.
- Rollback restores only the transaction's own snapshot.
- Windows 10 22H2+ and Windows 11 22H2+ remain supported.
- Chrome local activation remains a user action; no silent browser installation is attempted.

### Task 1: Windows accent surfaces

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/windows.py`
- Test: `tests/runtime/one_tone/test_windows_adapter.py`

- [ ] Add logical registry aliases for Start/Taskbar and TitleBar/WindowBorder `ColorPrevalence`, mapping both aliases to the real registry value name.
- [ ] Include both aliases in snapshot, apply, verify, and rollback expectations.
- [ ] Add tests for both in-memory values and both Windows Registry paths.

### Task 2: Windows Terminal window chrome

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/terminal.py`
- Test: `tests/runtime/one_tone/test_terminal_adapter.py`

- [ ] Build a named `One Tone` Terminal theme with `window`, `tabRow`, and `tab` colors.
- [ ] Select the named theme and set the selected profile tab color while preserving full-file rollback.
- [ ] Verify the selected theme, theme definition, profile scheme, and tab color.
- [ ] Add fixture coverage for the top bar and tab configuration.

### Task 3: VS Code-family surfaces and Cursor restart handling

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/vscode_family.py`
- Test: `tests/runtime/one_tone/test_vscode_family.py`

- [ ] Add standard theme IDs for title bar, side bar headers, activity bar top, tabs, panels, status bar, lists, inputs, and borders.
- [ ] Expand restart-required detection to Cursor and TRAE messages.
- [ ] Add tests for the expanded theme fields and Cursor restart fallback.

### Task 4: Chrome theme artifacts

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/chrome.py`
- Test: `tests/runtime/one_tone/test_chrome_adapter.py`

- [ ] Convert Palette hex values to integer RGB arrays in `manifest.json`.
- [ ] Generate an unpacked theme directory containing `manifest.json` and retain the ZIP artifact.
- [ ] Verify both artifacts and remove both during rollback.
- [ ] Add tests for RGB arrays and unpacked directory loading.

### Task 5: Documentation and final verification

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `README.md`

- [ ] Document Terminal top-bar coverage, Windows accent switches, Cursor/TRAE partial limits, and Chrome manual activation.
- [ ] Run `uv run pytest`, CLI help, Skill build inspection, and `git diff --check`.
