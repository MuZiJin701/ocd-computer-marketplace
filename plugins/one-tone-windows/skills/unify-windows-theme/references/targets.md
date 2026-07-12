# 支持目标

| 目标 | 范围 | 已知限制 |
| --- | --- | --- |
| `windows` | Windows 10/11 深色模式、桌面壁纸、Start/Taskbar 和标题栏强调色 | 需要注册表和桌面后端；部分应用需要重启 |
| `terminal` | Windows Terminal Profile、方案、Tab、Tab Row 和窗口顶部区域 | `frame`/`unfocusedFrame` 需要较新的 Windows Terminal Preview；修改后可能需要重启 |
| `vscode` | VS Code 工作台、标题栏、侧边栏、Activity Bar、Tab、Panel 和主题扩展 | AI 专属面板可能不受标准主题字段控制 |
| `cursor` | Cursor 通用工作台和主题扩展 | Cursor 专属界面可能不受标准主题字段控制；需重启后 Verify |
| `trae` | TRAE 通用工作台和主题扩展 | TRAE 专属界面可能不受标准主题字段控制；需重启后 Verify |
| `codex` | `config.toml` 的已验证 v1 主题字段 | 修改后需要用户手动重启 |
| `chrome` | 生成 Chrome 主题 ZIP 和可加载的 unpacked 目录 | Chrome 不支持本工具静默安装；用户需要在 `chrome://extensions` 手动加载和确认 |

Windows 10 支持 build `>= 19045`；Windows 11 支持 build `>= 22621`。不支持 JetBrains、Edge、Office、Contrast Theme 和其他未验证目标。

目标结果使用 `ok`、`partial`、`failed` 或 `skipped`，至少包含 `target`、`status`、`changed`、`verified` 和 `message`。
