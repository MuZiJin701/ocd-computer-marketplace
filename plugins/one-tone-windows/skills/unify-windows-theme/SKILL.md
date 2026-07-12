---
name: unify-windows-theme
description: >-
  当用户希望使用一个主色统一受支持的 Windows 目标，或希望预览、验证、回滚主题时使用。
---

# 统一 Windows 主题

支持目标和限制见 [references/targets.md](references/targets.md)。未知目标必须报告为 `skipped`，不得猜测兼容性。

## 安全流程

1. 确认 Seed Color 和目标列表。
2. 运行 Preview，展示 Plan ID 和检测结果。
3. 用户明确确认后，使用该 Plan ID 执行 Apply。
4. Apply 对每个目标独立 Snapshot、Apply 和内部检查；失败目标自动回滚，其他成功目标保留。
5. 用户需要重启应用时手动重启，然后运行 `verify <plan_id>`。
6. 用户要求撤销时，要求准确的 transaction ID，再运行 Rollback。

Windows 会同时设置 Start/Taskbar 和标题栏/窗口边框的强调色开关。Windows Terminal 会更新 Profile、Color Scheme 和窗口顶部 `theme`。VS Code、Cursor、TRAE 只保证标准 Workbench 主题字段；专属 AI 面板仍可能返回 `partial`。

Chrome 会生成 ZIP 和一个包含 `manifest.json` 的 unpacked 目录。Chrome 需要用户打开 `chrome://extensions`、开启开发者模式并手动选择该目录，本 Skill 不尝试静默安装浏览器扩展。

## 命令

```powershell
python .\scripts\run_one_tone.py preview '#7C3AED' --targets windows,terminal
python .\scripts\run_one_tone.py apply plan-... --confirm
python .\scripts\run_one_tone.py verify plan-...
python .\scripts\run_one_tone.py rollback tx-...
```

`verify` 只读取当前目标并与 Plan 对比，不创建事务、不 Snapshot、不 Apply、不 Restart、不 Rollback。
