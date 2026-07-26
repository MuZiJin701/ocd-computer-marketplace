# Apply/Verify JSON 报告安全化开发说明

## Problem Statement

Windows Target 的 `AccentPalette` 是二进制值。Apply 和 Verify 将包含该值的 Field inventory 放入机器可读 JSON 报告时，CLI 输出边界直接调用 JSON 序列化器，导致 `TypeError: Object of type bytes is not JSON serializable`。

这会让用户看到主题操作已经产生结果，却得到失败的命令退出码或不可解析的 JSON；自动化调用方也无法可靠读取 Apply、Verify 的状态。事务持久化已有二进制报告表示，但 CLI 输出没有复用同一安全边界。

## Solution

在统一的 CLI JSON 输出边界递归应用现有的 JSON-safe 报告转换，将二进制值转换为无损、可解析的报告表示，再交给标准 JSON 序列化器输出。

Apply 和 Verify 继续返回现有状态、Target、Field inventory、Transaction ID 和错误语义；Snapshot 仍保存并恢复原始值，Serialized report value 只承担诊断和机器读取职责。

## User Stories

1. As a Windows 用户, I want Apply to emit valid JSON when `AccentPalette` is binary, so that a successful theme operation is not reported as a serialization failure.
2. As a Windows 用户, I want Verify to emit valid JSON for the same Windows fields, so that verification results remain readable after Apply.
3. As an automation caller, I want every JSON-mode CLI response to be parseable JSON, so that I can consume status and Target results without special-case exception handling.
4. As an automation caller, I want binary report values to use a lossless representation, so that diagnostics do not silently change the reported value.
5. As a One-Tone 用户, I want the existing `ok`, `partial`, `failed` and `skipped` statuses to remain unchanged, so that JSON safety does not alter workflow meaning.
6. As a One-Tone 用户, I want Apply to retain its existing Transaction and rollback behavior, so that fixing output does not weaken recovery.
7. As a One-Tone 用户, I want Verify to remain read-only, so that making its output safe does not create a Transaction or Snapshot.
8. As a maintainer, I want one shared output-boundary fix, so that Apply, Verify and JSON error responses cannot drift into different serialization rules.
9. As a maintainer, I want the existing `json_safe` representation reused, so that the fix does not introduce another binary encoding or dependency.
10. As a maintainer, I want the root test harness and Skill runtime boundary unchanged, so that the fix remains local to the existing CLI contract.

## Implementation Decisions

- The highest test and implementation Seam is the shared CLI JSON emitter used by Apply, Verify and JSON error responses.
- The emitter reuses the existing recursive JSON-safe conversion used by Transaction persistence before calling the standard JSON serializer.
- Binary values use the existing lossless marker-and-Base64 Serialized report value representation; ordinary strings, numbers, lists and mappings retain their current JSON values.
- The conversion applies recursively to nested metadata and Field inventory entries, including generated Windows registry values.
- Human-readable output remains unchanged.
- Apply and Verify status aggregation, exit codes, output fields and error handling remain unchanged except that valid JSON is emitted instead of a serialization exception.
- Transaction JSON schema, Snapshot contents, Snapshot restoration, Plan integrity, Transaction IDs and Rollback behavior are unchanged.
- No new serializer abstraction, dependency, persistence format or runtime seam is introduced.

## Testing Decisions

- Tests assert external CLI behavior: the output parses as JSON, preserves status and Target fields, and represents nested binary values without raising an exception.
- A CLI JSON-output test must cover a payload containing nested binary report data, using the existing output seam rather than testing a new private helper.
- Apply and Verify coverage must include a Windows fixture result containing a binary generated value and confirm both commands return valid machine-readable JSON.
- Existing Transaction tests continue to verify that binary report values persist and that Snapshot-based Rollback restores the exact original bytes.
- Existing tests for human-readable output, status aggregation and Verify read-only behavior remain unchanged.
- Verification uses the repository’s existing commands: `uv run pytest`, the Skill CLI help command and `git diff --check`.

## Out of Scope

- Changing Windows registry values, `AccentPalette` generation or Windows Target support.
- Changing the Transaction JSON schema, Snapshot format or Rollback semantics.
- Adding a general binary deserializer to CLI consumers; the report representation is diagnostic and does not replace Snapshot data.
- Changing Preview, Apply, Verify or Rollback status semantics, confirmation requirements or exit-code policy.
- Fixing VS Code registration, Chrome activation, TRAE AI panels or other unrelated Target behavior.
- Running real desktop Apply or Verify as part of the default test suite.

## Further Notes

This is the focused implementation spec extracted from the broader project-slimming discussion. The fix should remain a small boundary change: serialize once at the shared CLI output seam, keep the existing report representation, and leave persistence and recovery responsibilities separate.
