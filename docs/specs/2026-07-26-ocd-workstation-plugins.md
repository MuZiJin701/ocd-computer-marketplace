# Zen 工作站规范插件开发说明

## Problem Statement

Zen Computer Marketplace 面向追求极简、规范、整齐和有序可循的跨 Agent 电脑使用场景。当前 Marketplace 只有统一 Windows 主题的 Plugin，缺少两个基础工作站能力：让桌面成为空白的启动入口，以及让基础开发工具集中、可检查地安装。

用户希望通过主动调用 Skill 来完成这些规范，而不是安装后台服务。桌面整理涉及不可逆删除和真实文件移动；工具链配置涉及系统目录、已有软件和不同安装管理器。若没有清晰的 Preview、确认、验证和回滚边界，Agent 可能误删用户内容、重复安装已有软件，或把无法固定路径的 winget 安装误报为完全符合规范。

## Solution

新增两个独立 Plugin，每个 Plugin 只包含一个对应 Skill：

1. `zen-desktop-zero`：将当前用户的 Resolved desktop 变成 Desktop zero。快捷方式直接删除；其他文件和文件夹按确定性分类移动到 `D:\data`；软件启动规范为使用 Windows 任务栏搜索。
2. `zen-scoop-toolchain`：在 `D:\software\scoop` 建立 Scoop 根目录，并帮助用户补齐 Core toolchain baseline：Python、Git、uv 和 Node.js。已有软件保留；缺失项优先通过 Scoop 安装，Scoop 无法提供时再提示 winget，并明确 winget 通常无法指定安装路径。

两个 Plugin 均由用户主动调用 Skill 运行，不建立后台监控服务，不接管对方目录，也不要求用户安装后自动执行。两者沿用仓库的 Preview → 用户确认 → 执行 → Verify 习惯；桌面文件移动保留隐藏的 Move rollback ledger，用户只有在明确提出回滚并提供 Cleanup transaction ID 时才触发回滚。

## User Stories

