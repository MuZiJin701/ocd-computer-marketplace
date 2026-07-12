# OCD Windows Theme Skill 简洁整改计划书

## 项目定位

本项目是“Windows 电脑强迫症使用 Skills 系列”的第一个 Codex Skill/Plugin，目标是进入个人 Codex 插件市场，而不只是提供一个独立 Python 命令行工具。

第一款 Skill 的用户价值：

> 用户选择喜欢的 Seed Color，Skill 生成统一的高对比度语义色板，并将其安全应用到 Windows 常用应用；所有修改先预览、可验证、可回滚。

产品分为两层：

1. Python 核心运行时：负责 Palette、Plan、Adapter、Transaction、Verify 和 Rollback。
2. Codex Skill/Plugin 包装层：负责触发条件、用户对话流程、脚本调用、风险确认、结果解释和插件市场元数据。

只有两层都完成，才算第一个 Skill 完整交付。

## 当前实施状态

- 已完成：Python 核心阶段 1–6、仓库级 Plugin Marketplace、可安装 Plugin 自包含 runtime、Skill 工作流，以及 Codex `config.toml` v1 Adapter。
- 已验证：自动化测试 62 项通过；当前机器的 Codex Preview 已识别 `C:\\Users\\30733\\.codex\\config.toml`，版本为 `codex-config-v1`。
- 已验证：使用翠绿色 Seed Color `#00A86B` 对 TRAE 完成真实单目标 Apply、Verify、Rollback；回滚会清理真实安装目录和 `extensions.json` 索引残留。
- 已验证：使用修复后的实现以 `#00A86B` 对 Windows、Windows Terminal、VS Code、Cursor、TRAE、Codex、Chrome 完成真实 Apply/Verify；最终事务为 `PARTIAL`，没有执行主动回滚。Windows、Terminal、Codex 验证通过；编辑器通用工作台验证通过；Chrome 主题包已生成。
- 当前限制：编辑器需要重启或重新加载窗口后才能显示新主题，AI 专属面板不受标准主题字段控制；Chrome 激活仍需用户手动加载主题包。未知配置结构标记为 `SKIPPED`。
- 新增边界：TRAE 的 `settings.json` 被运行中的 TRAE 锁定时无法 Apply，必须由用户先关闭应用；Cursor Glass UI 使用独立的 `Cursor Dark` 缓存，标准 VS Code 主题 Adapter 不能覆盖该界面层；Windows AccentPalette 必须在真实交互用户上下文中验证，沙箱 HKCU 不代表用户桌面。
- 新增实现：当 TRAE/兼容 CLI 明确返回“需要重启后才能重新安装同名扩展”时，Adapter 会从本次 VSIX 本地恢复扩展目录和 `extensions.json` 索引；其他 CLI 安装错误仍保持失败，不静默绕过。
- 最新真实验证：TRAE 已在关闭进程的真实用户配置上使用 `#00A86B` Apply，三个 `workbench` 主题字段、扩展目录、主题文件和扩展索引均验证通过；结果为 `PARTIAL`，仅因 AI 专属面板不受标准主题字段控制。
- 主题语义：`surface` 是所有目标应用和 Windows 桌面主界面的统一主题色；`background` 保留为 Palette 内部的深层背景语义，不再写入各 Adapter 的主界面背景字段。Windows 壁纸使用 `surface` 生成纯色 PNG。
- 当前原则：自动化 fixture 通过不等于真实目标 `FULL`；未完成真实验收的目标只能标为 `PARTIAL` 或 `SKIPPED`。

### 2026-07-11 架构修订结论

当前仓库先前已经完成了“仓库内可运行的 Python 核心 + 本地 Plugin/Skill 包装”，但尚未达到可从本地插件市场安装后独立运行的标准。本轮实施按以下结论调整：

