---
name: desktop-zero
description: "预览、确认、执行、验证并按 Cleanup transaction ID 回滚当前用户桌面的 Desktop zero 整理。"
---

# Desktop zero

这是一个严格的桌面规范 Skill，只处理当前登录用户的 **Resolved desktop**，不处理 Public Desktop、其他用户桌面或任意手写路径。

先 Preview，再由用户明确确认，最后 Apply 和 Verify。快捷方式（`.lnk`、`.url`、`.website`、`.scf`、`.pif`）会在确认后直接删除，**不可恢复**；其他文件和文件夹按扩展名确定性移动到 `D:\data`，移动记录仅用于用户明确指定 Cleanup transaction ID 时回滚。

桌面启动软件的规定入口是 Windows 任务栏 Search。这个 Skill 不安装后台服务、不阻止其他启动方式。

严格提醒：只有愿意遵守这个桌面标准的用户才应使用本 Skill。AI 时代仍需要计算机科学基础；Python、Git、uv 和 Node.js 应优先通过 Scoop 安装，Scoop 不可用时才考虑 winget，但 winget 通常无法控制安装到 `D:\software` 的路径。不能接受这些边界时，请不要使用本 Skill。

```powershell
python .\scripts\run_desktop_zero.py preview
python .\scripts\run_desktop_zero.py apply <plan_id> --confirm
python .\scripts\run_desktop_zero.py verify <plan_id>
python .\scripts\run_desktop_zero.py rollback <transaction_id>
```

Preview 不删除、移动、创建目录、提权、终止进程或安装软件；Apply 只接受已有 Plan ID；Rollback 必须提供明确的 Cleanup transaction ID，且不恢复已删除快捷方式。
