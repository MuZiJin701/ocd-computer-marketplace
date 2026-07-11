---
name: unify-windows-theme
description: >-
  Use when a user wants one seed color applied consistently to supported Windows
  targets, or wants to preview, verify, or roll back a theme. The workflow is
  safety-gated: Preview creates a hashed Plan without changing files, Apply
  accepts only that Plan after explicit confirmation, Verify runs the eight-step
  validation cycle, and Rollback restores one transaction's own backup.
---

# Unify Windows Theme

Use the repository's Python core through `uv`; do not invent adapter behavior or write directly to target configuration files. The supported targets are `windows`, `terminal`, `vscode`, `cursor`, `trae`, `codex`, and `chrome`. Unknown targets must be rejected or reported as skipped.

## Workflow

1. Confirm the seed color, selected targets, and whether the user wants a preview or a real change. A real Apply changes only explicitly selected targets and may create a generated wallpaper or Chrome theme ZIP.
2. Run Preview first. It generates a Palette and a hash-checked Plan under `plans/`; it must not modify system or application configuration.
3. Show the Plan ID, target detection results, warnings, and support limitations. Do not proceed to Apply without explicit user confirmation.
4. Apply by Plan ID only, with `--confirm`. The core creates a new transaction and snapshots each target before applying it. Never regenerate a Palette during Apply.
5. Verify with `--confirm`; use `--restart-apps` only after the user confirms that unsaved editor/terminal work is safe to close. Verify performs Detect → Snapshot → Apply → Verify → Restart → Verify Again → Rollback → Verify Restore.
6. Report `FULL`, `PARTIAL`, or `SKIPPED` per target. Chrome normally remains `PARTIAL` because loading the generated theme is a user action; an unverified Codex configuration remains `SKIPPED`.
7. If a user asks to undo a real Apply, require the exact transaction ID and run Rollback. Restore only that transaction's backup and report the restore verification.

## Commands

The PowerShell wrappers in `scripts/` emit JSON for automation:

```powershell
& .\scripts\preview.ps1 '#7C3AED' 'windows,terminal,vscode,cursor,trae,codex,chrome'
& .\scripts\apply.ps1 'plan-...' -ConfirmApply
& .\scripts\verify.ps1 'plan-...' -ConfirmVerify
& .\scripts\rollback.ps1 'tx-...'
```

For direct use from the repository root:

```powershell
uv run one-tone preview '#7C3AED' --targets windows,terminal --output json
uv run one-tone apply plan-... --confirm --output json
uv run one-tone verify plan-... --confirm --output json
uv run one-tone rollback tx-... --output json
```

Read [workflow.md](references/workflow.md) for the state and safety contract, and [target-matrix.md](references/target-matrix.md) before promising support for a target. The core's automated tests are fixture-based and do not prove a real machine's `FULL` status.
