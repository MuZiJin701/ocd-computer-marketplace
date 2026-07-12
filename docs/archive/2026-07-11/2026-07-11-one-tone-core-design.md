# One-Tone 阶段 1–2 核心设计

## 目标与范围

本次实现计划书的阶段 1–2，打通以下可运行数据流：

```text
Seed Color → Palette → Plan → Apply → Snapshot → Verify → Rollback
```

本次交付包含：

- Palette 生成、HEX 校验、相对亮度和对比度计算。
- Plan 序列化、确定性 Hash 和 Hash 校验。
- `preview`、`apply`、`rollback` CLI 命令。
- 独立 transaction 目录、快照、结果和恢复。
- 统一 `AdapterResult` 和 `ThemeAdapter` 接口。
- 文件型 Adapter，用于真实测试事务流程。
- 未验证的真实应用适配器只返回 `skipped`，不宣称支持。

本次不实现 Windows、Windows Terminal、VS Code、Cursor、TRAE、Codex 或 Chrome 的真实配置写入；这些目标将在后续阶段逐一验证后加入。

## 设计选择

采用小型标准库实现，避免在核心层引入数据库、后台服务、复杂状态机、插件运行时或依赖注入框架。`pytest` 作为开发测试依赖，由 `uv` 管理和运行。

Palette 使用 Seed Color 作为 accent 基础色，并生成固定语义字段：

```text
background, surface, foreground, muted_foreground,
accent, accent_foreground, selection_background,
selection_foreground, border, error, warning, success
```

生成后验证以下组合的对比度至少为 `7:1`：

- foreground / background
- accent_foreground / accent
- selection_foreground / selection_background

如果输入非法或无法满足约束，Preview 失败且不保存 Plan。

## 模块边界

### `palette.py`

只负责颜色值解析、颜色转换、语义色板生成、相对亮度和对比度计算。它不读写文件，也不依赖 Adapter 或 CLI。

### `plan.py`

定义 Plan 数据模型和序列化协议。Plan 包含 `id`、`seed_color`、`mode`、`targets`、`palette`、`created_at` 和 `hash`。Hash 对不含 `hash` 字段的规范 JSON 计算 SHA-256。加载时重新计算并拒绝不匹配的文件。

### `transaction.py`

以 `transactions/<transaction_id>/` 为事务边界，保存事务元数据、备份和每个目标结果。状态只有 `PENDING`、`APPLIED`、`PARTIAL`、`FAILED`、`ROLLED_BACK`。一次 Apply 永远创建新目录，不复用或覆盖其他事务。

### `adapters/`

定义所有目标共用的最小接口：`detect`、`snapshot`、`apply`、`verify`、`rollback`。结果统一为 `AdapterResult`，包含 `target`、`status`、`changed`、`verified`、`message`。核心编排器只依赖接口，不猜测目标配置格式。

文件型 Adapter 将一个 JSON 文件当作目标配置：Snapshot 复制原始文件，Apply 写入 Plan 的 Palette，Verify 比较目标配置，Rollback 恢复备份。它只用于本地流程验证。

### `cli.py`

`preview` 接收 Seed Color 和目标列表，生成并保存 Plan；不调用写入型 Adapter。`apply` 只接受已有 `plan_id` 和 `--confirm`，加载并验证 Plan Hash，再创建事务执行 Detect、Snapshot、Apply、Verify。任一目标失败时，自动恢复本次事务中已经成功修改的目标，并把事务标记为 `FAILED`。`rollback` 只接受明确的 `transaction_id`，恢复该事务的备份并验证恢复结果。

## 错误与部分成功

- 未知目标返回 `skipped`，不会修改文件。
- 未检测到目标时，不进入 Apply，也不会创建成功快照。
- Snapshot 失败的目标不允许 Apply。
- 已成功修改的目标在后续目标失败时立即进入本次事务的自动回滚集合。
- 自动回滚完成后，事务状态为 `FAILED`；如果回滚本身也失败，结果中保留每个目标的失败信息。
- 用户主动 Rollback 只读取指定事务的备份，不能使用其他事务的文件。

## 测试策略

测试先于实现，按单元和流程分层覆盖：

- Palette：规范化、非法颜色、对比度计算、12 个语义字段和 7:1 约束。
- Plan：序列化往返、确定性 Hash、篡改检测、只消费已有 Plan。
- Transaction：独立目录、状态迁移、备份隔离、恢复和重复事务。
- Adapter：`AdapterResult` 合同、成功、跳过、失败和部分结果。
- CLI/编排：Preview 无副作用、Apply Hash 校验、失败自动回滚、指定事务 Rollback。

自动验证命令：

```powershell
uv run pytest
```

## 阶段 1–2 验收标准

1. Preview 可保存可加载的 `plans/plan-*.json`，且只包含用户选择的目标。
2. Apply 不接受 Seed Color，不重新生成 Palette，并在执行前拒绝篡改的 Plan。
3. 每次 Apply 都创建独立事务目录并保存成功 Snapshot。
4. Apply 的每个目标至少经过 Detect、Snapshot、Apply、Verify。
5. 任一目标失败时，已修改目标自动恢复，事务结果可见。
6. Rollback 必须带明确 transaction ID，并验证恢复后的内容。
7. 所有自动测试通过；未验证的真实应用不标记为 FULL 或支持。
