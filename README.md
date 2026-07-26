# OCD Computer Marketplace

面向“强迫症电脑使用场景”的跨 Agent Skill 市场。

当前提供三个独立 Plugin：`one-tone-windows` 统一 Windows 主题，`ocd-desktop-zero` 整理当前用户桌面，`ocd-scoop-toolchain` 检查并补齐基础开发工具链。

One-Tone 支持 Windows 10 22H2+（build `>= 19045`）和 Windows 11 22H2+（build `>= 22621`）；Cursor 暂不在主题支持列表中。两个工作站 Plugin 也面向 Windows，并要求可用且可写的 D 盘，不会自动换用其他盘符。

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
skills update desktop-zero
skills update scoop-toolchain
skills remove unify-windows-theme
skills remove desktop-zero
skills remove scoop-toolchain
```

安装后重启 Codex。Skills CLI 的 Codex 全局目录是 `~/.codex/skills/`。

可选：Codex Plugin Marketplace：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/ocd-computer-marketplace.git
codex plugin add one-tone-windows@ocd-computer-marketplace
codex plugin add ocd-desktop-zero@ocd-computer-marketplace
codex plugin add ocd-scoop-toolchain@ocd-computer-marketplace
```

可选：CC Switch。在 Skills 页面添加以下仓库地址，刷新后选择 `unify-windows-theme`、`desktop-zero` 或 `scoop-toolchain`：

```text
https://github.com/MuZiJin701/ocd-computer-marketplace.git
```

可安装的 Plugin 包括 `one-tone-windows`、`ocd-desktop-zero` 和 `ocd-scoop-toolchain`。

## 使用

先让 Agent 预览，不要直接应用：

```text
使用翠绿色 #10B981 统一我的电脑主题，先预览，不要立即应用。
```

也可以直接运行命令：

```powershell
# 如果当前目录已经是 plugins/one-tone-windows/skills/unify-windows-theme：
python .\scripts\run_one_tone.py preview '#10B981'
# 如果当前目录是仓库根目录：
python .\plugins\one-tone-windows\skills\unify-windows-theme\scripts\run_one_tone.py preview '#10B981'
python .\plugins\one-tone-windows\skills\unify-windows-theme\scripts\run_one_tone.py apply plan-... --confirm
python .\plugins\one-tone-windows\skills\unify-windows-theme\scripts\run_one_tone.py verify plan-...
python .\plugins\one-tone-windows\skills\unify-windows-theme\scripts\run_one_tone.py rollback tx-...
```

流程是：`Preview → Apply → Verify → Rollback`。Apply 必须使用已有 Plan ID 并带 `--confirm`；Rollback 必须使用 Apply 返回的 Transaction ID。

结果状态包括 `ok`、`partial`、`failed` 和 `skipped`。

Desktop zero：

```powershell
python .\plugins\ocd-desktop-zero\skills\desktop-zero\scripts\run_desktop_zero.py preview
python .\plugins\ocd-desktop-zero\skills\desktop-zero\scripts\run_desktop_zero.py apply <plan_id> --confirm
python .\plugins\ocd-desktop-zero\skills\desktop-zero\scripts\run_desktop_zero.py verify <plan_id>
python .\plugins\ocd-desktop-zero\skills\desktop-zero\scripts\run_desktop_zero.py rollback <transaction_id>
```

快捷方式会被直接删除且不可恢复；其他桌面文件和文件夹按确定性规则移动到 `D:\data`。软件启动入口约定为 Windows 任务栏 Search，不安装后台监控。

Scoop toolchain：

```powershell
python .\plugins\ocd-scoop-toolchain\skills\scoop-toolchain\scripts\run_scoop_toolchain.py preview
python .\plugins\ocd-scoop-toolchain\skills\scoop-toolchain\scripts\run_scoop_toolchain.py apply <plan_id> --confirm
python .\plugins\ocd-scoop-toolchain\skills\scoop-toolchain\scripts\run_scoop_toolchain.py verify <plan_id>
```

