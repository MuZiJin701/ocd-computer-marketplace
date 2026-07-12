# OCD Windows Theme 当前计划

## 目标

完成一个小而可靠的 Windows 主题 Skill：先 Preview，再 Apply；Apply 失败只回滚失败目标；Verify 只检查当前状态；Rollback 恢复指定事务。

## 当前范围

- Windows 10 22H2+、Windows 11 22H2+
- Windows Terminal
- VS Code、Cursor、TRAE
- 独立 Codex Adapter
- Chrome 主题包

## 包结构

仓库根目录是 Marketplace 和测试入口。`one-tone-windows` 是第一个 Plugin 包，其中的 `unify-windows-theme` 是自包含 Skill 和 Python runtime。后续可以添加更多 Plugin 或纯 Skill。

## 验收标准

- `uv run pytest` 通过。
- Preview 不修改目标。
- Apply 使用已有 Plan Hash，并按目标独立 Snapshot、Apply、内部检查和补偿回滚。
- `verify <plan_id>` 只检查当前配置。
- `rollback <transaction_id>` 只恢复自身快照并验证结果。
- 目标限制明确报告为 `ok`、`partial` 或 `skipped`。

## 下一步

完成 Skill 自包含迁移、事务保留策略、文档归档和真实 Windows 10/11 目标验证。

历史方案和实施记录保存在 `docs/archive/`。
