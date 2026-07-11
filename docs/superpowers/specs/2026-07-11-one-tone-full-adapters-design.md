# One-Tone 阶段 3–6 适配器设计

## 目标与范围

本阶段在已完成的 Palette、Plan、Transaction 和 CLI 核心之上，增加计划书阶段 3–6 的目标适配：

- Windows 10 22H2+ 与 Windows 11 22H2+ 普通深色模式。
- Windows 桌面壁纸：由 Palette 生成确定性的深色渐变 PNG，并支持 Snapshot、Apply、Verify、Rollback。
- Windows Terminal：使用当前实际配置文件，只修改当前默认 Profile。
- VS Code、Cursor、TRAE：共用主题/VSIX 生成器，但保持独立 Adapter、独立配置路径和独立结果。
- Codex：独立 Adapter；只有实际配置格式被检测并验证后才写入。
- Chrome：生成主题 ZIP，Apply 明确要求用户在 Chrome 中加载/确认。
- 八步验收命令：Detect、Snapshot、Apply、Verify、Restart、Verify Again、Rollback、Verify Restore。

不实现 Contrast Theme、JetBrains、Edge、Office 或其他未列入范围的目标。AI 专属面板不属于 VS Code Family 的强制控制面；无法通过标准主题字段控制时返回 `partial`。

## 环境事实与路径策略

当前用户环境由用户确认：Windows 11 家庭版中文版，25H2，操作系统版本 26200.8655；Windows Terminal、VS Code、Cursor、TRAE、Codex、Chrome 使用 Scoop 或已存在用户配置。

已验证的路径优先级如下：

- Windows Terminal：`D:\software\scoop\apps\windows-terminal\current\settings\settings.json`
- VS Code 程序：`D:\software\scoop\apps\vscode\current\bin\code.cmd`；数据目录跟随 `current\data` 链接到 Scoop persist 数据。
- Cursor 程序：`D:\software\scoop\apps\cursor\current\resources\app\bin\cursor.cmd`；数据目录跟随 `current\data` 链接到 Scoop persist 数据。
- TRAE 程序：`D:\software\scoop\apps\trae\current\IDE\bin\trae.cmd`，用户配置为 `%APPDATA%\TRAE\User`，扩展目录为 `%USERPROFILE%\.trae\extensions`。

Adapter 不硬编码单一机器路径；每个目标使用“显式配置 → Scoop current/data → 标准用户目录”的顺序解析，并在 `detect` 结果中记录实际使用路径。

## 版本检测

Windows 注册表的 `ProductName` 可能保留旧文本，因此不单独使用它判断版本：

- build `>= 22621` 视为 Windows 11 22H2+。
- build `>= 19045` 且 `< 22000` 视为 Windows 10 22H2+。
- 更低或无法读取时返回 `skipped`，消息包含检测到的版本信息。

版本检测只决定是否进入 Adapter Apply；它不修改任何配置。

## Adapter 合同扩展

原有五个方法继续保留，并增加验证八步所需的两个操作：

```python
class ThemeAdapter(Protocol):
    def detect(self) -> AdapterResult: ...
    def snapshot(self, backup_dir: Path) -> AdapterResult: ...
    def apply(self, plan: Plan) -> AdapterResult: ...
    def verify(self, plan: Plan) -> AdapterResult: ...
    def restart(self) -> AdapterResult: ...
    def verify_again(self, plan: Plan) -> AdapterResult: ...
    def rollback(self, backup_dir: Path) -> AdapterResult: ...
```

`AdapterResult` 保留原有字段，并增加兼容的可选字段：

```python
requires_user_action: bool = False
```

Chrome 使用此字段明确要求用户加载主题；旧 Adapter 的五参数构造仍然有效。

## Windows 与壁纸 Adapter

Windows Adapter 使用 `winreg` 读取和写入当前用户范围的普通深色模式值，至少覆盖 `AppsUseLightTheme` 和 `SystemUsesLightTheme`，不触碰 Contrast Theme。壁纸生成器只依赖标准库，使用 background、surface、accent 生成固定尺寸的 PNG 斜向渐变；不下载网络资源，也不调用 AI 服务。

Snapshot 保存：

- 修改前的 Personalize 注册表值。
- 当前壁纸路径。
- 当前壁纸文件的副本（文件存在时）。

Apply 先生成事务资产，再写入注册表并调用 `SystemParametersInfoW` 设置壁纸。Verify 重新读取注册表、当前壁纸路径和生成文件。Windows 主题变化即时生效时，`restart` 返回“not required”并记录原因；Rollback 只读取当前事务备份并再次验证恢复。

## Windows Terminal Adapter

Adapter 读取 settings JSON，解析 `profiles.default`：

1. 字符串值按 GUID 或名称查找 Profile。
2. 值为 `null` 时选择第一个没有 `source` 的本地 Profile，并在结果中明确记录这是默认回退规则。
3. 找不到 Profile 时返回 `skipped`，不修改 `profiles.defaults` 或其他 Profile。

