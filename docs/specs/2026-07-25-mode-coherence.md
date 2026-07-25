# Mode coherence 开发说明

## Problem Statement

同一个 Seed Color 当前生成的 Light 和 Dark 两套主题虽然各自通过了对比度与区域区分校验，但用户看到的视觉身份断裂：Light 主题的大面积颜色接近白色，Dark 主题的大面积颜色接近黑色；Accent 也会随模式被推向相反的明度，像两套无关的主题。

现有算法优先满足每个 Mode 的局部可读性和明暗极性，没有对同一 Seed Color 的跨 Mode 连续性建立验收约束。现有测试也主要验证单个 Mode 内部的对比度与分离度，无法捕捉“浅色近白、深色近黑、Accent 失去主题身份”的用户可见问题。

## Solution

调整显式 Light/Dark Palette 的共享生成规则，使两个 Mode 仍然是同一 Seed Color 的呈现变体：

- Light/Dark 保留明确的明暗差异，但大面积 Tonal surface 不再无必要地接近纯白或纯黑；
- 同一 Seed Color 的 Accent 在两个 Mode 中保持同一色相家族和主题身份，只在有限范围内调整明度与色度以满足对比度；
- 文字颜色继续按 Mode 反转明度，浅色使用深文字、深色使用浅文字，以保留可读性；
- 以 Plan Palette 生成作为最高共享 seam，验证生成结果及其在 Adapter 产物和 Verify 中的可见效果；
- 只调整显式 `light`/`dark` 生成路径，保留无 Mode 的旧版单 Palette 调用行为。

## User Stories

1. As a user, I want Light and Dark themes created from one Seed Color to look like variants of the same theme, so that changing Mode does not change the theme identity.
2. As a user, I want Light surfaces to remain visibly tinted by my Seed Color without becoming near-white, so that the Light theme does not look like an unthemed default.
3. As a user, I want Dark surfaces to remain visibly tinted by my Seed Color without becoming near-black, so that the Dark theme does not look like a generic black theme.
4. As a user, I want the Accent hue to remain recognizable in both Modes, so that a purple, green or red Seed Color stays recognizable after contrast adjustment.
5. As a user, I want Accent contrast to be repaired through bounded lightness and chroma changes, so that readability does not erase the chosen theme identity.
6. As a user, I want Light and Dark text to use the correct polarity for their background, so that improved cross-Mode coherence does not reduce readability.
7. As a user, I want adjacent surfaces to remain distinguishable in both Modes, so that coherence does not collapse the interface into one flat color.
8. As a user, I want the same Mode-coherent colors to reach Windows, Windows Terminal, VS Code, TRAE, Codex and Chrome artifacts, so that one Mode does not diverge at an Adapter boundary.
9. As a user, I want Preview and Verify to report the same Palette values used by Apply, so that the displayed expectation matches the installed result.
10. As a maintainer, I want cross-Mode appearance constraints tested with representative and extreme Seed Colors, so that the issue does not return for saturated, very dark or very light inputs.
11. As a maintainer, I want the existing Plan and Adapter seams reused, so that this correction does not introduce a new theme-generation abstraction.
12. As a maintainer, I want legacy callers that request a single Palette without a Mode to retain their existing shape and behavior, so that compatibility is not changed by this user-facing correction.

## Implementation Decisions

- The highest shared seam is explicit Mode Palette generation consumed by Plan. Target-specific Adapter mappings remain unchanged unless an artifact test proves that an Adapter discards the corrected visual role.
- Mode coherence means shared Seed Color hue and visual identity, not identical Light/Dark RGB values. Light/Dark may use different lightness and contrast polarity.
- Tonal surface roles use explicit, moderate Light and Dark tone ladders. The ladders must preserve surface ordering and adjacent-region separation while avoiding unjustified near-white or near-black ordinary surfaces.
- Accent generation starts from the Seed Color's hue and bounded chroma. Candidate selection may adjust perceptual lightness and chroma for the target surface, but must prefer the closest valid theme-preserving candidate instead of maximizing contrast by selecting an opposite extreme.
- Foreground and semantic text roles continue to be selected against their actual surfaces. Text polarity may invert between Modes; this is intentional and remains governed by the existing contrast requirements.
- Appearance validation remains separate from WCAG contrast validation. A Palette can meet numeric contrast and still fail if its ordinary surfaces or Accent lose Mode coherence.
- Cross-Mode validation compares the two explicit Palettes for the same Seed Color. It checks Accent hue retention, bounded Accent chroma/lightness changes, non-extreme ordinary surfaces, deterministic tone ordering and required contrast/separation.
- Plan, Apply, Verify and Adapter contracts remain unchanged. The correction changes generated role values and their acceptance criteria, not the transaction model or Target support boundary.
- The no-Mode `generate_palette` compatibility path remains unchanged. New behavior is limited to the explicit Light/Dark path used by Plan and paired artifacts.

## Testing Decisions

- Tests assert observable Palette values and generated artifacts, not private helper structure or a particular candidate-search loop.
- Palette tests cover both explicit Modes for representative Seed Colors and the existing extreme-color matrix, including saturated, near-black and near-white inputs.
- Cross-Mode tests verify that the two Palettes retain the same Seed Color theme identity: Accent hue stays within a bounded tolerance, Accent changes remain bounded, and ordinary Tonal surfaces do not collapse into near-white/near-black extremes.
- Per-Mode tests continue to verify text contrast, Accent contrast, interactive separation, passive region separation and deterministic role ordering.
- Plan tests verify that both explicit Mode Palettes contain the corrected values and that Plan hashing remains deterministic.
- Existing Windows, Windows Terminal, VS Code/TRAЕ, Codex and Chrome fixture tests remain the highest artifact seams. They must confirm that large-area fields use Tonal surface roles and Accent/interactive fields preserve the corrected Mode relationship.
- Verify tests must compare the current Target state against the corrected Plan Palette without introducing a new Apply or transaction behavior.
- A compatibility test continues to verify that callers using the no-Mode Palette API retain the legacy single-Palette shape.
- Real desktop screenshots remain a separate acceptance matrix. At minimum, compare Light and Dark output for one saturated Seed Color and one high-lightness Seed Color across the supported Targets.

## Out of Scope

- Changing Windows system Light/Dark mode, automatic accent selection or high-contrast settings.
- Making Light and Dark use identical colors or identical text polarity.
- Replacing WCAG contrast checks with a subjective screenshot score.
- Changing the no-Mode legacy Palette behavior.
- Redesigning Target field inventories, transaction persistence, Snapshot/Rollback behavior or Adapter interfaces.
- Adding a new service, database, background process, dependency or theme-generation framework.
- Automatically switching Chrome or other Target themes between Modes.
- Supporting undocumented private Target fields.

## Further Notes

The user-visible failure is a cross-Mode coherence defect, not a failure of the existing per-Mode contrast checks. The implementation should therefore correct the shared Palette seam first and only change an Adapter when an observable artifact test demonstrates that the Adapter reintroduces the old near-white/near-black behavior.

The accepted domain term is **Mode coherence**: Light and Dark are presentation variants of the same Seed Color and must retain a shared visual identity while preserving the contrast polarity required by each Mode.
