# ADR 0004: Appearance-safe Palette generation

## Status

Accepted — 2026-07-25

## Context

The existing Palette generator validates text contrast and region separation, but a high-saturation Seed Color can still produce an unpleasant result. Contrast repair may select pure black for Accent, Border or Surface roles, while the raw Seed Color may be used as a large background. A red input can therefore pass numerical validation and still produce a harsh red/black interface.

## Decision

1. Seed Color is the immutable Theme anchor and Accent source, not a mandatory large-area Surface value.
2. Large-area roles use low-chroma Tonal surfaces with explicit Light/Dark tone ladders.
3. Accent retains the Seed Color hue within a bounded tolerance and adjusts lightness/chroma instead of falling back to black or white.
4. Palette generation uses OKLCH/OKLab-style perceptual controls; WCAG relative luminance remains the independent readability check.
5. Ordinary roles cannot use pure black or pure white as an unqualified contrast fallback.
6. Target mappings must preserve the distinction between large surfaces, text, Accent and interactive states. Chrome tints cannot be fixed all-zero HSL values.

## Consequences

- Red and other extreme colors remain recognizable without covering the UI in raw saturated color.
- Numerical contrast checks are complemented by explicit appearance constraints.
- Existing Target mappings and tests need review because some currently assume `surface == Seed Color`.
- The algorithm becomes more deliberate, but remains deterministic and dependency-light.

## Rejected Alternatives

- Keeping raw Seed Color as every large Surface and accepting uncomfortable output.
- Fixing every bad result in individual Adapters instead of correcting the shared Palette seam.
- Using only black/white fallback because it maximizes contrast but destroys semantic color identity.
- Replacing objective contrast checks with a subjective screenshot-only review.
