# ADR 0003: User-facing theme coherence and field evidence

## Status

Accepted — 2026-07-25; auto-detect preservation is superseded by ADR 0006.

## Context

One-Tone is intended to apply a user's Seed Color consistently across Windows, Windows Terminal, VS Code, TRAE, Codex and Chrome. Windows system Light/Dark mode is an existing user preference, not the source of the Seed Color and not a setting that One-Tone may silently change.

Several Target behaviors are easy to confuse:

- a Mode Palette is not the Windows system mode;
- Windows Accent color is distinct from Taskbar accent display;
- an editor extension can be registered without its theme being active;
- Chrome needs separate static Light/Dark themes and produces more than one file format;
- a technical field list is not a human-readable explanation of what the user will see.

## Decision

1. Seed Color is the single visual source across Targets. Light and Dark are presentation variants of that Seed Color. One-Tone does not change Windows system mode, automatic accent selection or high-contrast settings.
2. Windows reports Accent color and Taskbar accent display separately. Light and Dark both attempt Taskbar accent display; a native Light-mode limitation is reported as `partial` without making the whole Windows Target fail. This supersedes the former Light-mode `not-applicable` rule; see ADR 0009.
3. VS Code and TRAE install one paired theme extension. Activation uses the exact contributed Light/Dark labels. The existing `window.autoDetectColorScheme` preference is preserved; automatic switching is not silently enabled or disabled.
4. Chrome exposes exactly two canonical user-facing unpacked directories: Light and Dark. ZIP files, compatibility aliases and transaction copies are internal artifacts and must not be presented as additional themes.
5. Every Target has a versioned Field inventory. The inventory records the official source, version baseline, technical field, Visual role, Mode support and capability status. Fields without a stable official schema are not guessed; TRAE-specific fields are used only when discovered and verifiable.
6. User-facing Preview and Verify group fields by visual region and show the technical field and evidence only as expandable detail. The user should choose a theme by Target and Mode, not by raw configuration key or generated filename.

## Evidence baseline

- Windows settings and color registry fields: [Windows common settings](https://learn.microsoft.com/en-us/windows/apps/develop/settings/settings-common)
- Windows Terminal profile and paired color schemes: [Profile appearance](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/profile-appearance), [Color schemes](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/color-schemes)
- VS Code color fields and theme contributions: [Theme Color Reference](https://code.visualstudio.com/api/references/theme-color), [Contribution Points](https://code.visualstudio.com/api/references/contribution-points)
- Chrome theme manifest fields and tints: [Chrome themes](https://developer.chrome.com/docs/extensions/develop/ui/themes)
- TRAE-specific fields: no stable public theme-field schema is assumed; use installed-version or public-theme discovery only.

## Consequences

- The system mode remains visible as context, but it is not allowed to overwrite the product's Seed Color semantics.
- Some Windows results can be partial even when the main Accent color is applied and verified.
- Editor activation becomes deterministic and no longer depends on a base label that is absent from the extension manifest.
- Chrome output becomes understandable: users choose one of two directories, while packaging and rollback metadata remain implementation details.
- Field inventory maintenance becomes an evidence-backed documentation task. Adding an undocumented field requires discovery and verification, not a guessed mapping.

## Rejected alternatives

- Forcing Windows into Dark or Custom mode to make Taskbar accent display available: rejected because it changes a user accessibility/personalization preference.
- Treating extension installation as theme activation: rejected because registration and activation are separate Target capabilities.
- Showing every ZIP, alias and transaction copy as a Chrome theme: rejected because it creates duplicate user choices without new visual behavior.
- Inferring TRAE-private fields from VS Code or implementation similarity: rejected because it cannot be verified against a public schema.
