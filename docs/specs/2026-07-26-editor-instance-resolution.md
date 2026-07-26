# VS Code/TRAE 配置实例发现与安装证据开发说明

## Problem Statement

VS Code 和 TRAE 可能同时存在标准安装、便携版安装或多个用户数据实例。当前如果只检查固定的用户目录，可能把实际已经安装成功的主题误判为失败；如果 CLI 返回非零，也可能只是同时报告了与主题无关的错误。错误判定会触发不必要的自动回滚，导致用户看到主题短暂生效后又恢复旧主题。

这个问题不能通过加入当前机器的固定盘符、用户名或 Scoop 目录来解决。One-Tone 必须在多用户、多安装和便携版 Windows 环境中，以可验证的方式找到一个活动 Target 配置实例，并依据最终状态证据判断主题是否成功。

## Solution

在现有 Target Adapter 的 Preview → Plan → Apply → Verify 流程中增加通用的配置实例发现和安装证据规则：

- Preview 只读地生成并校验候选路径，选择唯一的 Active Target instance。
- 选择结果包含启动器/可执行文件、设置文件和扩展目录，并写入 Plan、纳入 Plan Hash。
- Apply 和 Verify 使用 Plan 中的同一组路径，不重新猜测或静默切换到其他实例。
- Theme registration 由扩展登记、主题产物、贡献标签和设置文件组成的证据判断，CLI 退出码只作为辅助信号。
- CLI 非零但安装证据完整时保留修改并报告 `partial`；证据不完整时才回滚失败 Target。
- 找不到唯一可信实例时报告 `skipped`，不修改多个实例，也不创建候选目录。

## User Stories

1. As a Windows 用户, I want VS Code 主题操作定位到实际使用的配置实例, so that便携版安装不会被错误报告为失败。
2. As a Windows 用户, I want TRAE 主题操作定位到实际使用的配置实例, so that主题安装不会因固定默认目录错误而失败。
3. As a multi-user Windows administrator, I want each user’s environment and application directories to be resolved independently, so that One-Tone never modifies another user’s configuration。
4. As a user with multiple editor installations, I want the resolver to associate paths with the selected launcher or executable, so that a standard installation is not confused with a portable installation。
5. As a portable-app user, I want generic portable layouts to be recognized without mentioning a specific package manager, so that the feature remains useful across installation methods。
6. As a user with explicit editor launch arguments, I want `--user-data-dir` and `--extensions-dir` to take precedence, so that my deliberate profile selection is respected。
7. As a safety-conscious user, I want Preview to discover paths without creating directories, so that inspection cannot mutate my editor configuration。
8. As a user with ambiguous editor profiles, I want the target to be skipped instead of modifying several candidates, so that One-Tone does not guess which profile I intended。
9. As a user running Apply after Preview, I want Apply to use the paths recorded in the Plan, so that the operation remains tied to the configuration I reviewed。
10. As a user running Verify later, I want Verify to use the same paths as Apply, so that a changed environment cannot make Verify inspect a different editor instance。
11. As a user whose editor CLI reports an unrelated error, I want complete installation evidence to preserve the applied theme, so that an unrelated warning does not trigger data-changing rollback。
12. As a user, I want a non-zero CLI result with complete installation evidence to be visible as `partial`, so that I know the theme is applied while still seeing the CLI problem。
13. As a user, I want missing registration, missing theme files, or inconsistent labels to remain failures, so that a physical extension directory is not mistaken for a usable theme。
14. As a user applying themes to several Targets, I want an unresolved VS Code/TRAE instance to affect only that Target, so that successful Targets remain applied。
15. As a maintainer, I want VS Code and TRAE to share the existing editor Adapter seam, so that the fix does not duplicate common theme-field behavior。
16. As a maintainer, I want the path resolution result to be part of the Plan integrity boundary, so that Apply cannot silently act on an unreviewed path。
17. As a maintainer, I want tests to exercise standard, portable, ambiguous and failing-CLI scenarios, so that the false-success and false-failure cases remain covered。
18. As a maintainer, I want no dependency on usernames, drive letters, Scoop or another installer, so that the runtime remains distributable and portable。

## Implementation Decisions

