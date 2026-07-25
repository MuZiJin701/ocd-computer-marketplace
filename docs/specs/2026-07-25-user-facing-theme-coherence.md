# 用户可理解的主题统一与字段证据开发说明

## Problem Statement

用户希望用自己选择的 Seed Color 统一 Windows、Windows Terminal、VS Code、TRAE、Codex 和 Chrome，而不是让 Windows 系统的浅色/深色设置决定主题颜色。当前实现和产物把几个不同概念混在一起：

- Mode Palette 与 Windows 系统模式边界不清楚；
- Windows Accent color 与 Taskbar accent display 被当作同一个能力；
- VS Code/TRAЕ 扩展注册成功后，主题不一定成为当前活动主题；
- Chrome 同时产生 Light/Dark、目录、ZIP 和兼容别名，用户不知道应该加载哪个；
- 技术字段清单没有统一的官方来源、版本基线和人类可读解释。

这会导致主题看起来不一致、任务栏可能保持黑色、编辑器需要手动选择主题、Chrome 出现重复选项，以及 Preview/Verify 无法准确说明哪些字段真正生效。

## Solution

建立以 Seed Color 为唯一视觉来源、以 Mode 为呈现变体、以 Target 能力为边界的统一模型：

- 同一 Seed Color 同时生成 Light 和 Dark 两套 Palette；Mode 不等于 Windows 系统模式；
- Palette 使用 Appearance-safe 规则：Seed Color 是 Theme anchor/Accent source，大面积区域使用低饱和 Tonal surface，并通过 OKLCH/OKLab 风格控制与 WCAG 验证共同保证舒适度和可读性；
- 不修改 Windows 系统模式、自动取色或高对比度设置；
- Windows 将 Accent color 与 Taskbar accent display 分开报告；
- VS Code/TRAЕ 使用扩展实际贡献的 Light/Dark 主题名完成注册和激活；
- Chrome 只向用户暴露两个 canonical unpacked 主题目录；
- 所有 `.one-tone` 运行时数据固定在 Skill-local runtime root 下，不随 Agent 当前工作目录变化；
- 每个 Target 使用有官方证据的版本化 Field inventory；
- Preview 和 Verify 按视觉区域展示结果，技术字段和来源作为可展开详情。

最高测试 seam 是 `Plan → Adapter 产物或持久化设置 → Verify 状态`。实现应复用现有 Adapter、Transaction 和 field capability 机制，不新增服务、数据库或运行时抽象。

## User Stories

