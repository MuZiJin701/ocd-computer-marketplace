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
- `tests/integration/`: explicit real-environment tests; not part of the default fixture suite.

Default tests use temporary files and fake registry/desktop backends. They do not modify the current desktop or installed applications. A passing fixture test is not evidence of a real target `FULL` result.
