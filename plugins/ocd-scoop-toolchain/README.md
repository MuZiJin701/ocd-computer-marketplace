# ocd-scoop-toolchain

独立分发的 `scoop-toolchain` Skill：检查并补齐 Python、Git、uv 和 Node.js。

```powershell
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py preview
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py apply <plan_id> --confirm
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py verify <plan_id>
```

Scoop 根目录固定为 `D:\software\scoop`；已有安装保留，winget fallback 必须报告实际路径和路径限制。
