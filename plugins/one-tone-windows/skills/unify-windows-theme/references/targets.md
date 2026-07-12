# 支持目标

| 目标 | 范围 | 已知限制 |
| --- | --- | --- |
| `windows` | Windows 10/11 当前用户模式下的桌面壁纸、Start/Taskbar 和标题栏强调色 | 壁纸使用 Seed 原色，强调色使用 Palette `accent`；不修改浅/深色模式和自动取色；需要注册表和桌面后端，部分应用需要重启 |
| `terminal` | Windows Terminal Profile、方案、Tab、Tab Row 和窗口顶部区域 | `frame`/`unfocusedFrame` 需要较新的 Windows Terminal Preview；修改后可能需要重启 |
| `vscode` | VS Code 工作台、标题栏、侧边栏、Activity Bar、Tab、Panel 和主题扩展 | AI 专属面板可能不受标准主题字段控制；Verify 会重新发现持久化扩展目录 |
| `cursor` | Cursor 通用工作台和主题扩展 | Cursor 专属界面可能不受标准主题字段控制；需重启后 Verify，Verify 会重新发现扩展目录 |
| `trae` | TRAE 通用工作台和主题扩展 | TRAE 专属界面可能不受标准主题字段控制；需重启后 Verify，Verify 会重新发现扩展目录 |
| `codex` | `config.toml` 的已验证 v1 主题字段；浅色和深色表的 `surface` 都等于 Seed | `ink`/`accent` 使用 Palette 对应语义，修改后需要用户手动重启 |
| `chrome` | 生成 Chrome 主题 ZIP 和可加载的 unpacked 目录 | Chrome 不支持本工具静默安装；用户需要在 `chrome://extensions` 手动加载和确认 |

Windows 10 支持 build `>= 19045`；Windows 11 支持 build `>= 22621`。

目标结果使用 `ok`、`partial`、`failed` 或 `skipped`，至少包含 `target`、`status`、`changed`、`verified` 和 `message`。Palette 的主文字对深层背景目标为 `>= 7:1`，UI 前景对实际背景目标为 `>= 4.5:1`；Seed 本身不因对比度计算被暗化。

`partial` 表示至少一个目标完成但存在失败、跳过或用户操作；若没有目标完成，或补偿回滚失败，则为 `failed`。目标名、Plan ID 和 Transaction ID 不得包含路径分隔符或 `..`。VS Code/Cursor/TRAE 的路径可通过 `ONE_TONE_<TARGET>_EXECUTABLE`、`ONE_TONE_<TARGET>_SETTINGS`、`ONE_TONE_<TARGET>_EXTENSIONS` 覆盖；Cursor launcher 的数据目录、Windows Terminal 的 Store/Scoop 用户配置和 Codex 的 `CODEX_HOME` 配置也会自动探测。Skill 不要求 Everything，不使用固定盘符或开发机临时路径。
