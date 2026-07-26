# One-Tone 项目协作规则

## Agent skills

### Issue tracker

任务和需求记录在 GitHub Issues，使用 gh CLI 操作。详见 docs/agents/issue-tracker.md。

### Triage labels

使用默认的五个 triage 标签：needs-triage、needs-info、ready-for-agent、ready-for-human、wontfix。详见 docs/agents/triage-labels.md。

### Domain docs

这是 single-context 项目；开始探索前先读根目录 CONTEXT.md，再读相关 ADR。详见 docs/agents/domain.md。

## 项目目标

这是一个小型、可验证、可回滚的 Windows 主题统一工具。核心流程：

~~~text
Preview → Apply → Verify → Rollback
~~~

支持范围以 `zen-one-tone-windows` 的 Target 矩阵（`plugins/one-tone-windows/skills/unify-windows-theme/references/targets.md`）为准，不根据相似应用猜测兼容性。
当前平台范围包括 Windows 10 22H2+（build >= 19045）和 Windows 11 22H2+（build >= 22621）。

## 仓库结构

- plugins/：Marketplace 下的可安装 Plugin 包；当前 `zen-one-tone-windows` 是第一个 Plugin。
- plugins/one-tone-windows/skills/unify-windows-theme/：第一个 Plugin 中可独立分发的 Skill 包和唯一运行时项目。
- tests/：按 Marketplace → Plugin → Skill 组织的根仓库测试，不随 Skill 分发。
- docs/：架构、测试、Agent 协作配置和 ADR。
- 根目录 pyproject.toml：仅用于开发和测试，不安装运行时包。

Skill 不得依赖 Codex Plugin 元数据、仓库根目录、开发机绝对路径或固定盘符才能运行。

## 核心安全规则

- Preview 只生成 Plan，不修改系统或应用配置。
- Apply 只接受已有 plan_id，应用前必须校验 Plan Hash。
- 每个目标修改前必须 Snapshot。
- 目标失败时只回滚失败目标；其他成功目标保持修改。
- Apply 每个操作后必须持久化事务记录；补偿回滚失败必须报告 failed。
- 至少一个目标成功且其他目标失败或 skipped 时才报告 partial；没有成功目标时报告 failed。
- Verify 只读取当前配置并与 Plan 对比，不创建事务、不 Snapshot、不 Apply、不 Restart、不 Rollback。
- Rollback 必须接受明确的 transaction_id，只能恢复该事务自己的快照或产物元数据，并验证恢复结果。
- 只修改用户明确选择的目标，不猜测未知目标兼容性。
- Plan ID、Transaction ID 和 target 必须是安全路径组件；未知 target 可安全 skipped，但不得创建越界路径。
- Plan、事务和目标配置 JSON 使用同目录临时文件加原子替换，避免中断造成截断文件。
- 事务快照默认保留最近 5 个已完成事务；只清理工具生成的数据。
- Seed Color 原样作为 Palette/Codex 的 surface 和 Windows 壁纸颜色；Windows 强调色使用 Palette accent，默认不得修改用户浅/深色模式或 AutoColorization。
- Cursor 暂不属于用户可见支持目标；显式输入 cursor 必须安全 skipped，不得访问或修改 Cursor 文件。

## 当前实现边界

- Windows Terminal 已覆盖所有发现的 Profile：统一 Scheme、ANSI、光标和 Tab 字段；窗口主题使用 applicationTheme = system，不强制深色模式。
- VS Code/TRAE 已覆盖标准 Workbench 的选择、光标、终端 ANSI、链接、通知、诊断和语义高亮字段；TRAE 专属 AI 面板仍需真实应用验证。
- Chrome 使用 Manifest V3 本地主题，覆盖框架、工具栏、标签、书签页、NTP、链接和地址栏文字；激活仍由用户手动确认。
- 文字对比度目标为深层背景 7:1，surface/强调背景文字 4.5:1；视觉 accent 不直接作为文字色。
- Codex 保持独立 Adapter，不与 VS Code/TRAE Adapter 合并。

## 技术约束

- 使用 Python 和 uv。
- 核心保持精简，不引入数据库、后台服务、复杂状态机或插件运行时框架。
- Adapter 使用结构化 AdapterResult，不得只返回布尔值。
- 修改共享模块前先检查所有调用方；优先复用已有模块和依赖。
- 只实现当前需求，不预建未来抽象、兼容层或目录。

## 测试与交付

~~~powershell
uv run pytest
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
git diff --check
~~~

默认测试使用 fixture，不修改当前桌面或已安装应用。真实桌面测试必须单独标记并明确风险。修改后报告实际运行的验证命令和结果。

保留无关的已有修改；未经明确要求，不提交、推送、发送消息、修改权限或影响生产资源。

## 文档同步

支持范围、命令、状态、目录结构或验收标准变化时，同步检查并按需更新：

- README.md
- docs/architecture.md
- docs/testing.md
- CONTEXT.md
- 对应 Skill 的 SKILL.md 和 references/targets.md