只更新当前 Profile 的背景、前景、选择色以及与 Palette 对应的 ANSI 颜色。Snapshot 保存整个原始 settings JSON；Apply 使用临时文件替换；Verify 比较目标 Profile 的字段；Restart 和 Verify Again 由显式 `--restart-apps` 控制。

## VS Code Family Adapter

`vscode_family.py` 提供共享的主题 JSON/VSIX 生成逻辑和 `EditorSpec`，每个目标由独立 Adapter 实例配置：

- `vscode`：使用 Scoop 的 `code.cmd` 与 VS Code 数据目录。
- `cursor`：使用 Scoop 的 `cursor.cmd` 与 Cursor 数据目录。
- `trae`：使用 Scoop 的 `trae.cmd`、`%APPDATA%\TRAE\User` 和 `.trae\extensions`。

Apply 生成一次以 Plan ID 区分的 VSIX，调用目标 CLI 安装，再只修改该目标的 `workbench.colorTheme`。Snapshot 保存 settings JSON；Rollback 恢复 settings 并卸载本次生成的扩展。Verify 检查扩展存在、主题名称和工作台设置；AI 专属面板不纳入字段猜测，无法确认时返回 `partial`。

## Codex Adapter

Codex 不复用 VS Code Family。Adapter 只在以下条件同时满足时工作：

- Detect 找到 Codex 实际配置文件。
- 配置格式和主题字段通过 fixture 与真实文件结构检查。
- Snapshot 能保存原始内容并确定恢复方式。

如果当前 Codex 只有可执行文件但没有已验证主题配置，Adapter 返回 `skipped`，不根据文件名或 VS Code 兼容性猜测格式。这样仍完成独立 Adapter 合同和测试，但不虚报 Codex 支持。

## Chrome Adapter

Adapter 生成 Chrome 主题 manifest 和 ZIP 资源，颜色来自同一 Palette。Snapshot 保存当前 Preferences 中可读取的主题信息；Apply 保存资源并返回 `partial`、`requires_user_action=True`，消息包含用户需要在 Chrome 中执行的加载/确认步骤。Adapter 不直接篡改 Chrome Preferences，也不使用不稳定的调试启动参数。Rollback 删除本事务生成的资源并报告用户需要恢复 Chrome 原主题时的明确步骤。

## 事务与八步验收

普通 `apply` 仍只做 Detect、Snapshot、Apply、Verify；默认不关闭应用。传入 `--restart-apps` 才允许执行 Restart 和 Verify Again。

新增 `verify` 命令执行完整验收：

```text
Detect → Snapshot → Apply → Verify → Restart → Verify Again → Rollback → Verify Restore
```

事务记录保存每个操作的 AdapterResult，并保存目标级 `support_level`：`FULL`、`PARTIAL` 或 `SKIPPED`。

- 八步均成功、无用户操作要求、应用版本已记录：`FULL`。
- 功能完成但有用户操作、AI 面板限制、无法自动重启或其他明确限制：`PARTIAL`。
- 未安装、配置格式未验证、系统版本不支持或目标未检测到：`SKIPPED`。

失败时沿用现有自动回滚策略：恢复本事务已经修改的目标，并保留失败和回滚结果。Rollback 仍只能读取明确 transaction ID 的备份。

## CLI 与安全边界

新增目标映射和命令参数：

```powershell
uv run one-tone preview "#7C3AED" --targets windows,terminal,vscode,cursor,trae,codex,chrome
uv run one-tone apply plan-... --confirm
uv run one-tone verify plan-... --confirm --restart-apps
uv run one-tone rollback tx-...
```

`--restart-apps` 是显式高影响选项；没有它时不结束或启动用户进程。未知目标继续返回 `skipped`。所有真实 Apply/Restart/Chrome 用户操作测试前，先显示目标、配置路径和影响范围，避免误改未选择的目标。

## 测试策略

- Windows：用注册表和系统 API 的可注入后端测试版本判断、普通深色值、壁纸生成、Snapshot、恢复和 Verify；默认测试不改当前用户桌面。
- Terminal：使用真实 JSON fixture 覆盖 GUID 默认 Profile、`null` 默认 Profile、缺失 Profile、只修改选中 Profile 和回滚。
- VS Code Family：使用临时数据目录和假的 CLI 入口覆盖 VSIX 生成、安装记录、settings 修改和恢复；三目标分别验证路径解析。
- Codex：覆盖未验证配置返回 `skipped`，以及显式 fixture 配置的完整 Adapter 合同。
- Chrome：覆盖 manifest/ZIP 生成、原主题信息保存和 `requires_user_action` 结果。
- Transaction/CLI：覆盖八步操作记录、FULL/PARTIAL/SKIPPED、失败自动回滚、Plan Hash 拒绝和显式 restart 参数。

真实目标只有在当前环境实际执行八步并记录版本后，才能在输出或文档中标为 `FULL`；自动化 fixture 测试不能替代真实验收。
