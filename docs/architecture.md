# Architecture

## Marketplace shape

The repository root is the Marketplace. It contains the Marketplace manifest, shared active documentation, the root test harness and one or more Plugin packages.

~~~text
.
├─ .agents/plugins/marketplace.json
├─ plugins/
│  ├─ README.md
│  └─ <plugin-name>/
│     ├─ .codex-plugin/plugin.json
│     ├─ README.md
│     └─ skills/
│        └─ <skill-name>/
│           ├─ SKILL.md
│           ├─ agents/
│           ├─ references/
│           ├─ scripts/
│           └─ runtime project
├─ tests/
│  ├─ README.md
│  ├─ marketplace/
│  └─ plugins/<plugin-name>/skills/<skill-name>/
│     └─ runtime/
├─ docs/
│  ├─ agents/
│  ├─ specs/
│  ├─ adr/
│  ├─ architecture.md
│  └─ testing.md
├─ CONTEXT.md
└─ pyproject.toml
~~~

The Plugin is the installable envelope. The Skill is the independently distributable capability. A Skill runtime belongs inside its Skill package; it must not depend on the Marketplace root or another Plugin.

## Runtime seams

- Plan Palette generation is the highest shared Seam for Seed Color, Mode and Visual role calculation.
- Each Target Adapter is the next Seam for mapping public Color fields to Palette roles and for Detect, Snapshot, Apply, Verify and Rollback.
- Transaction persistence is the safety Seam; it records each Target operation and keeps compensation local to the failed Target.
- Field inventory is the documentation and testing Seam; it defines expected coverage without coupling tests to private implementation helpers.
- Marketplace metadata is the installation Seam; it points to Plugin envelopes but does not contain runtime logic.

Do not add a shared runtime or cross-Plugin import layer until two Plugins genuinely need the same behavior. Reuse repository tooling and documentation conventions, not hidden runtime coupling.

## Responsibilities

- Marketplace manifest: list installable Plugin envelopes.
- Plugin envelope: provide Codex metadata and own its Skills.
- Skill package: provide instructions, references, launcher and runtime for one capability.
- Root test harness: run repository-wide marketplace, Plugin, Skill and runtime tests.
- Palette: generate explicit Light/Dark Visual roles, preserve Mode coherence across one Seed Color and validate text, region contrast and cross-Mode appearance.
- Plan: serialize Seed Color, light/dark Mode Palettes, Target selection and field capability expectations with an integrity hash. `palettes` is the only persisted Palette representation; the selected `mode` is the default lookup mode, not a system-mode switch.
- Storage: validate safe path components and perform atomic persistence.
- Transaction: journal Apply operations, preserve Snapshots and coordinate compensation.
- Target Adapters: map public field inventories to Palette roles and report field-level capability.
- CLI: expose Preview, Apply, Verify and Rollback without bypassing the workflow.

## Test layout

Tests mirror the distribution hierarchy:

- marketplace tests validate the manifest and cross-package indexes;
- Plugin tests validate the Codex envelope;
- Skill tests validate the distributable Skill package;
- runtime tests live below the matching Plugin and Skill so a future Plugin cannot accidentally reuse another Plugin's fixtures or assumptions.

## Structure audit

### Correct choices

- The Marketplace manifest is separate from Plugin metadata.
- Each Plugin has its own envelope and Skills directory.
- The first Plugin owns the complete One-Tone Skill runtime.
- The root harness is not packaged as a runtime distribution.
- Tests can exercise the Skill source without being shipped with it.

### Costs kept explicit

- The Skill path is deep because the distribution boundary is real.
- The root harness and Skill runtime have separate uv projects; commands must name which project they target.
- Plugin-specific runtime tests are more verbose in exchange for locality and future multi-Plugin isolation.

### Rules for future Plugins

1. Add one direct child under plugins.
2. Add one local Plugin envelope and README.
3. Put every Skill under that Plugin's skills directory.
4. Keep each Skill runtime self-contained.
5. Add matching tests under tests/plugins/<plugin>/skills/<skill>/.
6. Register only the Plugin envelope in the Marketplace manifest.
7. Do not move shared code into a root runtime until a second real implementation needs it and the seam has been reviewed.