1. As a Zen Computer Marketplace 用户, I want to install the desktop and toolchain capabilities independently, so that I can adopt only the workstation rules I accept.
2. As a Windows 用户, I want `zen-desktop-zero` to act only on my current Resolved desktop, so that the Public Desktop and other users are not modified.
3. As a Windows 用户, I want a Preview list of every shortcut that will be deleted, so that I can inspect irreversible operations before confirming them.
4. As a Windows 用户, I want desktop shortcuts to be deleted directly after explicit confirmation, so that the desktop contains no shortcut clutter.
5. As a Windows 用户, I want non-shortcut desktop files and folders classified by deterministic rules, so that the Agent does not guess their purpose from content.
6. As a Windows 用户, I want documents, images, videos, audio, archives, installers, code and unknown content to have stable destination categories, so that `D:\data` remains predictable.
7. As a Windows 用户, I want existing folders to be treated as units during classification, so that a folder’s internal structure is not silently rearranged.
8. As a Windows 用户, I want unknown extensions or ambiguous content to go to `D:\data\未分类`, so that no item is silently discarded or misclassified.
9. As a Windows 用户, I want name collisions to receive deterministic numeric suffixes, so that existing files are never overwritten.
10. As a Windows 用户, I want a locked or inaccessible item to remain in place when it cannot be safely moved, so that partial cleanup does not cause data loss.
11. As a Windows 用户, I want the Skill to continue processing independent items after one item fails, so that one bad file does not prevent the rest of the desktop from being organized.
12. As a Windows 用户, I want limited elevation to be attempted only when necessary, so that ordinary cleanup does not run with unnecessary administrator privileges.
13. As a Windows 用户, I want the Skill to identify the process locking a target before attempting to close it, so that it does not terminate unrelated applications.
14. As a Windows 用户, I want the Skill to avoid system and unknown processes, so that cleanup does not become a broad process-killing operation.
15. As a Windows 用户, I want the Skill to verify that the desktop is empty after execution, so that completion means a checked Desktop zero rather than a best-effort message.
16. As a Windows 用户, I want moved files to be restorable by a specific Cleanup transaction ID, so that I can recover an organization operation when needed.
17. As a Windows 用户, I want shortcut deletion to remain explicitly irreversible, so that the Skill does not falsely promise recovery for deleted links.
18. As a Windows 用户, I want normal cleanup results not to advertise hidden rollback data, so that the default experience remains minimal while explicit recovery remains available.
19. As a Windows 用户, I want the Skill to remind me to launch software from Windows Taskbar search, so that the desktop remains a clean workspace rather than an application launcher.
20. As a Windows 用户, I want the Skill to explain that it does not enforce launch behavior through a background service, so that the product boundary is clear.
21. As a Windows 用户, I want `zen-scoop-toolchain` to fail clearly when D drive is missing, unwritable or insufficient for the required setup, so that it never silently falls back to another drive.
22. As a Windows 用户, I want existing Python, Git, uv and Node.js installations to remain untouched, so that adopting the Skill does not reset my development environment.
23. As a Windows 用户, I want the Skill to detect which baseline tools are missing before installation, so that it performs only the work required to complete the baseline.
24. As a Windows 用户, I want Scoop to be installed under `D:\software\scoop` when it is missing, so that the primary package-managed toolchain has a predictable root.
25. As a Windows 用户, I want missing Python, Git, uv and Node.js packages to be installed through Scoop first, so that the preferred installation source and location remain consistent.
26. As a Windows 用户, I want the Skill to try winget only when Scoop cannot provide or install a missing baseline tool, so that fallback behavior is deliberate rather than default.
27. As a Windows 用户, I want the Skill to warn that winget generally cannot guarantee `D:\software` installation paths, so that a fallback install is not mistaken for full path conformity.
28. As a Windows 用户, I want the toolchain Skill to show missing items, chosen sources and path limitations before installation, so that system changes require explicit confirmation.
29. As a Windows 用户, I want the Skill to preserve existing projects, configuration, credentials and caches, so that “补齐工具链” does not become “清空开发环境”.
30. As a Windows 用户, I want the Skill to remind me that AI does not replace computer-science fundamentals, so that I continue learning PATHs, package managers, versions, permissions and basic system concepts.
31. As a maintainer, I want the two capabilities to be separate Plugin envelopes, so that each feature can be installed, tested and versioned independently.
32. As a maintainer, I want each new Plugin to contain one Skill and a self-contained runtime, so that no runtime import depends on the Marketplace root or the other Plugin.
33. As a maintainer, I want `zen-desktop-zero` to own `D:\data` and its category directories, so that directory responsibility is unambiguous.
34. As a maintainer, I want `zen-scoop-toolchain` to own `D:\software\scoop`, so that the two Plugins do not duplicate initialization or overwrite one another’s state.
35. As a maintainer, I want the external result model to distinguish `ok`, `partial`, `failed` and `skipped`, so that failed moves and path-constrained fallbacks remain visible.
36. As a maintainer, I want Preview to be read-only, so that listing desktop changes or missing tools cannot mutate the machine.
37. As a maintainer, I want transaction records to be written atomically, so that an interrupted operation does not leave a truncated rollback ledger.
38. As a maintainer, I want tests to use fake desktop, process and package-manager backends by default, so that the normal suite never deletes a real desktop or installs real software.
39. As a maintainer, I want real desktop and installation checks to be separately marked and risk-documented, so that destructive verification is never confused with fixture testing.
40. As a maintainer, I want the Skill documentation to state the strict user responsibility without insulting the user, so that the warning is firm, explicit and suitable for a public Marketplace.

## Implementation Decisions