- 仓库根目录是 Plugin Marketplace 根目录，不是单个 Plugin 根目录。
- 使用 `.agents/plugins/marketplace.json` 作为仓库级市场目录，使用 `plugins/one-tone-windows/` 作为可安装 Plugin 包。
- `one-tone-windows` 必须自包含 Python runtime、`pyproject.toml` 和 CLI；安装到 Codex cache 后不得依赖仓库根目录的 `src/` 或 `pyproject.toml`。
- `agents/openai.yaml` 放在 `skills/unify-windows-theme/agents/`，作为 Skill 元数据，不放在 Plugin 根目录。
- Skill 只负责触发、参数收集、确认和结果解释；Python runtime 负责全部 Palette、Plan、Adapter、Transaction、Verify 和 Rollback 业务逻辑。
- 不再维护四个重复的 PowerShell 包装入口；保留一个最小、可测试的 Python 启动脚本，仅负责定位 Plugin runtime 并转发 JSON CLI 参数。
- Codex 使用真实 `%USERPROFILE%\\.codex\\config.toml`；首个已验证配置 schema 为 `codex-config-v1`，只修改 Light/Dark ChromeTheme 的明确颜色字段并保留未知字段。
- 计划内的 `FULL` 仍然只表示真实目标完成八步验收，不因 Plugin 校验或自动化测试通过而提前标记。

## 0. 文档目的

本计划用于指导现有主题统一项目的简化整改。

目标不是建设通用桌面主题平台，而是完成一个小而可靠的工具：

> 用户选择一个颜色和目标应用，先预览方案，再确认应用；所有修改可验证、可回滚。

目标读者：

- 项目开发者
- 测试人员
- 后续维护者

---

## 1. 当前项目基线

当前方向已确定：

- 核心程序使用 Python 编写
- 使用 uv 管理依赖、运行和测试
- 用户输入一个 Seed Color
- 生成统一 Palette
- 支持 Windows 11 22H2+
- 支持 Windows 桌面普通深色模式和 Palette 驱动渐变壁纸
- 支持 Windows Terminal
- 支持 VS Code 兼容编辑器
- 支持 Codex
- 支持 Chrome
- 支持 Preview、Apply、Verify、Rollback

VS Code 兼容编辑器首批包括：

- VS Code
- Cursor
- TRAE

Codex 必须使用独立 Adapter 支持，不依赖 VS Code 兼容适配器。

不纳入本项目：

- JetBrains
- Edge
- Office
- 其他未验证应用

---

## 2. 当前主要问题

### 2.1 Preview 和 Apply 不一致

当前设计中，Preview 会生成主题方案，但 Apply 仍可以直接接收颜色重新生成。

风险：

- 用户预览的方案和实际应用的方案可能不同
- 无法确认实际应用的是哪一版配置

整改：

```text
preview
→ 生成 plan.json
→ 用户确认
→ apply plan.json
```

Apply 不再直接接收颜色。

---

### 2.2 Snapshot 和 Rollback 定义不清楚

当前只描述了“创建快照”和“回滚”，但没有明确：

- 回滚哪一次修改
- 部分失败时如何处理
- 多次应用后如何选择恢复点

整改：

每次 Apply 创建一个独立 transaction 目录。

```text
transactions/
└── 20260711-001/
    ├── transaction.json
    └── backup/
```

Rollback 必须指定 transaction_id。

---

### 2.3 Adapter 返回值过于简单

单纯返回 True / False 无法表达：

- 未安装
- 跳过
- 部分成功
- 应用成功但验证失败

整改：

统一返回简单结构化结果。

```python
@dataclass
class AdapterResult:
    target: str
    status: Literal["ok", "partial", "failed", "skipped"]
    changed: bool
    verified: bool
    message: str
```

---

### 2.4 “统一主题”缺少简单验收标准

本项目不要求所有应用 RGB 完全一致。

统一的定义是：

> 所有目标应用使用同一个 Palette Engine 生成的语义色板。

第一版只验收核心指标：

- 关键前景色 / 背景色对比度达到 7:1
- 主题配置写入成功
- 主题成功激活
- 应用重启后主题仍然存在
- Rollback 能恢复原配置
- 不修改无关设置

---

## 3. 目标用户流程

```text
选择颜色
→ 选择目标应用
→ Preview
→ 查看颜色和修改范围
→ 确认
→ Apply
→ Verify
→ 查看结果
→ 必要时 Rollback
```

示例：

```powershell
uv run one-tone preview "#7C3AED" --targets windows,terminal,vscode,cursor,trae,codex,chrome
```

输出：

```text
Plan ID: plan-20260711-001

Targets:
- Windows
- Windows Terminal
- VS Code
- Cursor
- TRAE
- Codex
- Chrome

Validation:
- Contrast: PASS
- Unsupported targets: 0
- Warnings: 1
```

