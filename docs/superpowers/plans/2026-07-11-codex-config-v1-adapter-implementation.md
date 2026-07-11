# Codex Config v1 Adapter Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace the placeholder Codex JSON adapter with a safe, versioned adapter for the real Codex desktop `config.toml` theme tables.

**Architecture:** Keep the adapter independent in `plugins/one-tone-windows/src/one_tone/adapters/codex.py`. Use `tomllib` to validate the complete document and a small line-preserving writer to update only verified theme keys without adding a runtime dependency. Default discovery uses `%USERPROFILE%/.codex/config.toml`; an explicit `ONE_TONE_CODEX_THEME_CONFIG` path remains supported.

**Tech Stack:** Python 3.11+ `tomllib`, `pathlib`, pytest, existing AdapterResult/Transaction contracts.

## Global Constraints

- Schema identifier is exactly `codex-config-v1`; unknown or malformed schemas return `skipped` at Detect.
- Update both `desktop.appearanceLightChromeTheme` and `desktop.appearanceDarkChromeTheme`.
- Update only `accent`, `ink`, `surface`, and existing `semanticColors.diffAdded`, `semanticColors.diffRemoved`, `semanticColors.skill` fields.
- Preserve `contrast`, `opaqueWindows`, `fonts`, comments, unknown keys, and unrelated Codex settings.
- Snapshot and Rollback operate only on the transaction's `backup/codex-config.toml`.
- Restart returns `partial` with `requires_user_action=true`; the adapter must not terminate Codex processes.
- Tests use temporary fixtures and must never write the user's actual `%USERPROFILE%/.codex/config.toml`.

### Task 1: Replace JSON fixtures with real TOML contract tests

**Files:**
- Modify: `tests/test_codex_adapter.py`

**Interfaces:**
- Tests will use `CodexAdapter`, `locate_verified_codex_config`, `CODEX_CONFIG_SCHEMA_V1`, and a fixture TOML document matching the current machine's structure.

- [ ] **Step 1: Write failing tests for v1 discovery and rejection**

```python
def test_codex_v1_config_is_detected(tmp_path):
    path = write_codex_v1_fixture(tmp_path / "config.toml")
    adapter = CodexAdapter(path)
    result = adapter.detect()
    assert result.status == "ok"
    assert result.version == CODEX_CONFIG_SCHEMA_V1


def test_codex_unknown_config_is_skipped(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[desktop]\nappearanceTheme = 'dark'\n", encoding="utf-8")
    assert CodexAdapter(path).detect().status == "skipped"
```

- [ ] **Step 2: Run the focused tests**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_codex_adapter.py -q`

Expected: FAIL because the current adapter only accepts the old JSON theme schema.

### Task 2: Implement versioned TOML detection and field-preserving updates

**Files:**
- Modify: `plugins/one-tone-windows/src/one_tone/adapters/codex.py`

**Interfaces:**
- Add `CODEX_CONFIG_SCHEMA_V1 = "codex-config-v1"`.
- Add `default_codex_config_path() -> Path`.
- Update `locate_verified_codex_config(explicit_path: Path | None = None) -> Path | None` to default to `%USERPROFILE%/.codex/config.toml` and return only v1 paths.
- Keep `CodexAdapter.detect/snapshot/apply/verify/restart/verify_again/rollback` conforming to `ThemeAdapter`.

- [ ] **Step 1: Implement schema validation**

Validate with `tomllib.loads` that `desktop` contains `appearanceTheme` as a string and both Light/Dark theme tables contain string `accent`, `ink`, `surface`, numeric `contrast`, and boolean `opaqueWindows`. Optional `semanticColors` and `fonts` must be tables when present.

- [ ] **Step 2: Implement targeted TOML updates**

Track TOML table headers while iterating the original text. Replace only matching scalar assignments in the two theme tables and their existing `semanticColors` tables. Serialize strings with `json.dumps`; preserve all other lines and keys.

- [ ] **Step 3: Implement the lifecycle**

Use `backup/codex-config.toml`, return schema version on successful results, return `skipped` for missing/invalid v1 files, return `partial`/manual-restart for `restart`, and verify rollback by byte comparison.

- [ ] **Step 4: Run focused tests**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_codex_adapter.py -q`

Expected: all Codex lifecycle tests pass.

### Task 3: Add CLI discovery and preservation regression tests

**Files:**
- Modify: `tests/test_cli.py`
- Modify: `tests/test_codex_adapter.py`

**Interfaces:**
- CLI Preview with `codex` and no `ONE_TONE_CODEX_THEME_CONFIG` must use an injected home directory fixture only when explicitly supplied by the test.

- [ ] **Step 1: Add preservation assertions**

After Apply, assert that the original comment, `desktop.appearanceTheme`, `contrast`, `opaqueWindows`, `fonts`, and an unrelated TOML key remain unchanged; assert mapped colors match the Plan in both theme tables.

- [ ] **Step 2: Add restart contract assertions**

Assert `adapter.restart().status == "partial"`, `verified is False`, and `requires_user_action is True`.

- [ ] **Step 3: Run the focused suite**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_codex_adapter.py tests/test_cli.py -q`

Expected: all focused tests pass.

### Task 4: Synchronize documentation and verify the actual machine in Preview mode

**Files:**
- Modify: `README.md`
- Modify: `plugins/one-tone-windows/README.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/references/target-matrix.md`
- Modify: `OCD_Windows_Theme_Skill_计划书.md` only if it is available in the worktree; otherwise report it for the main workspace update

**Interfaces:**
- Documentation states that Codex uses `%USERPROFILE%/.codex/config.toml`, reports `codex-config-v1`, preserves unknown fields, and needs a manual restart.

- [ ] **Step 1: Update support language**

Replace the current “unverified Codex configuration” limitation with “Codex config v1 supported; unknown config schemas are skipped; restart is manual and therefore normally PARTIAL.”

- [ ] **Step 2: Run the complete verification gate**

Run:

```powershell
uv run --no-cache pytest --basetemp .pytest-tmp
python C:\Users\30733\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins/one-tone-windows
python C:\Users\30733\.codex\skills\.system\skill-creator\scripts\quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
python plugins/one-tone-windows/skills/unify-windows-theme/scripts/run_one_tone.py preview '#00A86B' --targets codex
```

Expected: tests and validators pass; Preview reports Codex `ok`, `version = codex-config-v1`, and `changed = false`. No real Apply is executed.

- [ ] **Step 3: Commit the implementation**

```powershell
git add plugins/one-tone-windows/src/one_tone/adapters/codex.py tests/test_codex_adapter.py tests/test_cli.py README.md plugins/one-tone-windows/README.md plugins/one-tone-windows/skills/unify-windows-theme/references/target-matrix.md docs/superpowers
git commit -m "feat: support Codex config toml v1 themes"
```