- The Marketplace adds two independent Plugin envelopes, `zen-desktop-zero` and `zen-scoop-toolchain`. Each owns one Skill and one self-contained runtime; no shared cross-Plugin runtime is introduced for this first release.
- `zen-desktop-zero` resolves the current user’s Resolved desktop using Windows-known desktop resolution, including redirected locations such as OneDrive. It never targets the Public Desktop, another user’s desktop, an inferred fixed path or an arbitrary directory.
- The desktop Skill must fail before mutation when D drive is absent, unavailable, unwritable or otherwise unable to satisfy the required destination preconditions. It must not silently use another drive.
- The desktop Skill creates `D:\data` and only the category directories it owns. Existing content in `D:\data` is preserved.
- The fixed categories are `文档`, `图片`, `视频`, `音频`, `压缩包`, `安装包`, `代码` and `未分类`. The mapping is deterministic and based on extension and existing folder boundaries; content understanding by AI is not used for placement.
- Existing folders are moved as units to the selected category. An item that cannot be classified goes to `未分类`.
- The Preview result lists each shortcut deletion, each file or folder move, its category, its resolved destination, collision treatment and any preflight warning. Preview performs no delete, move, process termination, elevation, directory creation or package installation.
- Apply requires an explicit user confirmation after Preview. It deletes detected desktop shortcut entries directly. Non-shortcut files and folders are moved to their category directories. Common Windows shortcut forms are included in the detection contract; the implementation must not broaden the contract to arbitrary files merely because they are on the desktop.
- Destination name collisions never overwrite existing content. The Skill chooses a deterministic numeric suffix and records both source and final destination in the transaction.
- Independent operations continue after an item-level failure. A failed item remains in place, and the aggregate status is `partial` when at least one independent operation succeeds and another fails or is skipped; no successful operation is rolled back merely because a sibling failed.
- Constrained repair may request the minimum required elevation and may identify a process holding the specific target. It may attempt to close only a confirmed non-system process after showing the process and target to the user. It must not terminate unknown or system processes, change permissions broadly or close unrelated applications.
- Verify checks the resolved desktop, expected category destinations and transaction evidence without deleting, moving, elevating, terminating processes or creating a new transaction.
- Moved files receive an internal Move rollback ledger. Normal output does not advertise it. An explicit rollback command requires a Cleanup transaction ID and restores only that transaction’s moved files where safe; shortcut deletions are never represented as restorable operations.
- The desktop Skill includes a firm, non-insulting warning in `SKILL.md`: it is for users willing to follow a strict desktop standard; in the AI era, computer-science fundamentals remain important; Python, Git, uv and Node.js should be installed through Scoop when possible, with winget as a fallback whose installation path is usually not controllable; users who do not accept the strict standard should not use the Skill.
- The desktop Skill states that Taskbar search is the prescribed software launch entry. It does not install a background monitor, block other launch paths or attempt to enforce behavior outside an explicit Skill invocation.
- `zen-scoop-toolchain` creates and manages only `D:\software\scoop`. It never clears or claims ownership of unrelated content in `D:\software`.
- The toolchain Skill detects existing Python, Git, uv and Node.js installations and preserves them, including their projects, configuration, credentials, caches and PATH entries unless a documented, item-specific update is explicitly required by the install operation.
- If Scoop is missing, the Skill prepares a Scoop installation rooted at `D:\software\scoop`. If that root cannot be established, the operation fails without silently using Scoop’s default user directory.
- The Core toolchain baseline is Python, Git, uv and Node.js. Missing tools are resolved through Scoop first. If Scoop cannot provide or install a missing tool, the Skill may offer winget as a fallback.
- A winget fallback is reported with its actual installation evidence and path limitation. It is not described as satisfying the Scoop-root requirement when its path is outside `D:\software`.
- Toolchain Preview lists existing tools, missing tools, selected source, expected path, fallback risk and required permissions. Apply installs only after explicit confirmation. Verify re-detects the tools and reports source/path conformity without uninstalling or resetting existing software.
- The toolchain Skill includes the same firm fundamentals reminder in its `SKILL.md`; the wording must be direct and educational, not demeaning.
- Both Plugins use the repository’s safe path-component validation, atomic JSON persistence and structured result conventions where their runtimes need persisted Plans or Transactions. The implementation must not introduce a database, background service, dependency manager wrapper framework or cross-Plugin import layer.
- Plugin metadata, README documentation, Skill instructions, runtime launchers and tests follow the existing Marketplace → Plugin → Skill hierarchy. Root tests remain outside the distributable Plugins.
- The implementation should reuse existing repository testing and reporting patterns where they fit, but must not couple the new runtimes to the One-Tone theme runtime merely to avoid local code.

## Testing Decisions

