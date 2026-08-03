# Light Mode evidence-backed text readability

Status: ready-for-agent

## Problem Statement

Users report that text in the Light themes of the supported applications still looks blurry to the eye, even when the generated Palette passes the current numeric contrast checks. The supplied screenshots show the failure mode: ordinary labels and command output are technically present but visually weak against the surrounding tinted surfaces.

The current workflow has a shared Palette Seam and Target Adapters, but it does not yet distinguish all of the following cases:

- a shared Light `foreground` role that is too chromatic or too weak;
- a Dense primary text field mapped to `muted_foreground` or a state color;
- a field whose actual background differs from the background used by the Palette check;
- a Target state that needs a separate foreground/background pair;
- a private or undocumented field that should remain unsupported.

Existing Light themes demonstrate that readability is achieved through explicit field/state mappings, opaque low-chroma primary text, and weaker roles reserved for inactive or placeholder text. The project needs an evidence-backed way to learn those mappings without copying another theme's colors or creating a second source of truth.

## Solution

Build an evidence-backed Light readability improvement around the existing shared Palette and Field inventory seams.

The existing Field inventory becomes the single structured source for a Field Evidence Matrix. Each relevant Color field records its text class, expected background role, opacity policy, official field source, version baseline and reference theme evidence. Built-in Light themes from the installed VS Code and TRAE versions are the primary behavioral evidence; official schemas define field meaning; user themes are supplementary only.

Light Dense primary text uses the existing `foreground` Visual role, but the Light generator produces it as an opaque, low-chroma Neutral primary text color. It must reach `7:1` against its actual surface. `background_foreground` remains for deep backgrounds, and `muted_foreground` remains for inactive, placeholder and description text.

The implementation is accepted only when both fixture tests and real Light screenshots pass for Windows, Windows Terminal, VS Code, TRAE, Codex and Chrome using representative Seed Colors `#10B981` and `#FFD700`.

## User Stories

1. As a Windows user, I want readable Light-mode text in the supported desktop surfaces, so that the unified theme does not make ordinary labels look faded.
2. As a Windows Terminal user, I want default command output and profile text to remain clear in Light mode, so that long command sessions are comfortable to read.
3. As a Windows Terminal user, I want tab, tab-row and window labels to use the correct foreground for their actual background, so that chrome text does not inherit a weak content color.
4. As a VS Code user, I want editor text to use an opaque neutral primary foreground, so that code and prose remain readable on the Light editor surface.
5. As a VS Code user, I want panel, sidebar, activity bar, title bar, status bar and tab text to use field-appropriate foregrounds, so that the workbench does not contain isolated blurry regions.
6. As a VS Code user, I want menus, inputs, lists, widgets, breadcrumbs and settings text to have explicit foreground/background pairs where the built-in Light themes distinguish them, so that secondary UI remains legible.
7. As a TRAE user, I want the standard VS Code Light fields to receive the same readability treatment, so that common workbench areas are consistent across editor variants.
8. As a TRAE user, I want discoverable TRAE-specific fields to be checked against evidence before being mapped, so that unsupported private fields are not guessed.
9. As a Codex user, I want the Light theme's `ink` and ordinary reading text to use a neutral high-contrast role, so that the application remains readable without losing the Seed Color identity elsewhere.
10. As a Chrome user, I want toolbar, tab, bookmark, omnibox and NTP text to be readable against their generated Light backgrounds, so that the browser chrome does not look washed out.
11. As a user, I want Seed Color identity to remain visible in Tonal surfaces, Accent, borders, selections and semantic states, so that neutralizing primary text does not remove the theme's visual identity.
12. As a user, I want inactive, placeholder and descriptive text to remain visually secondary without becoming indistinguishable, so that hierarchy is preserved.
13. As a user, I want selected controls and state messages to retain their own readable foreground/background pair, so that selection, error, warning and success states remain clear.
14. As a user, I want syntax highlighting and ANSI semantic colors to remain distinct from ordinary reading text, so that code and terminal states do not collapse into a monochrome theme.
15. As a user, I want Light primary text to remain readable across both representative Seed Colors, so that the fix is not tuned to one green or one yellow input.
16. As a user, I want Preview and Verify to expose field-level evidence and capability status, so that a partial result explains which fields were supported and how they were mapped.
17. As a user, I want unsupported undocumented fields to remain unchanged and reported as unsupported or partial, so that the tool does not alter unknown application behavior.
18. As a maintainer, I want the Field Evidence Matrix to come from the existing Field inventory, so that tests, reports and documentation cannot silently diverge.
19. As a maintainer, I want installed-version built-in themes and official schemas recorded as evidence, so that a future field-mapping change has a reviewable basis.
20. As a maintainer, I want the shared Palette Seam tested before Target-specific seams, so that a common readability failure is fixed once rather than repeated in every Adapter.
21. As a maintainer, I want Adapter tests to catch Dense primary text mapped to `muted_foreground`, transparent colors or state colors, so that field-mapping regressions fail early.
22. As a maintainer, I want fixture tests to remain deterministic and real screenshots to remain a separate manual gate, so that the default suite is reliable without pretending to prove visual rendering.
23. As a maintainer, I want the existing Preview → Apply → Verify → Rollback safety contracts unchanged, so that readability improvements do not weaken reversibility.

## Implementation Decisions

