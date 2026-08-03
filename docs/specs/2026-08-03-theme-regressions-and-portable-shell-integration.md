# Theme regression fixes and portable Shell integration

## Status

ready-for-agent

## Problem Statement

真实桌面验证发现三个用户可见问题，当前 fixture 和字段契约没有完整覆盖：

1. TRAE 的 Light 主题中，资源管理器里的 Git 状态装饰色（例如未跟踪文件名、`U` 标记和状态点）与绿色调的侧栏背景过于接近。普通 `sideBar.foreground` 已经改善，但公开的 `gitDecoration.*` 字段没有进入主题字段清单，因而继续使用 Target 默认颜色。
2. Windows Terminal 中，命令输入后的行内预测文字由 PowerShell/PSReadLine 渲染。默认的浅灰、弱化预测色在生成的 Light Terminal surface 上不够清晰，容易与已输入命令混淆。该颜色不是 Windows Terminal Scheme 的普通 `foreground`。
3. Windows 任务栏在 Light → Dark → Light 的模式切换后可能不再显示 Accent。当前 Windows Adapter 只在 Dark Plan 中写入 Taskbar accent display，也没有覆盖模式往返后的字段 Verify。用户要求两种模式都使用同一个 Seed-derived Accent，并且不因为切换模式丢失任务栏颜色。

本开发说明要求修复这些回归，同时保持插件的泛化性、可移植性、易分发性和既有 Preview → Apply → Verify → Rollback 安全契约。

## Solution

沿用现有 Palette、Field inventory 和 Target Adapter seams：

- 将公开且可验证的 TRAE/VS Code Git 装饰字段加入现有 Field inventory 和 Field Evidence Matrix，使用现有语义文字角色生成 Light/Dark 映射。
- 将 PSReadLine 预测文字作为 `terminal` Target 的可选子能力，不新增顶层 `powershell` Target。Preview 发现可用 PowerShell、Profile、PSReadLine 版本和公开颜色字段；Apply 只管理 Windows Terminal 会话中的预测颜色；Verify 和 Rollback 检查并恢复 Profile 受管区块。
- 将 `InlinePrediction` 和列表预测颜色作为独立的 Shell/PSReadLine Color field，不复用 Terminal 普通正文色。预测颜色来自 Plan Palette 的现有角色，并按实际 Terminal surface 验证。
- Windows Adapter 在 Light/Dark 两种 Plan 模式下都尝试应用并 Verify 同一个 `StartTaskbarColorPrevalence` 与 Seed-derived Accent；不修改系统模式、自动取色或高对比度设置，不创建后台 watcher。若 Windows 版本仍拒绝在 Light 模式显示任务栏 Accent，必须报告真实的 `partial`/`unsupported` 能力状态。

## User Stories

