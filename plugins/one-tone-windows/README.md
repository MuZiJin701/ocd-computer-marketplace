# one-tone-windows

这是 One-Tone 的第一个 Plugin 包，包含一个自包含、可独立安装的 Skill：`unify-windows-theme`。

## Skill 包

```text
skills/unify-windows-theme/
├─ SKILL.md
├─ pyproject.toml
├─ examples/
├─ src/one_tone/
├─ scripts/run_one_tone.py
└─ references/targets.md
```

推荐全局安装到所有兼容 Agent：

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

只安装给 Codex：

```powershell
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g -a codex
```

从仓库根目录安装本地 Skill：

```powershell
npx skills add .\plugins\one-tone-windows\skills\unify-windows-theme --agent codex
```

可选的 Codex Plugin Marketplace 安装：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/ocd-computer-marketplace.git
codex plugin add one-tone-windows@ocd-windows-themes
```

CC Switch 可直接添加仓库地址：

```text
https://github.com/MuZiJin701/ocd-computer-marketplace.git
```

从 GitHub 通过 Vercel Skills CLI 安装到 Codex：

```powershell
npx skills add https://github.com/MuZiJin701/ocd-computer-marketplace/tree/main/plugins/one-tone-windows/skills/unify-windows-theme --global --agent codex --copy --yes
```

通过 CC Switch 时，在 Skills → Repository Management 添加 `MuZiJin701/ocd-computer-marketplace`，Subdirectory 填 `plugins/one-tone-windows/skills`，刷新后安装 `unify-windows-theme` 到 Codex。

从仓库根目录运行 Skill runtime：

```powershell
uv run --project .\plugins\one-tone-windows\skills\unify-windows-theme one-tone --help
```

进入 Skill 目录后运行：

```powershell
cd .\plugins\one-tone-windows\skills\unify-windows-theme
uv run --project . one-tone --help
```

Codex Plugin 元数据位于 `.codex-plugin/plugin.json`；Python runtime 不依赖该元数据。

默认 Preview 会处理全部已实现目标；路径会根据 Windows 用户目录和 PATH 探测。Cursor 命中 `.cmd`/`.bat` launcher 时还会读取 `--user-data-dir` 与 `--extensions-dir`，Windows Terminal 会从 Store、Scoop shim 对应的 `persist` 目录和用户目录查找配置，Codex 会读取 `CODEX_HOME` 或用户 `.codex` 配置。不同安装方式可使用 `ONE_TONE_VSCODE_*`、`ONE_TONE_CURSOR_*`、`ONE_TONE_TRAE_*`、`ONE_TONE_TERMINAL_*` 或 `ONE_TONE_CHROME_PREFERENCES` 环境变量覆盖。Skill 不依赖 Everything，也不包含开发机绝对路径或临时路径。

Seed Color 是统一主题的 `surface`：Codex 的浅色/深色主题表都写入该原色，Windows 壁纸生成该原色的纯色 PNG。Windows 强调色使用 Palette `accent`；Apply 不修改用户的浅/深色模式和 `AutoColorization`。若自动取色开启，结果会提示用户手动关闭，否则 Windows 可能覆盖固定强调色。Cursor 的 VSIX 注册失败时会退回到 `workbench.colorCustomizations`。

Chrome 只生成本地主题包；普通 Chrome 安全模型不允许本 Skill 静默安装任意本地扩展或主题，用户仍需在 `chrome://extensions` 确认加载。

事务记录会在每个操作后持久化。VS Code 系列 Verify 和 Chrome 主题产物 Rollback 支持 Apply、Verify/Rollback 分属不同进程的场景。