确认后：

```powershell
uv run one-tone apply plan-20260711-001 --confirm
```

回滚：

```powershell
uv run one-tone rollback tx-20260711-001
```

---

## 4. 核心执行流程

### 4.1 Preview

Preview 只负责生成方案，不修改系统。

```text
Detect
→ Generate Palette
→ Build Plan
→ Validate
→ Save plan.json
→ Show Preview
```

输出：

```text
plans/
└── plan-20260711-001.json
```

Plan 最小结构：

```json
{
  "id": "plan-20260711-001",
  "seed_color": "#7C3AED",
  "mode": "dark",
  "targets": [
    "windows",
    "terminal",
    "vscode",
    "cursor",
    "trae",
    "codex",
    "chrome"
  ],
  "palette": {},
  "hash": "..."
}
```

---

### 4.2 Apply

Apply 只消费已有 Plan。

```text
Load Plan
→ Verify Hash
→ Create Transaction
→ Snapshot
→ Apply
→ Verify
→ Save Result
```

Apply 不重新生成 Palette。

---

### 4.3 Rollback

```text
Load Transaction
→ Read Backup
→ Restore Targets
→ Verify Restore
→ Mark ROLLED_BACK
```

Rollback 只恢复指定事务。

---

## 5. 最小事务模型

第一版只保留 5 个状态：

```text
PENDING
APPLIED
PARTIAL
FAILED
ROLLED_BACK
```

Transaction 示例：

```json
{
  "id": "tx-20260711-001",
  "plan_id": "plan-20260711-001",
  "status": "APPLIED",
  "created_at": "2026-07-11T10:00:00+09:00",
  "targets": [
    "windows",
    "terminal",
    "vscode"
  ]
}
```

不使用：

- 数据库
- 事件溯源
- 复杂状态机框架
- 后台服务

---

## 6. Palette Engine

用户选择的是 Seed Color。

程序从 Seed Color 生成语义色板：

```text
Seed Color
→ OKLCH
→ 生成背景、前景、强调色、选中色、边框色
→ 对比度验证
→ 输出 Palette
```

Palette 至少包含：

```text
background
surface
foreground
muted_foreground
accent
accent_foreground
selection_background
selection_foreground
border
error
warning
success
```

第一版规则：

```text
关键 foreground / background >= 7:1
accent_foreground / accent >= 7:1
selection_foreground / selection_background >= 7:1
```

状态色：

- error 使用红色系
- warning 使用黄色或琥珀色系
- success 使用绿色系
- 不强制全部状态色跟随 Seed Hue

---

## 7. 支持范围

### 7.1 Core

- Windows 11 22H2+
- 普通深色模式
- 由 Palette 生成并可回滚的桌面渐变壁纸
- Windows Terminal

### 7.2 VS Code-Compatible Editors

一个主题生成器，共用一套 VSIX。

首批：

- VS Code
- Cursor
- TRAE

结构：

```text
Seed Color
→ Palette
→ VS Code Theme JSON
→ VSIX
→ 安装到已验证兼容编辑器
```

新增兼容应用时必须先验证：

- 可以安装 VSIX
- 可以激活主题
- 核心工作台颜色正常
- 重启后主题仍存在
- 可以恢复原主题

仅“支持 VSIX”不能直接标记为 FULL。

---

### 7.3 Codex

Codex 必须实现独立 Adapter，不把 Codex 视为 VS Code 兼容编辑器。

第一版目标：

- 检测 Codex 是否已安装或可配置
- 读取并保存 Codex 原有主题配置
- 根据同一 Palette 生成 Codex 可识别的主题配置
- 应用并激活主题
- 重启 Codex 后验证主题仍然存在
- 支持恢复原主题配置

实现时必须以当前 Codex 的实际配置格式和运行行为为准；在未完成 Detect、Snapshot、Apply、Verify、Restart、Rollback 全流程前，不得标记为 FULL。

---

### 7.4 Chrome

Chrome 独立 Adapter。

第一版目标：

- 生成 Chrome 主题资源
- 安装或加载主题
- 验证浏览器框架颜色
- 保存原主题信息
- 支持恢复

如自动激活机制不稳定，则允许：

