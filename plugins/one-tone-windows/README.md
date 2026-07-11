# One Tone Windows plugin

This Codex plugin exposes the `unify-windows-theme` Skill and contains a self-contained Python runtime. It does not install a global Skill, modify `$CODEX_HOME`, or publish to a marketplace by itself.

The Skill uses the safe flow `Preview → Plan → Apply → Verify → Rollback` and emits machine-readable JSON through `skills/unify-windows-theme/scripts/run_one_tone.py`. Run from a checkout with `uv` available:

```powershell
python .\skills\unify-windows-theme\scripts\run_one_tone.py preview '#7C3AED' --targets windows,terminal,vscode
```

See `skills/unify-windows-theme/references/` for the safety contract and target matrix. Validate the package from the repository root with the official plugin and Skill validators.
