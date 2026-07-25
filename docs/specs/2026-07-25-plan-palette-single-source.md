# Plan/Palette 单一事实源开发说明

## Problem Statement

当前 Plan 同时保存单套 `palette` 和按 Mode 保存的 `palettes`。不同 Adapter 读取入口不一致：有的使用选中 Mode，有的直接读取单套 Palette。这会让 Plan hash、Apply 输入和生成产物之间出现不易发现的偏差，新增或修改 Adapter 时尤其容易误用旧入口。

旧格式 Plan 只有一套 Palette，无法可靠推导缺失的另一种 Mode。若继续自动补齐，工具可能在 Apply 时生成用户没有 Preview 和确认过的主题数据。

## Solution

把 Plan 的 Mode Palette 集合收敛为唯一事实源：每个新 Plan 只保存 `light` 和 `dark` 两套 Palette，顶层 Mode 仅表示用户在 Preview 中选择的默认读取 Mode。所有 Adapter 通过统一的 Mode 读取边界获取 Palette，并保持各 Target 当前的单 Mode 或双 Mode 产物行为。

旧的单套 Palette Plan 不自动迁移，必须重新执行 Preview。这样 Apply 只使用经过当前规则生成、校验并纳入 hash 的完整 Plan。

## User Stories

1. As a Windows 用户, I want a Plan to contain one authoritative Palette set, so that Preview and Apply cannot use different color data.
2. As a Windows 用户, I want the selected Mode to remain the default lookup Mode, so that existing single-Mode behavior stays predictable.
3. As a Windows 用户, I want light and dark Palettes to be generated together, so that a Plan never silently invents a missing Mode during Apply.
4. As a Windows 用户, I want an old single-Palette Plan to be rejected clearly, so that I know when a new Preview is required.
5. As a maintainer, I want malformed or incomplete Mode Palette data rejected before Apply, so that invalid theme data cannot reach a Target Adapter.
6. As a maintainer, I want Palette reads to be isolated from Plan internals, so that an Adapter cannot accidentally mutate the Plan used for hash validation.
7. As a maintainer, I want single-Mode and paired-Mode Adapters to keep their existing responsibilities, so that this cleanup does not expand the Adapter interface or change unrelated Target behavior.
8. As a maintainer, I want Plan hashes to cover the canonical Palette set, so that persisted Plans remain tamper-evident and reproducible after reload.
9. As a maintainer, I want regression tests to cross the Plan/Palette Seam, so that tests verify persisted Plans and generated artifacts rather than private helper structure.

## Implementation Decisions

- The highest shared Seam is the Plan/Palette boundary. Target-specific field mapping remains inside each Adapter.
- A new Plan persists exactly two Mode Palettes, `light` and `dark`, under the canonical `palettes` representation. The single `palette` representation is removed from new persistence and from the Plan API.
- The top-level `mode` remains part of the Plan as the selected/default lookup Mode. It does not authorize or perform a Windows light/dark system-mode change.
- The Mode lookup boundary returns a copy of the selected Palette. No new Palette value object is introduced; existing Palette data and visual-role rules remain unchanged.
- Plan serialization and hash calculation use the canonical `palettes` representation. Palette ordering must not change the canonical hash after save and reload.
- Plan loading requires exactly `light` and `dark`, validates both Palettes with the existing Palette validation rules, and rejects missing Modes, extra Modes, inconsistent Palette data and hash mismatches.
- A persisted Plan containing only the legacy single `palette` field is rejected as expired. It is not migrated by copying one Palette into both Modes or by guessing the missing Mode.
- Adapters that produce one Mode use the Plan's selected/default Mode. Adapters that already produce paired artifacts explicitly read both Modes. Adapter interfaces and Target-specific responsibilities do not change.
- Existing standalone Palette generation behavior is not redesigned. This spec changes the Plan boundary and its consumers, not the Palette algorithm or the Target Field inventory.
- Transaction workflow, Plan ID safety, Snapshot rules, Apply/Verify/Rollback contracts, Field inventory, and Target coverage are unchanged.

## Testing Decisions

- Tests cross the highest available Plan/Palette Seam and assert observable behavior: serialized Plan shape, hash stability, load failures and generated Adapter artifacts.
- Plan tests verify that new persistence contains `palettes` with exactly both Modes and no legacy `palette` field.
- Plan loading tests verify rejection of legacy Plans, missing or extra Modes, invalid Palette content, inconsistent Mode data and tampered hashes.
- Read-isolation tests verify that changing the value returned by the Mode lookup boundary does not mutate the Plan's stored Palette.
- Adapter regression tests verify that single-Mode outputs use the selected Mode and paired outputs use both Mode Palettes. They should assert generated files or payloads, not private helper calls.
- Existing transaction, Field inventory and real-desktop test boundaries remain unchanged. This cleanup does not add a new service, database, background process or live desktop dependency.
- Completion requires the repository's existing full test suite, runtime CLI help check and whitespace check to pass. No commit or external deployment is part of this spec.

## Out of Scope

- Redesigning the Palette algorithm, Visual roles or contrast thresholds.
- Adding a Palette value object, database, cache, service or new Adapter abstraction.
- Making every Target apply both Modes when its current artifact is single-Mode.
- Changing Windows system mode, automatic accent selection or high-contrast settings.
- Changing Chrome activation behavior or Target Field inventory coverage.
- Migrating, repairing or silently rewriting old persisted Plans.
- Replacing the existing Transaction workflow or changing Preview, Apply, Verify or Rollback safety contracts.
- Real desktop validation or screenshot collection.

## Further Notes

This is a focused architecture follow-up to the broader theme-field coverage work. The intended change is deliberately narrow: one canonical Palette source and one read boundary, with the smallest possible impact on existing Adapter seams. The existing field-coverage development specification remains the source for Target coverage, contrast and visual acceptance requirements.

