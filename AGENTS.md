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
- VS Code、TRAE
- Codex（独立 Adapter）
- Chrome

当前实现目标以仓库 Skill 的目标矩阵为准；不要根据相似应用猜测兼容性。

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
- Apply 每个操作后必须持久化事务记录；补偿回滚失败必须报告 `failed`。
- 至少一个目标成功且其他目标失败或 skipped 时才报告 `partial`；没有成功目标时报告 `failed`。
- Verify 只读取当前配置并与 Plan 对比，不创建事务、不 Snapshot、不 Apply、不 Restart、不 Rollback。
- Rollback 必须接受明确的 `transaction_id`，只能恢复该事务自己的快照或产物元数据，并验证恢复结果。
- 只修改用户明确选择的目标，不猜测未知目标兼容性。
- Plan ID、Transaction ID 和 target 必须是安全路径组件；未知 target 仍可 `skipped`，但不得创建越界路径。
- Plan、事务和目标配置 JSON 使用同目录临时文件加原子替换，避免中断造成截断文件。
- 事务快照默认保留最近 5 个已完成事务；只清理工具生成的数据。
- 可分发 Skill 不得依赖开发机绝对路径、固定盘符或机器上的临时路径；运行期路径必须通过用户目录、PATH、launcher 参数或显式环境变量发现。
- Seed Color 原样作为 Palette/Codex 的 `surface` 和 Windows 壁纸颜色；Windows 强调色使用 Palette `accent`，默认不得修改用户浅/深色模式或 `AutoColorization`。
- Cursor 暂不属于用户可见支持目标；显式输入 `cursor` 必须安全 `skipped`，不得访问或修改 Cursor 文件。

## 当前实现结论（2026-07-17）

- Windows Terminal 已覆盖所有发现的 Profile：统一 Scheme、ANSI、光标和 Tab 字段；窗口主题使用 `applicationTheme = system`，不强制深色模式。黑色/亮黑色不再复用背景色。
- VS Code/TRAE 已补齐标准 Workbench 的选择、光标、终端 ANSI、链接、通知、诊断和语义高亮字段；TRAE 专属 AI 面板仍需真实应用验证，不能仅凭标准 VS Code 字段宣称完全覆盖。
- Chrome 本地主题使用 Manifest V3，并覆盖框架、工具栏、标签、书签页、NTP、链接和地址栏文字；激活仍必须由用户在 Chrome 中手动确认。
- 文字对比度目标为深层背景 `7:1`，surface/强调背景文字 `4.5:1`；颜色角色使用 `foreground`、`background_foreground`、`accent_text`、`success_text`、`warning_text`、`error_text` 及其实际背景配对，不把视觉 `accent` 直接当作文字色。
- 证据入口：`tests/runtime/one_tone/test_terminal_adapter.py`、`test_vscode_family.py`、`test_chrome_adapter.py`；完整验证命令为 `uv run pytest`。

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

修改完成后运行与风险相称的测试、CLI 冒烟和 `git diff --check`，报告实际结果。保留无关的已有修改；只有用户明确要求时才提交或推送远程仓库。

## 文档同步

支持范围、命令、状态、目录结构或验收标准变化时，同步更新：

- `README.md`
- `OCD_Windows_Theme_Skill_计划书.md`
- `docs/architecture.md`
- `docs/testing.md`
- 对应 Skill 的 `SKILL.md` 和 `references/targets.md`
