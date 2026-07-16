# Testing

Run the complete repository suite from the root:

```powershell
uv run pytest
```

The root `pyproject.toml` is a non-package test harness. To run the Skill CLI from the repository root, point `uv` at the Skill project:

```powershell
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
```

The Skill can also be run from its own directory with `uv run --project . one-tone --help`.

Tests stay in the repository and are not included in the distributable Skill.

## Test layers

- `tests/marketplace/`: Marketplace manifest and paths.
- `tests/plugins/`: Codex Plugin envelope.
- `tests/skills/`: Skill files, launcher and active documentation.
- `tests/runtime/one_tone/`: Palette, Plan, Transaction and Adapter behavior.
- 当前仓库不包含 `tests/integration/` 目录；真实 Windows 目标测试需单独执行并明确风险，不属于默认 fixture 套件。

The runtime fixture suite covers cross-process-style adapter instances, transaction journaling, failed compensation, safe path components, atomic plan/transaction writes, environment path overrides, Cursor exclusion, default target selection, Scoop Terminal discovery, and Codex `system` appearance detection. It does not prove real Windows registry, desktop wallpaper, editor CLI, or Chrome activation compatibility.

Palette and adapter tests also verify that the Seed is preserved exactly as `surface`, primary and semantic text variants are readable on `surface`, Codex semantic fields use `success_text`/`error_text`/`accent_text`, `background_foreground` is readable on the deep background, the Windows wallpaper is a solid Seed-colored PNG, Windows accents come from `accent`, and Apply preserves the user's mode and automatic colorization registry values. The contrast checks use 7:1 for deep-background text and 4.5:1 for surface/emphasis text; when a Seed's theoretical maximum is lower, the algorithm selects the maximum attainable contrast.

Default tests use temporary files and fake registry/desktop backends. They do not modify the current desktop or installed applications. A passing fixture test is not evidence of a real target `FULL` result.
