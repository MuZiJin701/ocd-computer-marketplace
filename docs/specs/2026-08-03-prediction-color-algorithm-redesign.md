# 预测文字颜色算法重设计

## Problem Statement

Windows Terminal 中，PowerShell/PSReadLine 的行内预测和列表预测已经进入现有 Profile 集成，但真实浅色主题截图表明预测文字仍然难以与用户已经输入的命令区分。

当前实现对 `#10B981` 生成的浅色 Palette 使用接近黑色的预测色。截图中普通文字为 `#0C0D0E`，预测文字为 `#2F3337`，两种颜色都已实际渲染，说明问题不是 Profile 未生效或 Windows Terminal 忽略颜色，而是颜色算法在满足背景可读性时把预测色限制得过于接近普通文字。

现有 `4.5:1` 背景对比度约束只能保证文字可读，不能保证预测文字与已输入文字之间具有足够的视觉区分。现有低色度中性色约束和固定预测色相也限制了候选空间，无法稳定覆盖不同 Seed Color、浅色模式和深色模式。

算法需要保持插件的泛化性、可移植性和易分发性，不得加入针对当前机器、用户路径、终端截图或固定安装版本的特殊颜色或逻辑。

## Solution

重新设计 `prediction_foreground` 的生成算法，使它成为由 Seed Color 派生的、可辨识的预测文字角色：

- 借鉴成熟动态主题算法对 Hue、Chroma、Tone 的分离思想，尤其参考 Material Color Utilities 的 HCT、互补色、相邻色和动态对比度设计；不引入该库作为运行时依赖。
- 使用现有纯 Python 的 OKLab/OKLCH 能力生成和评价候选，不再使用固定预测色相。
- 从 Seed-derived 色相生成互补色、三角色和必要的相邻候选，并避开现有强调色、成功色、警告色和错误色的语义色相邻域。
- 对每个候选独立搜索明度和色度，使其同时满足实际 Terminal surface 的可读性和与普通文字的视觉区分。
- 浅色和深色共享同一组 Seed-derived 色相家族，但根据各自背景独立选择明度、色度和最终颜色。
- 只修改预测颜色；不修改预测来源、键绑定、字体、字重、斜体、布局或其他 ANSI 样式。
- 如果候选无法满足硬约束，保留原有设置并报告 `partial` 或 `unsupported`，不得静默复用普通文字色。

最高测试 seam 是共享 Palette 生成/验证。Terminal Adapter 继续负责能力发现、Profile 持久化、事务安全和字段映射，但不重新实现颜色选择算法。

## User Stories

1. As a Windows Terminal user, I want inline PowerShell predictions to be visibly different from text I have already typed, so that I can distinguish a suggestion from the accepted command.
2. As a Windows Terminal user, I want list-view predictions to use the same distinguishable prediction role, so that switching prediction view does not restore the ambiguity.
3. As a Windows Terminal user, I want selected list predictions to retain a readable selection foreground/background pair, so that selection state remains distinct from unselected prediction text.
4. As a user of a Light theme, I want prediction text to remain readable against the generated Light Terminal surface, so that improving distinction does not make suggestions faint.
5. As a user of a Dark theme, I want prediction text to remain readable against the generated Dark Terminal surface, so that the redesign does not only solve Light mode.
6. As a theme user, I want prediction colors to be derived from my Seed Color, so that the result remains visually related to the generated theme.
7. As a theme user, I want prediction colors to use controlled hue variation when neutral colors cannot be sufficiently distinguished, so that visibility takes priority over an overly strict neutral constraint.
8. As a theme user, I want prediction colors not to resemble success, warning, error or accent text, so that a suggestion is not mistaken for a status message.
9. As a user changing only the Seed Color slightly, I want the prediction color to change continuously, so that small theme adjustments do not cause abrupt color jumps.
10. As a user switching between Light and Dark modes, I want the prediction hue family to remain coherent while its tone adapts to the background, so that the theme does not lose its identity.
11. As a user with a high-contrast or unusual Seed Color, I want the algorithm to evaluate the actual generated surface, so that a global contrast assumption does not produce an unreadable prediction.
12. As a user on a host that cannot support the prediction field, I want the capability reported as unsupported or partial, so that the tool does not claim a color change that the host cannot render.
13. As a user with an existing PowerShell Profile, I want unrelated Profile content preserved, so that changing prediction colors does not overwrite shell customizations.
14. As a user applying the same plan more than once, I want the prediction color integration to remain idempotent, so that repeated Apply operations do not duplicate or drift the managed block.
15. As a user rolling back a transaction, I want the previous prediction configuration restored, so that the algorithm redesign remains reversible under the existing transaction contract.
16. As a user of different Windows installations, I want no fixed user path, drive, installed version or machine-specific color in the algorithm, so that the Plugin remains portable and distributable.
17. As a maintainer, I want the Terminal Adapter to consume a validated Palette role, so that color selection has one source of truth and sibling terminal paths do not diverge.
18. As a maintainer, I want deterministic candidate generation and scoring, so that plans, tests and rollback metadata remain reproducible.
19. As a maintainer, I want visual screenshot acceptance in addition to numeric tests, so that native terminal rendering issues are not hidden by fixture success.
20. As a maintainer, I want the existing Preview → Apply → Verify → Rollback boundaries preserved, so that a color algorithm change does not expand the runtime safety model.

