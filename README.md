# One-Tone Windows

从一个 Seed Color 生成统一 Palette，并安全应用到受支持的 Windows 目标。

## 支持范围

- Windows 10 22H2+（build >= 19045）
- Windows 11 22H2+（build >= 22621）
- Windows 桌面主题和可回滚壁纸
- Windows Terminal、VS Code、Cursor、TRAE、Codex、Chrome

不支持 JetBrains、Edge、Office、Contrast Theme 或其他未验证目标。

## 工作流

```text
Preview → Apply → Verify → Rollback
```

```powershell
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone preview "#7C3AED" --targets windows,terminal --output json
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone apply plan-... --confirm
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone verify plan-...
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone rollback tx-...
```

- `preview` 生成带 Hash 的 Plan，不修改目标。
- `apply` 只接受已有 `plan_id`。每个目标独立 Snapshot、Apply、内部检查；失败目标自动回滚，成功目标保留。
- `windows` 同时设置 Start/Taskbar 和标题栏/窗口边框强调色开关；`terminal` 覆盖 Profile、Tab 和窗口顶部区域。
- `vscode`、`cursor`、`trae` 覆盖标准工作台主题字段，但专属 AI 界面可能返回 `partial`。
- `verify <plan_id>` 只读取当前配置并与 Plan 对比，不创建事务、不重启应用。
- 用户手动重启应用后，再次执行同一个 `verify <plan_id>`。
- `rollback <transaction_id>` 恢复该事务快照并验证恢复结果。
- `chrome` 生成 ZIP 和可加载目录；Chrome 主题仍需用户在 `chrome://extensions` 手动加载。
- 目标结果使用 `ok`、`partial`、`failed` 或 `skipped`。

## 目录

```text
.agents/plugins/marketplace.json
plugins/one-tone-windows/
└─ skills/unify-windows-theme/
   ├─ SKILL.md
   ├─ pyproject.toml
   ├─ examples/
   ├─ src/one_tone/
   └─ scripts/
tests/
```

Skill 包自带 Python runtime，可独立使用；Codex Plugin 元数据只是可选兼容层。根项目只提供测试入口。运行期 Plan、主题产物和事务快照保存在当前工作目录的 `.one-tone/`，默认保留最近 5 个已完成事务。

## 测试

```powershell
uv run pytest
```

测试使用 fixture，不会修改当前桌面。真实目标必须在目标机器上单独验证。
