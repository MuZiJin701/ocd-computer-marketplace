# One-Tone Marketplace and Workflow Simplification Design

## Goal

让仓库同时支持 Windows 10/11、可独立安装的通用 Agent Skill 和可选的 Codex Plugin 外壳，并把主题修改流程收缩为可理解、可测试、可回滚的三个命令：`apply`、`verify`、`rollback`。

## Decisions

### 1. Platform scope

- Windows 10 22H2+，build `>= 19045`。
- Windows 11 22H2+，build `>= 22621`。
- 普通深色模式；不实现 Contrast Theme。
- Windows 版本检测优先使用 `CurrentBuild`，不根据 `ProductName` 猜测。

### 2. Package boundaries

仓库根目录是 Marketplace 和开发测试入口：

```text
plugins/
└─ one-tone-windows/
   ├─ .codex-plugin/plugin.json       # 可选 Codex Plugin 外壳
   └─ skills/
      └─ unify-windows-theme/          # 独立 Skill 包和唯一 runtime 来源
         ├─ SKILL.md
         ├─ pyproject.toml
         ├─ uv.lock
         ├─ src/one_tone/
         ├─ scripts/
         └─ references/
```

- Skill 包必须自包含 Python runtime，不能依赖仓库根目录或 Codex Plugin 元数据。
- `run_one_tone.py` 根据自身 Skill 根目录调用 `uv run --project`。
- `.codex-plugin/plugin.json` 只负责 Codex 兼容和 Marketplace 发现，不拥有另一份 runtime。
- 纯 Skill 可以放在顶层 `skills/<skill-name>/`，不要求存在 Plugin 元数据。
- 最终分发包不包含仓库测试、历史计划或开发缓存。

### 3. Tests

测试统一保留在仓库根目录，不复制进 Plugin 或 Skill 包：

```text
tests/
├─ test_marketplace.py
├─ test_plugin_package.py
├─ test_skill_package.py
├─ test_palette.py
├─ test_plan.py
├─ test_transaction.py
├─ test_adapters.py
└─ integration/
   └─ test_full_lifecycle.py
```

- Marketplace 测试只检查 Marketplace 清单和插件路径。
- Plugin 测试只检查 `.codex-plugin/plugin.json` 和插件外壳。
- Skill 测试检查 `SKILL.md`、自包含 `pyproject.toml`、启动脚本和分发边界。
- Runtime 测试覆盖 Palette、Plan、Transaction 和 AdapterResult 合同。
- 默认测试只使用 fixture 和 fake backend；真实桌面测试单独标记为 integration。
- 根目录的 `uv run pytest` 是唯一标准测试命令。

### 4. Apply

`apply <plan_id> --confirm` 只接受已经保存且 Hash 校验通过的 Plan。

对每个目标独立执行：

```text
Detect → Snapshot → Apply → Verify
```

- Snapshot 成功后 Apply 或内部 Verify 失败：只恢复当前目标。
- 当前目标失败后继续处理其他目标。
- 已成功的其他目标保持修改。
- 有目标失败、跳过或部分成功时，事务为 `PARTIAL`。
- 事务创建、Plan 校验或存储系统失败时，事务为 `FAILED`。
- Apply 返回 `transaction_id`，供后续 Rollback 使用。

### 5. Verify

`verify <plan_id>` 是只读、原子检查：

```text
读取 Plan → Detect 当前目标 → 对比当前配置与 Plan → 返回结果
```

Verify 不执行 Snapshot、Apply、Restart、Rollback，也不自动创建事务。

- 全部目标符合：`ok`。
- 有 `partial`、`skipped` 或用户操作要求：`partial`。
- 有明确配置不符合：`failed`。
- 用户手动重启应用后，可以再次执行同一个 `verify <plan_id>`。

### 6. Rollback

`rollback <transaction_id>` 只恢复该事务保存的快照，并在每个目标恢复后立即验证。

- 各目标独立恢复，单个目标失败不阻止其他目标恢复。
- 只能使用当前事务自己的快照。
- 已被保留策略清理的事务返回明确的快照过期错误。

### 7. Snapshot retention

每次 Apply 仍必须创建目标快照，但事务目录按保留数量自动清理：

```text
.one-tone/transactions/<transaction_id>/<target>/snapshot/
```

- 默认保留最近 5 个已完成事务。
- `PENDING` 和当前事务不得清理。
- 只清理工具生成的事务目录。
- 通过 `--keep-transactions N` 调整数量。

### 8. Documentation

日常文档保持最小集合：

```text
README.md
OCD_Windows_Theme_Skill_计划书.md
docs/architecture.md
docs/testing.md
plugins/one-tone-windows/README.md
plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md
plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md
AGENTS.md
```

- README 只说明用途、支持范围、命令、安全边界和快速测试。
- 计划书压缩为当前状态、目标、限制和下一步。
- `architecture.md` 说明 Marketplace、Plugin、Skill 和 runtime 的关系。
- `testing.md` 说明测试目录、命令和真实环境测试边界。
- Skill 的 `SKILL.md` 只保留触发条件、确认门禁和命令。
- `targets.md` 只保留目标矩阵和已知限制。
- 旧的长规格、实施计划和重复引用资料移动到 `docs/archive/`，不作为当前入口。
- `AGENTS.md` 只保留安全规则、当前支持范围、核心流程、测试要求和文档同步规则。

## Rejected alternatives

- **Global rollback on any failure:** rejected because one broken target would unnecessarily undo successful targets.
- **Eight-step public Verify:** rejected because it mixes inspection, mutation, restart and rollback.
- **Duplicate runtime under Plugin and Skill:** rejected because the two copies would drift.
- **Delete all historical documentation:** rejected because it loses design context; archive it instead.

## Migration notes

1. Move the runtime and launcher into the Skill package without copying source files.
2. Restore Windows 10 detection and its tests.
3. Replace `run_full_cycle` with target-scoped Apply compensation and read-only Verify.
4. Change public Verify to accept `plan_id`; keep Rollback on `transaction_id`.
5. Add transaction retention and per-target snapshot directories.
6. Reorganize root tests and add package-boundary tests.
7. Rewrite `AGENTS.md`, README, plan, Skill references and maintainer docs.
8. Archive superseded specs and plans after the new docs are validated.