```text
requires_user_action
```

但必须在结果中明确报告。

---

## 8. Adapter 设计

所有 Adapter 保持相同的最小接口：

```python
class ThemeAdapter:
    def detect(self) -> AdapterResult:
        ...

    def snapshot(self, backup_dir: Path) -> AdapterResult:
        ...

    def apply(self, plan: Plan) -> AdapterResult:
        ...

    def verify(self, plan: Plan) -> AdapterResult:
        ...

    def rollback(self, backup_dir: Path) -> AdapterResult:
        ...
```

AdapterResult：

```python
@dataclass
class AdapterResult:
    target: str
    status: Literal["ok", "partial", "failed", "skipped"]
    changed: bool
    verified: bool
    message: str
```

第一版不增加更多字段，只有出现真实需求时再扩展。

---

## 9. 建议目录结构

```text
OCD/
├── .agents/
│   └── plugins/
│       └── marketplace.json
├── plugins/
│   └── one-tone-windows/
│       ├── .codex-plugin/
│       │   └── plugin.json
│       ├── pyproject.toml
│       ├── uv.lock
│       ├── README.md
│       ├── src/
│       │   └── one_tone/
│       │       ├── cli.py
│       │       ├── palette.py
│       │       ├── plan.py
│       │       ├── transaction.py
│       │       └── adapters/
│       │           ├── windows.py
│       │           ├── terminal.py
│       │           ├── vscode_family.py
│       │           ├── codex.py
│       │           └── chrome.py
│       └── skills/
│           └── unify-windows-theme/
│               ├── SKILL.md
│               ├── agents/
│               │   └── openai.yaml
│               ├── scripts/
│               │   └── run_one_tone.py
│               ├── references/
│               │   ├── supported-targets.md
│               │   ├── safety-and-confirmation.md
│               │   └── result-schema.md
│               └── assets/
├── tests/
└── docs/
```

Plugin 包内部结构为：

```text
one-tone-windows/
├── .codex-plugin/
│   └── plugin.json
├── pyproject.toml
├── uv.lock
├── README.md
├── src/
│   └── one_tone/
│       ├── cli.py
│       ├── palette.py
│       ├── plan.py
│       ├── transaction.py
│       └── adapters/
│           ├── windows.py
│           ├── terminal.py
│           ├── vscode_family.py
│           ├── codex.py
│           └── chrome.py
├── tests/
│   ├── test_palette.py
│   ├── test_plan.py
│   ├── test_transaction.py
│   └── test_adapters.py
└── skills/
    └── unify-windows-theme/
        ├── SKILL.md
        ├── agents/
        │   └── openai.yaml
        ├── scripts/
        │   └── run_one_tone.py
        ├── references/
        │   ├── supported-targets.md
        │   ├── safety-and-confirmation.md
        │   └── result-schema.md
        └── assets/
            └── README.md
```

核心模块只保留：

1. cli.py
2. palette.py
3. plan.py
4. transaction.py
5. adapters/

不提前增加：

- services/
- repositories/
- providers/
- factories/
- dependency injection framework

Skill 包装层允许增加 `SKILL.md`、`agents/openai.yaml`、最小启动脚本、引用资料和必要资源，但不在 Skill 内重复实现 Adapter。开发仓库通过根目录测试入口运行；安装后的 Plugin 通过自身目录中的 `pyproject.toml` 和 `uv run --project <plugin-root> one-tone ...` 运行，不能依赖 Plugin 外部目录。

---

## 10. 改造差距矩阵

| 当前 | 问题 | 改造动作 | 验证 |
|---|---|---|---|
| Apply 接收颜色 | 预览和应用可能不一致 | Apply 只接收 plan_id | Hash 一致性测试 |
| Snapshot 不明确 | 无法确定回滚对象 | 每次 Apply 创建事务目录 | Apply/Rollback 测试 |
| bool 返回值 | 无法表达部分成功 | 使用 AdapterResult | Contract Test |
| 全部应用默认修改 | 范围过大 | 用户选择 Targets | Target Selection Test |
| Adapter 分散 | VS Code 系应用重复实现 | 合并 vscode_family | 三应用兼容验证 |
| Codex 未纳入统一流程 | 无法保证 Codex 支持 | 增加独立 codex Adapter | Codex 全流程验证 |
| 无简单验收标准 | 无法判断成功 | 对比度、激活、持久化、回滚 | 自动测试 + 手工验证 |

