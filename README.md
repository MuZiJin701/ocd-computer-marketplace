# OCD Computer Marketplace

一个面向“强迫症电脑使用场景”的跨 Agent Skill 市场。

这里的目标不是堆积脚本，而是把电脑整理、统一、检查和维护这类重复工作，封装成可复用、可验证、可回滚的 Agent Skill。Skill 以 `SKILL.md` 为入口，必要时携带脚本、参考资料和独立 runtime，能够被 Codex、Vercel Skills 生态和 CC Switch 等工具分发或管理。

## 当前插件

| Plugin | Skill | 用途 | 当前状态 |
| --- | --- | --- | --- |
| `one-tone-windows` | `unify-windows-theme` | 使用一个 Seed Color 统一 Windows 及常用应用主题 | 可用 |

`unify-windows-theme` 当前覆盖：Windows 桌面、Windows Terminal、VS Code、Cursor、TRAE、Codex 和 Chrome 本地主题包。Cursor 如果不能注册 VSIX，会退回到 `workbench.colorCustomizations`，因此不再出现“设置写入成功但界面完全不变”的假成功；默认 Preview 会探测全部这些目标，只有用户明确指定目标时才缩小范围。

Windows 目标支持 Windows 10 22H2+（build `>= 19045`）和 Windows 11 22H2+（build `>= 22621`）。

核心流程：

```text
Preview → 用户确认 → Apply → Verify → Rollback
```

它的关键语义是：用户输入的 Seed Color 原样作为 Codex 的 `surface` 和 Windows 壁纸颜色；Windows 系统强调色使用 Palette 的 `accent`；Apply 不修改用户当前浅色/深色模式或 Windows 自动取色设置。若 Windows 自动取色已开启，Preview/Apply 会明确提示它可能覆盖固定强调色，用户需要在系统设置中关闭“自动从背景中选取强调色”。

Palette 的文字色按实际背景分别计算：`foreground` 用于 Seed `surface`，`background_foreground` 用于深层 `background`，因此翠绿色不会再使用低对比度的通用白色文字。

Chrome 当前生成本地主题 ZIP 和 unpacked 目录。普通本地 Skill 无法绕过 Chrome 的安全策略静默安装任意扩展或主题，因此 Chrome 的加载需要用户在 `chrome://extensions` 确认；企业策略或 Chrome Web Store 发布属于另一种部署方式。

## 仓库结构

```text
.
├─ .agents/plugins/marketplace.json       # Marketplace 清单
├─ plugins/
│  └─ one-tone-windows/
│     ├─ .codex-plugin/plugin.json        # 可选的 Codex Plugin 外壳
│     └─ skills/
│        └─ unify-windows-theme/           # 自包含、可独立分发的 Skill
│           ├─ SKILL.md
│           ├─ references/
│           ├─ examples/
│           ├─ scripts/
│           └─ src/one_tone/               # Python runtime
├─ docs/                                   # 架构、测试和设计记录
├─ tests/                                  # 仓库级 fixture 测试
├─ AGENTS.md
└─ OCD_Windows_Theme_Skill_计划书.md
```

根目录是 Marketplace 和测试入口；Plugin 是可选的 Codex 外壳；Skill 目录可以脱离仓库根目录独立安装和运行。测试、历史方案和开发缓存不进入最终 Skill 分发包。

## 安装

### 推荐：Skills 全局安装

优先使用 Vercel Labs 的 `skills` CLI 全局安装。这样安装后，支持该 Skill 目录的 Agent 可以复用同一份 Skill：

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

如果只想让 Codex 使用：

```powershell
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g -a codex
```

不想全局安装 CLI 时使用 `npx`：

```powershell
npx skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

常用管理命令：

```powershell
skills list
skills update unify-windows-theme
skills remove unify-windows-theme
```

Codex 的全局 Skills 目录是 `~/.codex/skills/`；安装后重启 Codex，使新 Skill 被加载。

### 可选：Codex Plugin Marketplace

本仓库同时是 Codex marketplace，marketplace 名称为 `ocd-windows-themes`，Plugin 目录为 `plugins/one-tone-windows/`：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/ocd-computer-marketplace.git
codex plugin add one-tone-windows@ocd-windows-themes
```

### 通过 CC Switch

在 CC Switch 的 Skills 页面添加仓库地址：

```text
https://github.com/MuZiJin701/ocd-computer-marketplace.git
```

刷新仓库后安装 `unify-windows-theme`，再选择 Codex。CC Switch 会把 Skill 管理到对应 Agent 的 Skill 目录，并负责后续更新、卸载和恢复。

## 使用

安装后，可以直接向 Codex 描述目标：

```text
使用翠绿色 #10B981 将我的电脑主题统一，先预览，不要立即应用。
```

正确的默认行为是生成包含全部已实现目标的 Plan，并展示每个目标的探测结果。用户确认后才 Apply：

```powershell
python .\scripts\run_one_tone.py preview '#10B981'
python .\scripts\run_one_tone.py apply plan-... --confirm
python .\scripts\run_one_tone.py verify plan-...
python .\scripts\run_one_tone.py rollback tx-...
```

`verify <plan_id>` 只读检查 Plan；Apply 会返回 `transaction_id`，Rollback 只接受该事务 ID。结果状态包括 `ok`、`partial`、`failed` 和 `skipped`。

也可以直接运行 Skill runtime：

```powershell
uv run --project .\plugins\one-tone-windows\skills\unify-windows-theme one-tone --help
```

跨平台路径写法：

```powershell
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
```

只在用户明确要求时指定目标，例如：

```powershell
python .\scripts\run_one_tone.py preview '#10B981' --targets windows,codex
```

## 路径探测

运行时不包含开发机盘符，不依赖 Everything，也不使用机器临时路径。它按以下顺序发现目标：

- 用户显式环境变量覆盖。
- Windows 用户目录和标准应用目录。
- PATH 中的可执行文件。
- Cursor launcher 的 `--user-data-dir`、`--extensions-dir`。
- Windows Terminal 的 Store 路径、Scoop shim 对应的 `persist` 路径和用户目录。
- Codex 的 `CODEX_HOME/config.toml` 或 `%USERPROFILE%\.codex\config.toml`。

必要时可使用 `ONE_TONE_<TARGET>_...` 环境变量覆盖设置文件、可执行文件和扩展目录。

## 开发与验证

```powershell
uv run pytest
uv lock --check
git diff --check
```

默认测试使用 fixture，不修改当前桌面。真实 Windows、应用重启和 Chrome 加载仍需在目标机器上单独验证。

## 后续方向

- 增加更多面向电脑整理、统一和维护的 Plugin/Skill。
- 为成熟 Plugin 增加宣传海报、安装示意图和使用案例，统一放入独立的宣传资源目录，不混入 Skill runtime。
- 持续补充不同 Windows 安装方式和不同 Agent 分发器的实机验证记录。

## 相关文档

- [Plugin 说明](plugins/one-tone-windows/README.md)
- [Skill 说明](plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md)
- [目标矩阵](plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md)
- [架构说明](docs/architecture.md)
- [测试说明](docs/testing.md)