1. As a TRAE user, I want untracked files and Git status markers to remain readable on the Light sidebar, so that repository state is not hidden by the themed background.
2. As a TRAE user, I want added, modified, renamed, staged, deleted, ignored, conflicting and submodule states to remain visually distinct, so that I can understand repository state quickly.
3. As a VS Code-family user, I want the same public Git decoration coverage in VS Code and TRAE, so that the shared Workbench behavior does not diverge without evidence.
4. As a TRAE user, I want ordinary file labels to keep the primary foreground role, so that Git decoration fixes do not recolor all Explorer text.
5. As a user, I want Git decoration colors to be checked against their actual adjacent background, so that a numeric check on the wrong surface cannot pass a visually weak mapping.
6. As a Windows Terminal user, I want inline PowerShell predictions to be visibly different from text I have already typed, so that I can tell suggestion from command input.
7. As a Windows Terminal user, I want inline predictions to remain readable in both Light and Dark modes, so that prediction is useful regardless of system appearance.
8. As a Windows Terminal user, I want list-view prediction labels and selected predictions to have their own readable colors, so that changing prediction view style does not reintroduce the same ambiguity.
9. As a Windows Terminal user, I want PSReadLine prediction colors to be changed only in Windows Terminal sessions, so that VS Code terminals and standalone PowerShell sessions keep their own preferences.
10. As a user on an older PowerShell or PSReadLine version, I want unsupported prediction fields reported clearly, so that the tool does not write settings that the host cannot understand.
11. As a user, I want the tool to discover PowerShell Profile locations from the host rather than assuming a user name, drive or installation layout, so that the Skill remains portable.
12. As a user, I want existing Profile content preserved byte-for-byte outside the managed integration, so that enabling prediction colors does not overwrite my shell customizations.
13. As a user, I want PSReadLine Profile changes to have Snapshot, Verify and Rollback behavior, so that a failed or unwanted shell customization is reversible.
14. As a Windows user, I want the same Seed-derived Accent to remain the taskbar Accent in both Light and Dark modes, so that switching appearance does not remove the theme identity.
15. As a Windows user, I want taskbar Accent display to be attempted in Light mode as well as Dark mode, so that the tool does not intentionally drop the color on a mode transition.
16. As a Windows user, I want Light → Dark → Light mode changes to be included in real verification, so that Apply success is not mistaken for mode-switch recovery.
17. As a Windows user on a build that ignores Light-mode taskbar Accent display, I want a truthful partial or unsupported result, so that the tool does not claim a visual state Windows did not produce.
18. As a user, I want system mode, automatic accent selection and high contrast settings preserved, so that the fix does not override accessibility or personal preferences.
19. As a maintainer, I want Git decoration and PSReadLine fields to extend the existing Field inventory, so that reports, tests and documentation use one source of truth.
20. As a maintainer, I want no concrete user path, installed version, machine color or temporary directory embedded in the implementation, so that the Skill can be distributed to other Windows users.
21. As a maintainer, I want capability discovery to happen during Preview and the resolved inputs to remain stable through Apply and Verify, so that later operations do not silently switch hosts or Profiles.
22. As a maintainer, I want Terminal settings and PSReadLine Profile operations to remain under the existing `terminal` Target transaction, so that users do not need to learn a new top-level target.
23. As a maintainer, I want a failure in optional PSReadLine integration to leave successful Windows Terminal Scheme changes intact while reporting `partial`, so that one unsupported shell does not undo an independent target operation.
24. As a maintainer, I want fixture tests and real screenshot gates separated, so that deterministic tests prove field contracts without pretending to prove native rendering.
25. As a maintainer, I want the existing Light readability acceptance for all six Targets to remain in force, so that these focused fixes do not narrow the broader visual quality bar.

## Implementation Decisions

- The shared Palette remains the highest color-generation Seam. No machine-specific colors are added. Existing `success_text`, `warning_text`, `error_text`, `accent_text`, `muted_foreground`, `selection_foreground` and `selection_background` roles are reused first.
- The existing Field inventory remains the only structured field registry. Add evidence metadata for Git decorations and PSReadLine prediction fields, including Mode, visual region, text class, paired background role, opacity policy, public source and version baseline.
- TRAE and VS Code-family adapters map public `gitDecoration.*` fields as follows: added/untracked/staged to `success_text`; modified to `warning_text`; renamed/submodule to `accent_text`; deleted/conflicting to `error_text`; ignored/inactive to `muted_foreground`.
- Git decoration fields are semantic state text, not Dense primary text. They must remain opaque and meet the applicable state-text contrast target against their actual background; they must not alter ordinary `sideBar.foreground`.
- PSReadLine is an optional `terminal` sub-capability. It is not a new top-level Target and does not change the default target list.
- Preview discovers PowerShell hosts, their Profile paths, PSReadLine availability/version and supported public prediction color fields through the host. It persists the resolved inputs in the Plan so Apply and Verify do not rediscover a different Profile.
- Apply manages a clearly delimited Profile integration that is guarded by the standard Windows Terminal session marker. It preserves all unrelated Profile content and uses the existing atomic persistence and per-Target transaction rules.
- `InlinePrediction` and `ListPrediction` use the Palette's secondary text role after actual-background validation. `ListPredictionSelected` uses the Palette selection foreground/background pair. The implementation emits host-supported ANSI or console color representations without hardcoding a machine-specific color.
- Prediction source and key bindings are not changed. The change covers prediction rendering colors only.
- PSReadLine versions or hosts without the required public fields remain unchanged and report `unsupported` or `partial`; unknown Profile syntax and undocumented prediction settings are not guessed.
- Windows applies the same Plan Accent to the taskbar in both Light and Dark modes by attempting `StartTaskbarColorPrevalence=1` together with the existing Accent fields. It does not maintain two independent taskbar Accent values.
- Windows Apply and Verify do not toggle system mode, automatic colorization, high contrast or a background service. Mode-cycle verification is a separate real-desktop gate.
- If the operating system ignores taskbar Accent display in Light mode, the Adapter reports the observed capability instead of treating a registry write as visual proof. This preserves the distinction between Accent color and Taskbar accent display.
- Optional PSReadLine failure is local to the `terminal` Target. Windows Terminal Scheme success remains applied when safe; aggregate status follows the existing `ok`/`partial`/`failed` rules.
- No second Field inventory, theme framework, database, watcher, fixed drive, user-specific path or new runtime service is introduced.

