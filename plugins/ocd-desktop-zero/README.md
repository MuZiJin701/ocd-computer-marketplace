# zen-desktop-zero

独立分发的 `zen-desktop-zero` Skill：只处理当前用户的 Resolved desktop，不处理 Public Desktop 或其他用户桌面。

```powershell
python .\skills\desktop-zero\scripts\run_desktop_zero.py preview
python .\skills\desktop-zero\scripts\run_desktop_zero.py apply <plan_id> --confirm
python .\skills\desktop-zero\scripts\run_desktop_zero.py verify <plan_id>
python .\skills\desktop-zero\scripts\run_desktop_zero.py rollback <transaction_id>
```

快捷方式删除不可恢复；其他内容按确定性规则移动到 `D:\data`，移动记录仅在明确指定事务 ID 时用于回滚。

分类目录固定为：`文档`、`图片`、`视频`、`音频`、`压缩包`、`安装包`、`代码` 和 `未分类`。执行前必须 Preview 并明确确认；锁定项失败时保留原位并报告。软件启动入口约定为 Windows 任务栏 Search，Skill 不安装后台监控。
