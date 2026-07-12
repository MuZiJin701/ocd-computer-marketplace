# OCD Windows Theme 项目协作规范

## 项目目标

本项目是一个基于 Python 的 Windows 主题统一工具。用户选择 Seed Color 和目标应用后，工具必须支持：

```text
Preview → Plan → Apply → Verify → Rollback
```

项目目标是“小而可靠”，不建设通用桌面主题平台。

## 明确支持范围

仅支持以下目标：

- Windows 11
- Windows Terminal
- VS Code
- Cursor
- TRAE
- Codex
- Chrome

以下目标明确不实现、不适配、不标记为支持：

- JetBrains
- Edge
- Office
- 其他未验证应用

Codex 必须使用独立 Adapter，不得直接归入 VS Code 兼容编辑器 Adapter。

## 技术约束

- 使用 Python。
- 使用 `uv` 管理依赖、运行程序和测试。
- 核心模块保持精简：`cli.py`、`palette.py`、`plan.py`、`transaction.py` 和 `adapters/`。
- 不提前引入数据库、后台服务、事件溯源、复杂状态机、插件运行时或依赖注入框架。
- 同类目标应复用实现，但不得为了复用而隐藏目标差异。

## 核心数据流规则

### Preview

- 只检测环境、生成 Palette、构建 Plan、执行验证并保存 `plan.json`。
- 不得修改系统、应用配置或用户文件。

### Apply

- 只接受已有 `plan_id`，不得重新接收 Seed Color 并生成新的 Palette。
- 应用前必须验证 Plan Hash。
- 每次 Apply 必须创建独立 transaction 目录并保存原始配置备份。
- 没有成功 Snapshot 的目标不得进入 Apply。

### Verify

每个目标至少验证：

1. Detect
2. Snapshot
3. Apply
4. Verify
5. Restart
6. Verify Again
7. Rollback
8. Verify Restore

### Rollback

- 必须通过明确的 `transaction_id` 执行。
- 只能恢复该事务保存的备份。
- 恢复后必须再次验证配置和主题状态。
- 不得覆盖其他事务的备份。

## 结果模型

Adapter 不得只返回 `True` 或 `False`。统一使用结构化结果，至少包含：

```python
AdapterResult(
    target: str,
    status: Literal["ok", "partial", "failed", "skipped"],
    changed: bool,
    verified: bool,
    message: str,
)
```

Codex、Chrome 以及其他 Adapter 都必须遵守相同的最小接口：

```python
detect()
snapshot(backup_dir)
apply(plan)
verify(plan)
rollback(backup_dir)
```

## 安全与变更边界

- 只修改用户明确选择的目标。
- 不修改无关设置。
- 修改配置前必须备份原始内容。
- 未知目标必须拒绝或标记为 `skipped`，不得猜测兼容性。
- 自动应用失败时必须保留清晰的失败结果，并按照事务策略回滚已修改目标。
- 不删除或覆盖用户现有文件，除非该文件属于当前事务且已有备份。
- 保留与当前任务无关的用户修改。

## Palette 验收要求

Palette 至少包含：

```text
background
surface
foreground
muted_foreground
accent
accent_foreground
selection_background
selection_foreground
border
error
warning
success
```

关键 foreground/background、accent foreground/accent、selection foreground/selection background 的对比度目标为 `>= 7:1`。

## 测试与验证

开发完成后至少运行：

```powershell
uv run pytest
```

必须覆盖：

- Palette 生成和对比度计算
- Plan 序列化和 Hash 校验
- Transaction 创建、状态变化和恢复
- AdapterResult 合同
- 失败和部分成功路径
- 各支持目标的 Apply、Verify、Restart、Rollback 流程

只有完成实际验证的目标才能标记为 `FULL`。实现未知或未验证目标不属于本项目范围。

## 文档同步

如果支持范围、命令、状态模型、目录结构或验收标准发生变化，必须同步更新：

- `OCD_Windows_Theme_Skill_计划书.md`
- `README.md`（如果已经创建）
- 相关测试

所有实现应保持小范围、可验证、可回滚，并优先遵循项目计划书中的阶段顺序。
