# Cursor 下线与高对比度主题设计

## 目标

暂时从用户可见目标矩阵和默认流程中移除 Cursor，避免在 Cursor 没有实际加载主题时产生误导性结果；同时参考当前 Codex 配置的 `surface`、`ink`、`accent` 和 `contrast=100` 语义，重做 Palette 的文字对比度选择。

## 已确认事实

- 当前 Codex 配置的浅色和深色主题都使用 `surface`、`ink`、`accent`、`contrast` 字段；实际配置为 `surface=#9CCC65`、`ink=#3A541C`、`accent=#FAFCF7`、`contrast=100`。
- `appearanceTheme` 当前为 `system`，本次不得修改系统浅色/深色模式选择。
- Cursor 当前虽然可以写入设置文件，但用户界面没有可靠反映主题，现有 VSIX 和 `workbench.colorCustomizations` 兜底都未达到可接受的用户体验。

## 设计

### Cursor 目标边界

- 从正式支持目标、默认目标探测、用户 README 和 Skill 的用户流程中移除 `cursor`。
- 保留现有 Cursor Adapter 源码和测试作为隔离实验代码，但不在生产目标注册表中暴露。
- 显式输入 `cursor` 时返回安全的 `skipped`，不读取、写入、快照或删除 Cursor 文件。
- 其他编辑器 VS Code 和 TRAE 不改变行为。

### Palette 对比度

- `surface` 始终原样等于 Seed Color。
- `background` 继续是深层背景，`background_foreground` 针对它计算，目标至少 `7:1`。
- `foreground` 映射 Codex 的 `ink`，针对 `surface` 搜索同色相候选，目标至少 `5.5:1`；当输入色的理论最大对比度不足时取最大可得值。
- `muted_foreground` 目标至少 `4.5:1`，但搜索评分偏向更接近主文字的候选，避免过灰。
- `accent_text`、`error_text`、`warning_text`、`success_text` 针对 `surface` 计算，供关键字和终端 ANSI 强调文字使用，目标至少 `5.5:1`。
- `accent_foreground` 和 `selection_foreground` 针对各自背景分别计算，目标至少 `5.5:1`。
- 候选搜索使用更密的同色相 HSL 网格，并优先选择接近可读亮度且保留色相/色度的候选；只有无法满足阈值时才取最大可得对比度，不把强调文字固定成纯黑或纯白。
- Codex 两个 Chrome Theme 表的 `contrast` 写为 `100`；`appearanceTheme` 原样保留为 `system` 或用户已有值。

### README

根 README 改为面向用户的短文档：安装、支持目标、Preview/Apply/Verify/Rollback 命令、Chrome 手动确认和 Windows 自动取色提醒。算法、适配器、事务安全和历史设计移至项目文档，不在 README 展开。

## 验收标准

- 默认 Preview 不再列出 Cursor，支持矩阵只列出 Windows、Windows Terminal、VS Code、TRAE、Codex 和 Chrome。
- 显式传入 Cursor 不产生文件变更，并返回 `skipped`。
- `#10B981` 的主文字和关键强调文字达到 `5.5:1`，且仍保持强调色相，不使用浅色强调色直接叠在浅色 `surface` 上。
- Codex Apply/Verify 覆盖两套主题的 `contrast=100`，不修改 `appearanceTheme`。
- README 不再描述 Cursor 支持或回退方案，普通用户可以直接按命令完成安装和使用。
- `uv run pytest`、`git diff --check` 和 CLI 冒烟检查通过。
