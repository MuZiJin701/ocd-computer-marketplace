# Cursor Exclusion and High Contrast Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Remove Cursor from the user-facing target matrix and make generated themes use Codex-compatible, high-contrast semantic colors.

**Architecture:** Keep the existing Cursor adapter isolated but remove it from the production target registry and default target discovery. Replace sparse foreground selection with dense same-hue candidate search, then write `contrast=100` into both verified Codex chrome theme tables while preserving `appearanceTheme`.

**Tech Stack:** Python 3.11+, `uv`, pytest, TOML-preserving text replacement, standard-library HSL and WCAG contrast calculations.

## Global Constraints

- `surface` is exactly the user Seed Color.
- Do not modify `appearanceTheme`, `AppsUseLightTheme`, `SystemUsesLightTheme`, or `AutoColorization`.
- Explicit Cursor input is `skipped` and must not write, snapshot, or delete Cursor files.
- Only user-selected supported targets may be changed.
- Keep the Skill independently distributable; no developer-machine paths or temporary paths in the package.

### Task 1: Lock the new target and palette contracts with failing tests

**Files:**
- Modify: `tests/runtime/one_tone/test_adapters.py`
- Modify: `tests/runtime/one_tone/test_palette.py`
- Modify: `tests/runtime/one_tone/test_codex_adapter.py`
- Modify: `tests/runtime/one_tone/test_cli.py`

**Interfaces:**
- Tests consume the existing target registry, `generate_palette`, `validate_palette`, `CodexAdapter`, and CLI parser.
- Later tasks make these existing interfaces satisfy the new assertions.

- [ ] **Step 1: Add a failing test for Cursor exclusion.** Assert the default adapter target names do not include `cursor`, and explicit `cursor` returns `skipped` without creating a settings or extension file.
- [ ] **Step 2: Add failing contrast assertions.** For `#10B981`, require `foreground/surface >= 7`, `background_foreground/background >= 7`, `accent_foreground/accent >= 7`, `selection_foreground/selection_background >= 7`, and require the primary foreground to remain non-achromatic.
- [ ] **Step 3: Add a failing Codex contrast assertion.** Apply a plan to a valid TOML fixture with `contrast=20`, then assert both light and dark theme tables contain `contrast=100` while `appearanceTheme` remains unchanged.
- [ ] **Step 4: Run only the new tests and confirm RED.**

```powershell
uv run --no-cache pytest tests/runtime/one_tone/test_adapters.py tests/runtime/one_tone/test_palette.py tests/runtime/one_tone/test_codex_adapter.py tests/runtime/one_tone/test_cli.py -q
```

Expected: failures for Cursor still being registered, current contrast thresholds, and Codex preserving the old contrast value.

### Task 2: Remove Cursor from production target discovery

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/__init__.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/cli.py`
- Modify: `tests/runtime/one_tone/test_adapters.py`
- Modify: `tests/runtime/one_tone/test_cli.py`

**Interfaces:**
- `build_target_adapters()` remains the production registry entry point.
- `SUPPORTED_TARGETS` or equivalent discovery output must omit Cursor.

- [ ] **Step 1: Remove `cursor` from the production registry and default detection list.** Leave `vscode_family.py` Cursor classes untouched for future experiments.
- [ ] **Step 2: Return `skipped` for explicit `cursor` before adapter construction or filesystem access.** Use the existing structured `AdapterResult` path.
- [ ] **Step 3: Run the Task 1 target tests and confirm GREEN.**

### Task 3: Implement dense high-contrast Palette search

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/palette.py`
- Modify: `tests/runtime/one_tone/test_palette.py`

**Interfaces:**
- Preserve `generate_palette(seed_color, mode="dark") -> dict[str, str]`.
- Preserve `contrast_ratio()` and `validate_palette()` public behavior.

- [ ] **Step 1: Expand same-hue candidates over lightness increments of at most `0.02` and saturation variants derived from the source color.** Exclude only exact `#000000` and `#FFFFFF` from normal candidates.
- [ ] **Step 2: Add a candidate score that first satisfies the requested contrast threshold, then maximizes retained saturation and minimizes distance from the source hue/lightness direction.** If no candidate satisfies the threshold, return the candidate with maximum contrast.
- [ ] **Step 3: Generate `foreground` against `surface` at `7:1`; generate `muted_foreground` at `4.5:1` but bias it toward the primary foreground; generate accent and selection foregrounds at `7:1`.
- [ ] **Step 4: Update validation pairs to match the generated semantic contracts and run all palette tests.**

### Task 4: Align Codex Adapter with high contrast

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/codex.py`
- Modify: `tests/runtime/one_tone/test_codex_adapter.py`

**Interfaces:**
- Keep schema detection compatible with existing valid Codex config files.
- `_theme_updates()` must include `contrast: 100` for both chrome tables.

- [ ] **Step 1: Extend the verified replacement map to write `contrast=100` only inside the two appearance theme tables.** Keep all unrelated TOML text unchanged.
- [ ] **Step 2: Extend `_matches_plan()` to require `contrast == 100` in both theme tables without requiring a particular `appearanceTheme`.
- [ ] **Step 3: Run Codex adapter tests and confirm GREEN.**

### Task 5: Synchronize user-facing and project documentation

**Files:**
- Modify: `README.md`
- Modify: `AGENTS.md`
- Modify: `OCD_Windows_Theme_Skill_计划书.md`
- Modify: `docs/architecture.md`
- Modify: `docs/testing.md`
- Modify: `plugins/one-tone-windows/README.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md`
- Modify: `docs/superpowers/specs/2026-07-12-one-tone-safety-repair-design.md`

**Interfaces:**
- User-facing docs list only the supported target set.
- The Skill explains Seed/surface, Codex contrast 100, and manual Windows automatic-accent behavior in concise operational language.

- [ ] **Step 1: Rewrite root README around installation and commands; remove implementation explanations and Cursor claims.**
- [ ] **Step 2: Update support matrices, project rules, architecture, test guidance, Skill, and current plan references to omit Cursor from current support and describe the new contrast thresholds.**
- [ ] **Step 3: Scan the distributable Skill for developer-machine paths and temporary paths.**

### Task 6: Full verification and delivery

**Files:**
- Verify all modified files.

- [ ] **Step 1: Run the complete test suite.**

```powershell
uv run --no-cache pytest
```

- [ ] **Step 2: Run CLI help and a read-only palette smoke check.**
- [ ] **Step 3: Run `git diff --check` and the package path scan.**
- [ ] **Step 4: Review the diff, commit the implementation, and push `main` only after all checks pass.**
