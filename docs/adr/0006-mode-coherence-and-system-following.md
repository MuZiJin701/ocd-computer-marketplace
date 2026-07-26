# ADR 0006: Mode coherence and system-mode following

## Status

Accepted — 2026-07-26; supersedes the auto-detect preservation parts of ADR 0003.

One-Tone keeps Light and Dark as variants of one Seed Color: corresponding large-area roles must retain their hue and ordering, and their OKLCH lightness difference must not exceed `0.35`. Apply enables native system-mode following where a Target supports paired themes (Windows Terminal, VS Code and TRAE; Codex already uses `system`), while Chrome remains manual and Windows system mode is never changed or watched by a background service.

