# Testing

## Default verification

Run from the repository root:

~~~powershell
uv run pytest
uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help
git diff --check
~~~

The root project is a test harness. The Skill project owns the one-tone console script. Tests remain outside the distributable Skill and mirror the Marketplace → Plugin → Skill hierarchy. Runtime tests for One-Tone live under the matching Plugin and Skill test directory.

## Required coverage for the theme-field work

- Palette tests cover both light and dark modes, exact Seed Color anchor preservation, distinct surface roles, passive region separation and interactive boundary separation.
- Palette tests also cover appearance-safe Tonal surfaces, Theme anchor hue retention, bounded chroma, no unjustified pure-black/pure-white ordinary roles and extreme Seed Colors such as red, yellow, cyan and near-black.
- Palette and Plan tests also verify Mode coherence: explicit Light/Dark Accents retain one Seed Color identity, corresponding large-area roles stay within `0.35` OKLCH lightness difference, ordinary surfaces avoid near-white/near-black collapse, and incoherent persisted Mode pairs are rejected.
- Plan tests cover mode Palettes, field capability expectations and stable Plan hashes.
- Windows tests cover safe registry and wallpaper outputs, preserved mode/automatic-color/high-contrast settings, and field-level partial results.
- Windows Terminal tests cover paired Schemes, Profile `colorScheme` mappings, all profile entries, all documented color fields, Tab/Tab Row/window fields and system mode selection.
- VS Code and TRAE tests cover the standard public Workbench field inventory, exact contributed Light/Dark labels, enabled auto-detect settings and discoverable TRAE-specific fields.
- VS Code/TRAE instance tests cover standard and portable layouts, multiple-instance ambiguity, read-only path discovery, Plan-persisted paths, registration evidence, and non-zero CLI results with successful installation evidence.
- Codex tests cover every verified v1 color field in both theme tables and preserve unknown configuration keys.
- Chrome tests cover exactly two canonical Light/Dark unpacked directories, internal ZIP manifests, all public colors, tints and display properties, plus manual activation status.
- Transaction tests retain per-Target Snapshot, operation persistence, compensation and rollback behavior and cover JSON-safe binary report values.
- CLI tests cover parseable JSON-mode Apply and Verify responses when nested report metadata contains binary values.

## Test style

Tests cross the highest available Seam and assert external behavior:

- Generated Palette and Plan data, not private color helper calls.
- JSON, TOML and ZIP artifacts, not internal dictionary construction.
- AdapterResult status and field capability payloads, not logging text.
- Temporary files and fake registry/desktop backends for default tests.
- Real installed applications only in separately marked, risk-documented tests.

A passing fixture test is not proof that a real desktop Target renders every public field. Manual screenshots remain required for visual acceptance.

The runtime Plan stores both `light` and `dark` Palettes under one canonical `palettes` field. The legacy persisted `palette` field is rejected rather than guessed or migrated. `Plan.palette_for(mode)` returns a copy; single-mode Adapters use the Plan's selected mode, while paired artifact Adapters explicitly cover both modes. Existing v1 callers that invoke `generate_palette(seed)` retain the original single-palette shape; new Plan and artifact paths use explicit modes.
