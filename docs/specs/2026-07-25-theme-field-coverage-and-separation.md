# 主题字段覆盖与相邻区域可区分性开发说明

## Problem Statement

用户使用统一主题后，部分界面区域与周围颜色过于接近，难以判断工具栏、标签、面板、输入区、非活动区、选区和焦点边界的范围。现有实现还没有把六个 Target 的完整公开主题字段固化为可验收的 Field inventory，因此“字段已覆盖”和“字段可见且可区分”都难以证明。

现有 Palette 主要验证文字对比度，不能防止相邻背景复用同一颜色；多个 Target 也把同一个 surface 或 foreground 映射到过多视觉区域。

## Solution

以 Plan 作为最高共享 Seam，生成浅色和深色两套 Palette，并把每个 Target 的公开 Color field 映射到少量稳定 Visual role。

主题生成必须同时满足：

- 所有公开、稳定、颜色相关字段都有 Field inventory 和覆盖状态；
- 同语义字段可以复用同一颜色；
- 相邻 UI region 不得复用同一颜色；
- 普通相邻背景的对比度至少为 1.2:1；
- 选区、焦点、边框和强调控件相对邻近背景至少为 3:1；
- 文字对比度继续保持 surface 上至少 4.5:1、深层 background 上至少 7:1；
- Seed Color 保持原样，不为满足对比度而暗化；
- 字段或版本不支持时按字段记录 unsupported，并将 Target 聚合为 partial；
- Chrome 生成独立的 light 和 dark 主题产物；
- Windows Terminal 生成 light/dark 双 Scheme，但保持系统模式选择，不替用户切换模式。

## User Stories

1. As a Windows 用户, I want to preview all six Targets before applying a theme, so that I know which fields and versions are supported.
2. As a Windows 用户, I want my Seed Color to remain exact in the main surface role, so that the theme still reflects the color I chose.
3. As a Windows 用户, I want adjacent background regions to be visibly different, so that toolbars, panels, tabs, inputs and content areas do not merge visually.
4. As a Windows 用户, I want active, inactive, hover, focus and selected states to be distinguishable, so that I can understand the current UI state.
5. As a Windows 用户, I want normal text to meet the 4.5:1 contrast target, so that labels and content remain readable.
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

## Implementation Decisions

- The highest shared Seam is Plan Palette generation. It produces one Palette per Mode and exposes the selected mode data to Adapters; Target-specific mapping stays inside each Adapter.
- Plan has one canonical Palette representation: new persisted Plans contain `palettes` with exactly `light` and `dark`; `palette` is not serialized or exposed. The top-level `mode` remains the user's selected/default lookup Mode and never changes the Windows system mode.
- Loading a Plan rejects legacy single-Palette data, missing or extra Modes, invalid Palette content and hash mismatches. A legacy Plan must be re-created through Preview rather than silently migrated.
- Adapters use `palette_for(mode)`, which returns a copy. Single-Mode outputs use the Plan's selected Mode; paired artifacts explicitly generate both Modes. Adapter interfaces and Target-specific responsibilities remain unchanged.
- Palette gains a small number of surface roles: surface, surface_subtle and surface_raised. Existing background, selection, border, foreground and semantic text roles remain shared where their meaning is the same.
- Seed Color is immutable. Contrast and region separation may adjust derived roles, saturation and lightness, but never the Seed Color.
- Palette validation checks text contrast, adjacent-region separation and interactive boundary separation. Relative luminance is used because it already exists in the runtime and requires no dependency.
- Each Target has a Field inventory based on its public stable theme schema. The inventory is the source of truth for generated-field tests and Verify reporting.
- Version-sensitive fields are capability checked. Supported fields continue to Apply; unsupported fields remain unchanged and contribute to Target partial status.
- Windows controls only user-visible color outputs that are safe and documented. Mode selectors, automatic accent selection and high-contrast settings remain detect-only.
- Windows Terminal uses paired light/dark Schemes and a system-selected theme. VS Code and TRAE publish paired light/dark theme definitions in one installable theme package.
- Chrome publishes separate light and dark static theme packages because a local Chrome theme does not provide a mode-switching color table. User activation remains manual.
- TRAE-specific fields are optional discoveries from the installed application or its public theme data. They are never guessed from private implementation details.
- Codex coverage is limited to the verified v1 color schema. Unknown configuration keys are preserved, not invented.
- Field-level capability results roll up to the existing Target status vocabulary. A Target with successful supported fields and unsupported fields is partial; write failures or failed compensation remain failed.
- The repository keeps one distributable Skill runtime and one root test harness. It does not introduce a new service, database or theme plugin framework.
- The canonical development spec lives in the active docs/specs area. Historical design and implementation notes are not restored as active architecture.

## Testing Decisions

- Tests verify observable generated plans, theme artifacts, persisted settings and status payloads; they do not assert private helper structure.
- Palette tests cover both modes, immutable Seed Color, role uniqueness for adjacent regions, 1.2:1 passive separation, 3:1 interactive separation and existing text contrast.
- Plan tests cover serializing both mode Palettes and field capability expectations while preserving hash integrity.
- Plan tests cover the canonical `palettes` payload, rejection of legacy/malformed Plans, Palette validation on load, copy-on-read behavior and removal of direct `plan.palette` access.
- Adapter tests cover the existing Windows, Terminal, VS Code-family, Codex and Chrome fixture seams. Each test compares generated fields with the Field inventory and checks mode-specific mappings.
- Chrome tests inspect both static manifests and validate colors, tints and display properties.
- VS Code-family tests verify the paired theme package, standard fields, and discovered TRAE fields when present.
- Transaction tests retain the existing per-Target Snapshot, persistence, compensation and rollback checks.
- A separate real-desktop test matrix records manual screenshots for one dark Seed and one high-lightness Seed across the six Targets. It is explicitly excluded from the default fixture suite.

## Out of Scope

- Fonts, layout settings, animations, behavior switches and non-color configuration.
- Undocumented or private fields that cannot be discovered and verified.
- Silent Chrome theme installation or automatic Chrome mode switching.
- Changing Windows light/dark mode, automatic accent selection, high-contrast mode or other accessibility settings.
- Cursor as a user-visible Target.
- Replacing the existing transaction model, adding a database or introducing a background service.
- Treating a passing fixture test as proof that a real installed application renders every field.
- Restoring the deleted historical archive and superpowers documents as active documentation.

## Further Notes

The current project structure is intentionally split at the distribution boundary but has avoidable documentation debt:

- The nested Skill runtime is the correct distributable boundary, but its depth makes direct imports, CLI commands and test configuration harder to discover.
- The root project is a non-package test harness while the Skill owns the runtime project. This is valid but creates two uv entry points and should be documented as a deliberate boundary.
- There was no durable Field inventory, so “all fields” could not be audited consistently across Adapters.
- The domain context previously mixed vocabulary, invariants and implementation details. It should remain a short glossary; architecture and testing contracts belong in their own documents.
- The active documentation set should have one canonical development-spec location, one architecture document and one testing document. Historical material may remain deleted or archived separately.
