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
- Apply 每个操作后持久化事务记录；补偿失败为 `failed`，没有成功目标时不返回成功。
- `verify <plan_id>` 只检查当前配置。
- `rollback <transaction_id>` 只恢复自身快照/产物元数据并验证结果，支持跨进程执行。
- Plan、Transaction 和 target 标识不能穿越运行时目录；配置写入使用原子替换。
- 目标限制明确报告为 `ok`、`partial` 或 `skipped`。
- Seed Color 原样作为 Palette/Codex 的 `surface` 和 Windows 壁纸颜色；Windows 强调色使用 Palette `accent`，不修改用户浅/深色模式或 `AutoColorization`。
- Preview 默认覆盖全部已实现目标；编辑器、Windows Terminal 和 Codex 路径通过用户目录、PATH、Scoop shim、launcher 参数和环境变量覆盖探测，不写入机器特定盘符或临时路径。

## 下一步

下一阶段聚焦真实 Windows 10/11 目标验证，并记录 VS Code/Cursor/TRAE、Windows Terminal、Codex 和 Chrome 的实际兼容性结果。编辑器路径可通过 `ONE_TONE_<TARGET>_*` 环境变量覆盖。

历史方案和实施记录保存在 `docs/archive/`。
