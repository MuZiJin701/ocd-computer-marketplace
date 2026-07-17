# Architecture

## Layers

```text
Marketplace
  └─ Plugin package
      └─ Skill package
          ├─ SKILL.md
          ├─ Python runtime
          └─ target Adapters
```

- `.agents/plugins/marketplace.json` lists installable Codex Plugin packages.
- `plugins/one-tone-windows/.codex-plugin/plugin.json` is an optional Codex wrapper.
- `plugins/one-tone-windows/skills/unify-windows-theme/` is the canonical Skill package.
- The Skill package owns `pyproject.toml`, `src/one_tone/` and its launcher.
- The root `pyproject.toml` is only the development/test entrypoint; it is not installable and does not expose a runtime command.
- The Skill `pyproject.toml` owns the `one-tone` console script and is the only runtime project.

## Runtime boundaries

- `palette.py`: Seed Color and contrast-safe, hue-coherent Palette. `surface` preserves the normalized Seed exactly; `foreground` and semantic text variants are selected for `surface` with a target of at least 4.5:1, while `background_foreground` is selected for the deep `background` with a target of at least 7:1.
- `plan.py`: immutable Plan, serialization and Hash validation.
- `storage.py`: safe path-component validation and atomic text/JSON persistence.
- `transaction.py`: per-target Apply journaling, compensation, Verify, rollback metadata and snapshot retention.
- `adapters/`: target-specific Detect, Snapshot, Apply, Verify and Rollback.
- `cli.py`: Preview, Apply, Verify and Rollback command wiring.

The runtime has no database, background service or plugin runtime framework.

## Palette and discovery semantics

- Codex `surface` is the normalized Seed Color in both `appearanceLightChromeTheme` and `appearanceDarkChromeTheme`; Codex `ink` maps to the chromatic `foreground`, Codex `accent` maps to Palette `accent`, and both Chrome theme tables use `contrast=100` without changing `appearanceTheme`.
- Codex semantic text fields use contrast-safe variants: `semanticColors.diffAdded` maps to `success_text`, `diffRemoved` to `error_text`, and `skill` to `accent_text`; Palette `accent` is reserved for visual emphasis surfaces, borders, and system accent values.
- Windows wallpaper is a solid PNG of the exact Seed Color. Windows registry accent values and the generated accent palette use Palette `accent`, never a darkened `surface`.
- Windows Apply does not write `AppsUseLightTheme`, `SystemUsesLightTheme`, or `AutoColorization`; the user's current mode and automatic color choice remain under user control.
- When `AutoColorization` is already enabled, Windows Detect/Apply/Verify reports `partial` and requires user action because Windows may recalculate the accent from the wallpaper after Apply. The runtime does not silently change that setting.
- Editor discovery uses PATH, standard per-user locations, and explicit environment overrides. No machine-specific absolute path or temporary path is required at runtime. Cursor remains isolated in source for future experiments but is not a production target.
- Preview defaults to the complete implemented target set and prints one detection result per target; `--targets` is an explicit narrowing option, not a required discovery input.

## Target field coverage

- Windows Terminal writes a named scheme with `background`, `foreground`, selection colors, cursor color, and all ANSI colors. Black/bright-black use the readable surface foreground instead of the background. The named window theme uses `applicationTheme = system`, so applying a palette does not force Windows Terminal or Windows into dark mode. Every discovered profile receives the scheme and tab color so profile-level overrides cannot leave stale, unreadable text behind. Field names follow the [Windows Terminal themes](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/themes) and [color schemes](https://learn.microsoft.com/en-us/windows/terminal/customize-settings/color-schemes) settings.
- VS Code and TRAE use the standard [Workbench color IDs](https://code.visualstudio.com/api/references/theme-color), including editor selection foreground, multi-cursor, terminal cursor and ANSI colors, links, notifications, lists, inputs, and diagnostic text. The theme enables `semanticHighlighting` and supplies `semanticTokenColors` according to the [semantic highlighting guide](https://code.visualstudio.com/api/language-extensions/semantic-highlight-guide); TextMate fallback rules remain in `tokenColors`. This covers the common workbench only, not proprietary AI panels.
- Chrome generates a Manifest V3 theme using the current [Chrome theme color fields](https://chromium.googlesource.com/chromium/src/+/HEAD/chrome/browser/themes/browser_theme_pack.cc), including active/inactive frame, toolbar text/icons, tab text, bookmarks, NTP text/links, and omnibox text. Activation remains a user action.

Transaction records are persisted after each target operation. Adapter results may carry JSON-safe target metadata; Chrome uses this to remove generated artifacts in a later Rollback process. VS Code-family Verify discovers the installed extension from the persisted extension directory rather than relying on adapter instance state.

`APPLIED` means every selected target completed successfully. `PARTIAL` means at least one target completed while another target was skipped, failed, or requires user action. `FAILED` means no target completed or compensation failed.
