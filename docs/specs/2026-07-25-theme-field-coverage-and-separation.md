# 主题字段覆盖与相邻区域可区分性开发说明

## Problem Statement

用户使用统一主题后，部分界面区域与周围颜色过于接近，难以判断工具栏、标签、面板、输入区、非活动区、选区和焦点边界的范围。现有实现还没有把六个 Target 的完整公开主题字段固化为可验收的 Field inventory，因此“字段已覆盖”和“字段可见且可区分”都难以证明。

现有 Palette 主要验证文字对比度，不能防止相邻背景复用同一颜色；多个 Target 也把同一个 surface 或 foreground 映射到过多视觉区域。另有两个用户可见缺口：Windows 生成的二进制 `AccentPalette` 进入 Transaction 报告时会让 JSON 持久化失败；支持双模式的应用已经生成 Light/Dark 产物，却没有统一配置为跟随当前 Windows 系统模式。

## Solution

以 Plan 作为最高共享 Seam，生成浅色和深色两套 Palette，并把每个 Target 的公开 Color field 映射到少量稳定 Visual role。

主题生成必须同时满足：

- 所有公开、稳定、颜色相关字段都有 Field inventory 和覆盖状态；
- 同语义字段可以复用同一颜色；
- 相邻 UI region 不得复用同一颜色；
- 普通相邻背景的对比度至少为 1.2:1；
- 选区、焦点、边框和强调控件相对邻近背景至少为 3:1；
- Light Mode 的 Dense primary text 使用不透明、低色度的 Neutral primary text 角色，对实际 surface 至少 7:1；其他文字对实际 surface 至少 4.5:1，深层 background 上至少 7:1；
- Seed Color 保持原样，不为满足对比度而暗化；
- 字段或版本不支持时按字段记录 unsupported，并将 Target 聚合为 partial；
- Chrome 生成独立的 light 和 dark 主题产物；
- Windows Terminal 生成 light/dark 双 Scheme，并让支持的配置跟随系统模式，不替用户切换系统模式。
- 同一 Visual role 在 Light/Dark 中的 OKLCH 明度差不超过 `0.35`，同时保留两种模式的可读性方向。
- Apply 必须在包含二进制生成值的 Windows 结果时仍然完成 Transaction JSON 持久化；报告值可读且无损，Snapshot 恢复语义不变。

## User Stories

1. As a Windows 用户, I want to preview all six Targets before applying a theme, so that I know which fields and versions are supported.
2. As a Windows 用户, I want my Seed Color to remain the exact Theme anchor and Accent source, so that the theme still reflects the color I chose without covering large regions in an uncomfortable raw color.
3. As a Windows 用户, I want adjacent background regions to be visibly different, so that toolbars, panels, tabs, inputs and content areas do not merge visually.
4. As a Windows 用户, I want active, inactive, hover, focus and selected states to be distinguishable, so that I can understand the current UI state.
5. As a Windows 用户, I want Light Mode dense primary text to meet the 7:1 contrast target, so that labels and content remain readable in real screenshots.
6. As a Windows 用户, I want deep-background text to meet the 7:1 target, so that secondary UI remains readable.
7. As a Windows 用户, I want light and dark Palette variants, so that the same Seed Color remains coherent in both modes.
8. As a Windows Terminal 用户, I want complete light and dark ANSI Schemes, so that terminal text, cursor and selection remain readable in either mode.
9. As a Windows Terminal 用户, I want tab rows, active tabs, inactive tabs, frames and unfocused frames to be distinct, so that the terminal window structure is visible.
10. As a VS Code 用户, I want all stable public Workbench color fields covered, so that settings, breadcrumbs, widgets, lists, notifications, diagnostics and editor states do not fall back to unrelated colors.
11. As a TRAE 用户, I want standard VS Code fields and discoverable TRAE-specific fields covered, so that the common editor and available AI UI receive the same treatment.
12. As a Codex 用户, I want every known color field in the verified v1 theme schema updated in both mode tables, so that Codex does not retain stale semantic colors.
13. As a Chrome 用户, I want complete colors, tints and display properties in the generated theme, so that browser chrome, tabs, bookmarks, omnibox and controls use a consistent theme.
14. As a Chrome 用户, I want separate light and dark theme packages, so that I can manually activate the mode I need without silent extension installation.
15. As a Windows 用户, I want Windows wallpaper, accent palette, Start/Taskbar, title bars, borders and DWM color outputs aligned, so that the desktop and applications do not look like unrelated themes.
16. As a Windows 用户, I want system mode, automatic accent selection and high-contrast settings preserved, so that the tool does not override accessibility or personal preferences.
17. As a Windows 用户, I want unsupported fields reported individually, so that a partial result explains what the installed version cannot provide.
18. As a Windows 用户, I want a failed field or Target to be compensated without losing successful Target changes, so that an incomplete theme remains recoverable.
19. As a maintainer, I want a versioned Field inventory, so that adding or removing a platform field is an explicit reviewable change.
20. As a maintainer, I want generated field mappings tested through the existing Adapter seams, so that tests verify behavior rather than private helper structure.
21. As a maintainer, I want Preview, Apply, Verify and Rollback to retain their current safety contracts, so that improving coverage does not weaken reversibility.
22. As a maintainer, I want real desktop screenshots kept separate from fixture tests, so that visual evidence is useful without making the default suite depend on installed applications.
23. As a Windows 用户, I want Apply to persist a complete Transaction even when a generated registry value is binary, so that a successful theme change does not become an unrecorded or unusable transaction.
24. As a Windows 用户, I want Windows Terminal, VS Code, TRAE and Codex to use the Light/Dark variant matching the Windows system mode when they support native following, so that switching Windows mode does not require reapplying the Plan.
25. As a maintainer, I want binary Transaction report values to remain distinct from Snapshots, so that JSON diagnostics do not become an accidental rollback format.