- The highest implementation Seam is the shared Palette generator. It owns Light `foreground` generation and the existing contrast/appearance validation; it does not learn Target-specific field names.
- The existing Field inventory remains the only structured registry. Extend its field entries with text class, paired background role, opacity policy, reference theme and evidence source rather than introducing a second registry.
- The human-readable Field Evidence Matrix is derived from the same inventory data. It records public meaning, Mode, UI state, adjacent UI region, expected Visual role, expected background role, source and version baseline.
- Evidence source precedence is: installed-version built-in Light themes, official public theme schemas, then user themes as supplementary evidence. Arbitrary online theme colors are not a normative source.
- Dense primary text includes editor and terminal bodies, command output, panels, sidebars, tabs, menus, toolbars, browser text and Codex `ink`.
- Dense primary text excludes syntax highlighting, ANSI semantic colors, selection text, disabled text, placeholder text, description text and error/warning/success state text.
- Light Dense primary text uses the existing `foreground` Visual role. The role is generated as opaque, low-chroma Neutral primary text rather than a strongly Seed-colored gray.
- `background_foreground` continues to serve deep backgrounds. `muted_foreground` continues to serve inactive, placeholder and description fields. Existing semantic `*_text` roles continue to serve syntax, ANSI and state semantics.
- No new `neutral_foreground` Palette role is added initially. A new role requires Field Evidence Matrix evidence that an existing role cannot represent the semantic distinction.
- Light Dense primary text must reach `7:1` against its actual surface. Other ordinary or state text keeps the applicable `4.5:1` target, and deep-background text keeps `7:1`.
- Dense primary text must be opaque. It must not use `muted_foreground`, transparent colors or semantic state colors. Transparency remains available for backgrounds, selections and decorative regions where the Target schema supports it.
- Target Adapters remain responsible for mapping public fields to Visual roles and actual background pairs. They are not allowed to copy colors from reference themes.
- Fix order follows the smallest shared Seam: fix shared Light `foreground` generation when multiple Targets fail; fix one Adapter when one Target or field fails; leave unverifiable private fields unsupported or partial.
- Windows system mode, automatic accent selection, high contrast settings, Chrome manual activation and all existing Preview/Apply/Verify/Rollback contracts remain unchanged.
- The change covers all six Targets and two representative Light Seed Colors: `#10B981` and `#FFD700`.

## Testing Decisions

- Tests assert external behavior at the highest available Seam. They inspect generated Palette/Plan data, field inventory reports, JSON/TOML/theme artifacts and AdapterResult metadata rather than private color helper calls.
- Palette tests cover Light Neutral primary text, opacity, `7:1` Dense primary text contrast on the actual Light surface, existing `4.5:1` secondary/state contrast, deep-background `7:1`, surface separation and preservation of Seed Color identity in non-text roles.
- Field inventory tests cover the new evidence metadata, stable source/version values, text classifications and paired background roles. They also verify that existing inventory consumers continue to receive field-level capability information.
- VS Code-family tests compare generated Light theme fields against the evidence-backed mapping for editor, terminal, panel, sidebar, activity bar, title bar, status bar, tabs, lists, menus, inputs, widgets, breadcrumbs, settings, links and diagnostics.
- Windows Terminal tests compare Light Scheme fields, default foreground/background pairs, tab/window text fields and ANSI/state mappings against the inventory; semantic ANSI colors are not treated as Dense primary text.
- Codex tests verify Light `ink` and known Light table fields use the neutral primary role while semantic colors retain their dedicated roles and unknown configuration keys remain preserved.
- Chrome tests inspect Light manifest colors and text fields for toolbar, tabs, bookmarks, NTP and omnibox against their expected background roles.
- Windows tests verify the supported user-visible outputs remain safe and that the readability work does not change system mode, automatic colorization or high-contrast behavior.
- Regression tests explicitly fail if a Dense primary text field is mapped to `muted_foreground`, a transparent value or a semantic state color.
- Two manual screenshot passes cover all six Targets for `#10B981` and `#FFD700` in Light mode. A passing fixture suite is not sufficient for visual acceptance.
- The existing repository patterns for Palette tests, Field inventory reports, Adapter artifact tests, fixture backends and separate real-desktop checks are reused. No new test framework or runtime service is introduced.
- Verification for the documentation-only planning phase is `git diff --check`. Runtime implementation must additionally run the repository's standard test and CLI checks.

## Out of Scope

- Changing Dark Mode behavior except where paired-mode tests are needed to ensure Mode coherence is preserved.
- Copying concrete colors from VS Code, TRAE or other existing themes into One-Tone output.
- Raising every text field to `7:1`; secondary, semantic and state fields retain their distinct roles and applicable thresholds.
- Fonts, font weight, layout, spacing, rendering engines, animations or accessibility settings outside the stated color mappings.
- Undocumented or private Target fields that cannot be discovered and verified.
- Adding a second Field inventory, a new theme plugin framework, a database, a background watcher or a rendering service.
- Automatic Chrome activation or automatic Windows mode switching.
- Committing user-specific screenshots or treating the supplied screenshots as a substitute for the six-Target matrix.

## Further Notes

- The confirmed architectural trade-off is to neutralize Light Dense primary text while retaining Seed Color identity in surfaces and emphasis roles.
- The accepted rationale is recorded in ADR 0008, and the terms Field Evidence Matrix, Dense primary text and Neutral primary text are part of the project glossary.
- The implementation should update the versioned Field inventory and its evidence report before changing Adapter mappings, so that every mapping change has a documented reason.
- Real screenshots should be captured only after fixture outputs, field-level reports and generated artifacts pass. Failures should be classified as shared Palette, Adapter mapping, Target rendering limitation or unsupported field.
