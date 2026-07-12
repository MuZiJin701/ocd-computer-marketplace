# One-Tone Marketplace and Workflow Simplification Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox ( - [ ] ) syntax for tracking.

**Goal:** Restructure One-Tone as a self-contained Skill package with an optional Codex Plugin wrapper, restore Windows 10/11 support, simplify Apply/Verify/Rollback, prune old snapshots, and reduce repository documentation.

**Architecture:** plugins/one-tone-windows/skills/unify-windows-theme/ becomes the single source of the Skill instructions and Python runtime. The repository root owns all tests and development tooling. Apply compensates per target, public Verify is read-only by plan_id, and Rollback restores per-target snapshots by transaction_id.

**Tech Stack:** Python 3.11+, uv, standard library, pytest, Windows registry/desktop APIs, Codex Plugin metadata, Vercel Agent Skills SKILL.md format.

## Global Constraints

- Support Windows 10 22H2+ (build >= 19045) and Windows 11 22H2+ (build >= 22621).
- Keep Windows Terminal, VS Code, Cursor, TRAE, Codex and Chrome as the current target set.
- Keep Codex as an independent Adapter; do not merge it into VS Code Family.
- Keep Preview -> Apply -> Verify -> Rollback as the public workflow.
- verify <plan_id> performs only current-state detection and comparison; it does not Snapshot, Apply, Restart, Rollback or create a Transaction.
- Apply failures roll back only the failing target; successful targets remain applied.
- Every Apply snapshots before mutation and every Rollback verifies restoration.
- Keep the default snapshot retention at 5 completed transactions; make it configurable.
- Final Plugin/Skill distributions must not include repository tests, historical documents, caches or generated transactions.
- Preserve unrelated existing worktree changes; do not reset or overwrite them.

---

## Task 1: Establish the final test layout and package contract

**Files:**
- Create: tests/marketplace/test_marketplace.py
- Create: tests/plugins/test_one_tone_windows_plugin.py
- Create: tests/skills/test_unify_windows_theme_skill.py
- Move: existing runtime tests into tests/runtime/one_tone/
- Modify: tests/conftest.py
- Modify: pyproject.toml

**Interfaces:**
- Root test command remains uv run pytest.
- Package tests inspect plugins/one-tone-windows/skills/unify-windows-theme/.
- Runtime tests import one_tone through the root development package path.

- [ ] Step 1: Move tests into stable ownership directories.

~~~text
tests/test_marketplace_package.py  -> tests/marketplace/test_marketplace.py
tests/test_plugin_package.py       -> tests/plugins/test_one_tone_windows_plugin.py
tests/test_project_smoke.py        -> tests/skills/test_unify_windows_theme_skill.py
tests/test_adapters.py              -> tests/runtime/one_tone/test_adapters.py
tests/test_palette.py               -> tests/runtime/one_tone/test_palette.py
tests/test_plan.py                  -> tests/runtime/one_tone/test_plan.py
tests/test_transaction.py           -> tests/runtime/one_tone/test_transaction.py
tests/test_cli.py                   -> tests/runtime/one_tone/test_cli.py
tests/test_*_adapter.py             -> tests/runtime/one_tone/test_*_adapter.py
~~~

- [ ] Step 2: Add package-boundary regression assertions.

~~~python
def test_skill_package_contains_runtime_and_launcher():
    root = Path("plugins/one-tone-windows/skills/unify-windows-theme")
    assert (root / "SKILL.md").is_file()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src/one_tone/cli.py").is_file()
    assert (root / "scripts/run_one_tone.py").is_file()


def test_distributable_skill_does_not_depend_on_plugin_root():
    script = (Path("plugins/one-tone-windows/skills/unify-windows-theme") / "scripts/run_one_tone.py").read_text(encoding="utf-8")
    assert "plugins/one-tone-windows/src" not in script
    assert "Path(__file__).resolve().parents[1]" in script
~~~

- [ ] Step 3: Run the focused tests and record the expected failure.

~~~powershell
uv run pytest tests/skills/test_unify_windows_theme_skill.py -q
~~~

Expected: FAIL because the runtime has not moved into the Skill package yet.

- [ ] Step 4: Keep paths stable from either test entrypoint.

Retain the root change-directory behavior in tests/conftest.py so tests can run from the repository root or the Skill project directory. Do not add repository tests to the distributable Skill.

- [ ] Step 5: Run the root suite.

~~~powershell
uv run pytest
~~~

