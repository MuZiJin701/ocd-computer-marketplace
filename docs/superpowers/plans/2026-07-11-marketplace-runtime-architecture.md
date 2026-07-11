# Marketplace Runtime Architecture Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Make the repository a repo-scoped Codex plugin marketplace whose `one-tone-windows` plugin remains runnable after installation from its own package directory.

**Architecture:** Keep the repository root as the development and marketplace catalog root. Move the single source of truth for the Python runtime into `plugins/one-tone-windows/`; retain a thin root development `pyproject.toml` that points tests and the developer CLI at that same source without copying business code. Add `.agents/plugins/marketplace.json`, place Skill metadata under the Skill directory, and replace four PowerShell launchers with one tested Python process-forwarding script.

**Tech Stack:** Python 3.11+, `uv`, pytest, JSON, Markdown, PowerShell only for user shell examples, Codex Plugin/Skill validators.

## Global Constraints

- Python core remains the only implementation of Palette, Plan, Adapter, Transaction, Verify, and Rollback behavior.
- The installed Plugin must not depend on the repository root or a sibling `src/` directory.
- Skill scripts may locate the Plugin runtime and forward arguments, but must not duplicate business logic.
- Apply remains Plan-ID-only and requires the existing CLI confirmation gate.
- Preserve Windows 10/11 scope, wallpaper support, current Terminal profile behavior, independent Codex Adapter, and Chrome `requires_user_action` semantics.
- Do not write to global Codex configuration, global marketplaces, or the real Windows/app targets during tests.

### Task 1: Add failing architecture contract tests

**Files:**
- Modify: `tests/test_plugin_package.py`
- Create: `tests/test_marketplace_package.py`

**Interfaces:**
- The tests will require `.agents/plugins/marketplace.json`, the Plugin-local `pyproject.toml`, Skill-local `agents/openai.yaml`, one `run_one_tone.py`, and no `*.ps1` wrappers.

- [ ] **Step 1: Write failing tests**

```python
def test_repo_marketplace_points_to_plugin():
    payload = json.loads(Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    entry = payload["plugins"][0]
    assert entry["source"]["path"] == "./plugins/one-tone-windows"


def test_plugin_contains_runtime_and_skill_metadata():
    root = Path("plugins/one-tone-windows")
    assert (root / "pyproject.toml").is_file()
    assert (root / "src/one_tone/cli.py").is_file()
    assert (root / "skills/unify-windows-theme/agents/openai.yaml").is_file()
    assert (root / "skills/unify-windows-theme/scripts/run_one_tone.py").is_file()
    assert not list((root / "skills/unify-windows-theme/scripts").glob("*.ps1"))
```

- [ ] **Step 2: Run the focused tests**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_plugin_package.py tests/test_marketplace_package.py -q`

Expected: FAIL because the marketplace file, Plugin-local runtime, metadata location, and Python launcher do not yet exist.

### Task 2: Make the Plugin self-contained without duplicating core code

**Files:**
- Move: `src/one_tone/` → `plugins/one-tone-windows/src/one_tone/`
- Move: `pyproject.toml` → `plugins/one-tone-windows/pyproject.toml`
- Move: `uv.lock` → `plugins/one-tone-windows/uv.lock`
- Create: `pyproject.toml` at repository root as a development/test harness pointing at `plugins/one-tone-windows/src/one_tone`
- Modify: `tests/conftest.py` only if the root test harness needs explicit source discovery

**Interfaces:**
- Both root development and Plugin runtime expose `one-tone = one_tone.cli:main`.
- The Plugin-local build configuration packages `src/one_tone`; the root harness references that same directory and never copies it.

- [ ] **Step 1: Move the source and project metadata**

Use `git mv` for the source directory and project files. Set the Plugin project package configuration to:

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/one_tone"]
```

Set the root harness package configuration to:

```toml
[tool.hatch.build.targets.wheel]
packages = ["plugins/one-tone-windows/src/one_tone"]
```

