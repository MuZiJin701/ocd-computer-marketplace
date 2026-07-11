# One Tone Windows plugin

This project-local Codex plugin exposes the `unify-windows-theme` Skill. It packages the existing Python core; it does not install a global Skill, modify `$CODEX_HOME`, or publish to a marketplace.

The Skill uses the safe flow `Preview → Plan → Apply → Verify → Rollback` and emits machine-readable JSON through the PowerShell wrappers under `skills/unify-windows-theme/scripts/`. Run from a checkout with `uv` available:

```powershell
& .\skills\unify-windows-theme\scripts\preview.ps1 '#7C3AED' 'windows,terminal,vscode'
```

See `skills/unify-windows-theme/references/` for the safety contract and target matrix. Validate the package from the repository root with the official plugin and Skill validators.