1. As a Windows 用户, I want Seed Color to remain the single visual source, so that my chosen color is consistent across all Targets.
2. As a Windows 用户, I want Light and Dark to be presentation variants of the same Seed Color, so that changing Mode does not change the theme identity.
3. As a Windows 用户, I want the tool to leave my Windows system mode unchanged, so that my personal and accessibility preferences are preserved.
4. As a Windows 用户, I want Preview to distinguish the selected Mode from the current Windows system mode, so that I understand why some system surfaces may render differently.
5. As a Windows 用户, I want Accent color and Taskbar accent display reported separately, so that a taskbar limitation does not hide a successful accent-color change.
6. As a Windows 用户, I want a pure Light-mode taskbar limitation reported as `not-applicable` or `partial`, so that the result explains the platform rule instead of claiming the entire Target failed.
7. As a Windows 用户, I want automatic accent selection and high-contrast settings preserved, so that Windows does not overwrite my preferences silently.
8. As a VS Code 用户, I want the generated extension to be registered and activated automatically, so that I do not need to open the theme picker after Apply.
9. As a TRAE 用户, I want the same automatic registration and activation behavior as VS Code for the shared theme fields, so that the common editor UI is immediately themed.
10. As an editor user, I want Light and Dark settings to refer to the exact labels contributed by the extension, so that activation cannot target a non-existent base label.
11. As an editor user, I want my existing automatic color-scheme preference preserved, so that the tool does not silently force or disable system-based theme switching.
12. As a Chrome 用户, I want exactly one canonical Light directory and one canonical Dark directory, so that I know which two choices are real themes.
13. As a Chrome 用户, I want ZIP files and rollback copies hidden from the installation instructions, so that packaging details do not look like duplicate themes.
14. As a Chrome 用户, I want the installation instructions to point to the unpacked directory required by Chrome, so that manual activation is straightforward.
15. As a maintainer, I want every Target field tied to an official source and version baseline, so that field coverage is reviewable and reproducible.
16. As a maintainer, I want fields without a stable public schema excluded from guessed mappings, so that private implementation details cannot become false guarantees.
17. As a TRAE maintainer, I want TRAE-specific fields included only when discovered and verified from the installed version or public theme data, so that unsupported AI surfaces remain honestly partial.
18. As a maintainer, I want each field mapped to a small set of Visual roles, so that semantically equivalent fields can share colors without making adjacent regions indistinguishable.
19. As a user, I want Preview to group results by visual region, so that I can understand “editor”, “taskbar”, “terminal” and “browser chrome” without reading raw configuration keys.
20. As a maintainer, I want technical field names, evidence URLs, generated values and capability status available as details, so that human readability does not remove auditability.
21. As a maintainer, I want Verify to report field-level results and aggregate them into the existing Target status vocabulary, so that partial results explain exactly what remains unresolved.
22. As a maintainer, I want fixture tests to validate generated artifacts and persisted settings through existing Adapter seams, so that tests prove observable behavior rather than helper structure.
23. As a maintainer, I want real-desktop checks kept separate from the default fixture suite, so that installed application behavior is verified without making ordinary tests environment-dependent.
24. As a user, I want a saturated Seed Color such as red to remain recognizable without filling large areas with harsh raw color, so that the theme is comfortable for long sessions.
25. As a user, I want ordinary Palette roles not to collapse to pure black or pure white, so that contrast repair does not create visually broken regions.
26. As a maintainer, I want Palette generation to use perceptual lightness, chroma and hue controls, so that visual quality is not determined only by RGB blending.
27. As a maintainer, I want extreme Seed Colors tested across both Modes and all Target artifacts, so that red, yellow, cyan, purple, near-black and near-white inputs remain stable.
28. As a maintainer, I want the default `.one-tone` directory to live beside the installed Skill package, so that Agents cannot scatter runtime state across working directories.

## Implementation Decisions

- Seed Color is immutable as the Theme anchor and Accent source for all Targets; it is not required to equal a large-area `surface` role.
- Large-area `background`, `surface`, `surface_subtle`, `surface_raised`, editor backgrounds and wallpapers use low-chroma Tonal surfaces. Accent and interactive states retain the Theme anchor relationship.
- Palette generation uses OKLCH/OKLab-style perceptual lightness/chroma/hue controls. WCAG relative luminance remains the independent contrast check.
- Ordinary roles cannot use pure black or pure white as an unqualified contrast fallback. Accent keeps the Seed Color hue within a bounded tolerance; repair adjusts perceptual lightness/chroma instead of unrestricted blending to black or white.
- Palette validation reports appearance-safety failures separately from contrast failures. Representative and extreme Seed Colors must pass deterministic role, hue, chroma, separation and readability constraints.
- Plan contains Light and Dark Palettes. The selected Mode is a lookup/default choice, not permission to modify Windows system mode.
- Windows system mode, automatic accent selection and high-contrast settings remain detect-only.
- Windows exposes separate field-level statuses for Accent color and Taskbar accent display. A Taskbar accent display unavailable in pure Light mode is `not-applicable`; successful Accent color application remains visible.
- If automatic accent selection can overwrite the selected accent, Apply/Verify reports the condition and does not silently disable it.
- VS Code/TRAЕ generate one extension containing paired Light/Dark theme definitions. Settings must use the exact contributed labels, not a shared base label that is absent from the extension manifest.
- Existing `window.autoDetectColorScheme` preference is preserved. The tool may set the preferred Light/Dark labels required by the generated extension, but does not silently change the user's automatic switching preference.
- Theme registration and Theme activation are separate capabilities. Verify must check both extension presence and active theme selection.
- Chrome generates two canonical user-facing unpacked directories, one per Mode. ZIPs, compatibility aliases and transaction copies may exist internally but are not user-facing choices and must not be listed as separate themes.
- Chrome remains manual activation; the tool does not silently install or activate a local Chrome theme.
- The default `.one-tone` runtime directory is resolved from the installed Skill package root, not from the process current working directory. Plans, Transactions, generated wallpapers, editor artifacts and Chrome artifacts use this root unless an explicit test/runtime override is supplied.
- Field inventory is versioned per Target and records: official source, version baseline, technical field, field category, Visual role, Mode support, generated value, capability status and verification evidence.
- Official stable schemas are preferred. Windows and Windows Terminal use Microsoft documentation; VS Code uses the official Theme Color Reference and theme contribution schema; Chrome uses the official theme manifest schema. TRAE-specific fields require installed-version or public-theme discovery. Codex remains bounded by its verified v1 schema until an authoritative public schema exists.
- Human-facing Preview/Verify groups inventory entries by visual region and uses plain-language labels. Technical names and source evidence remain available as details.
- Existing Plan, AdapterResult, Snapshot, Apply, Verify and Rollback contracts remain in place. No new service, database, background process or Adapter framework is introduced.
- Runtime path resolution must derive the Skill root from the runtime module location and must not hard-code the repository root, a drive letter or an Agent working directory.
- Chrome theme tints must use a no-change or Palette-derived value; fixed all-zero HSL tints are not allowed.

