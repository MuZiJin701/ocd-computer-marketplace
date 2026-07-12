# OCD Computer Marketplace

一个面向“强迫症电脑使用场景”的跨 Agent Skill 市场。

这里的目标不是堆积脚本，而是把电脑整理、统一、检查和维护这类重复工作，封装成可复用、可验证、可回滚的 Agent Skill。Skill 以 `SKILL.md` 为入口，必要时携带脚本、参考资料和独立 runtime，能够被 Codex、Vercel Skills 生态和 CC Switch 等工具分发或管理。

## 当前插件

| Plugin | Skill | 用途 | 当前状态 |
| --- | --- | --- | --- |
| `one-tone-windows` | `unify-windows-theme` | 使用一个 Seed Color 统一 Windows 及常用应用主题 | 可用 |

`unify-windows-theme` 当前覆盖：Windows 桌面、Windows Terminal、VS Code、Cursor、TRAE、Codex 和 Chrome 本地主题包。默认 Preview 会探测全部这些目标；只有用户明确指定目标时才缩小范围。

Windows 目标支持 Windows 10 22H2+（build `>= 19045`）和 Windows 11 22H2+（build `>= 22621`）。

核心流程：

```text
Preview → 用户确认 → Apply → Verify → Rollback
```

它的关键语义是：用户输入的 Seed Color 原样作为 Codex 的 `surface` 和 Windows 壁纸颜色；Windows 系统强调色使用 Palette 的 `accent`；Apply 不修改用户当前浅色/深色模式或 Windows 自动取色设置。

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

### 通过 Codex Plugin Marketplace

在 Codex 的 Plugins/Marketplace 界面添加本仓库：

```text
https://github.com/MuZiJin701/ocd-computer-marketplace
```

然后安装 `one-tone-windows` Plugin。Plugin 会提供 `unify-windows-theme` Skill。界面名称会随 Codex 版本略有变化，但安装对象应是 Plugin，而不是仓库根目录下的测试项目。

### 通过 Vercel Skills CLI

Vercel Skills CLI 支持从 GitHub 仓库中的直接 Skill 目录安装。安装到当前用户的 Codex：

```powershell
npx skills add https://github.com/MuZiJin701/ocd-computer-marketplace/tree/main/plugins/one-tone-windows/skills/unify-windows-theme --global --agent codex --copy --yes
```

检查安装结果：

```powershell
npx skills list --global --agent codex
```

更新：

```powershell
npx skills update unify-windows-theme --global --yes
```

### 通过 CC Switch

在 CC Switch 的 Skills 页面执行：

1. 打开 Repository Management，添加仓库。
2. Owner 填 `MuZiJin701`，Name 填 `ocd-computer-marketplace`，Branch 填 `main`。
3. Subdirectory 填 `plugins/one-tone-windows/skills`。
4. Refresh 后找到 `unify-windows-theme`，点击 Install，并选择 Codex。

CC Switch 会把 Skill 管理到 Codex 的 Skill 目录，并负责后续更新、卸载和恢复。不同版本的 CC Switch 可能把源文件放在自己的统一 Skill 目录，再同步到 `~/.codex/skills/`。

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