## Testing Decisions

- Tests assert external behavior at the highest available Seam: generated Palette/Plan data, Field inventory reports, theme artifacts, discovered Profile metadata, persisted Profile content, registry values and structured AdapterResult capability status.
- Field inventory tests verify all public Git decoration fields, their state classification, role mapping, paired background and evidence metadata. They fail if a Git decoration is silently treated as ordinary foreground or copied from a reference theme.
- VS Code-family artifact tests verify Light/Dark `gitDecoration.*` mappings for both VS Code and TRAE, while preserving unknown theme fields and ordinary Explorer foreground behavior.
- PSReadLine discovery tests use fake PowerShell host outputs and multiple Profile layouts. They cover portable/standard discovery, unsupported PSReadLine versions, missing fields, existing user content, managed-block idempotence, WT-session guarding and Plan-persisted resolved inputs.
- PSReadLine transaction tests verify Snapshot, atomic Apply, field-level Verify, preservation of unrelated Profile content, local rollback and `partial` results when the optional sub-capability is unavailable.
- Terminal artifact tests continue to verify Scheme, ANSI, cursor, selection, Tab, Tab Row and system-following fields. They additionally verify that PSReadLine prediction colors are not confused with Terminal `foreground` or ANSI semantic colors.
- Windows fixture tests verify that Light and Dark Apply both attempt and Verify `StartTaskbarColorPrevalence=1`, preserve system-mode and automatic-colorization fields, and report observed unsupported behavior without claiming visual success.
- A real Windows acceptance pass covers Apply in Light mode, Dark → Light and Light → Dark transitions, taskbar display, post-transition Verify and rollback. No watcher or re-Apply is used during the mode-cycle test.
- Real screenshot gates cover TRAE Git decorations, Windows Terminal inline/list predictions and Windows taskbar behavior for representative Seeds `#10B981` and `#FFD700`. Fixture success is not sufficient for native visual acceptance.
- Existing six-Target Light readability, contrast, mode coherence and safety tests remain required. No new test framework or runtime service is introduced.
- Documentation-only validation is `git diff --check`; runtime implementation additionally runs the repository's standard pytest and CLI checks.

## Out of Scope

- Modifying fonts, font weight, layout, spacing, anti-aliasing, rendering engines or accessibility settings.
- Changing PowerShell prediction source, installing prediction plugins or changing PSReadLine key bindings.
- Modifying PowerShell sessions outside Windows Terminal, except for preserving their shared Profile content.
- Adding a top-level `powershell` Target or changing the default target list.
- Guessing undocumented TRAE AI-panel or private Git decoration fields.
- Copying concrete colors from installed themes or using machine-specific colors, paths or versions.
- Adding a background watcher, scheduled task or service to react to mode changes.
- Forcing Windows system mode, disabling automatic accent selection, changing high contrast or using unsupported shell hacks as proof of taskbar support.
- Automatically activating Chrome themes or changing unrelated Target behavior.

## Further Notes

- The confirmed domain distinction is: Git decoration is semantic state text; inline prediction is Shell/PSReadLine text; neither is ordinary Dense primary text.
- The Windows taskbar requirement is intentionally stronger than the current `not-applicable` Light-mode rule. The implementation must attempt the requested state and report native limitations honestly; the Field Evidence Matrix must distinguish requested, applied and visually verified states.
- The new capability changes a Target boundary and Profile persistence behavior, so the durable rationale is recorded in ADR 0009.
