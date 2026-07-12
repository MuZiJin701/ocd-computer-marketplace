# One-Tone Codex Skill/Plugin 产品化设计

## 目标与范围

本阶段把已经完成的 Python 核心运行时包装成一个可校验、可安装的项目内 Codex Skill/Plugin。完整用户体验为：

```text
自然语言请求
→ 识别 Seed Color 和 Targets
→ Preview
→ 展示 Plan、目标和风险
→ 请求 Apply 确认
→ Apply
→ Verify
→ 解释 FULL/PARTIAL/SKIPPED
→ 必要时 Rollback
```

本阶段包含计划书的阶段 0、阶段 7 和阶段 8：

- `.codex-plugin/plugin.json` 插件骨架。
- `skills/unify-windows-theme/SKILL.md` 触发条件和工作流。
- `agents/openai.yaml` UI 展示元数据。
- Skill 脚本、引用资料和必要资源。
- CLI 的稳定 JSON 输出或等价机器可读调用接口。
- 插件本地校验、打包和市场发布前检查。

本阶段不做：

- 自动安装到全局 `$CODEX_HOME`。
- 修改用户全局 Codex 配置。
- 在 Skill 中复制 Palette、Adapter 或 Transaction 业务逻辑。
- 把 fixture 测试结果标记为真实目标 `FULL`。
- 没有用户确认时执行系统、应用重启、Chrome 加载或其他外部写入。

## 设计原则

### 单一业务实现

Python 核心是唯一的业务实现层。Skill 只负责对话编排、参数收集、风险确认、调用 CLI 和结果解释；脚本只做稳定的进程调用、参数转发和 JSON 解析。

### 项目内可复现

插件目录、Skill 目录、校验结果和构建产物都位于当前项目。执行时优先调用项目自己的 `uv run one-tone ...`，不依赖用户机器上已安装的同名命令。

### 明确的副作用门禁

- `preview` 不修改系统或应用。
- `apply` 必须带 `--confirm`，并且只消费已有 Plan ID。
- `verify --restart-apps` 是允许进程重启的显式门禁。
- Chrome 的 `requires_user_action` 必须回传给用户，Skill 不得把资源生成解释为主题已激活。
- Rollback 必须使用明确 transaction ID。

## 目录和职责

```text
.codex-plugin/
└── plugin.json                 # 使用官方 scaffold/校验工具生成的插件元数据

skills/unify-windows-theme/
├── SKILL.md                    # 触发描述、对话流程和调用规则
├── agents/
│   └── openai.yaml             # UI 展示名称、简介和默认提示词
├── scripts/
│   ├── one_tone_preview.py     # 调用 preview 并输出机器可读结果
│   ├── one_tone_apply.py       # 校验 confirm 和 Plan ID 后调用 apply
│   ├── one_tone_verify.py      # 调用 verify，转发 restart 许可
│   └── one_tone_rollback.py    # 校验 transaction ID 后调用 rollback
├── references/
│   ├── supported-targets.md    # 目标、版本、路径和 FULL/PARTIAL/SKIPPED 规则
│   ├── safety-and-confirmation.md
│   └── result-schema.md        # Plan、Transaction、AdapterResult 的解释
└── assets/
    └── README.md               # 只有需要被 Skill 使用的资源才放入此处
```

插件 ID、Skill 名称、manifest 字段和 `agents/openai.yaml` 字段不凭记忆手写；实现时先运行本地 plugin/skill scaffold，再按校验工具报告调整。

## Skill 对话协议

### 触发

`SKILL.md` 的 frontmatter description 覆盖以下自然语言意图：统一 Windows 主题、生成高对比度主题、把多个常用应用改成同一颜色、预览/应用/回滚主题。描述中明确该 Skill 只支持计划书列出的目标。

### 参数收集

Skill 在 Preview 前必须获得或明确以下参数：

- Seed Color；未提供时请求 HEX 色值。
- Targets；未提供时展示支持目标并请求选择。
- 是否允许应用重启；默认不允许。
- Chrome 是否允许用户手动加载/确认；Chrome 被选择时必须明确提示。

### 结果处理

Skill 按 CLI 的 JSON 结果解释：

- `FULL`：八步验收、版本记录和自动激活证据完整。
- `PARTIAL`：有用户操作、AI 面板限制、无法自动重启或其他明确限制。
- `SKIPPED`：未安装、配置格式未验证、版本不支持或目标未检测到。
- `FAILED`：操作失败；展示失败目标、已执行的自动回滚和下一步。

Skill 不根据目标名称猜测兼容性，不将 `partial` 改写成成功，不隐藏 Plan ID 或 transaction ID。

## CLI 机器可读接口

当前 CLI 已有稳定的人类可读输出；产品化阶段增加统一 JSON 输出选项，例如：

```powershell
uv run one-tone preview "#7C3AED" --targets windows,terminal --output json
uv run one-tone apply plan-... --confirm --output json
uv run one-tone verify plan-... --confirm --restart-apps --output json
uv run one-tone rollback tx-... --output json
```

JSON 至少包含：`command`、`plan_id` 或 `transaction_id`、`status`、目标结果、`support_level`、`requires_user_action`、`message` 和错误信息。人类可读输出保持兼容；脚本只解析 JSON，不解析表格或自然语言行。

## 验证分层

### 静态结构验证

- 插件 manifest 使用 plugin-creator scaffold 生成并通过其校验。
- Skill 使用 skill-creator 初始化并通过 `quick_validate.py`。
- `SKILL.md` frontmatter、目录名和资源路径有效。
- `agents/openai.yaml` 与 `SKILL.md` 的名称、描述和默认提示词一致。

### 脚本验证

- Preview 脚本能调用项目 CLI 并解析 JSON。
- Apply 脚本拒绝缺少 Plan ID 或 confirm 的调用。
- Verify 脚本默认不传 restart 许可，只有显式参数才传 `--restart-apps`。
- Rollback 脚本拒绝空 transaction ID。

### 核心回归验证

使用项目可写的临时缓存和 pytest 临时目录运行 `uv run pytest`，避免当前环境默认 uv cache 和系统 Temp 权限错误干扰结果。核心 34 项测试必须保持通过。

### 真实目标验证

真实目标仍按计划书的八步执行：

```text
Detect → Snapshot → Apply → Verify → Restart → Verify Again → Rollback → Verify Restore
```

只有在目标机器实际完成八步并保存版本/结果证据后，才在引用资料、Skill 输出或发布说明中标记 `FULL`。

## 发布边界

第一版只生成项目内插件包和校验报告。发布前交付：

- 插件包结构和 manifest 校验结果。
- Skill 校验结果。
- 自动测试结果。
- 支持目标矩阵和已知限制。
- 三个市场示例：统一紫色主题、统一蓝绿色主题、只更新编辑器不更新系统。

在用户明确要求之前，不执行全局安装、不推送远程仓库、不发送市场发布请求。
