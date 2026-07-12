# One-Tone 安全与跨进程一致性修复设计

## 目标

修复 One-Tone 在跨进程 Verify/Rollback、事务中途失败、路径边界和结果聚合方面的安全问题，并让文档明确这些保证的边界。

## 范围

- VS Code、Cursor、TRAE：Verify 必须从持久化扩展目录重新发现 One-Tone 扩展。
- Chrome：Rollback 必须在新进程中根据事务元数据删除本次生成的 ZIP 和 unpacked 目录。
- TransactionStore：每个操作后保存结果；自动回滚失败必须暴露为 failed；没有成功目标的 Apply 必须失败。
- Plan、transaction 和 target 标识：禁止通过路径分隔符或 `..` 离开各自的运行时目录。
- 配置和事务 JSON：使用同目录临时文件加原子替换，降低进程中断造成截断文件的风险。
- 文档、测试和 `AGENTS.md` 同步描述新的状态和验证限制。
- Palette 语义：Seed 原样作为 Codex `surface` 和 Windows 壁纸；Windows registry accent 使用 Palette `accent`；用户前景使用色相关联的派生色，并对实际背景满足可读对比度，不使用黑/白二选一规则。
- 路径语义：可分发 Skill 不携带机器特定绝对路径或临时路径；Cursor `.cmd`/`.bat` launcher 的 `--user-data-dir` 和 `--extensions-dir` 可作为运行时发现来源。

## 设计

事务记录仍使用 JSON 文件，不引入数据库或后台服务。`apply_plan` 在每个 detect、snapshot、apply、verify 和 auto_rollback 操作后持久化记录；操作失败后根据恢复结果决定 `PARTIAL` 或 `FAILED`。只有至少一个目标成功应用且其他目标失败或 skipped 时才使用 `PARTIAL`。

每个 TransactionRecord 保存 Chrome 产物相对路径等可恢复元数据。Rollback 使用记录中的 `plan_id` 和元数据重新建立目标状态，不依赖当前 Python 进程的 adapter 内存字段。VS Code Verify 通过扩展索引和受控目录扫描查找主题文件。

所有外部标识使用安全组件校验：只允许字母、数字、`.`、`_` 和 `-`，并拒绝空值、路径分隔符和 `..`。未知 target 仍然返回 `skipped`，但不创建任何越界目录。

## 验证

- 先为每个已确认问题添加会失败的回归测试，再实现最小修复。
- 运行完整 `uv run pytest`、Skill CLI `--help`、`uv lock --check` 和 `git diff --check`。
- 现有 fixture 测试不替代真实 Windows 10/11 桌面验证；文档明确这一点。
