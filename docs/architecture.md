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

- `palette.py`: Seed Color and contrast-safe Palette.
- `plan.py`: immutable Plan, serialization and Hash validation.
- `storage.py`: safe path-component validation and atomic text/JSON persistence.
- `transaction.py`: per-target Apply journaling, compensation, Verify, rollback metadata and snapshot retention.
- `adapters/`: target-specific Detect, Snapshot, Apply, Verify and Rollback.
- `cli.py`: Preview, Apply, Verify and Rollback command wiring.

The runtime has no database, background service or plugin runtime framework.

Transaction records are persisted after each target operation. Adapter results may carry JSON-safe target metadata; Chrome uses this to remove generated artifacts in a later Rollback process. VS Code-family Verify discovers the installed extension from the persisted extension directory rather than relying on adapter instance state.

`APPLIED` means every selected target completed successfully. `PARTIAL` means at least one target completed while another target was skipped, failed, or requires user action. `FAILED` means no target completed or compensation failed.