- Reuse the existing Target Adapter and workflow seams. Do not introduce a service, database, background watcher, new dependency or separate editor runtime.
- Define an Active Target instance as one launcher/executable together with its user-data directory and extension directory. A Target may have more than one instance on one machine.
- Resolve candidates in this order: explicit launcher arguments; generic portable layout associated with the executable; operating-system environment variables and standard application defaults; then cross-validation against settings, extension registration, extension artifacts and contributed labels. Runtime discovery does not execute CLI queries that may create application state.
- Treat candidate discovery and Verify as read-only. Only Apply may create a missing extension directory after the Plan has selected that exact path.
- Require one candidate to establish consistent ownership by the same launcher/executable. If multiple candidates remain valid but indistinguishable, return `skipped` with an ambiguity reason and do not modify any candidate.
- Persist the selected executable, settings path and extension directory in the Target portion of the Plan and include them in the Plan Hash. Apply and Verify must consume these resolved values and must fail safely if they become unavailable; they must not rediscover a different instance.
- Define successful Theme registration using all of the following evidence: the target extension is present in the registration index; the registered artifact and theme files are readable; the package metadata exposes the expected Light/Dark labels; and the Plan-required settings and selected theme labels are readable and match.
- Treat a zero CLI exit code as supporting evidence only. If the CLI exits non-zero but all registration and activation evidence is valid, preserve the change and return `partial` with the CLI diagnostic. If required evidence is missing or inconsistent, return `failed` and roll back only that Target.
- Keep registration and activation as separate concepts. An extension can be registered without being the active theme; Verify must report the distinction through the existing AdapterResult and field capability data.
- Preserve existing aggregate status rules: a successful Target plus skipped/failed or user-action results produces overall `partial`; no successful Target produces overall `failed`.
- Use the existing transaction Snapshot and compensation behavior. This specification changes the failure decision boundary, not the recovery contract.
- Keep the existing supported Workbench fields and TRAE-specific discoverable-field boundary unchanged. This work addresses instance resolution and result classification, not new theme fields.

## Testing Decisions

The highest useful test seam is the existing Target Adapter workflow exercised through Preview, Plan, Apply and Verify. Tests should assert external behavior and persisted artifacts, not private path-scoring helpers or implementation-specific call order.

Tests will cover:

- standard user-directory resolution for VS Code and TRAE;
- generic portable layouts associated with an executable;
- explicit user-data and extension-directory arguments taking precedence;
- multiple valid candidates that resolve uniquely to one executable/profile;
- ambiguous candidates returning `skipped` without creating directories or modifying any candidate;
- Plan persistence and hash coverage for the selected executable, settings path and extension directory;
- Apply and Verify using the Plan paths even when another candidate appears later;
- stale or missing Plan paths failing safely without fallback to another instance;
- extension artifacts present without registration being rejected as incomplete registration evidence;
- missing theme files, missing contributed labels and mismatched settings being rejected;
- non-zero CLI exit with complete evidence returning `partial` and preserving the applied state;
- non-zero CLI exit with incomplete evidence returning `failed` and rolling back only the failed Target;
- aggregate status behavior when editor resolution is skipped alongside successful Targets.

Prior art is the existing VS Code/TRAE shared Adapter, AdapterResult status model, Plan Hash validation, transaction Snapshot/compensation tests, and CLI JSON report tests. No new test framework or separate integration service is needed. Real desktop verification remains separately marked and risk-documented.

## Out of Scope

- Hard-coding any username, drive letter, Scoop path, installation-manager path or undocumented private editor directory.
- Modifying multiple editor instances in one operation.
- Guessing an active instance when candidate evidence is ambiguous.
- Creating directories during Preview, path discovery or Verify.
- Changing the supported VS Code/TRAE theme-field inventory or adding coverage for TRAE private AI-panel fields that are not discoverable and verifiable.
- Changing the Preview, Apply, Verify, Rollback confirmation model, transaction identifiers, Snapshot ownership or compensation scope.
- Adding a background process to watch editor profiles or automatically repair moved installations.
- Silently migrating historical Plans or Transactions to a newly discovered path.

## Further Notes

The implementation should treat the current machine findings as regression examples, not as algorithmic assumptions: a portable VS Code profile exposed a different data directory than the standard user directory, and TRAE produced a non-zero CLI result after recording a successful extension installation. The general contract is evidence-based instance resolution, so other users and installation layouts must work without adding machine-specific branches.

The existing domain terms Active Target instance, Theme registration, Plan, Partial and Snapshot remain the canonical vocabulary for implementation and review.