- [ ] **Step 2: Run the core suite**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp`

Expected: the existing 37 tests pass with imports served from the Plugin-local source.

### Task 3: Add marketplace catalog and correct Skill metadata

**Files:**
- Create: `.agents/plugins/marketplace.json`
- Move: `plugins/one-tone-windows/agents/openai.yaml` → `plugins/one-tone-windows/skills/unify-windows-theme/agents/openai.yaml`
- Modify: `plugins/one-tone-windows/.codex-plugin/plugin.json`
- Modify: `plugins/one-tone-windows/README.md`

**Interfaces:**
- Marketplace entry uses `source.source = "local"`, `source.path = "./plugins/one-tone-windows"`, `policy.installation = "AVAILABLE"`, `policy.authentication = "ON_INSTALL"`, and `category = "Productivity"`.

- [ ] **Step 1: Add the catalog**

```json
{
  "name": "ocd-windows-themes",
  "interface": { "displayName": "OCD Windows Themes" },
  "plugins": [
    {
      "name": "one-tone-windows",
      "source": { "source": "local", "path": "./plugins/one-tone-windows" },
      "policy": { "installation": "AVAILABLE", "authentication": "ON_INSTALL" },
      "category": "Productivity"
    }
  ]
}
```

- [ ] **Step 2: Run JSON and plugin validators**

Run:

```powershell
python -c "import json; json.load(open('.agents/plugins/marketplace.json', encoding='utf-8'))"
python C:\Users\30733\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins/one-tone-windows
python C:\Users\30733\.codex\skills\.system\skill-creator\scripts\quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
```

Expected: all commands exit 0.

### Task 4: Replace PowerShell wrappers with one Python runtime launcher

**Files:**
- Delete: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/preview.ps1`
- Delete: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/apply.ps1`
- Delete: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/verify.ps1`
- Delete: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/rollback.ps1`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/run_one_tone.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `tests/test_plugin_package.py`

**Interfaces:**
- `run_one_tone.py` accepts the exact core CLI arguments after the script name, appends `--output json` if absent, executes `uv run --project <plugin-root> one-tone ...`, and returns the subprocess exit code.
- The launcher resolves `<plugin-root>` as `Path(__file__).resolve().parents[3]`.

- [ ] **Step 1: Add the failing launcher contract test**

Assert the script contains `uv`, `--project`, and `parents[3]`, and that the Skill documents `python scripts/run_one_tone.py`.

- [ ] **Step 2: Implement the minimal launcher**

```python
from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main(argv: list[str] | None = None) -> int:
    args = list(sys.argv[1:] if argv is None else argv)
    if "--output" not in args:
        args.extend(["--output", "json"])
    plugin_root = Path(__file__).resolve().parents[3]
    return subprocess.run(["uv", "run", "--project", str(plugin_root), "one-tone", *args]).returncode


if __name__ == "__main__":
    raise SystemExit(main())
```

- [ ] **Step 3: Verify the launcher from a directory outside the repository**

Run from a temporary directory:

```powershell
python <absolute-plugin-path>\skills\unify-windows-theme\scripts\run_one_tone.py preview '#7C3AED' --targets windows,terminal
```

Expected: JSON Preview succeeds and writes its Plan under the temporary working directory, proving the launcher uses the Plugin runtime rather than the caller's repository.

### Task 5: Synchronize documentation and release checks

**Files:**
- Modify: `README.md`
- Modify: `plugins/one-tone-windows/README.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `tests/test_project_smoke.py`

**Interfaces:**
- Documentation distinguishes repository development commands from installed Plugin commands.
- Documentation states that marketplace installation copies the Plugin and that the Plugin is self-contained.

- [ ] **Step 1: Update commands and examples**

Use `uv run --project plugins/one-tone-windows one-tone ...` for Plugin-local commands and `python .../run_one_tone.py ...` for Skill execution. Remove references to the deleted PowerShell wrapper names.

- [ ] **Step 2: Run the full release gate**

Run:

```powershell
uv run --no-cache pytest --basetemp .pytest-tmp
python C:\Users\30733\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py plugins/one-tone-windows
python C:\Users\30733\.codex\skills\.system\skill-creator\scripts\quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
```

Expected: all tests and validators pass; no real target configuration is changed.

- [ ] **Step 3: Commit the focused architecture correction**

```powershell
git add .agents plugins pyproject.toml uv.lock src tests README.md docs
git commit -m "refactor: make one-tone plugin marketplace-ready"
```
