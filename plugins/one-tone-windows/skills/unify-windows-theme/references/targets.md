# 支持目标

| 目标 | 范围 | 已知限制 |
| --- | --- | --- |
| `windows` | Windows 10/11 当前用户模式下的桌面壁纸、Start/Taskbar 和标题栏强调色 | 壁纸使用 Seed 原色，强调色使用 Palette `accent`；不修改浅/深色模式和自动取色；自动取色开启时报告 `partial` 并要求用户手动关闭；需要注册表和桌面后端，部分应用需要重启 |
| `terminal` | Windows Terminal 所有 Profile、Scheme、ANSI、光标、Tab、Tab Row 和窗口顶部区域 | `frame`/`unfocusedFrame` 需要较新的 Windows Terminal Preview；`applicationTheme` 保持 `system`；修改后可能需要重启 |
| `vscode` | VS Code 工作台、标题栏、侧边栏、Activity Bar、Tab、Panel、选择/光标、终端 ANSI、链接、诊断和语义高亮主题扩展 | AI 专属面板可能不受标准主题字段控制；Verify 会重新发现持久化扩展目录 |
| `trae` | TRAE 通用工作台、选择/光标、终端 ANSI、链接、诊断、语义高亮和主题扩展 | TRAE 专属 AI 界面可能不受标准主题字段控制；需重启后 Verify，Verify 会重新发现扩展目录 |
| `codex` | `config.toml` 的已验证 v1 主题字段；浅色和深色表使用同一 Seed 派生的 Tonal `surface` | `ink` 使用 `foreground`，`semanticColors.diffAdded`/`diffRemoved`/`skill` 使用对应的 `success_text`/`error_text`/`accent_text`；`accent` 仅用于强调背景和边框；修改后需要用户手动重启 |
| `chrome` | 生成 Manifest V3 Chrome Light/Dark 两个 canonical unpacked 主题目录，覆盖浏览器框架、工具栏、标签、书签页、NTP、链接和地址栏文字；ZIP 仅为内部打包产物 | Chrome 不支持本工具静默安装；用户需要在 `chrome://extensions` 手动加载和确认 |

Windows 10 支持 build `>= 19045`；Windows 11 支持 build `>= 22621`。

目标结果使用 `ok`、`partial`、`failed` 或 `skipped`，至少包含 `target`、`status`、`changed`、`verified` 和 `message`。Palette 的 `background_foreground` 对深层背景目标为 `>= 7:1`，主文字和强调文字对实际 `surface` 目标为 `>= 4.5:1`（理论最大值不足时取最大可得值）；Accent 和选区背景上的文字也使用 `>= 4.5:1`。Seed 本身不因对比度计算被暗化。所有语义文字字段必须使用对比度安全的 `*_text` 变体，不能直接复用视觉强调色。

`partial` 表示至少一个目标完成但存在失败、跳过或用户操作；若没有目标完成，或补偿回滚失败，则为 `failed`。目标名、Plan ID 和 Transaction ID 不得包含路径分隔符或 `..`。VS Code/TRAE 的路径可通过 `ONE_TONE_<TARGET>_EXECUTABLE`、`ONE_TONE_<TARGET>_SETTINGS`、`ONE_TONE_<TARGET>_EXTENSIONS` 覆盖；Windows Terminal 的 Store/Scoop 用户配置和 Codex 的 `CODEX_HOME` 配置也会自动探测。Skill 不要求 Everything，不使用固定盘符或开发机临时路径。

## 主题字段开发基线

下表是下一阶段实现和测试必须维护的 Field inventory 范围。每个字段必须生成并 Verify，或按实际版本记录为 unsupported。

| Target | 公开字段范围 | 模式/产物要求 |
| --- | --- | --- |
| windows | 壁纸、Accent Palette、Accent color、Taskbar accent display、标题栏、窗口边框、DWM afterglow；模式选择、自动取色和高对比度只读 | 不强制模式；保持用户策略；纯 Light Mode 的 Taskbar accent display 为 `not-applicable` |
| terminal | 完整 Scheme、ANSI、cursor、selection、Profile tabColor、Tab/Tab Row、frame/unfocusedFrame 和窗口主题字段 | light/dark 双 Scheme，theme 使用 system |
| vscode | 官方稳定 Workbench 颜色 ID：基础、编辑器、选择/光标、侧栏、Activity Bar、Tab、Panel、Input、List、Widget、Settings、Breadcrumb、通知、诊断、链接、语义和语法字段 | 一个安装包包含 Light/Dark 两套主题；设置使用扩展实际贡献的精确标签 |
| trae | VS Code 标准字段，加上安装版本中可发现且可验证的 TRAE 专属字段 | 一个安装包包含 Light/Dark 两套主题；设置使用精确标签；专属字段可 partial |
| codex | 已验证 v1 两套主题表的 surface、ink、accent、contrast 和 semanticColors 颜色字段 | 同一 Plan 同时更新 light/dark 表；保留未知键 |
| chrome | 完整公开 colors、tints、display_properties；包括 frame、toolbar、tabs、bookmark、NTP、omnibox、separator、button、incognito 等稳定字段 | 生成两个 canonical unpacked 目录；内部 ZIP 不作为额外用户选项，用户手动加载 |

相邻背景角色的目标为至少 1.2:1；边框、焦点、选区和强调控件相对邻近背景至少 3:1；文字继续使用 surface 4.5:1、deep background 7:1。字段清单不得把私有、实验或不可验证字段伪装成完整支持。