## Implementation Decisions

- Keep `prediction_foreground` as the dedicated Palette role. It is a predictable, distinguishable text role, not an alias for `muted_foreground`, Terminal `foreground` or any semantic status text.
- Replace the fixed prediction hue with Seed-derived hue candidates. Candidate families must include complementary and triadic relationships and may include analogous candidates when needed for a valid result.
- Use the existing OKLCH representation to separate hue, chroma and lightness during candidate construction. Use OKLab distance for perceptual separation and the existing luminance contrast calculation for background readability.
- Treat background contrast `>= 4.5:1` as a hard requirement for normal prediction text. This is the readability floor, not the sole visibility criterion.
- Treat OKLab distance `ΔE_OK >= 0.20` from ordinary `foreground` as the target distinguishability requirement. The previous `0.08` threshold is insufficient for this user-visible case.
- Raise the current low-chroma restriction from `0.04` to a controlled OKLCH chroma target around `0.10`. This value is a soft scoring boundary, not permission to choose arbitrary high-saturation colors.
- Generate candidate tones separately for Light and Dark surfaces. Light mode should prefer a dark readable prediction color; Dark mode should prefer a light readable prediction color. The hue family remains Seed-derived and coherent across modes.
- Reject or penalize candidates too close in hue to existing `accent_text`, `success_text`, `warning_text` and `error_text` roles. Prediction is an interaction-state cue, not a semantic status cue.
- Rank valid candidates in this order: satisfy hard readability and distinguishability constraints; maximize perceptual distance from ordinary text; avoid semantic color collisions; maximize contrast margin; then minimize chroma and unnecessary deviation from the Seed-derived theme.
- Keep candidate generation deterministic and continuous. Use a stable, documented candidate order and deterministic tie-breakers. Do not use randomness or machine-specific presets.
- If no candidate meets both hard constraints, do not silently use ordinary `foreground`. Leave the existing prediction configuration unchanged and return the existing structured `partial` or `unsupported` capability status through the Terminal Adapter.
- Preserve the current Terminal Adapter boundary: it discovers supported PSReadLine fields, serializes the selected Palette colors for the host, and manages the guarded Profile block. It must not contain a second color-generation algorithm.
- Preserve the current Windows Terminal session guard. The change remains limited to the supported Windows Terminal/PSReadLine integration and does not alter standalone PowerShell or unrelated terminal preferences.
- Do not add Material Color Utilities or another runtime package. The project remains Python/uv based and distributable as a self-contained Skill.
- Update the Palette validation contract so generated and supplied `prediction_foreground` values are checked against the actual mode surface, the new distinguishability target and the controlled chroma policy.
- Keep existing transaction, snapshot, atomic persistence, rollback and Verify behavior unchanged. The redesign changes the Palette output and its validation, not the transaction model.