## Implementation Decisions

- The highest shared Seam is Plan Palette generation. It produces one Palette per Mode and exposes the selected mode data to Adapters; Target-specific mapping stays inside each Adapter.
- Plan has one canonical Palette representation: new persisted Plans contain `palettes` with exactly `light` and `dark`; `palette` is not serialized or exposed. The top-level `mode` remains the user's selected/default lookup Mode and never changes the Windows system mode.
- Loading a Plan rejects legacy single-Palette data, missing or extra Modes, invalid Palette content and hash mismatches. A legacy Plan must be re-created through Preview rather than silently migrated.
- Adapters use `palette_for(mode)`, which returns a copy. Single-Mode outputs use the Plan's selected Mode; paired artifacts explicitly generate both Modes. Adapter interfaces and Target-specific responsibilities remain unchanged.
- Palette gains a small number of Tonal surface roles: surface, surface_subtle and surface_raised. Existing background, selection, border, foreground and semantic text roles remain shared where their meaning is the same.
- Seed Color is immutable as the Theme anchor and Accent source. Large-area Tonal surfaces, editor backgrounds and wallpapers may use derived low-chroma colors rather than the raw Seed Color.
- Palette generation uses OKLCH/OKLab-style perceptual lightness/chroma/hue control. Palette validation continues to use relative luminance for WCAG contrast and additionally checks appearance safety: bounded surface chroma, stable Accent hue, explicit mode tone ladders and no unjustified pure-black/pure-white fallback for ordinary roles.
- Mode coherence additionally limits the OKLCH lightness difference of corresponding large-area roles to `0.35`; each mode keeps the same tonal role ordering and its own text contrast direction.
- Each Target has a Field inventory based on its public stable theme schema. The inventory is the source of truth for generated-field tests and Verify reporting.
- Field inventory records the official source, version baseline, technical field, Visual role, Mode support and field-level capability status. Fields without a stable official schema must not be guessed.
- Version-sensitive fields are capability checked. Supported fields continue to Apply; unsupported fields remain unchanged and contribute to Target partial status.
- Windows controls only user-visible color outputs that are safe and documented. Accent color and Taskbar accent display are separate fields; Mode selectors, automatic accent selection and high-contrast settings remain detect-only. Light and Dark both attempt Taskbar accent display; a native Light-mode limitation is reported as `partial` and must not turn the whole Windows Target into failed. The former `not-applicable` rule is superseded by ADR 0009.
- Windows Terminal uses paired light/dark Schemes, a system-selected window theme, and paired `colorScheme` mappings for Profiles. VS Code and TRAE publish paired light/dark theme definitions in one installable theme package.
- VS Code and TRAE Apply selects the actual contributed Light/Dark theme labels and enables `window.autoDetectColorScheme`; it does not select a non-existent base label.
- Codex keeps `appearanceTheme = system`; Chrome produces paired artifacts but requires manual activation; Windows system mode remains unchanged and is not watched by a background service.
- Transaction report values must be JSON-safe. Binary generated values use a lossless serialized report representation and remain separate from Snapshot data used for Rollback.
- Chrome publishes exactly two user-facing canonical unpacked theme directories, one Light and one Dark. ZIPs, compatibility aliases and transaction copies are internal artifacts, not additional themes for users to choose.
- TRAE-specific fields are optional discoveries from the installed application or its public theme data. They are never guessed from private implementation details; absence of a stable public schema is itself a reason to report the field as unsupported or partial.
- Codex coverage is limited to the verified v1 color schema. Unknown configuration keys are preserved, not invented.
- Field-level capability results roll up to the existing Target status vocabulary. A Target with successful supported fields and unsupported fields is partial; write failures or failed compensation remain failed.
- Serialized report values are JSON-safe at the Transaction persistence boundary. Binary values use a lossless representation for reporting; Rollback continues to read only the Transaction's own Snapshot or artifact metadata.
- Native system-mode following is configured only for paired-theme Targets: Windows Terminal Profiles use Light/Dark `colorScheme` mappings with `applicationTheme = system`; VS Code and TRAE enable `window.autoDetectColorScheme`; Codex keeps `appearanceTheme = system`.
- Chrome remains a pair of manually activated canonical themes. Windows system mode is preserved and is neither changed nor watched by a background service.
- The repository keeps one distributable Skill runtime and one root test harness. It does not introduce a new service, database or theme plugin framework.
- The canonical development spec lives in the active docs/specs area. Historical design and implementation notes are not restored as active architecture.