## Testing Decisions

- Tests assert observable JSON, ZIP/directory manifests, persisted settings, extension registration, active theme selection and status payloads. They do not assert private helper structure.
- Plan tests verify both Mode Palettes, immutable Seed Color and the distinction between selected Mode and Windows system mode.
- Palette tests verify Theme anchor preservation, low-chroma Tonal surfaces, deterministic Mode tone ladders, Accent hue retention, no unjustified pure-black/pure-white ordinary roles and extreme Seed Colors.
- Windows tests verify Accent color independently from Taskbar accent display, including the pure Light-mode `not-applicable`/`partial` result and preservation of system mode, automatic accent selection and high-contrast settings.
- VS Code/TRAЕ tests verify that the extension contributes the exact Light/Dark labels, settings select those labels, extension registration is detected, activation is verified, and an existing auto-detect setting is preserved.
- Chrome tests verify exactly two canonical unpacked directories, correct Light/Dark manifests, all inventory `colors`, `tints` and display-property fields, and that ZIP/alias artifacts are not presented as user choices.
- Field inventory tests compare generated fields against the documented inventory and reject undocumented guessed fields.
- Preview/Verify tests verify visual-region grouping, technical-field detail, evidence metadata and field-level status aggregation into `ok`, `partial`, `failed`, `skipped` or `not-applicable` semantics as applicable.
- Existing transaction tests retain per-Target Snapshot, persistence, compensation and explicit Rollback guarantees.
- CLI tests run from different current working directories and verify that the default `.one-tone` path remains the Skill-local runtime root; fixture tests continue to use explicit temporary overrides.
- Chrome tests reject all-zero tints and verify that large browser regions use Tonal surfaces while interactive regions retain the Accent relationship.
- Real desktop validation remains a separate matrix for Windows, Windows Terminal, VS Code, TRAE, Codex and Chrome; it is not part of the default fixture suite.

## Out of Scope

- Changing Windows Light/Dark system mode, automatic accent selection or high-contrast mode without a separately approved explicit opt-in.
- Making Chrome switch Light/Dark themes automatically.
- Silent Chrome theme installation or bypassing Chrome's manual local-theme confirmation.
- Guessing undocumented TRAE AI-panel fields from VS Code similarity or private implementation details.
- Replacing WCAG contrast checks with a subjective screenshot-only score, or changing the existing contrast thresholds without a separate decision.
- Adding fonts, layout settings, animations, behavior switches or non-color configuration.
- Publishing Chrome themes to the Web Store or introducing enterprise deployment.
- Treating a passing fixture test as proof that every installed application renders every field correctly.

## Further Notes

The implementation should first correct the highest-risk user-visible seams: exact editor theme activation labels, duplicate Chrome artifacts and Windows field-level taskbar status. Official evidence should be maintained alongside each Field inventory revision.

Evidence baseline:

- Windows: https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-common
- Windows Terminal: https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-appearance and https://learn.microsoft.com/en-us/windows/terminal/customize-settings/color-schemes
- VS Code: https://code.visualstudio.com/api/references/theme-color and https://code.visualstudio.com/api/references/contribution-points
- Chrome: https://developer.chrome.com/docs/extensions/develop/ui/themes
- TRAE: no stable public theme-field schema is assumed; installed-version or public-theme discovery is required.