Scoop 根目录固定为 `D:\software\scoop`。工具链只补齐缺失的 Python、Git、uv 和 Node.js，不卸载或重置已有软件；Scoop 无法提供时才考虑 winget，winget 的安装路径通常不可控。

两者都必须先 Preview，Apply 必须使用已有 Plan ID 并显式确认。结果状态包括 `ok`、`partial`、`failed` 和 `skipped`。

只处理指定目标时：

```powershell
python .\plugins\one-tone-windows\skills\unify-windows-theme\scripts\run_one_tone.py preview '#10B981' --targets windows,terminal,codex
```

## 注意事项

- Seed Color 作为 Codex 和 Windows 的 Theme anchor/Accent source；大面积 Codex Surface 和 Windows 壁纸使用 appearance-safe 的 Tonal surface，避免纯色铺满。Codex 主题保持用户当前 `appearanceTheme`，并使用高对比度配置。
- Windows Terminal 会为所有已发现 Profile 写入成对 Light/Dark Scheme、ANSI 颜色和 Tab 颜色，Profile 随 Windows 系统模式切换，窗口主题使用 `system`，不强制 Windows 深色模式。
- VS Code 和 TRAE 主题覆盖标准 Workbench、编辑器选择/光标、终端 ANSI、链接、通知和语义高亮字段，并启用应用自带的系统模式自动跟随；各自的 AI 专属面板仍由应用自行决定。
- Windows 开启“自动从背景中选取强调色”时，系统可能覆盖固定强调色；想保持稳定颜色，请在 Windows 设置中关闭该选项。
- Chrome 会生成 Manifest V3 本地主题的 Light/Dark 两个 canonical unpacked 目录；ZIP 是内部打包产物，需到 `chrome://extensions` 手动加载；普通本地 Skill 不能静默安装 Chrome 扩展。
- `.one-tone` 默认固定在 Skill 根目录下，与 Agent 当前工作目录无关；Target 路径仍通过用户目录、PATH、launcher 参数或环境变量探测，不依赖开发机盘符、Everything 或机器临时路径。仅测试或明确的高级用法可以覆盖运行时目录。

## 仓库结构

```text
.agents/plugins/marketplace.json                       # Marketplace manifest
plugins/                                                # Plugin envelopes
plugins/<plugin>/skills/<skill>/                       # Self-contained Skill packages
tests/plugins/<plugin>/skills/<skill>/runtime/         # Runtime tests matching distribution
tests/marketplace/                                     # Marketplace tests
docs/specs/                                            # Active development specs
docs/architecture.md                                   # Repository structure and seams
docs/testing.md                                        # Verification contract
CONTEXT.md                                             # Domain glossary
```

更多细节见 [领域上下文](CONTEXT.md)、[统一主题 Skill](plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md)、[Desktop zero Skill](plugins/ocd-desktop-zero/skills/desktop-zero/SKILL.md)、[Scoop toolchain Skill](plugins/ocd-scoop-toolchain/skills/scoop-toolchain/SKILL.md)、[目标矩阵](plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md) 和 [测试说明](docs/testing.md)。任务使用 GitHub Issues；Agent 协作配置见 docs/agents/。

## 开发说明

已确认的主题字段覆盖、浅深模式、相邻区域可区分性、版本能力和验收范围见 [主题字段覆盖与相邻区域可区分性开发说明](docs/specs/2026-07-25-theme-field-coverage-and-separation.md)。当前结构审计见 [架构说明](docs/architecture.md)。

工作站 Plugin 的已执行开发说明见 [OCD 工作站规范插件开发说明](docs/specs/2026-07-26-ocd-workstation-plugins.md)。

当前结构保留“根测试 harness + 可独立分发 Skill runtime”的边界；新增 docs/specs 作为主动开发说明目录，历史规划材料不作为当前架构入口。
