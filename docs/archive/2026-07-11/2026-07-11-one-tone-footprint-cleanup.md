# One-Tone 运行期目录精简实施计划

> **供 Agent 使用：** 实施此计划时必须使用 `superpowers:subagent-driven-development`（推荐）或 `superpowers:executing-plans` 子技能。各步骤使用复选框跟踪。

**目标：** 通过将运行期数据移出源码目录、保留历史计划并清理已确认的生成产物，让 One-Tone 插件保持精简。

**架构：** 保留现有自包含插件 runtime 和事务代码。增加一个小型 CLI 默认目录解析器，使用当前项目下的单一 `.one-tone/` 目录；测试和自动化仍可通过 `--plans-dir`、`--transactions-dir` 和 `--state-dir` 显式覆盖默认值。

**技术栈：** Python 3.11+、`uv`、`pytest`、PowerShell。

## 全局约束

- 使用 Python 和 `uv`。
- 保留 `Preview → Plan → Apply → Verify → Rollback` 工作流。
- Codex 必须保持独立 Adapter。
- 生产代码保留回滚所需的最小事务备份。
- 不得仅凭 fixture 测试声称目标达到 `FULL`。
- 黄色主题只能通过明确保存的 Plan 应用到 7 个受支持目标。

---

### 任务 1：用失败测试锁定运行期目录契约

**文件：**

- 修改：`tests/test_cli.py`

- [ ] **步骤 1：添加单一项目目录默认值测试**

```python
def test_cli_defaults_runtime_data_to_single_project_directory():
    from one_tone.cli import _build_parser

    args = _build_parser().parse_args(["preview", "#FFD700", "--targets", "windows"])

    assert args.plans_dir == Path(".one-tone") / "plans"
    assert args.transactions_dir == Path(".one-tone") / "transactions"
    assert args.state_dir == Path(".one-tone") / "state"
```

- [ ] **步骤 2：运行聚焦测试并确认失败**

运行：`uv run pytest tests/test_cli.py::test_cli_defaults_runtime_data_to_single_project_directory -q`

预期：失败，因为解析器仍然默认使用三个分离的相对目录。

### 任务 2：实现小型默认目录解析器

**文件：**

- 修改：`plugins/one-tone-windows/src/one_tone/cli.py`
- 测试：`tests/test_cli.py`

- [ ] **步骤 1：在 `_build_parser` 前添加解析器**

```python
def _default_runtime_dir() -> Path:
    return Path(".one-tone")
```

- [ ] **步骤 2：替换 6 个相对目录默认值**

```python
runtime_dir = _default_runtime_dir()
preview.add_argument("--plans-dir", type=Path, default=runtime_dir / "plans")
preview.add_argument("--transactions-dir", type=Path, default=runtime_dir / "transactions")
preview.add_argument("--state-dir", type=Path, default=runtime_dir / "state")
```

Apply、Verify 和 Rollback 使用相同的 `runtime_dir` 模式，同时保留所有显式命令行覆盖参数。

- [ ] **步骤 3：运行聚焦测试和完整测试套件**

运行：`uv run pytest tests/test_cli.py::test_cli_defaults_runtime_data_to_single_project_directory -q`

预期：通过。

运行：`uv run pytest`

预期：所有测试通过。

### 任务 3：忽略并记录运行期产物

**文件：**

- 修改：`.gitignore`
- 修改：`README.md`
- 修改：`plugins/one-tone-windows/README.md`
- 修改：`plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- 修改：`plugins/one-tone-windows/skills/unify-windows-theme/references/workflow.md`

- [ ] **步骤 1：添加项目内运行期忽略规则**

添加 `/state/`、`/transactions/`、`/plugins/one-tone-windows/state/`、`/plugins/one-tone-windows/transactions/`、`/plugins/one-tone-windows/plans/`、`/.tmp/`、`/.pytest-tmp-*/`、`/debug.log` 和 `/plugins/one-tone-windows/.uv-cache/`；保留已有的 `/plans/` 规则。

- [ ] **步骤 2：记录默认数据目录**

说明运行期数据默认位于当前项目下的 `.one-tone/`，历史设计和实施文档仍保留在 `docs/`。

- [ ] **步骤 3：运行文档和 CLI 冒烟检查**

运行：`uv run one-tone --help`

预期：退出码为 0，并列出 `preview`、`apply`、`verify`、`rollback` 命令。

### 任务 4：删除已确认的生成产物

**文件：**

- 删除：`.tmp/`
- 删除：`.pytest-tmp-*` 目录
- 删除：`.pytest_cache/`
- 删除：根目录和插件目录下的 `state/`
- 删除：根目录和插件目录下的 `transactions/`
- 删除：插件 `.uv-cache/`
- 删除：生成的 `__pycache__/` 目录和 `debug.log`

- [ ] **步骤 1：解析每个删除目标，并确认目标位于仓库根目录内**
- [ ] **步骤 2：只删除已确认的生成目录和文件**
- [ ] **步骤 3：确认历史文档和生成的 Plan JSON 仍然保留**

### 任务 5：验证并准备黄色主题 Plan

**文件：**

- 不修改源码。

- [ ] **步骤 1：运行 `uv run pytest` 并检查 `git status --short`**
- [ ] **步骤 2：为 `windows,terminal,vscode,cursor,trae,codex,chrome` 使用 `#FFD700` 运行 Preview**
- [ ] **步骤 3：在 Apply 前展示保存的 Plan ID 和目标检测结果**
- [ ] **步骤 4：获得明确 Apply 确认后运行 Apply；如需完整验收，再在提示重启影响后运行 Verify**
