# Zen Computer Marketplace

面向极简、有序电脑使用场景的跨 Agent Skill 市场。

当前提供三个独立 Plugin：`zen-one-tone-windows` 统一 Windows 主题，`zen-desktop-zero` 整理当前用户桌面，`zen-scoop-toolchain` 检查并补齐基础开发工具链。

One-Tone 支持 Windows 10 22H2+（build `>= 19045`）和 Windows 11 22H2+（build `>= 22621`）；Cursor 暂不在主题支持列表中。两个工作站 Plugin 也面向 Windows，并要求可用且可写的 D 盘，不会自动换用其他盘符。

## 安装

推荐使用 Vercel Labs Skills CLI 全局安装，让其他兼容 Agent 也能复用：

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/zen-computer-marketplace.git -g
```

只安装到 Codex：

```powershell
skills add https://github.com/MuZiJin701/zen-computer-marketplace.git -g -a codex
```

不安装 CLI 时：

```powershell
npx skills add https://github.com/MuZiJin701/zen-computer-marketplace.git -g
```

管理 Skill：

```powershell
skills list
skills update zen-one-tone-windows
skills update zen-desktop-zero
skills update zen-scoop-toolchain
skills remove zen-one-tone-windows
skills remove zen-desktop-zero
skills remove zen-scoop-toolchain
```

安装后重启 Codex。Skills CLI 的 Codex 全局目录是 `~/.codex/skills/`。

可选：Codex Plugin Marketplace：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/zen-computer-marketplace.git
codex plugin add zen-one-tone-windows@zen-computer-marketplace
codex plugin add zen-desktop-zero@zen-computer-marketplace
codex plugin add zen-scoop-toolchain@zen-computer-marketplace
```

可选：CC Switch。在 Skills 页面添加以下仓库地址，刷新后选择 `zen-one-tone-windows`、`zen-desktop-zero` 或 `zen-scoop-toolchain`：

```text
https://github.com/MuZiJin701/zen-computer-marketplace.git
```

可安装的 Plugin 包括 `zen-one-tone-windows`、`zen-desktop-zero` 和 `zen-scoop-toolchain`。

## 使用

直接告诉 Agent 你要做什么。每个 Skill 都会先预览，再等你确认。

### 统一 Windows 主题

```text
使用 $zen-one-tone-windows，把我的电脑主题统一为翠绿色 #10B981。先预览，不要立即应用。
```

### 整理桌面

```text
使用 $zen-desktop-zero，预览并整理当前用户桌面。删除快捷方式，把其他内容分类移动到 D:\data。先不要执行。
```

快捷方式会直接删除，无法恢复。其他文件和文件夹可以按明确的 Transaction ID 回滚。软件启动入口约定为 Windows 任务栏 Search；这个 Skill 不安装后台监控。

### 配置基础工具链

```text
使用 $zen-scoop-toolchain，检查 Python、Git、uv 和 Node.js。缺失项优先通过 Scoop 安装到 D:\software\scoop，先预览，不要安装。
```

已有软件不会被卸载或重置。Scoop 无法提供时，Skill 才会建议使用 winget；winget 通常无法指定安装路径。

### 执行规则

- 先 Preview，再确认执行
- Preview 不修改电脑
- Apply 只执行已有且已确认的 Plan
- Verify（verify）只检查结果
- 结果会说明 `ok`、`partial`、`failed` 或 `skipped`

## 注意事项

- Seed Color 作为 Codex 和 Windows 的 Theme anchor/Accent source；大面积 Codex Surface 和 Windows 壁纸使用 appearance-safe 的 Tonal surface，避免纯色铺满。Codex 主题保持用户当前 `appearanceTheme`，并使用高对比度配置。
- Windows Terminal 会为所有已发现 Profile 写入成对 Light/Dark Scheme、ANSI 颜色和 Tab 颜色，Profile 随 Windows 系统模式切换，窗口主题使用 `system`，不强制 Windows 深色模式。
- VS Code 和 TRAE 主题覆盖标准 Workbench、编辑器选择/光标、终端 ANSI、链接、通知和语义高亮字段，并启用应用自带的系统模式自动跟随；各自的 AI 专属面板仍由应用自行决定。
- Windows 开启“自动从背景中选取强调色”时，系统可能覆盖固定强调色；想保持稳定颜色，请在 Windows 设置中关闭该选项。
- Chrome 会生成 Manifest V3 本地主题的 Light/Dark 两个 canonical unpacked 目录；ZIP 是内部打包产物，需到 `chrome://extensions` 手动加载；普通本地 Skill 不能静默安装 Chrome 扩展。
- `.one-tone` 默认固定在 Skill 根目录下，与 Agent 当前工作目录无关；Target 路径仍通过用户目录、PATH、launcher 参数或环境变量探测，不依赖开发机盘符、Everything 或机器临时路径。仅测试或明确的高级用法可以覆盖运行时目录。

## 仓库结构

```text
.
├─ .agents/plugins/marketplace.json       # Marketplace 清单
├─ plugins/                               # 可安装的 Plugin
│  ├─ zen-one-tone-windows/               # zen-one-tone-windows Plugin
│  │  └─ skills/zen-one-tone-windows/     # zen-one-tone-windows Skill 与 runtime
│  ├─ zen-desktop-zero/                   # zen-desktop-zero Plugin
│  │  └─ skills/zen-desktop-zero/         # zen-desktop-zero Skill 与 runtime
│  └─ zen-scoop-toolchain/                # zen-scoop-toolchain Plugin
│     └─ skills/zen-scoop-toolchain/      # zen-scoop-toolchain Skill 与 runtime
├─ tests/                                 # Marketplace、Plugin、Skill 测试
├─ docs/                                  # 架构、测试、ADR 和开发说明
└─ CONTEXT.md                             # 项目领域词汇
```

更多细节见 [领域上下文](CONTEXT.md)、[zen-one-tone-windows Skill](plugins/zen-one-tone-windows/skills/zen-one-tone-windows/SKILL.md)、[zen-desktop-zero Skill](plugins/zen-desktop-zero/skills/zen-desktop-zero/SKILL.md)、[zen-scoop-toolchain Skill](plugins/zen-scoop-toolchain/skills/zen-scoop-toolchain/SKILL.md)、[目标矩阵](plugins/zen-one-tone-windows/skills/zen-one-tone-windows/references/targets.md) 和 [测试说明](docs/testing.md)。任务使用 GitHub Issues；Agent 协作配置见 docs/agents/。

## 开发说明

已确认的主题字段覆盖、浅深模式、相邻区域可区分性、版本能力和验收范围见 [主题字段覆盖与相邻区域可区分性开发说明](docs/specs/2026-07-25-theme-field-coverage-and-separation.md)。当前结构审计见 [架构说明](docs/architecture.md)。

工作站 Plugin 的已执行开发说明见 [Zen 工作站规范插件开发说明](docs/specs/2026-07-26-zen-workstation-plugins.md)。

当前结构保留“根测试 harness + 可独立分发 Skill runtime”的边界；新增 docs/specs 作为主动开发说明目录，历史规划材料不作为当前架构入口。

维护者验证 One-Tone 的流程是：`preview '#10B981'` → `apply plan-... --confirm` → `verify plan-...` → `rollback tx-...`。Skill 目录内的入口示例是 `python .\scripts\run_one_tone.py preview '#10B981'`。
