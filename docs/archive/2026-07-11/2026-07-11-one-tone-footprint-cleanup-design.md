# One-Tone 运行期目录精简设计

## 目标

让 One-Tone 保持为一个小型主题插件：源码、Skill、测试和历史文档留在仓库；运行期 Plan、主题包、事务备份和临时文件不再污染项目目录。

## 设计

- 根目录 `.venv` 继续负责仓库测试，插件目录 `.venv` 继续保证插件可独立运行；两者职责不同，不删除。
- CLI 默认使用当前项目下的单一 `.one-tone/` 目录，包含 `plans/`、`transactions/` 和 `state/`，便于集中管理。
- 保留事务代码和每次 Apply 的最小备份，因为 Rollback 仍是安全边界；只清理当前仓库中已有的历史运行产物。
- 保留 `docs/superpowers/plans/`、`docs/superpowers/specs/` 和项目计划书；忽略生成的 `plans/`、`state/`、`transactions/`、`.tmp/`、`.pytest-tmp-*` 和缓存。
- 黄色主题使用现有插件流程，目标为 `windows,terminal,vscode,cursor,trae,codex,chrome`；先 Preview，确认 Plan 后 Apply，再 Verify。

## 验收

- 默认 CLI 运行目录统一位于当前项目的 `.one-tone/`。
- `uv run pytest` 全部通过。
- 清理后仓库不再包含已确认删除的状态、事务、缓存和临时产物。
- 黄色主题流程只使用生成的 Plan，不重新生成 Palette。
