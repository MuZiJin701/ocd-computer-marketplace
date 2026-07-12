---
name: unify-windows-theme
description: >-
  当用户希望使用一个主色统一受支持的 Windows 目标，或希望预览、验证、回滚主题时使用。
---

# 统一 Windows 主题

默认处理全部已实现目标：`windows`、`terminal`、`vscode`、`cursor`、`trae`、`codex`、`chrome`。只有用户明确指定目标时才缩小范围；不要把“统一电脑主题”解释成只处理当前提到的一个应用。

## 安全流程

1. 确认 Seed Color。用户没有指定目标时，使用全部默认目标运行 Preview。
2. 运行 Preview，展示一个 Plan ID 和每个目标的检测结果；不要自行创建只包含 Windows 的窄范围 Plan。
3. 用户明确确认后，使用该 Plan ID 执行 Apply。
4. Apply 对每个目标独立 Snapshot、Apply 和内部检查，并在每个操作后持久化事务记录；失败目标自动回滚，其他成功目标保留。补偿失败报告为 `failed`；无成功目标时整体为 `failed`，混合成功/失败或需要用户操作时为 `partial`。
5. 用户需要重启应用时手动重启，然后运行 `verify <plan_id>`。VS Code、Cursor、TRAE Verify 会重新扫描持久化扩展目录，不依赖 Apply 进程内状态。
6. 用户要求撤销时，要求准确的 transaction ID，再运行 Rollback；Chrome 生成的 ZIP/unpacked 产物通过事务元数据跨进程清理。

Windows 使用 Palette `accent` 设置 Start/Taskbar、标题栏/窗口边框和 DWM 强调色，并生成 Seed Color 原色的纯色壁纸；不会修改 `AppsUseLightTheme`、`SystemUsesLightTheme` 或 `AutoColorization`。如果 Windows 自动取色已开启，必须提示用户手动关闭它，否则 Windows 可能在壁纸变化后覆盖固定强调色。Windows Terminal 会更新 Profile、Color Scheme 和窗口顶部 `theme`。VS Code、TRAE 更新标准 Workbench 主题字段；Cursor 优先安装主题 VSIX，失败时写入 `workbench.colorCustomizations` 作为直接 fallback，并要求重启 Cursor。

Seed Color 与 Codex 配置语义一致：它原样写入浅色和深色主题表的 `surface`。`foreground` 针对 `surface` 计算，`background_foreground` 针对深层 `background` 计算；`ink`、`muted_foreground` 和控件前景采用同色相的派生色，并按实际背景计算对比度；不会用“只能黑色或白色”的前景规则。

Chrome 目标生成 ZIP 和一个包含 `manifest.json` 的 unpacked 主题目录。Chrome 不允许普通本地 Skill 对任意扩展或主题执行安全的静默安装；因此必须由用户在 `chrome://extensions` 确认加载。企业策略或 Chrome Web Store 发布的扩展属于另一种部署方式，不在本 Skill 的权限范围内。

## 命令

```powershell
python .\scripts\run_one_tone.py preview '#10B981'
python .\scripts\run_one_tone.py apply plan-... --confirm
python .\scripts\run_one_tone.py verify plan-...
python .\scripts\run_one_tone.py rollback tx-...
```

需要缩小范围时再显式使用 `--targets windows,codex`。Preview 的 `--targets` 默认值就是全部已实现目标。

`verify` 只读取当前目标并与 Plan 对比，不创建事务、不 Snapshot、不 Apply、不 Restart、不 Rollback。

Plan ID、Transaction ID 和 target 必须是安全路径组件。编辑器和 Terminal 的实际路径会优先使用用户目录与 PATH 探测；Cursor 的 `.cmd`/`.bat` launcher 会被解析以获得 `--user-data-dir` 和 `--extensions-dir`，也可通过 `ONE_TONE_<TARGET>_...` 环境变量覆盖。运行时不依赖 Everything、固定盘符或开发机临时路径。fixture 测试不代表真实 Windows 桌面目标已验证。