---

## 11. 分阶段整改

### 阶段 0：建立 Codex Skill/Plugin 产品骨架

完成：

```text
用户自然语言请求
→ Skill 触发
→ 收集 Seed Color 和 Targets
→ 调用 one-tone preview
→ 请求确认
→ 调用 one-tone apply/verify/rollback
→ 解释结构化结果
```

验收：

- 创建 `.agents/plugins/marketplace.json`，通过 `./plugins/one-tone-windows` 指向 Plugin。
- 创建 `plugins/one-tone-windows/.codex-plugin/plugin.json`，将 Skill 正确打包为插件。
- 创建 `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`，包含清晰触发描述和 Preview → Plan → Apply → Verify → Rollback 流程。
- 创建 `plugins/one-tone-windows/skills/unify-windows-theme/agents/openai.yaml`，提供 Skill 的市场展示名称、简介和默认提示词。
- 将 Python 核心和 `pyproject.toml` 放入 Plugin 包，使安装后的 Plugin 不依赖仓库外部路径。
- Skill 不重复实现 Python Adapter，只调用核心 CLI 或脚本。
- Skill 在 Apply、Restart、Chrome 用户操作前明确提示影响并请求确认。

此阶段完成后，才具备可安装的 Skill/Plugin 形态。

---

### 阶段 1：整理核心数据流

完成：

```text
Seed Color
→ Palette
→ Plan
→ Apply Plan
```

验收：

- Preview 生成 plan.json
- Apply 不接收颜色
- Plan Hash 校验通过
- Palette 测试通过

---

### 阶段 2：加入事务和回滚

完成：

```text
Apply
→ Transaction
→ Snapshot
→ Apply
→ Verify
→ Rollback
```

验收：

- 每次 Apply 都有独立事务
- 可以恢复指定事务
- 失败结果可见
- 不覆盖其他事务备份

---

### 阶段 3：完成 Windows、壁纸和 Terminal

验收：

- Windows 11 普通深色主题应用成功
- Palette 驱动壁纸生成、应用和恢复成功
- Terminal 配色应用成功
- 重启后仍有效
- Rollback 和 Verify Restore 成功

此阶段可发布：

```text
v0.1
```

---

### 阶段 4：完成 VS Code Family

包括：

- VS Code
- Cursor
- TRAE

验收：

- 同一 Palette 生成同一主题 VSIX
- 三个应用分别完成安装测试
- 三个应用分别完成激活测试
- 三个应用分别完成重启测试
- 三个应用分别完成恢复测试

此阶段可发布：

```text
v0.2
```

---

### 阶段 5：完成 Codex

验收：

- Codex 独立 Adapter 完成
- Codex 主题配置生成成功
- Codex 主题应用并激活成功
- Codex 重启后主题仍然存在
- Codex 原主题恢复成功

此阶段可发布：

```text
v0.3
```

---

### 阶段 6：完成 Chrome

验收：

- 主题资源生成成功
- 应用或加载流程明确
- 用户操作要求明确
- 恢复原主题成功

此阶段可发布：

```text
v0.4
```

---

### 阶段 7：完成 Skill 工作流和资源封装

完成：

- `SKILL.md`：触发条件、参数收集、目标选择、风险确认、错误解释和回滚指导。
- `scripts/run_one_tone.py`：只定位当前 Plugin runtime、调用 `uv run --project <plugin-root> one-tone ... --output json` 并转发退出码；不得复制业务逻辑。
- `references/supported-targets.md`：支持目标、版本检测、FULL/PARTIAL/SKIPPED 规则。
- `references/safety-and-confirmation.md`：系统配置、应用重启、Chrome 手动加载和回滚确认。
- `references/result-schema.md`：Plan、Transaction、AdapterResult 和支持级别的解释。
- `agents/openai.yaml`：符合 Codex UI/市场展示约束。

验收：

