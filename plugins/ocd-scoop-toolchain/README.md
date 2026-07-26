# ocd-scoop-toolchain

独立分发的 `scoop-toolchain` Skill：检查并补齐 Python、Git、uv 和 Node.js。

```powershell
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py preview
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py apply <plan_id> --confirm
python .\skills\scoop-toolchain\scripts\run_scoop_toolchain.py verify <plan_id>
```

Scoop 根目录固定为 `D:\software\scoop`；已有安装、项目、配置、凭据和缓存保留。缺失工具优先通过 Scoop 安装，失败时才使用 winget，并报告实际路径和路径限制。执行前必须 Preview 并明确确认；该 Skill 不卸载或重置已有软件。
