# One-Tone Safety Repair Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 修复 One-Tone 的跨进程一致性、事务恢复、路径安全和结果状态问题，并同步项目文档。

**Architecture:** 保留当前 JSON 文件事务模型。新增受控标识校验、原子 JSON 写入和事务操作日志持久化；跨进程 adapter 通过事务记录或持久化目录发现状态，不依赖进程内字段。

**Tech Stack:** Python 3.11+, `uv`, `pytest`, Windows registry/desktop adapters, JSON/TOML/ZIP。

## Global Constraints

- 支持 Windows 10 build >= 19045 和 Windows 11 build >= 22621。
- Preview 不修改系统或应用配置；Apply 只接受已保存且 Hash 有效的 Plan。
- 每个目标独立 Snapshot、Apply、Verify 和补偿 Rollback。
- Verify 只读；Rollback 只恢复指定 transaction 自己的快照。
- 不引入数据库、后台服务或复杂插件运行时框架。
- 未知 target 必须 `skipped`，不得创建越界路径。

---

### Task 1: 固化跨进程回归测试

**Files:**
- Modify: `tests/runtime/one_tone/test_vscode_family.py`
- Modify: `tests/runtime/one_tone/test_chrome_adapter.py`
- Modify: `tests/runtime/one_tone/test_transaction.py`
- Modify: `tests/runtime/one_tone/test_cli.py`

**Interfaces:**
- Tests consume the existing `VSCodeFamilyAdapter`, `ChromeAdapter`, `TransactionStore`, `apply_plan`, and CLI `main` interfaces.
- Tests establish the required behavior before production changes.

- [ ] **Step 1: Write failing tests**

Add tests for a fresh VS Code adapter verifying the extension installed by another adapter instance; a fresh Chrome adapter removing artifacts created by another instance; an auto-rollback failure producing `FAILED`; an all-skipped Apply returning a non-success result; and a target such as `../../escaped` being rejected.

- [ ] **Step 2: Run the focused tests**

Run:

```powershell
uv run pytest tests/runtime/one_tone/test_vscode_family.py tests/runtime/one_tone/test_chrome_adapter.py tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
```

Expected: the new tests fail for the existing cross-process, status, and path behaviors.

- [ ] **Step 3: Keep the failure evidence**

Confirm each failure is caused by the missing behavior, not an import or test setup error, before modifying runtime code.

### Task 2: Add safe identifiers and atomic JSON persistence

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/plan.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/base.py`
- Test: `tests/runtime/one_tone/test_plan.py`
- Test: `tests/runtime/one_tone/test_transaction.py`

**Interfaces:**
- Add one internal safe-component validator used by plan and transaction path builders.
- Add one atomic text/JSON writer that writes a sibling temporary file and replaces the destination.
- Preserve existing public `Plan`, `TransactionStore`, and `AdapterResult` shapes unless a persisted metadata field is required for recovery.

- [ ] **Step 1: Write failing identifier and atomic-write tests**

Test that invalid plan IDs, transaction IDs, and target names raise `ValueError`, and that atomic JSON writing leaves the original destination intact when replacement fails.

- [ ] **Step 2: Run the focused tests**

```powershell
uv run pytest tests/runtime/one_tone/test_plan.py tests/runtime/one_tone/test_transaction.py -q
```

Expected: the new tests fail against direct path concatenation and direct `write_text` behavior.

- [ ] **Step 3: Implement the minimal helpers**

Use a strict safe-component rule, validate before constructing paths, and use `os.replace`/`Path.replace` only after the temporary file has been fully written and flushed.

- [ ] **Step 4: Run the focused tests**

```powershell
uv run pytest tests/runtime/one_tone/test_plan.py tests/runtime/one_tone/test_transaction.py -q
```

Expected: PASS.

### Task 3: Make transaction application recoverable

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/cli.py`
- Test: `tests/runtime/one_tone/test_transaction.py`
- Test: `tests/runtime/one_tone/test_cli.py`

**Interfaces:**
- `TransactionRecord` may carry a JSON-safe `metadata` mapping for target artifacts.
- `TransactionStore.save` remains the persistence boundary and is called after every operation append.
- `apply_plan` returns `FAILED` when no target successfully applies or when compensation fails; it returns `PARTIAL` only for mixed outcomes or user-action limitations.

