# ADR 0008: Evidence-backed Light text readability

## Status

Accepted — 2026-08-03

## Context

Light themes can satisfy the existing numeric contrast checks while still looking blurry in real application screenshots. Existing Light themes show that readability depends on more than a shared foreground value:

- dense reading text uses an opaque, low-chroma foreground;
- inactive, placeholder and description text use separate weaker roles;
- controls and selections define paired background/foreground fields;
- syntax, ANSI and semantic state colors remain distinct from ordinary reading text.

The current project already has a shared Palette seam and a versioned Field inventory, but it does not yet record enough evidence to distinguish a weak Palette role from an incorrect Target field mapping.

## Decision

1. Use a Field Evidence Matrix to record each relevant Color field's public meaning, Mode, state, adjacent background, evidence source and reference theme.
2. Extend the existing Field inventory to carry that evidence and text classification; do not create a second independent field registry.
3. Use installed-version built-in Light themes as the primary behavioral evidence, official schemas as the source of field meaning, and user themes only as supplementary evidence.
4. Define Light Dense primary text as continuous-reading UI text: editor and terminal bodies, command output, panels, sidebars, tabs, menus, toolbars, browser text and Codex `ink`. Exclude syntax/ANSI semantic colors, selection, disabled, placeholder and status text.
5. Reuse the existing `foreground` Visual role for Light Neutral primary text. Keep `background_foreground` for deep backgrounds and `muted_foreground` for secondary text; add a new Palette role only when evidence proves an independent semantic is required.
6. Light Dense primary text must be opaque, low-chroma and at least `7:1` against its actual surface. Other ordinary/state text keeps the applicable `4.5:1` target; deep-background text keeps `7:1`.
7. Diagnose at the smallest shared seam: fix the shared Light `foreground` generation when multiple Targets fail, then fix an individual Adapter mapping when one Target or field fails, and leave unverifiable private fields unsupported.
8. Accept the change only when fixture checks and real Light screenshots both pass for all six Targets using representative Seeds `#10B981` and `#FFD700`.

## Consequences

- Light primary text becomes more readable without forcing Seed Color hue into every text field.
- Adapter mappings become evidence-backed instead of relying on field-name similarity.
- The Field inventory and Verify reports gain enough context to explain why a field uses a role and background pair.
- Real screenshots remain a separate manual acceptance gate; passing fixtures alone is insufficient.
- Some semantic and inactive text remains below the primary-text target by design.

## Rejected alternatives

- Raising every text field to `7:1`, which would flatten semantic and state distinctions.
- Copying colors directly from an existing theme, which would discard the user's Seed Color and Mode coherence.
- Adding a new `neutral_foreground` role immediately, which duplicates the existing `foreground` seam before evidence requires it.
- Patching each Adapter independently, which would leave shared Palette failures duplicated and inconsistent.
- Treating private or undocumented fields as supported based on visual similarity alone.
