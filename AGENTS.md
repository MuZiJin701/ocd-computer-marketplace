# One-Tone 项目协作规则

## 项目目标

这是一个小型、可验证、可回滚的 Windows 主题统一工具。核心流程：

```text
Preview → Apply → Verify → Rollback
```

## 支持范围

- Windows 10 22H2+（build >= 19045）
- Windows 11 22H2+（build >= 22621）
- Windows Terminal
- VS Code、Cursor、TRAE
- Codex（独立 Adapter）
- Chrome

不支持 JetBrains、Edge、Office、Contrast Theme 和其他未验证目标。

## 包结构

- 根目录是 Plugin Marketplace 和统一测试入口。
- `plugins/<name>/` 是可选 Codex Plugin 包。
- `plugins/<name>/skills/<skill>/` 是可独立分发的 Skill 包和 runtime。
- Skill 不得依赖 Codex Plugin 元数据或仓库根目录才能运行。

## 核心安全规则

- Preview 只生成 Plan，不修改系统或应用配置。
- Apply 只接受已有 `plan_id`，应用前必须校验 Plan Hash。
- 每个目标修改前必须 Snapshot。
- 目标失败时只回滚失败目标；其他成功目标保持修改。
- Apply 失败结果必须保留清晰的 `partial` 或 `failed` 信息。
- Verify 只读取当前配置并与 Plan 对比，不创建事务、不 Snapshot、不 Apply、不 Restart、不 Rollback。
- Rollback 必须接受明确的 `transaction_id`，只能恢复该事务自己的快照，并验证恢复结果。
- 只修改用户明确选择的目标，不猜测未知目标兼容性。
- 事务快照默认保留最近 5 个已完成事务；只清理工具生成的数据。

## 技术约束

- 使用 Python 和 `uv`。
- 核心保持精简，不引入数据库、后台服务、复杂状态机或插件运行时框架。
- Adapter 使用结构化 `AdapterResult`，不得只返回布尔值。
- Codex 必须保持独立 Adapter。

## 测试与交付

```powershell
uv run pytest
```

测试放在仓库根目录，最终 Plugin/Skill 分发包不包含测试。默认测试使用 fixture；真实桌面测试必须单独标记并明确风险。

修改完成后运行与风险相称的测试、CLI 冒烟和 `git diff --check`，报告实际结果。保留无关的已有修改，不主动推送远程仓库。

## 文档同步

支持范围、命令、状态、目录结构或验收标准变化时，同步更新：

- `README.md`
- `OCD_Windows_Theme_Skill_计划书.md`
- `docs/architecture.md`
- `docs/testing.md`
- 对应 Skill 的 `SKILL.md` 和 `references/targets.md`
