# One-Tone Windows Theme Core

One-Tone 将同一个 Seed Color 生成的 Palette 应用于 Windows 10/11、Windows Terminal、VS Code Family、Codex 和 Chrome，并通过 Plan、Transaction 和回滚保持可验证。

## 支持范围

- Windows 10 22H2+ 与 Windows 11 22H2+ 普通深色模式。
- Windows 桌面：生成 Palette 驱动的深色渐变壁纸，并支持 Snapshot、Apply、Verify、Rollback。
- Windows Terminal：修改实际 `settings.json` 中当前默认 Profile。
- VS Code、Cursor、TRAE：共用主题/VSIX 生成器，但分别检测、应用和回滚。
- Codex：独立 Adapter；未验证真实配置格式时返回 `skipped`。
- Chrome：生成主题 ZIP；Apply 返回 `partial` 和 `requires_user_action`，要求用户加载/确认。

不支持 Contrast Theme、JetBrains、Edge、Office 或其他未验证目标。VS Code Family 的 AI 专属面板不通过标准主题字段控制时返回 `partial`。

## Scoop 路径

默认探测这些实际路径，也可由代码调用时传入显式路径：

```text
D:\software\scoop\apps\windows-terminal\current\settings\settings.json
D:\software\scoop\apps\vscode\current\bin\code.cmd
D:\software\scoop\apps\cursor\current\resources\app\bin\cursor.cmd
D:\software\scoop\apps\trae\current\IDE\bin\trae.cmd
```

## 命令

```powershell
uv run one-tone preview "#7C3AED" --targets windows,terminal,vscode,cursor,trae,codex,chrome
uv run one-tone apply plan-... --confirm
uv run one-tone verify plan-... --confirm --restart-apps
uv run one-tone rollback tx-...
```

`preview` 只生成 Plan 并执行 Detect，不修改目标。`apply` 只接受已有 `plan_id`，执行前校验 Plan Hash。`verify` 执行八步验收：

```text
Detect → Snapshot → Apply → Verify → Restart → Verify Again → Rollback → Verify Restore
```

只有八步完成、记录实际应用版本且没有用户操作要求时才标记 `FULL`；限制明确时为 `PARTIAL`；未安装或格式未验证时为 `SKIPPED`。

默认不关闭或启动应用。`--restart-apps` 会允许 Windows Terminal、编辑器等目标结束并重新启动进程；执行前请确认未保存的工作已处理。

## 壁纸、事务和 Chrome

Windows Adapter 使用 Palette 生成确定性的深色渐变 PNG，在 Apply 时设置桌面壁纸；事务会保存原壁纸路径和原文件，Rollback 恢复它们。事务目录为 `transactions/<transaction_id>/`，只使用该事务自己的备份。

Chrome Adapter 只生成主题 ZIP，不直接修改 Chrome Preferences。结果中的 `requires_user_action` 表示需要用户在 Chrome 中加载/确认主题；Rollback 会删除本事务生成的 ZIP，并明确提示用户恢复浏览器原主题。

## 验证

```powershell
uv run pytest
```

测试使用临时 fixture 和注入的系统后端，不会改变当前桌面。自动化测试通过不等于真实目标已达 `FULL`；真实目标必须在对应机器上完成八步流程并记录版本。
