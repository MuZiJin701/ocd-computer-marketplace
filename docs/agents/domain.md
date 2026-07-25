# Domain docs

This is a single-context repository.

## Before exploring

1. Read the root CONTEXT.md.
2. Read relevant files in docs/adr/.
3. Read docs/architecture.md or docs/testing.md when the task changes runtime boundaries or verification.

Use the terms defined in CONTEXT.md for issue titles, plans, tests, and implementation discussion. If a needed term is missing or ambiguous, record the ambiguity before inventing a new synonym.

## Layout

~~~text
CONTEXT.md                 # shared domain vocabulary and invariants
docs/
  agents/                  # engineering-skill configuration
  adr/                     # architecture decision records
  specs/                  # active development specifications
  architecture.md          # implementation boundaries
  testing.md               # verification contract
~~~

CONTEXT.md is a glossary, not an implementation spec. Read the active development spec for feature decisions, docs/architecture.md for module seams and structure, and docs/testing.md for verification contracts.

The current package boundary is intentional: the Skill owns the distributable runtime and the root project owns the test harness. Do not move runtime code merely to shorten the path.

ADRs are added only for durable architectural decisions. Do not create placeholder ADRs for ordinary changes.
