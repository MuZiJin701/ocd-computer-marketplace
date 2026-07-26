# 项目瘦身开发说明

## Problem Statement

当前项目已经完成 6 个 Target 和 `Preview → Apply → Verify → Rollback` 安全流程，但内部仍有几类维护负担：

- `FileAdapter` 和 `file-demo` 只服务于测试与隐藏 CLI 分支，不是用户可见 Target；
- `atomic_write_json` 与 `SupportLevel` 没有调用方；
- Cursor 已明确不属于支持范围，但仍需核对 VS Code-family Adapter 中的遗留逻辑；VS Code/TRAE 的通用重启回退属于受支持目标的行为，不应误删；
- 5 份开发 spec 与 ADR、Skill 说明、目标矩阵和测试契约重复描述相同决策；
- Skill 测试中有重复的 README 工作流检查；
- 根项目与 Skill 项目的独立分发边界容易被误判为冗余，但它是 Skill 可独立安装和测试隔离的必要边界。

这些问题增加了代码、测试和文档的维护面，却没有为当前支持范围提供新的用户价值。

## Solution

在不改变用户可见功能范围、安全流程、Target Adapter 契约、Plan/Transaction 持久化契约或 Skill 分发边界的前提下，删除无产品价值的测试运行时替身、死代码、已退出支持范围的 Cursor 专属逻辑和重复文档/测试。

瘦身后的项目继续支持 Windows、Windows Terminal、VS Code、TRAE、Codex 和 Chrome，并继续执行完整的 Preview、Apply、Verify 和 Rollback 流程。

## User Stories

1. As a One-Tone 用户, I want all six existing Targets to remain available, so that瘦身不会减少已承诺的主题统一范围。
2. As a One-Tone 用户, I want Preview、Apply、Verify 和 Rollback to keep their existing meaning, so that安全操作习惯不会改变。
3. As a One-Tone 用户, I want the default Target set to remain unchanged, so that一次主题统一仍然覆盖全部已实现 Target。
4. As a One-Tone 用户, I want unsupported Targets such as Cursor to be reported as `skipped`, so that工具不会伪装成支持了未验证的应用。
5. As a One-Tone 用户, I want ordinary cursor color fields in supported Targets to remain available, so that删除 Cursor Target 逻辑不会误删 Terminal 或编辑器中的光标主题字段。
6. As a One-Tone 用户, I want Plan Hash、Transaction ID、Snapshot、Apply、Verify 和 Rollback behavior to remain unchanged, so that瘦身不会削弱恢复能力或篡改检测。
7. As a maintainer, I want the production runtime not to contain the undocumented `file-demo` Target, so that测试替身不会伪装成产品能力。
8. As a maintainer, I want transaction tests to retain a local test double, so that transaction success、失败补偿、部分成功和显式 Rollback 仍然可验证。
9. As a maintainer, I want unused helpers and aliases removed, so that代码搜索结果只保留真实调用路径。
10. As a maintainer, I want VS Code and TRAE to continue sharing their verified common Adapter, so that瘦身不会把合法复用误拆成重复实现。
11. As a maintainer, I want Cursor-specific fallback and restart branches removed, so that未支持 Target 不再增加编辑器 Adapter 的复杂度。
12. As a maintainer, I want the explicit Cursor path to remain a safe skip, so that删除专属实现不会让未知或未支持输入进入真实写入流程。
13. As a maintainer, I want the Field inventory and capability reporting to remain intact, so that字段级证据和 partial 结果不会因清理而丢失。
14. As a maintainer, I want the existing AdapterResult structure to remain intact, so that结果仍然能表达 `ok`、`partial`、`failed` 和 `skipped`。
15. As a maintainer, I want one canonical development spec for the current theme-field and visual acceptance baseline, so that同一决策不需要在多份 spec 中同步维护。
16. As a maintainer, I want durable architectural trade-offs to remain in ADRs, so that文档合并不会丢失历史原因和被拒绝的替代方案。
17. As a maintainer, I want architecture and testing documents to keep their own responsibilities, so that canonical spec、架构边界和验证契约不会重新混成一份大文档。
18. As a maintainer, I want README workflow checks to assert each unique contract once, so that文档测试既能发现回归又不会重复维护相同断言。
19. As a maintainer, I want the root Marketplace project and Skill runtime project to remain separate, so that Skill can continue to be independently installed and the root can remain test-only。
20. As a maintainer, I want no new dependency、service、database or abstraction introduced by this cleanup, so that瘦身结果不会用新的结构抵消删除所得。
21. As a maintainer, I want the full repository verification commands to pass after cleanup, so that删除内容不会破坏分发、CLI 或运行时行为。
22. As a maintainer, I want undocumented `file-demo` compatibility to remain out of the product contract, so that测试工具不会继续扩大支持边界。

## Implementation Decisions

