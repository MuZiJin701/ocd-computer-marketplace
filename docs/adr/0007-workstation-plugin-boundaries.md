# ADR 0007: Workstation Plugin boundaries

## Status

Accepted — 2026-07-26

## Context

The Marketplace now includes two workstation capabilities in addition to One-Tone: desktop organization and baseline toolchain setup. Both capabilities modify user-visible Windows state, but they have different ownership, rollback and external-tool boundaries.

The desktop capability deletes shortcuts and moves other desktop content. The toolchain capability preserves existing software and installs only missing Python, Git, uv and Node.js, preferring Scoop under a fixed D-drive root. A shared runtime or background service would make the independently distributable Skills harder to install, test and roll back.

## Decision

1. `ocd-desktop-zero` and `ocd-scoop-toolchain` are separate Plugin envelopes, each containing one self-contained Skill runtime.
2. `ocd-desktop-zero` owns the current user’s Resolved desktop and `D:\data` category destinations. It does not process the Public Desktop or other users.
3. `ocd-scoop-toolchain` owns `D:\software\scoop`. It preserves unrelated content in `D:\software` and does not uninstall or reset existing tools.
4. The two Plugins do not import a shared root runtime and do not install a background enforcement service. Shared behavior is represented through documentation and external result conventions until a second real implementation justifies a reviewed seam.
5. Each Skill keeps its own Preview, explicit confirmation, Apply and Verify boundary. Desktop file moves have explicit transaction-ID rollback; deleted shortcuts are not restorable. Winget fallback is allowed but reports path non-conformity when Windows chooses the installation path.

## Consequences

- Users can install or invoke desktop organization and toolchain setup independently.
- Tests remain local to each Plugin and can use separate fake desktop, process and installer backends.
- Some workflow logic is intentionally duplicated across Skill runtimes; this preserves independent distribution and avoids premature shared infrastructure.
- The Marketplace and Plugin metadata must register both new envelopes, and README, Skill and testing documents must describe their distinct safety boundaries.
- Adding background enforcement, broad deletion, cross-Plugin imports or a third directory-initialization Plugin requires a new architectural decision.

## Rejected Alternatives

- One combined workstation Plugin: rejected because desktop deletion and toolchain installation have different user consent and recovery boundaries.
- A shared root runtime: rejected because no second implementation currently justifies cross-Plugin coupling.
- A background service that blocks non-Search launches: rejected because Skill invocation is the product boundary and continuous enforcement would add hidden system state.
- A Plugin that owns and clears all of `D:\data` or `D:\software`: rejected because existing user content must be preserved.