## Testing Decisions

- Test the external Palette behavior at the shared generation/validation seam. Tests must verify that Light and Dark palettes expose prediction colors that meet the background contrast and distinguishability requirements.
- Cover representative Seed Colors spanning green, yellow, blue, red, purple and orange families, including the previously observed green Seed case. Do not assert one fixed RGB output; assert the documented constraints, role relationships and deterministic output.
- Add tests for candidate hue derivation so a changed Seed Color does not always produce the same fixed prediction hue.
- Add tests for semantic color avoidance so prediction candidates are not selected from the neighborhood of success, warning, error or accent roles when an alternative valid candidate exists.
- Add tests for Light/Dark coherence: both modes should retain a related Seed-derived hue family while independently meeting their own background contrast requirements.
- Add tests for stability across nearby Seed Colors and repeated generation. The same input must produce the same output, and small Seed changes must not cause unnecessary candidate jumps.
- Add tests that distinguish the hard `4.5:1` background contrast gate from the `ΔE_OK >= 0.20` prediction-vs-foreground gate. A color can pass the first and fail the second; validation must report that failure.
- Add tests for the controlled chroma policy, including cases where the old `0.04` ceiling cannot meet the new distinguishability target and the new target near `0.10` can.
- Add tests for the no-valid-candidate path. The Palette/Adapter must preserve the existing setting and return structured `partial` or `unsupported` status rather than silently falling back to ordinary foreground.
- Keep Terminal Adapter fixture tests focused on external behavior: consuming the generated role, serializing Light/Dark values, preserving unrelated Profile content, idempotent managed-block upgrade, capability discovery, Verify and Rollback.
- Keep tests for unsupported PSReadLine fields and legacy hosts unchanged except for assertions required by the new Palette contract.
- Add real Windows Terminal screenshot gates for Light and Dark modes with representative Seeds. The screenshot must show inline and, where available, list predictions visibly distinct from typed text; fixture tests alone cannot prove native rendering quality.
- Continue running the repository standard checks: full pytest, CLI help, and `git diff --check`. Real desktop validation must remain separate from fixture tests and must not be represented as completed unless actually performed.

## Out of Scope

- Changing PowerShell prediction sources, prediction plugins, key bindings or completion behavior.
- Changing fonts, font size, font weight, italic style, layout, spacing, anti-aliasing, rendering engines or accessibility settings.
- Adding a new top-level PowerShell target or changing the existing target list.
- Applying prediction colors to standalone PowerShell sessions, VS Code terminals or other unsupported hosts.
- Modifying Windows Terminal Scheme ANSI semantic colors to simulate PSReadLine prediction colors.
- Adding a background watcher, scheduled task, service or automatic re-Apply for theme or mode changes.
- Adding machine-specific RGB constants, fixed user paths, fixed drives, installed-version assumptions or screenshot-specific exceptions.
- Importing Material Color Utilities or another external runtime color library.
- Redesigning the broader Palette roles, taskbar behavior, TRAE/VS Code Git decorations or unrelated theme regressions.
- Treating a successful Profile write or registry/configuration write as proof of native visual acceptance.

## Further Notes

- The current screenshot is useful diagnostic evidence: the Profile integration is active because both the ordinary text color and the generated prediction color appear in the rendered image. The remaining defect is algorithmic visual separation, not missing wiring.
- Material Color Utilities is used as design prior only. Its HCT model and dynamic scheme concepts motivate the separation of hue, chroma and tone; the implementation remains local to the existing runtime to preserve distribution simplicity. See the [Material Color Utilities project](https://github.com/material-foundation/material-color-utilities).
- WCAG contrast is a minimum readability criterion. It does not establish sufficient distinction between two adjacent text roles, so the separate OKLab distance requirement is intentional. See the [W3C contrast guidance](https://www.w3.org/WAI/WCAG22/Understanding/contrast-minimum.html).
- The durable architectural rationale should be recorded in an ADR only after implementation confirms the final algorithm and fallback behavior. This spec is the implementation contract for that follow-up.
