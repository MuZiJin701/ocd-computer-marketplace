# ADR 0009: Portable Shell integration and taskbar mode recovery

## Status

Accepted — 2026-08-03

## Context

Real Light-mode screenshots exposed three gaps that are not solved by the shared `foreground` role alone:

- TRAE Git status decorations use public `gitDecoration.*` fields that were missing from the Field inventory.
- PowerShell/PSReadLine inline prediction is rendered by the Shell, not by Windows Terminal's Scheme, and its Profile configuration has host-specific discovery and rollback needs.
- Windows taskbar Accent display was only applied for Dark mode, so mode changes could lose the user-requested taskbar color.

The Skill must remain portable and distributable. It cannot assume a fixed user path, drive, installation manager, PowerShell version, PSReadLine version or machine-specific color. It must also preserve the existing Target and transaction safety boundaries.

## Decision

1. Extend the existing Field inventory with public Git decoration fields and evidence-backed semantic mappings. Reuse existing Palette semantic roles rather than adding a dedicated Git palette.
2. Treat PSReadLine prediction colors as an optional sub-capability of the `terminal` Target, not as a new top-level Target. Discover the host Profile and supported public fields during Preview, persist the resolved inputs in the Plan, and manage only the Windows Terminal session integration with Snapshot, Apply, Verify and Rollback.
3. Add a dedicated `prediction_foreground` Palette role. Generate it independently for Light and Dark so it remains neutral, readable against the actual Terminal surface, and perceptually distinct from `foreground` using `ΔE_OK >= 0.08` and contrast `>= 4.5:1`. Map inline and unselected list prediction text to this role; map selected prediction to the existing selection foreground/background pair. Do not change prediction sources or key bindings.
4. Attempt and Verify the same taskbar Accent display state in Light and Dark modes without changing Windows system mode, automatic colorization, high contrast or introducing a watcher. Report native Light-mode limitations as actual `partial` or `unsupported` capability.
5. Keep all new behavior behind public, discoverable, version-capability-checked seams. Unknown fields, unsupported hosts and undocumented configuration remain unchanged.

## Consequences

- TRAE and VS Code Git state remains readable without recoloring ordinary Explorer labels.
- Windows Terminal predictions become visibly distinct from typed commands while remaining tied to the generated Palette.
- Prediction colors no longer depend on `muted_foreground`, whose contrast can be valid while its visual difference from `foreground` is too small.
- The `terminal` transaction may include both Windows Terminal settings and a discovered PowerShell Profile; optional shell failure can produce `partial` without hiding successful Scheme changes.
- The user-requested taskbar state is tested across mode transitions, but some Windows builds may still report a native limitation in Light mode.
- Preview and Verify gain discovered-host metadata, and fixture tests must cover multiple PowerShell/PSReadLine capability shapes.

## Rejected alternatives

- Treating Git decorations as ordinary `foreground`, which leaves default green status colors on tinted Light surfaces.
- Changing only Windows Terminal `foreground`, which cannot control PSReadLine prediction rendering.
- Adding a fixed `powershell` top-level Target, which expands the user-facing target model for a capability deliberately scoped to Windows Terminal.
- Hardcoding `$PROFILE` paths, installed versions or per-machine ANSI colors, which breaks portability and distribution.
- Reusing `muted_foreground` for predictions, because readability alone does not guarantee a visible distinction from typed text.
- Running a background mode watcher, which adds a service/state boundary for a problem that can be verified and reported without one.
- Treating a successful `ColorPrevalence` registry write as proof that Windows visually displays a Light-mode taskbar Accent.
