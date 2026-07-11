# Workflow and safety contract

## State flow

```text
Preview → Plan → Apply → Verify → Rollback
```

`preview` creates a deterministic Palette from the seed color, detects the selected targets, validates the Palette contrast, and saves `plans/<plan_id>.json`. It is read-only with respect to the system and application targets.

`apply` loads exactly `plans/<plan_id>.json` and verifies its hash before doing anything. It creates `transactions/<transaction_id>/`, saves target snapshots in that transaction's `backup/` directory, and applies only targets present in the Plan. If a later target fails, already changed targets are automatically restored from the same transaction.

`verify` runs the complete eight-step flow and leaves the target restored. Use `--restart-apps` only when closing and reopening the supported apps is acceptable. A normal automated test result is not evidence that the real installed target is `FULL`.

`rollback` takes an explicit transaction ID. It never searches for another transaction's backup and it re-verifies the restored state through the adapter result.

## Confirmation gates

- Do not call Apply or Verify until the user has seen the Plan ID and explicitly confirmed the change.
- Do not pass `--restart-apps` without a separate warning about unsaved work.
- Do not claim that a target is supported merely because an executable or settings file exists; report the adapter's structured result and support level.
- Do not apply an unverified target. `skipped` and `partial` are valid outcomes and must be shown to the user.

## Result interpretation

Every target result contains `target`, `status`, `changed`, `verified`, and `message`; it may also contain `requires_user_action` and `version`. The JSON CLI output is the stable interface for wrappers and automation. `FULL` requires the real eight-step cycle, a detected version, successful verification, and no user action requirement.
