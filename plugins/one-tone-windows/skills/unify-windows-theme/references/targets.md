# 支持目标

| 目标 | 范围 | 已知限制 |
| --- | --- | --- |
| `windows` | Windows 10/11 普通深色模式和桌面壁纸 | 需要注册表和桌面后端 |
| `terminal` | Windows Terminal 当前 Profile | 修改后可能需要用户手动重启 |
| `vscode` | VS Code 工作台和主题扩展 | AI 专属面板可能不受标准主题字段控制 |
| `cursor` | Cursor 工作台和主题扩展 | 部分 Cursor 专属界面不受标准主题字段控制 |
| `trae` | TRAE 工作台和主题扩展 | 运行中的 TRAE 可能锁定配置文件 |
| `codex` | `config.toml` 的已验证 v1 主题字段 | 修改后需要用户手动重启 |
| `chrome` | 生成 Chrome 主题 ZIP | 用户需要手动加载和确认 |

Windows 10 支持 build `>= 19045`；Windows 11 支持 build `>= 22621`。不支持 JetBrains、Edge、Office、Contrast Theme 和其他未验证目标。

目标结果使用 `ok`、`partial`、`failed` 或 `skipped`，至少包含 `target`、`status`、`changed`、`verified` 和 `message`。