The highest useful seams are the public Skill workflow and its structured result boundary: Preview, Apply, Verify and explicit Rollback for desktop organization; Preview, Apply and Verify for toolchain setup. Tests assert external filesystem, process-safety, transaction and installation-source behavior rather than private classification helpers or command-construction details.

Tests will cover:

- Plugin metadata, Marketplace registration and the one-Plugin/one-Skill package shape for both new Plugins.
- Resolved desktop discovery for the normal desktop and a redirected desktop, with Public Desktop and another user’s desktop excluded.
- D-drive preflight success and failure for missing, unavailable and unwritable destinations.
- Read-only Preview results for shortcut deletion, category moves, collision suffixes, existing folders and unknown extensions.
- Apply confirmation requirements and proof that Preview alone never changes files or starts installers.
- Shortcut deletion, deterministic file classification and preservation of unclassified items in `未分类`.
- Collision behavior proving that existing destination content is not overwritten.
- Partial operation behavior when one item is locked, inaccessible or otherwise fails.
- Constrained repair behavior with fake locking processes: only confirmed non-system holders may be attempted, while unknown/system processes are never terminated.
- Verify behavior for an empty desktop, remaining failed items and destination evidence.
- Internal rollback ledger persistence, explicit transaction-ID selection, successful restoration of moved files and non-restorability of deleted shortcuts.
- Atomic persistence and recovery from an interrupted ledger write.
- Existing tool detection for Python, Git, uv and Node.js, including preservation of already installed tools and user data.
- Scoop root setup at `D:\software\scoop`, failure without fallback when the fixed root is unavailable, and preservation of unrelated `D:\software` content.
- Scoop-first installation ordering, missing-package fallback to winget, and reporting of actual paths when winget cannot satisfy the Scoop-root constraint.
- Toolchain confirmation requirements, no uninstall behavior and verification of installed/missing baseline tools.
- Structured `ok`, `partial`, `failed` and `skipped` aggregation for mixed desktop and installation outcomes.
- Documentation checks for the strict warning, Taskbar search rule, path limitations, irreversible shortcut deletion and explicit rollback requirements.

Prior art is the existing Marketplace and Plugin envelope tests, Skill package tests, fixture-based runtime tests, atomic storage tests, Transaction tests, structured AdapterResult/status tests and CLI contract tests. Default tests must use temporary directories and fakes. Real desktop deletion, process termination, elevation, Scoop installation and winget installation are separate risk-documented tests and are not part of the default suite.

## Out of Scope

- Clearing or modifying the Public Desktop, another user’s desktop, arbitrary paths or the whole `D:\data` or `D:\software` root.
- Deleting non-shortcut desktop files or folders. Non-shortcut content is moved and recorded for rollback.
- Restoring deleted shortcuts. Shortcut deletion is an explicit irreversible rule.
- AI-based file-content classification, automatic semantic renaming or automatic folder restructuring.
- Silent overwrite of destination content, silent collision resolution or broad permission changes.
- Terminating system, unknown or unrelated processes.
- A background service, scheduled task, shell policy, application blocker or launch-path enforcement mechanism.
- Uninstalling, resetting or cleaning existing Python, Git, uv, Node.js, Scoop, project files, configuration, credentials or caches.
- Guaranteeing that winget installs into `D:\software`; the fallback is explicitly path-constrained and may be partial.
- Installing arbitrary software beyond the Core toolchain baseline.
- Automatically changing Windows settings, taskbar behavior, search configuration or the user’s default shell.
- Combining the two Plugins into a shared runtime or adding a third directory-initialization Plugin.
- Implementing the Plugins, updating the Marketplace manifest, adding runtime dependencies or changing README/architecture/testing documentation in this specification-only step.

## Further Notes

The strictness is a product choice, not an excuse to hide destructive behavior. The Skill must be direct about user responsibility while still presenting the exact deletion and move plan before execution. The internal rollback ledger is intentionally quiet in the normal user-facing result, but its existence and transaction-ID contract must remain testable and documented for explicit recovery requests.

At implementation time, the two Plugins should be added independently and verified with the repository’s standard commands. Any request to reuse a root runtime, add background enforcement, broaden deletion, or make winget path-conformant should be treated as a new architectural decision rather than smuggled into this feature.