Expected: existing tests pass except for the new package-boundary assertions waiting for Task 2.

- [ ] Step 6: Commit the test-layout change.

~~~powershell
git add tests pyproject.toml
git commit -m "test: separate marketplace skill and runtime coverage"
~~~

## Task 2: Make the Skill package self-contained

**Files:**
- Move: plugins/one-tone-windows/src/one_tone/ to plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/
- Move: plugins/one-tone-windows/pyproject.toml to plugins/one-tone-windows/skills/unify-windows-theme/pyproject.toml
- Move: plugins/one-tone-windows/uv.lock to plugins/one-tone-windows/skills/unify-windows-theme/uv.lock
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/scripts/run_one_tone.py
- Modify: root pyproject.toml
- Modify: plugins/one-tone-windows/README.md
- Test: tests/skills/test_unify_windows_theme_skill.py

**Interfaces:**
- Skill project root: plugins/one-tone-windows/skills/unify-windows-theme.
- Launcher command: uv run --project <skill_root> one-tone ....
- Root development project imports the same source directory and owns no duplicate runtime.

- [ ] Step 1: Add the launcher-path assertion.

~~~python
def test_launcher_uses_skill_root_as_uv_project():
    script = (Path("plugins/one-tone-windows/skills/unify-windows-theme") / "scripts/run_one_tone.py").read_text(encoding="utf-8")
    assert "skill_root = Path(__file__).resolve().parents[1]" in script
    assert '"--project", str(skill_root)' in script
~~~

- [ ] Step 2: Run the focused test.

~~~powershell
uv run pytest tests/skills/test_unify_windows_theme_skill.py::test_launcher_uses_skill_root_as_uv_project -q
~~~

Expected: FAIL because the launcher still resolves the old Plugin root.

- [ ] Step 3: Move the runtime and update the launcher.

Use this launcher implementation:

~~~python
skill_root = Path(__file__).resolve().parents[1]
return subprocess.run(
    ["uv", "run", "--project", str(skill_root), "one-tone", *args],
    check=False,
).returncode
~~~

Update the root wheel package path:

~~~toml
[tool.hatch.build.targets.wheel]
packages = ["plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone"]
~~~

Remove the duplicate Plugin-root runtime files after the Skill copy is verified. Keep .codex-plugin/plugin.json and the Skill directory.

Remove the Skill package pytest configuration and pytest development dependency. The Skill distribution has no tests; root pyproject.toml remains the only test entrypoint. Regenerate the Skill uv.lock after removing that development dependency.

- [ ] Step 4: Run the Skill-local CLI smoke check.

From plugins/one-tone-windows/skills/unify-windows-theme/:

~~~powershell
uv run one-tone --help
~~~

Expected: help lists preview, apply, verify and rollback. Run the complete test suite only from the repository root with uv run pytest.

- [ ] Step 5: Commit the package move.

~~~powershell
git add pyproject.toml plugins/one-tone-windows tests
git commit -m "refactor: make one-tone skill self-contained"
~~~

## Task 3: Restore Windows 10 and Windows 11 detection

**Files:**
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/windows.py
- Modify: tests/runtime/one_tone/test_windows_adapter.py

**Interfaces:**
- detect_windows_version(registry) -> tuple[str, int] | None returns ("windows-10", build) for Windows 10 and ("windows-11", build) for Windows 11.
- WindowsAdapter.detect() returns skipped below the supported build floors.

- [ ] Step 1: Change the regression test to require Windows 10.

~~~python
def test_build_19045_is_windows_10():
    backend = InMemoryRegistryBackend({"CurrentBuild": "19045", "ProductName": "Windows 10 Pro"})
    assert detect_windows_version(backend) == ("windows-10", 19045)
~~~

- [ ] Step 2: Run the focused test.

~~~powershell
uv run pytest tests/runtime/one_tone/test_windows_adapter.py::test_build_19045_is_windows_10 -q
~~~

Expected: FAIL while the current implementation rejects Windows 10.

- [ ] Step 3: Restore the explicit build rules.

~~~python
if build >= 22621:
    return "windows-11", build
if 19045 <= build < 22000:
    return "windows-10", build
return None
~~~

Update the skipped message to mention both supported families. Keep the legacy product-name test to prove the build number is authoritative.

- [ ] Step 4: Run Windows adapter tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_windows_adapter.py -q
~~~

Expected: all Windows adapter tests pass.

- [ ] Step 5: Commit platform support.

