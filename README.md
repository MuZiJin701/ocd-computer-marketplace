# One-Tone Windows Theme Core

这是计划书阶段 1–2 的核心实现：把 Seed Color 变成可校验的 Palette，先保存 Plan，再通过独立 Transaction 执行 Apply、Verify 和 Rollback。

## 当前范围

当前阶段支持：

- Palette 生成和关键颜色对比度 `>= 7:1` 验证。
- Plan JSON 序列化和 SHA-256 Hash 校验。
- `preview`、`apply`、`rollback` 命令。
- 独立事务目录、原始配置备份、失败自动回滚。
- `file-demo` 文件型 Adapter，用于本地验证完整流程。

本阶段不实现真实应用适配：Windows 11、Windows Terminal、VS Code、Cursor、TRAE、Codex 和 Chrome 目前不会被标记为支持或 FULL。未知目标会返回 `skipped`，不会猜测兼容性或修改文件。

## 使用方式

```powershell
uv run one-tone preview "#7C3AED" --targets codex,chrome
uv run one-tone apply plan-... --confirm
uv run one-tone rollback tx-...
```

Preview 只生成 `plans/<plan_id>.json`，不创建事务，也不修改目标。Apply 只接受已有 `plan_id`，会在执行前校验 Plan Hash。

要演示成功的文件型 Adapter，可先创建 `state/file-demo.json`：

```json
{"theme": "original"}
```

然后运行：

```powershell
uv run one-tone preview "#7C3AED" --targets file-demo
uv run one-tone apply plan-... --confirm
uv run one-tone rollback tx-...
```

事务保存在 `transactions/<transaction_id>/`，原始内容位于该事务自己的 `backup/` 目录。任一目标在 Apply 或 Verify 阶段失败时，已修改目标会自动恢复，事务状态为 `FAILED`；混合成功和未验证目标时状态为 `PARTIAL`。

## 验证

```powershell
uv run pytest
```

本项目刻意保持小范围：不使用数据库、后台服务、复杂状态机或插件运行时。后续阶段只有在完成 Detect、Snapshot、Apply、Verify、Restart、Verify Again、Rollback、Verify Restore 后，才可将真实目标加入支持范围。
