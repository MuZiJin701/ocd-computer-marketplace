---
name: scoop-toolchain
description: "预览、确认、安装并验证固定 D:\software\scoop 根目录下的 Python、Git、uv 和 Node.js 基础工具链。"
---

# Scoop toolchain

先 Preview，再由用户明确确认，Apply 只安装缺失工具，不卸载、重置或清理已有软件、项目、配置、凭据、缓存和 PATH。

Scoop 根目录严格为 `D:\software\scoop`。如果该根目录无法建立，不会偷偷使用 Scoop 默认用户目录。缺失工具优先 Scoop；Scoop 无法提供或安装失败时才可报告 winget fallback，并展示实际路径和“通常无法控制安装到 D:\software”的限制。工具启动仍通过 Windows 任务栏 Search。

严格提醒：只有愿意遵守这个标准的用户才应使用本 Skill。AI 时代仍需要计算机科学基础；Python、Git、uv 和 Node.js 是基础工具，不应把 AI 当作基础知识的替代品。不能接受这些边界时，请不要使用本 Skill。

```powershell
python .\scripts\run_scoop_toolchain.py preview
python .\scripts\run_scoop_toolchain.py apply <plan_id> --confirm
python .\scripts\run_scoop_toolchain.py verify <plan_id>
```

Preview 不创建 Scoop 根目录、不启动安装器；Apply 必须使用已有 Plan ID 并显式确认。
