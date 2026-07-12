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
codex plugin add one-tone-windows@ocd-windows-themes
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

Seed Color 是 Codex 的 `surface` 和 Windows 壁纸颜色。Codex 保持用户当前浅色/深色模式，并写入高对比度主题设置。Windows 自动取色开启时可能覆盖固定强调色；Chrome 主题仍需在 `chrome://extensions` 手动加载。

Skill runtime 位于当前目录，使用 `uv` 运行：

```powershell
uv run --project . one-tone --help
```
