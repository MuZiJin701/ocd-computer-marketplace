# ocd-desktop-zero

独立分发的 `desktop-zero` Skill：只处理当前用户的 Resolved desktop。

```powershell
python .\skills\desktop-zero\scripts\run_desktop_zero.py preview
python .\skills\desktop-zero\scripts\run_desktop_zero.py apply <plan_id> --confirm
python .\skills\desktop-zero\scripts\run_desktop_zero.py verify <plan_id>
python .\skills\desktop-zero\scripts\run_desktop_zero.py rollback <transaction_id>
```

快捷方式删除不可恢复；其他内容按确定性规则移动到 `D:\data`，移动记录仅在明确指定事务 ID 时用于回滚。