~~~powershell
git add plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/windows.py tests/runtime/one_tone/test_windows_adapter.py
git commit -m "fix: support Windows 10 22H2 alongside Windows 11"
~~~

## Task 4: Implement target-scoped Apply compensation

**Files:**
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/base.py
- Modify: tests/runtime/one_tone/test_transaction.py

**Interfaces:**
- Add TransactionStore.backup_path_for(transaction_id, target) -> Path returning <root>/<transaction_id>/<target>/snapshot.
- apply_plan(...) -> TransactionRecord continues to return one transaction record, but each target owns its snapshot and compensation result.
- ThemeAdapter.rollback(backup_dir) receives only the current target's snapshot directory.

- [ ] Step 1: Add a two-target failure test.

Use a recording fake adapter and assert:

~~~python
assert record.status == TransactionStatus.PARTIAL
assert failing_target.rollback_calls == 1
assert successful_target.rollback_calls == 0
assert failing_target.state == "original"
assert successful_target.state == "applied"
~~~

- [ ] Step 2: Run the focused test.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py::test_apply_rolls_back_only_failed_target -q
~~~

Expected: FAIL because the current transaction loop stops on failure and uses one flat backup directory.

- [ ] Step 3: Add per-target backup paths.

~~~python
target_backup = store.backup_path_for(record.id, target)
snapshot = adapter.snapshot(target_backup)
~~~

Use the same target_backup for the current target's immediate compensation.

- [ ] Step 4: Continue after target failure and compensate locally.

For every target, execute Detect, Snapshot, Apply and internal Verify. If any operation fails, call adapter.rollback(target_backup), append auto_rollback, mark that target partial, and continue with the remaining targets. Do not add the failed target to a global rollback list.

- [ ] Step 5: Run transaction tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py -q
~~~

Expected: all transaction tests pass, including failure and partial-success paths.

- [ ] Step 6: Commit target-scoped compensation.

~~~powershell
git add plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/base.py tests/runtime/one_tone/test_transaction.py
git commit -m "feat: isolate apply rollback per target"
~~~

## Task 5: Replace public Verify with a read-only Plan check

**Files:**
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/cli.py
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/base.py
- Modify: adapter implementations that only support the old restart flow
- Modify: tests/runtime/one_tone/test_transaction.py
- Modify: tests/runtime/one_tone/test_cli.py

**Interfaces:**
- Add verify_plan(plan: Plan, adapters: Mapping[str, ThemeAdapter]) -> dict[str, AdapterResult].
- verify CLI accepts plan_id, loads the Plan, calls verify_plan, and emits per-target results plus aggregate ok/partial/failed.
- verify does not accept --confirm or --restart-apps.
- Remove run_full_cycle and the public eight-step lifecycle.
- Required ThemeAdapter methods are detect, snapshot, apply, verify and rollback.

- [ ] Step 1: Add the read-only verification tests.

~~~python
def test_verify_plan_reads_current_state_without_transaction(tmp_path):
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-verify-001")
    result = verify_plan(plan, {"file-demo": adapter})
    assert result["file-demo"].status == "ok"
    assert not list(tmp_path.glob("**/transaction.json"))
~~~

Also assert that verify plan-verify-001 --confirm is rejected and verify plan-verify-001 is accepted.

- [ ] Step 2: Run the focused tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
~~~

Expected: FAIL because Verify currently invokes the full-cycle transaction path and requires confirmation.

- [ ] Step 3: Implement verify_plan.

~~~python
def verify_plan(plan: Plan, adapters: Mapping[str, ThemeAdapter]) -> dict[str, AdapterResult]:
    return {
        target: adapters.get(target, UnsupportedAdapter(target)).verify(plan)
        for target in plan.targets
    }
~~~

The CLI builds adapters without restart permission, emits the results, and returns a nonzero exit code only for aggregate failed.

- [ ] Step 4: Make Rollback use per-target snapshots.

In TransactionStore.rollback, call adapter.rollback(self.backup_path_for(record.id, target)) for each target with a successful Snapshot. The Adapter rollback result is the restore verification result.

- [ ] Step 5: Remove the old lifecycle surface.

Delete run_full_cycle and remove restart/verify_again from the required Protocol and adapter tests. Manual restart is documented as an external user action followed by another verify plan_id.

- [ ] Step 6: Run CLI and transaction tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
~~~

Expected: all tests pass and Verify creates no transaction directory.

- [ ] Step 7: Commit the simplified workflow.