## Testing Decisions

- Tests verify observable generated plans, theme artifacts, persisted settings and status payloads; they do not assert private helper structure.
- Palette and Adapter tests cover both modes, immutable Theme anchor, low-chroma Tonal surfaces, stable Accent hue, neutral Light primary text, no unjustified pure-black/pure-white ordinary roles, `0.35` cross-mode OKLCH lightness limits for large-area roles, 1.2:1 passive separation, 3:1 interactive separation, opaque Light dense-primary-text `7:1` contrast, other text `4.5:1` contrast and real Light screenshots across representative and extreme Seed Colors.
- Plan tests cover serializing both mode Palettes and field capability expectations while preserving hash integrity.
- Plan tests cover the canonical `palettes` payload, rejection of legacy/malformed Plans, Palette validation on load, copy-on-read behavior and removal of direct `plan.palette` access.
- Adapter tests cover the existing Windows, Terminal, VS Code-family, Codex and Chrome fixture seams. Each test compares generated fields with the Field inventory and checks mode-specific mappings.
- Chrome tests inspect both canonical manifests and validate colors, tints and display properties; tests also assert that user-facing output contains only the two canonical unpacked directories.
- VS Code-family tests verify the paired theme package, standard fields, and discovered TRAE fields when present.
- Windows Terminal tests verify paired `colorScheme` mappings and `applicationTheme = system`; VS Code-family tests verify exact contributed Light/Dark labels and enabled auto-detect settings.
- Transaction tests verify that Windows binary generated values can be persisted in the transaction report without changing Snapshot restoration semantics.
- Transaction tests retain the existing per-Target Snapshot, persistence, compensation and rollback checks.
- A separate real-desktop test matrix records manual screenshots for one dark Seed and one high-lightness Seed across the six Targets. It is explicitly excluded from the default fixture suite.
- A transaction integration test exercises a Windows Adapter result containing a binary generated value through TransactionStore persistence and reload; it also verifies Snapshot-based Rollback remains exact.
- Target fixture tests verify native following configuration: paired Terminal Profile mappings, VS Code/TRAE auto-detect enabled, Codex system mode preserved, and Chrome manual activation status.

## Out of Scope

- Fonts, layout settings, animations, behavior switches and non-color configuration.
- Undocumented or private fields that cannot be discovered and verified.
- Silent Chrome theme installation or automatic Chrome mode switching.
- Changing Windows light/dark mode, automatic accent selection, high-contrast mode or other accessibility settings.
- Cursor as a user-visible Target.
- Replacing the existing transaction model, adding a database or introducing a background service.
- Treating a passing fixture test as proof that a real installed application renders every field.
- Running a background watcher or service to react to later Windows mode changes.
- Restoring the deleted historical archive and superpowers documents as active documentation.

## Further Notes

The current project structure is intentionally split at the distribution boundary but has avoidable documentation debt:

- The nested Skill runtime is the correct distributable boundary, but its depth makes direct imports, CLI commands and test configuration harder to discover.
- The root project is a non-package test harness while the Skill owns the runtime project. This is valid but creates two uv entry points and should be documented as a deliberate boundary.
- There was no durable Field inventory, so “all fields” could not be audited consistently across Adapters.
- The domain context previously mixed vocabulary, invariants and implementation details. It should remain a short glossary; architecture and testing contracts belong in their own documents.
- The active documentation set should have one canonical development-spec location, one architecture document and one testing document. Historical material may remain deleted or archived separately.
