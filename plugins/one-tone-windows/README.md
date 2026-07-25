# one-tone-windows

提供可独立分发的 `unify-windows-theme` Skill，用一个 Seed Color 统一 Windows 桌面、Windows Terminal、VS Code、TRAE、Codex 和 Chrome 本地主题。Cursor 暂不属于当前支持目标。

## 安装

```powershell
npm install -g skills
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g
```

只安装到 Codex：

```powershell
skills add https://github.com/MuZiJin701/ocd-computer-marketplace.git -g -a codex
```

可选的 Codex Plugin Marketplace：

```powershell
codex plugin marketplace add https://github.com/MuZiJin701/ocd-computer-marketplace.git
codex plugin add one-tone-windows@ocd-computer-marketplace
```

CC Switch：在 Skills 页面添加

```text
https://github.com/MuZiJin701/ocd-computer-marketplace.git
```

然后安装 `unify-windows-theme`。

## 命令

```powershell
python .\scripts\run_one_tone.py preview '#10B981'
python .\scripts\run_one_tone.py apply plan-... --confirm
python .\scripts\run_one_tone.py verify plan-...
python .\scripts\run_one_tone.py rollback tx-...
```

Seed Color 是 Codex 和 Windows 的 Theme anchor/Accent source；Codex 的 `surface` 与 Windows 壁纸使用同一 Seed 派生的 Tonal surface。Codex 保持用户当前浅色/深色模式，并写入高对比度主题设置。Windows 自动取色开启时可能覆盖固定强调色；Chrome 主题仍需在 `chrome://extensions` 手动加载。

Skill runtime 位于当前目录，使用 `uv` 运行：

```powershell
uv run --project . one-tone --help
```

## 开发边界

主题字段扩展的正式开发说明位于仓库的 docs/specs。它要求覆盖 Windows、Windows Terminal、VS Code、TRAE、Codex 和 Chrome 的公开颜色字段，并记录模式、版本能力和相邻区域可区分性；本 Skill 仍保持独立 runtime，不依赖仓库根目录。