~~~powershell
git add plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone tests
git commit -m "refactor: make verify a read-only plan check"
~~~

## Task 6: Add bounded transaction snapshot retention

**Files:**
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/cli.py
- Modify: tests/runtime/one_tone/test_transaction.py
- Modify: tests/runtime/one_tone/test_cli.py

**Interfaces:**
- Add TransactionStore.prune(keep: int = 5, preserve: set[str] | None = None) -> list[str].
- Add --keep-transactions to apply, defaulting to 5.
- Prune only transaction directories beneath the configured transaction root.

- [ ] Step 1: Add retention tests.

Create six completed transaction directories with deterministic timestamps and assert:

~~~python
removed = store.prune(keep=5, preserve={current_id})
assert len(removed) == 1
assert store.path_for(current_id).is_dir()
assert pending_path.is_dir()
~~~

Also assert prune(keep=0) raises ValueError and a missing snapshot produces a clear Rollback error instead of reading another transaction's backup.

- [ ] Step 2: Run the focused retention tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py -k retention -q
~~~

Expected: FAIL because no pruning method or CLI option exists.

- [ ] Step 3: Implement safe pruning.

Sort only valid transaction directories by their recorded created_at, preserve the current transaction and all PENDING records, and remove only the oldest completed directories beyond keep. Return removed transaction IDs.

- [ ] Step 4: Connect pruning to Apply.

After saving the Apply record, call:

~~~python
removed = store.prune(keep=args.keep_transactions, preserve={record.id})
~~~

Include removed IDs in JSON output and never delete paths outside the transaction store root.

- [ ] Step 5: Run transaction and CLI tests.

~~~powershell
uv run pytest tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
~~~

Expected: all tests pass and the default retention is 5.

- [ ] Step 6: Commit retention.

~~~powershell
git add plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/cli.py tests
git commit -m "feat: bound transaction snapshot retention"
~~~

## Task 7: Rewrite active documentation and AGENTS.md

