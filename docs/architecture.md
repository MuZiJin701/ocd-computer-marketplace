# Architecture

## Layers

```text
Marketplace
  └─ Plugin package
      └─ Skill package
          ├─ SKILL.md
          ├─ Python runtime
          └─ target Adapters
```

- `.agents/plugins/marketplace.json` lists installable Codex Plugin packages.
- `plugins/one-tone-windows/.codex-plugin/plugin.json` is an optional Codex wrapper.
- `plugins/one-tone-windows/skills/unify-windows-theme/` is the canonical Skill package.
- The Skill package owns `pyproject.toml`, `src/one_tone/` and its launcher.
- The root `pyproject.toml` is only the development/test entrypoint; it is not installable and does not expose a runtime command.
- The Skill `pyproject.toml` owns the `one-tone` console script and is the only runtime project.

## Runtime boundaries

- `palette.py`: Seed Color and contrast-safe, hue-coherent Palette. `surface` preserves the normalized Seed exactly; `foreground` is selected for `surface` with a target of at least 4.5:1, while `background_foreground` is selected for the deep `background` with a target of at least 7:1.
- `plan.py`: immutable Plan, serialization and Hash validation.
- `storage.py`: safe path-component validation and atomic text/JSON persistence.
- `transaction.py`: per-target Apply journaling, compensation, Verify, rollback metadata and snapshot retention.
- `adapters/`: target-specific Detect, Snapshot, Apply, Verify and Rollback.
- `cli.py`: Preview, Apply, Verify and Rollback command wiring.

The runtime has no database, background service or plugin runtime framework.

## Palette and discovery semantics

- Codex `surface` is the normalized Seed Color in both `appearanceLightChromeTheme` and `appearanceDarkChromeTheme`; Codex `ink` maps to the chromatic `foreground`, and Codex `accent` maps to Palette `accent`.
- Windows wallpaper is a solid PNG of the exact Seed Color. Windows registry accent values and the generated accent palette use Palette `accent`, never a darkened `surface`.
- Windows Apply does not write `AppsUseLightTheme`, `SystemUsesLightTheme`, or `AutoColorization`; the user's current mode and automatic color choice remain under user control.
- When `AutoColorization` is already enabled, Windows Detect/Apply/Verify reports `partial` and requires user action because Windows may recalculate the accent from the wallpaper after Apply. The runtime does not silently change that setting.
- Editor discovery uses PATH, standard per-user locations, and explicit environment overrides. Cursor `.cmd`/`.bat` launchers may provide the actual data directories through `--user-data-dir` and `--extensions-dir`. No machine-specific absolute path or temporary path is required at runtime.
- Cursor uses the installed VSIX when available and falls back to direct `workbench.colorCustomizations` when its running instance rejects or fails to register the local VSIX.
- Preview defaults to the complete implemented target set and prints one detection result per target; `--targets` is an explicit narrowing option, not a required discovery input.

Transaction records are persisted after each target operation. Adapter results may carry JSON-safe target metadata; Chrome uses this to remove generated artifacts in a later Rollback process. VS Code-family Verify discovers the installed extension from the persisted extension directory rather than relying on adapter instance state.

`APPLIED` means every selected target completed successfully. `PARTIAL` means at least one target completed while another target was skipped, failed, or requires user action. `FAILED` means no target completed or compensation failed.
