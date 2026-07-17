# OCD Computer Marketplace

面向“强迫症电脑使用场景”的跨 Agent Skill 市场。

当前提供 `unify-windows-theme`：输入一个 Seed Color，统一 Windows 桌面、Windows Terminal、VS Code、TRAE、Codex 和 Chrome 本地主题。

支持 Windows 10 22H2+（build `>= 19045`）和 Windows 11 22H2+（build `>= 22621`）。Cursor 暂不在支持列表中。

## 安装

推荐使用 Vercel Labs Skills CLI 全局安装，让其他兼容 Agent 也能复用：

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

只安装到 Codex：

```powershell
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g -a codex
```

不安装 CLI 时：

```powershell
npx skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

管理 Skill：

```powershell
skills list
skills update unify-windows-theme
skills remove unify-windows-theme
```

安装后重启 Codex。Skills CLI 的 Codex 全局目录是 `~/.codex/skills/`。

可选：Codex Plugin Marketplace：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/ocd-computer-marketplace.git
codex plugin add one-tone-windows@ocd-windows-themes
```

可选：CC Switch。在 Skills 页面添加以下仓库地址，刷新后安装 `unify-windows-theme`：

```text
https://github.com/MuZiJin701/ocd-computer-marketplace.git
```

## 使用

先让 Agent 预览，不要直接应用：

```text
使用翠绿色 #10B981 统一我的电脑主题，先预览，不要立即应用。
```

也可以直接运行命令：

```powershell
python .\scripts\run_one_tone.py preview '#10B981'
python .\scripts\run_one_tone.py apply plan-... --confirm
python .\scripts\run_one_tone.py verify plan-...
python .\scripts\run_one_tone.py rollback tx-...
```

流程是：`Preview → Apply → Verify → Rollback`。Apply 必须使用已有 Plan ID 并带 `--confirm`；Rollback 必须使用 Apply 返回的 Transaction ID。

结果状态包括 `ok`、`partial`、`failed` 和 `skipped`。

只处理指定目标时：

```powershell
python .\scripts\run_one_tone.py preview '#10B981' --targets windows,terminal,codex
```

## 注意事项

- Seed Color 会作为 Codex 的 `surface` 和 Windows 壁纸颜色；Codex 主题保持用户当前 `appearanceTheme`，并使用高对比度配置。
- Windows Terminal 会为所有已发现 Profile 写入同一套 Scheme、ANSI 颜色和 Tab 颜色，窗口主题使用 `system`，不强制 Windows 深色模式。
- VS Code 和 TRAE 主题覆盖标准 Workbench、编辑器选择/光标、终端 ANSI、链接、通知和语义高亮字段；各自的 AI 专属面板仍由应用自行决定。
- Windows 开启“自动从背景中选取强调色”时，系统可能覆盖固定强调色；想保持稳定颜色，请在 Windows 设置中关闭该选项。
- Chrome 会生成 Manifest V3 本地主题 ZIP 和 unpacked 目录，需到 `chrome://extensions` 手动加载；普通本地 Skill 不能静默安装 Chrome 扩展。
- 运行时路径通过用户目录、PATH、launcher 参数或环境变量探测，不依赖开发机盘符、Everything 或机器临时路径。

## 仓库结构

```text
plugins/one-tone-windows/skills/unify-windows-theme/  # 可独立分发的 Skill
docs/                                                  # 项目文档
tests/                                                 # 仓库测试
.agents/plugins/marketplace.json                       # Marketplace 清单
```

更多细节见 [Skill 说明](plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md)、[目标矩阵](plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md) 和 [测试说明](docs/testing.md)。
