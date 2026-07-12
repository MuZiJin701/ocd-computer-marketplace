# Skill Boundary Cleanup Implementation Plan

**Goal:** Keep the repository root as a test-only harness, make the Skill package self-contained, and remove obsolete local runtime artifacts.

**Architecture:** The root project provides pytest and source-path configuration only. The Skill project owns the `one-tone` console script and runtime package. Plugin examples live beside the Skill documentation, while generated state remains ignored and outside the distributable package.

**Tech Stack:** Python 3.11+, `uv`, pytest, Hatchling only for the Skill package.

## Tasks

### Task 1: Move the Skill example

- Move `plugins/one-tone-windows/examples/preview-request.md` to `plugins/one-tone-windows/skills/unify-windows-theme/examples/preview-request.md`.
- Update Plugin and Skill documentation trees if needed.
- Add a package test asserting the example is inside the Skill and the old directory is absent.

### Task 2: Decouple the root test harness

- Remove the root project console script and Hatch build package mapping from `pyproject.toml`.
- Add `tool.uv.package = false` and pytest `pythonpath` pointing to the Skill source directory.
- Regenerate `uv.lock`.
- Update root and Plugin README commands so root execution uses `uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone ...`, while direct Skill execution uses the Skill directory as project root.
- Update architecture and tests to assert the root is test-only and the Skill owns the runtime command.

### Task 3: Remove confirmed generated artifacts and verify

- Delete `plugins/one-tone-windows/.venv`, `plugins/one-tone-windows/plans`, and `plugins/one-tone-windows/.one-tone` as confirmed by the user.
- Keep `.gitignore` rules for `.one-tone/`, virtual environments, and legacy Plugin plans.
- Run `uv run pytest`, a root CLI command through the Skill project, a direct Skill command, and `git diff --check`.

