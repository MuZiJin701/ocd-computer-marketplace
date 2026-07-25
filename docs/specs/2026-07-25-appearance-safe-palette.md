# Appearance-safe Palette 开发说明

## Problem Statement

当前 Palette 主要通过 WCAG 对比度和相邻区域对比度验证，但没有验证人眼观感。对于高饱和 Seed Color，例如纯红，算法会把普通 Surface、Border、Selection 或 Accent 调整为纯黑，并把 Seed Color 直接铺到大面积界面区域。结果虽然可能通过数值验证，却出现刺眼的纯色、黑色区域、暗色文字和 Target 之间观感不一致。

Chrome 还把多个 tint 固定为全零 HSL 值，导致按钮、标签或其他浏览器控件出现黑色。VS Code、TRAE、Codex、Windows 和 Chrome 共享同一 Palette 语义，因此一个不安全的 Palette 会被放大到多个 Target。

## Solution

将 Palette 生成从“contrast-safe”提升为“appearance-safe”：

- Seed Color 作为 Theme anchor 和 Accent source 原样保留；
- 大面积背景、Surface、编辑器背景和壁纸使用低饱和 Tonal surface；
- Accent 保持 Seed Color 的主要色相和视觉身份，但允许调整明度和饱和度以适配背景；
- 使用 OKLCH/OKLab 风格的感知明度、色度和色相控制生成角色；
- 使用现有 WCAG 相对亮度公式继续验证文本和交互对比度；
- 普通角色不得无理由坍缩为纯黑或纯白；
- Chrome tint 使用无修改或从 Palette 派生的安全值，不使用固定全零 tint；
- 每个 Target 按视觉区域映射角色，而不是把 Seed Color 直接写入所有大面积字段。

## User Stories

1. As a user, I want a red Seed Color to produce a recognizable red theme without large areas becoming pure red.
2. As a user, I want large backgrounds and surfaces to remain calm and readable, so that the theme is comfortable for long sessions.
3. As a user, I want the Accent to remain recognizably derived from my Seed Color, so that the theme does not turn black when contrast is adjusted.
4. As a user, I want Light and Dark Palettes to use deliberate tone ladders, so that the same Seed Color produces coherent variants.
5. As a user, I want ordinary UI roles to avoid unjustified pure black and pure white, so that the interface does not look unfinished or harsh.
6. As a user, I want text colors to be readable without becoming muddy same-hue text, so that foregrounds remain visually distinct from surfaces.
7. As a user, I want Chrome tabs, buttons and controls to use safe tints, so that browser chrome does not become black because of a placeholder value.
8. As a user, I want Windows wallpaper and application surfaces to use tonal derivatives, so that a chosen color is represented without overwhelming the desktop.
9. As a maintainer, I want palette generation and palette validation to have separate responsibilities, so that perceptual quality is not hidden inside a contrast fallback.
10. As a maintainer, I want extreme Seed Colors tested, so that pure red, yellow, cyan, purple, near-black and high-lightness inputs do not produce pathological roles.
11. As a maintainer, I want Target mappings to distinguish large surfaces, interactive accents, text and status colors, so that one unsafe mapping does not spread across every Target.
12. As a maintainer, I want Palette output to remain deterministic, so that Preview, Apply and Verify use the same role values.

## Implementation Decisions

- The highest shared seam remains Plan Palette generation and the existing Adapter output/Verify boundary.
- Seed Color is immutable as the Theme anchor. It is not required to equal the large-area `surface` role.
- `background`, `surface`, `surface_subtle` and `surface_raised` form a low-chroma Tonal surface family. Their hue may follow the Theme anchor, but their chroma is capped independently from the Seed Color.
- Light and Dark use explicit tone ladders. Light uses high perceptual lightness with nearby but distinguishable surfaces; Dark uses low perceptual lightness with nearby but distinguishable surfaces. The ordering must be deterministic and validated.
- `accent` retains the Seed Color hue within a bounded tolerance and uses bounded chroma. Its lightness is selected against the relevant surface and interaction background; it is never replaced by black or white merely because those colors have higher contrast.
- `foreground` and `muted_foreground` use readable near-neutral or restrained chromatic values selected against their actual surfaces. A dark same-hue foreground is not acceptable solely because it passes a numeric threshold.
- `selection_background`, `border`, `focus` and interactive backgrounds use Accent-derived colors with explicit separation from their neighboring surface.
- Error, warning and success roles remain semantically independent from the Theme anchor, but their text variants must satisfy the same readability rules.
- Generation uses OKLCH/OKLab-style coordinates for lightness/chroma/hue manipulation. WCAG relative luminance remains the acceptance calculation for text and interactive contrast.
- The search/repair loop adjusts perceptual lightness and chroma within bounds. It must not use unrestricted blending toward `#000000` or `#FFFFFF` as the default repair strategy.
- Ordinary roles may use near-black or near-white only when required by their semantic role and supported by the role constraints. Pure black/pure white is rejected for ordinary Tonal surfaces, Accent, Border and Selection roles unless an explicit exception is documented.
- Target mappings must prefer Tonal surface roles for large areas and Theme anchor/Accent roles for small emphasis areas. The mapping must not reintroduce raw Seed Color as every Target's large background.
- Chrome `tints` must use Chrome's no-change value or a Palette-derived HSL value. Fixed `[0, 0, 0]` tints are prohibited.
- Palette validation reports appearance-safety errors separately from WCAG contrast errors so Preview and Verify can explain the failure.

## Testing Decisions

- Tests assert generated Palette values and observable Adapter artifacts, not private helper structure.
- A representative Seed Color matrix covers primary and secondary hues, low/medium/high lightness and low/high chroma. It must include pure red, yellow, cyan, purple, near-black and near-white inputs.
- Palette tests verify Theme anchor preservation, Tonal surface chroma caps, deterministic Light/Dark tone ordering, Accent hue retention, text contrast, interactive contrast and passive region separation.
- Palette tests reject unjustified pure-black/pure-white ordinary roles and detect same-hue foregrounds that are technically valid but violate the appearance constraints.
- Chrome tests inspect generated `colors`, `tints` and display properties and specifically reject all-zero tints.
- VS Code/TRAЕ, Codex, Terminal and Windows fixture tests verify that large-area fields use Tonal surface roles while Accent and interactive fields retain the Theme anchor relationship.
- Windows wallpaper tests verify that generated wallpapers use the Tonal palette composition instead of an unbounded flat Seed Color fill.
- Existing Plan hash, Transaction, Snapshot, Apply, Verify and Rollback tests remain unchanged except for expected Palette payloads and field-level status details.
- Real desktop screenshots remain a separate acceptance matrix and should include at least a saturated red Seed Color and one high-lightness Seed Color.

## Out of Scope

- Changing Windows system Light/Dark mode, automatic accent selection or high-contrast settings.
- Replacing WCAG contrast validation with a subjective visual score.
- Adding a database, background service, theme plugin framework or new Adapter abstraction.
- Supporting undocumented private Target fields.
- Making Chrome themes automatically switch modes.
- Redesigning non-color settings such as fonts, layout, animations or behavior switches.

## Further Notes

This spec refines the existing theme-field coverage work. The previous requirement that the raw Seed Color equal every main `surface` is superseded by the Theme anchor rule. Codex, Windows wallpaper and other large-area Target mappings must be reviewed together so that the new Palette semantics are not lost at an Adapter boundary.