- 用户说“统一我的 Windows 主题”“把常用应用换成紫色高对比度主题”等自然语言时可以触发 Skill。
- Skill 先询问或识别 Seed Color、Targets 和是否允许重启。
- Preview 不产生外部变更；Apply 前展示 Plan ID、目标和修改范围。
- 失败时能解释失败目标、自动回滚结果和下一步。
- Skill 能把 `FULL`、`PARTIAL`、`SKIPPED` 转换为用户可理解的结果。

---

### 阶段 8：插件市场发布准备

验收：

- `.agents/plugins/marketplace.json` 可被 Codex 识别，且 `source.path` 使用以 `./` 开头的仓库相对路径。
- `.codex-plugin/plugin.json` 元数据完整且名称、描述和 Skill 路径一致。
- Plugin 安装到 Codex cache 后，仍能从自身目录启动 Python CLI，不读取仓库根目录的 runtime。
- Skill 目录通过 `quick_validate.py` 或等价校验。
- 插件安装后可发现 `unify-windows-theme` Skill。
- README 提供安装、触发示例、支持范围、权限影响和已知限制。
- 至少准备 3 个市场示例：统一紫色主题、统一蓝绿色主题、仅更新编辑器不更新系统。
- 发布前完成自动测试、fixture 测试和目标机器八步验收记录。

第一版市场发布标记：

```text
v1.0-skill
```

---

## 12. 测试和发布标准

### 12.1 自动测试

必须覆盖：

- Palette 生成
- 对比度计算
- Plan Hash
- Plan 序列化
- Transaction 创建
- Transaction 恢复
- AdapterResult
- AdapterResult 的 `requires_user_action` 与版本记录
- 失败路径

运行：

```powershell
uv run pytest
```

---

### 12.2 每个目标的验证

每个应用至少检查：

```text
1. Detect
2. Snapshot
3. Apply
4. Verify
5. Restart
6. Verify Again
7. Rollback
8. Verify Restore
```

---

### 12.3 发布标准

每个版本发布前必须满足：

- 目标功能完成
- 自动测试通过
- 目标应用版本记录完整
- 只有八步完成、无用户操作要求且版本记录完整的目标才能标记 `FULL`
- 用户操作、AI 面板限制或无法自动重启的目标标记 `PARTIAL`
- 未安装或未验证配置格式的目标标记 `SKIPPED`
- 回滚测试通过
- 已知限制写入 README
- 计划外应用不得标记为支持或 FULL
- 不修改用户未选择的目标
- 不修改无关配置

---

## 13. 当前开放问题

以下决策已确认，并作为阶段 3–6 的实施约束：

1. 首版只支持普通深色模式，不实现 Contrast Theme。
2. Windows Terminal 修改当前默认 Profile，不生成独立 Scheme。
3. Chrome 生成主题资源并允许用户确认/加载一步，结果标记 `requires_user_action`。
4. VS Code、Cursor、TRAE 只强制验收通用工作台、编辑器和终端；AI 专属面板不可控时标记 `partial`。
5. 失败时自动回滚全部已修改目标。
6. 只有完成 Detect、Snapshot、Apply、Verify、Restart、Verify Again、Rollback、Verify Restore 八步并记录实际应用版本，才标记 `FULL`。

---

## 14. 简化原则

整个项目始终遵守以下原则：

### 原则 1：少支持，但支持可靠

宁可明确支持 7 个目标，也不宣称支持所有软件。

### 原则 2：先验证，再加入兼容列表

未知应用不得因为“看起来兼容”而加入支持范围。

### 原则 3：不建立大框架

第一版不增加数据库、后台服务、插件运行时和复杂状态机。

### 原则 4：同类应用尽量复用

VS Code、Cursor、TRAE 共用一个 VS Code-Compatible Adapter。

### 原则 5：预览和应用必须一致

Preview 生成 Plan，Apply 只消费这个 Plan。

### 原则 6：任何修改都必须可恢复

没有 Snapshot 的目标不能进入 Apply。

---

## 15. 项目最终目标

第一阶段只需要打通：

```text
用户选择颜色
→ 选择应用
→ Preview
→ 生成 Plan
→ Apply
→ Snapshot
→ Verify
→ Rollback
```

项目完成后的稳定支持范围：

```text
Windows 11 22H2+
Windows Terminal
VS Code
Cursor
TRAE
Codex
Chrome
```

项目的核心价值保持简单：

> 选一个颜色，选几个应用，先预览，再统一，并且随时可以恢复。
