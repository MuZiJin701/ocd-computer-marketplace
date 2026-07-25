# ADR 0005: Skill-local runtime root

## Status

Accepted — 2026-07-25

## Context

The CLI previously defaulted to a relative `.one-tone` path. Because relative paths follow the process current working directory, an Agent could create separate Plans, Transactions, wallpapers and theme artifacts in unrelated directories.

The user wants the generated runtime data to stay beside the installed Skill package, where the Skill and its generated artifacts are easy to inspect together.

## Decision

The default runtime root is the Skill-local runtime root: the directory containing the installed Skill package. The default `.one-tone` directory is resolved from the runtime module location and not from the current working directory, repository root, drive letter or Agent-specific path.

The root contains the existing `plans`, `transactions` and `state` subdirectories plus Target-specific generated artifacts. Tests and explicit advanced invocations may provide a temporary or alternate runtime root.

## Consequences

- Running the CLI from different directories uses the same `.one-tone` store for the same Skill installation.
- The runtime must derive its location from package/module resources, so the implementation remains portable across installations.
- Skill updates or replacement may affect colocated runtime data; rollback and persistence metadata must remain valid across normal package updates or provide a documented migration boundary.
- Test fixtures must always override the runtime root rather than writing into the installed Skill directory.

## Rejected Alternatives

- A relative `.one-tone` directory under the current working directory: rejected because Agents can scatter state across repositories and terminals.
- A repository-root directory: rejected because the Skill must not depend on a checkout or development workspace.
- A hard-coded absolute path: rejected because Skill installations can live on different drives and in different package managers.
- A user-profile-only default: rejected for this product decision because the user explicitly wants artifacts colocated with the installed Skill root.