- [ ] **Step 1: Write failing transaction-state tests**

Cover incremental result persistence, failed compensation, all-skipped Apply, and rollback of a partial snapshot where the adapter can clean generated artifacts.

- [ ] **Step 2: Run the focused tests and confirm RED**

```powershell
uv run pytest tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
```

- [ ] **Step 3: Implement operation journaling and status aggregation**

Save after detect/snapshot/apply/verify/auto_rollback, record compensation results, and derive the final status from successful targets plus compensation outcomes. Do not silently convert a failed rollback into `PARTIAL`.

- [ ] **Step 4: Run the focused tests**

```powershell
uv run pytest tests/runtime/one_tone/test_transaction.py tests/runtime/one_tone/test_cli.py -q
```

Expected: PASS.

### Task 4: Repair VS Code family and Chrome process boundaries

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/vscode_family.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/adapters/chrome.py`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/src/one_tone/transaction.py`
- Test: `tests/runtime/one_tone/test_vscode_family.py`
- Test: `tests/runtime/one_tone/test_chrome_adapter.py`

**Interfaces:**
- VS Code Verify discovers the matching installed extension through `_installed_extension_dirs()` and validates its theme file.
- Chrome persists generated artifact paths in transaction metadata and receives that metadata during rollback, or uses an equivalent persisted lookup.

- [ ] **Step 1: Implement VS Code discovery**

Replace the process-local fallback `extensions_dir / f"one-tone-{target}"` with a scan of registered One-Tone extension directories and select the directory containing the generated theme file.

- [ ] **Step 2: Implement Chrome persisted cleanup**

Persist the generated ZIP and unpacked paths under the transaction target metadata; remove only those paths during rollback and verify they no longer exist.

- [ ] **Step 3: Run the focused tests**

```powershell
uv run pytest tests/runtime/one_tone/test_vscode_family.py tests/runtime/one_tone/test_chrome_adapter.py -q
```

Expected: PASS, including fresh-adapter tests.

### Task 5: Sync documentation and project rules

**Files:**
- Modify: `AGENTS.md`
- Modify: `README.md`
- Modify: `OCD_Windows_Theme_Skill_计划书.md`
- Modify: `docs/architecture.md`
- Modify: `docs/testing.md`
- Modify: `plugins/one-tone-windows/README.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md`

**Interfaces:**
- Documentation must describe persisted transaction journals, cross-process Verify/Rollback behavior, failed compensation, safe target handling, and the absence of real-desktop integration tests.

- [ ] **Step 1: Update safety and workflow rules**

Document the exact `PARTIAL` versus `FAILED` semantics, atomic persistence expectation, and target/path validation rule in `AGENTS.md` and the architecture/testing documents.

- [ ] **Step 2: Update user-facing Skill docs**

Document that VS Code family Verify and Chrome Rollback are process-independent, while Chrome activation remains a user action and fixture tests do not prove real target compatibility.

- [ ] **Step 3: Run documentation contract tests**

```powershell
uv run pytest tests/marketplace tests/plugins tests/skills -q
```

Expected: PASS.

### Task 6: Full verification and publish

**Files:**
- No additional source files; review all changed files.

- [ ] **Step 1: Run the complete verification set**

```powershell
uv run pytest
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
uv lock --check
uv lock --project plugins/one-tone-windows/skills/unify-windows-theme --check
git diff --check
```

- [ ] **Step 2: Review the final diff and status**

Confirm only the intended code, tests, docs, plan, and spec files are changed; do not include `.one-tone`, `.pytest_cache`, or unrelated files.

- [ ] **Step 3: Commit**

```powershell
git add AGENTS.md README.md OCD_Windows_Theme_Skill_计划书.md docs plugins tests
git commit -m "fix: harden one-tone transaction recovery"
```

- [ ] **Step 4: Push**

```powershell
git push origin main
```

- [ ] **Step 5: Verify remote alignment**

```powershell
git status --short --branch
git log -1 --oneline --decorate
```

Expected: `main` tracks `origin/main` at the new commit with no intended changes left unstaged.