- 保留 6 个已支持 Target、完整安全工作流、`AdapterResult`、`ThemeAdapter`、`UnsupportedAdapter`、Field inventory、Plan 和 Transaction 契约。
- 从生产运行时移除仅用于测试和隐藏 CLI 分支的 `FileAdapter`，同时移除 `file-demo` 的 Target 构建分支和公共导出。事务测试改用测试目录中的最小本地替身，继续覆盖真实 Transaction seam。
- 删除只被 `FileAdapter` 使用的 JSON 写入包装，以及没有调用方的原子 JSON 写入辅助函数和 `SupportLevel` 类型别名；保留实际共享的原子文本写入函数。
- 从 VS Code-family Adapter 移除真正属于 Cursor 的设置回退、注册失败补偿、重启兼容和验证分支，并删除对应的 Cursor 行为测试；保留 VS Code/TRAE 的通用重启回退。显式 `cursor` 仍由统一 Target 构建入口安全映射为 `UnsupportedAdapter`；Terminal、VS Code 和 TRAE 的普通光标字段继续保留。
- VS Code/TRAE 的 Theme registration 只有在 Target 的主题登记存在、登记指向的主题产物可用且贡献的主题标签可被读取时才算成功；仅发现本地扩展目录不算注册成功。主题注册与主题激活继续分开报告。
- Apply、Verify 的机器可读 JSON 输出必须安全表示二进制 Serialized report value；该表示只用于报告，不改变 Snapshot 的精确恢复职责。
- 保留 VS Code 与 TRAE 的共享 Adapter 和 `EditorSpec`，因为两者仍共同覆盖已支持的标准 Workbench 主题字段，拆分会增加重复实现。
- 将当前 5 份开发 spec 收敛为一份 canonical 主题字段/视觉验收 spec；删除已被该 canonical spec、ADR、架构文档、测试文档或 Skill 说明覆盖的重复 spec，并更新仍指向已删除 spec 的入口说明。
- 保留 ADR 作为长期架构决策记录，保留 `architecture` 作为分发/模块边界说明，保留 `testing` 作为验证契约，保留 Skill 与 `targets` 作为用户流程和 Target 支持矩阵。
- 将重复的 README 工作流检查合并为一个测试，保留所有唯一断言，不减少 README、Skill、Marketplace 和分发结构契约。
- 不合并根项目与 Skill 项目，不移动 Skill runtime，不缩短或重排 Marketplace → Plugin → Skill 的分发目录，不改变两份 uv 项目的职责。
- 不改变外部命令、默认 Target、配置路径探测、生成产物、Plan/Transaction JSON schema、状态语义、回滚规则、依赖集合或真实桌面风险边界。
- 这次清理不为未记录的 `file-demo` 用法提供迁移或兼容层；`file-demo` 不属于当前用户可见支持范围。对已支持 Target 的历史 Plan 和 Transaction 不得采用猜测式迁移。

## Testing Decisions

- 最高测试 Seam 是现有仓库级验收：通过完整测试套件同时验证运行时行为、分发边界、CLI 契约和主动文档契约；不新增测试框架或测试基础设施。
- 测试只断言外部行为和公开契约：默认 6 个 Target、显式 Cursor 的 `skipped`、AdapterResult 字段、Plan/Transaction 安全行为、真实 Adapter 产物和文档入口；不为被删除的私有 helper 保留测试。
- Transaction 测试使用测试侧最小替身，继续覆盖 Snapshot、逐操作持久化、成功、部分成功、失败补偿、全 skipped、显式 Rollback 和 retention 行为。
- VS Code-family 测试继续覆盖 VS Code/TRAE 的共享主题产物、严格注册/激活、通用重启恢复、跨实例 Verify 和 Rollback；删除仅针对 Cursor fallback 的场景，不删除共同 Adapter 行为测试。
- CLI 测试补充 Apply、Verify 的二进制 Serialized report value JSON 输出检查，并确认未登记但存在本地目录的编辑器主题不会被视为注册成功。
- CLI 测试继续覆盖默认 Target、显式目标、Preview/Apply/Verify/Rollback 参数、路径探测和 Skill-local runtime root；移除 `file-demo` 专属入口测试。
- 文档测试将 README 工作流的重复检查合并为一项，并继续验证安装命令、Preview/Verify/Transaction 信息、支持平台、分发路径和不支持 Cursor 的边界。
- 文档清理后必须确认没有入口继续引用被删除的 spec，也没有把 ADR、architecture、testing、Skill 和 Target 矩阵的职责重新混淆。
- 验收命令保持项目既定入口：`uv run pytest`、`uv run --project plugins/one-tone-windows/skills/unify-windows-theme one-tone --help` 和 `git diff --check`。

## Out of Scope

- 删除或缩减 Windows、Windows Terminal、VS Code、TRAE、Codex 或 Chrome 的任何用户可见支持能力。
- 改变 Preview、Apply、Verify、Rollback 的语义、确认要求、Plan Hash、Transaction ID、Snapshot、补偿回滚或 partial/failed 聚合规则。
- 将 Cursor 重新加入支持范围；也不删除支持 Target 中名称含 `cursor` 的普通颜色字段。
- 合并根测试 harness 与 Skill runtime，移动运行时代码，改变 Marketplace、Plugin 或 Skill 分发边界。
- 引入新的共享 Adapter 基类、工厂、服务、数据库、缓存、依赖或兼容层。
- 重写 Palette 算法、Field inventory、Target schema、视觉角色、对比度阈值或真实桌面验证策略。
- 为未记录的 `file-demo` 使用场景提供迁移、持久化恢复或用户文档。
- 删除仍然承载长期取舍的 ADR，或把 ADR 仅作为重复 spec 的副本处理。

## Further Notes

这是一轮低风险维护性清理，不是功能重构。实现顺序应先移除生产侧测试替身和 Cursor 专属分支，再删除死代码，随后收敛 spec 与重复测试，最后运行完整验收命令。

如果删除某个候选项需要改变安全流程、Target 支持、持久化格式或分发边界，应停止删除并将其作为新的架构决策单独讨论。
