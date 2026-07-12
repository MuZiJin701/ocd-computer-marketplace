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

从仓库根目录安装本地 Skill：

```powershell
npx skills add .\plugins\one-tone-windows\skills\unify-windows-theme --agent codex
```

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