**Files:**
- Modify: AGENTS.md
- Modify: README.md
- Modify: OCD_Windows_Theme_Skill_计划书.md
- Modify: plugins/one-tone-windows/README.md
- Modify: plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md
- Create: plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md
- Create: docs/architecture.md
- Create: docs/testing.md
- Move: old docs/superpowers/specs/*.md and docs/superpowers/plans/*.md into docs/archive/2026-07-11/, excluding the current 2026-07-12 design and implementation plan
- Remove after migration: plugins/one-tone-windows/skills/unify-windows-theme/references/workflow.md and target-matrix.md
- Test: tests/skills/test_unify_windows_theme_skill.py and documentation smoke tests

**Interfaces:**
- All active docs use Windows 10/11 support and the four-command workflow.
- No active doc describes the removed eight-step Verify or global Apply rollback.
- AGENTS.md remains authoritative but concise.

- [ ] Step 1: Add documentation regression assertions.

~~~python
def test_active_docs_describe_current_workflow():
    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Windows 10 22H2+" in readme
    assert "verify <plan_id>" in readme
    assert "transaction_id" in readme
    assert "八步" not in readme


def test_agents_documents_current_scope():
    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "Windows 10" in agents
    assert "Windows 11" in agents
    assert "只回滚失败目标" in agents
~~~

- [ ] Step 2: Run documentation tests.

~~~powershell
uv run pytest tests/skills/test_unify_windows_theme_skill.py -q
~~~

Expected: FAIL because active docs still contain old support and lifecycle descriptions.

- [ ] Step 3: Rewrite AGENTS.md and README.md.

Keep only project goal, supported targets, public commands, safety rules, test command, and documentation synchronization rules. Remove historical narrative, duplicated acceptance tables and old eight-step wording.

- [ ] Step 4: Rewrite Skill and package docs.

SKILL.md keeps trigger conditions, confirmation gates and commands. references/targets.md contains one compact table for Windows 10/11 and application limits. Package README contains installation and one local command example.

- [ ] Step 5: Add maintainer docs and archive historical docs.

Copy the current long plan to docs/archive/2026-07-11/ before replacing OCD_Windows_Theme_Skill_计划书.md with a concise roadmap. Move superseded specs/plans into the archive; keep the current 2026-07-12 design and implementation plan active.

- [ ] Step 6: Run documentation tests and scan old wording.

~~~powershell
uv run pytest tests/skills/test_unify_windows_theme_skill.py -q
rg -n "Windows 11 only|八步|run_full_cycle" README.md AGENTS.md OCD_Windows_Theme_Skill_计划书.md plugins/one-tone-windows/skills docs/architecture.md docs/testing.md
~~~

Expected: documentation tests pass and no active document describes the removed workflow.

- [ ] Step 7: Commit documentation cleanup.

~~~powershell
git add AGENTS.md README.md OCD_Windows_Theme_Skill_计划书.md docs plugins/one-tone-windows/README.md plugins/one-tone-windows/skills tests
git commit -m "docs: simplify project guidance and workflow references"
~~~

## Task 8: Restore ignore rules and validate distributable boundaries

**Files:**
- Create or modify: .gitignore
- Modify: tests/plugins/test_one_tone_windows_plugin.py
- Modify: tests/skills/test_unify_windows_theme_skill.py

**Interfaces:**
- Generated .one-tone/, __pycache__/, .pytest_cache/, dist/, build/ and virtual environments are ignored.
- The final Skill package contains SKILL.md, references, scripts, pyproject.toml, lockfile and runtime source, but no repository tests or archive documents.

- [ ] Step 1: Add boundary assertions.

~~~python
def test_skill_package_does_not_include_repository_tests_or_archive():
    root = Path("plugins/one-tone-windows/skills/unify-windows-theme")
    assert not (root / "tests").exists()
    assert not (root / "docs").exists()


def test_generated_runtime_directories_are_ignored():
    ignore = Path(".gitignore").read_text(encoding="utf-8")
    assert ".one-tone/" in ignore
    assert "__pycache__/" in ignore
    assert ".pytest_cache/" in ignore
~~~

- [ ] Step 2: Run the focused boundary tests.

~~~powershell
uv run pytest tests/plugins tests/skills -q
~~~

Expected: FAIL until ignore rules and final package layout are complete.

- [ ] Step 3: Add minimal ignore rules.

~~~gitignore
.venv/
__pycache__/
.pytest_cache/
.one-tone/
dist/
build/
*.egg-info/
~~~

Do not add broad rules that hide source, documentation or transaction backups outside .one-tone/.

- [ ] Step 4: Run boundary tests and inspect status.

~~~powershell
uv run pytest tests/plugins tests/skills -q
git status --short
~~~

Expected: boundary tests pass; unrelated pre-existing changes remain visible.

- [ ] Step 5: Commit repository hygiene.

~~~powershell
git add .gitignore tests
git commit -m "chore: keep generated runtime data out of source"
~~~

## Task 9: Run final validation and package smoke checks

**Files:**
- No source changes expected.
- Inspect: README.md, AGENTS.md, docs/architecture.md, docs/testing.md and Skill package files.

**Interfaces:**
- Root command: uv run pytest.
- Skill command: uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help.
- Public CLI commands are exactly preview, apply, verify and rollback.

- [ ] Step 1: Run the complete root suite.

~~~powershell
uv run pytest
~~~

Expected: all unit and contract tests pass; real integration tests remain deselected unless explicitly requested.

- [ ] Step 2: Run the Skill-local CLI smoke check.

~~~powershell
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
~~~

Expected: help lists preview, apply, verify and rollback, and no command refers to run_full_cycle.

- [ ] Step 3: Build the Skill package.

From plugins/one-tone-windows/skills/unify-windows-theme/ run:

~~~powershell
uv build
~~~

Inspect the generated wheel and confirm it contains only the Python runtime. Separately inspect the Skill directory and confirm it contains SKILL.md, scripts/ and references/ but no tests/, docs/, .one-tone/ or .pytest_cache/ entries.

- [ ] Step 4: Run repository hygiene checks.

~~~powershell
git diff --check
git status --short
~~~

Expected: no whitespace errors; only scoped implementation changes plus pre-existing user changes remain.

- [ ] Step 5: Commit the validated release state.

~~~powershell
git add plugins/one-tone-windows pyproject.toml tests docs README.md AGENTS.md .gitignore
git commit -m "feat: simplify one-tone skill workflow and packaging"
~~~

## Review checkpoints

- After Task 2: verify a Skill-only installation can locate its own runtime.
- After Task 4: verify one failed target leaves successful targets applied.
- After Task 5: verify verify <plan_id> creates no transaction directory.
- After Task 6: verify old snapshots are pruned without touching current or pending transactions.
- After Task 7: review concise docs before archiving old material.
- After Task 9: report actual test counts and environment warnings separately from failures.
