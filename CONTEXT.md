# Zen Computer Marketplace Domain Context

Zen Computer Marketplace 是面向极简、有序电脑使用场景的跨 Agent Skill 市场。One-Tone 是其中把同一 Seed Color 统一到受支持 Windows Target 的可回滚主题工具；工作站 Plugin 提供桌面和基础工具链规范。

## Language

### Color language

**Seed Color**  
用户选择的源颜色，作为主题统一的起点和产品语义中的主色。  
_Avoid_: 随机主题色、默认主色

**Palette**  
由 Seed Color 派生的一组颜色角色，而不是一组按界面字段随意生成的颜色。  
_Avoid_: 颜色字典、字段颜色

**Theme anchor**

Seed Color 在 Palette 中保留的身份和色相来源，用于生成 Accent 和主题强调状态；它不要求直接铺满大面积 Surface。

_Avoid_: 所有背景必须使用的颜色

**Tonal surface**

围绕 Theme anchor 的低饱和、分明明度层级的背景角色，用于大面积界面区域；它保留主题色相但不复制 Seed Color 的完整饱和度。

_Avoid_: 把 Accent 直接当作所有背景

**Appearance-safe Palette**

同时满足可读性、相邻区域区分和视觉舒适度的 Palette；它限制大面积饱和度、保持 Accent 的色相身份，并避免普通角色无理由坍缩为纯黑或纯白。

_Avoid_: 只通过对比度检查的 Palette

**Visual role**  
Palette 中描述一种稳定视觉语义的角色，例如 surface、surface_subtle、surface_raised、foreground、selection 或 border。  
_Avoid_: 某个应用的临时颜色、每个字段一个颜色

**Adjacent UI region**  
在同一视图中视觉上相邻、需要彼此分辨的背景区域，例如工具栏与内容区、活动标签与非活动标签、面板与编辑器。  
_Avoid_: 任意两个颜色、所有颜色必须不同

**Color field**  
某个 Target 公开主题 schema 中接受颜色、色调或显示属性的字段。  
_Avoid_: 所有配置项

**Field Evidence Matrix**

按 Target、Mode、界面状态和相邻区域记录 Color field 的公开来源、实际语义与可读性证据，用于决定字段映射和验收；它不直接规定颜色值。
_Avoid_: 主题颜色抄录表、截图集合

**Dense primary text**

Light Mode 中需要连续阅读或快速辨认的普通文字，例如编辑器/终端正文、命令行输出、表格内容、导航标签和常规控件标签；它不包括选中态、禁用态或装饰性文字。
_Avoid_: 所有前景色、强调文字

**Neutral primary text**

供 Dense primary text 使用的低色度、接近中性的文字角色；它可以脱离 Seed Color 的色相，以保持阅读清晰度，而 Seed Color 身份由 Tonal surface、Accent 和语义状态保留。
_Avoid_: 带主题色的所有文字、纯黑兜底

**Accent color**

Windows 或应用用于强调控件、链接、标题栏和边框的用户可见颜色。它可以存在于浅色和深色系统模式中。

_Avoid_: 任务栏一定会显示的颜色

**Taskbar accent display**

Windows Shell 是否把 Accent color 显示到开始菜单和任务栏的独立能力；它受系统模式和用户设置限制。

_Avoid_: Accent color 本身

### Target language

**Marketplace**  
仓库级的 Codex Plugin 安装索引；只负责登记可安装的 Plugin，不承载插件运行时。

**Plugin**  
一个可安装的插件包，包含 `.codex-plugin/plugin.json`、插件说明和一个或多个 Skill。

**Skill package**  
Plugin 内可独立分发的能力单元；其说明、引用资料、脚本和运行时项目都放在同一个 Skill 目录内。

**Target**  
一个独立的主题集成：Windows、Windows Terminal、VS Code、TRAE、Codex 或 Chrome。  
_Avoid_: 应用（当 Windows 系统也在讨论范围内时）

**Theme registration**

Target 记录主题扩展或主题包，使其出现在可选择的主题清单中；仅有本地主题产物并不算注册成功。注册成功需要登记、登记指向的主题产物、贡献的主题标签和目标设置形成一致证据。注册成功不代表该主题已经成为当前活动主题。

_Avoid_: 已自动生效

**Active Target instance**
由同一个启动器/可执行文件、用户数据目录和扩展目录组成的 Target 配置实例。同一台机器可以有多个实例；不能仅凭用户名、固定盘符、安装管理器或默认目录猜测活动实例。

_Avoid_: 当前用户目录、唯一安装

**Theme activation**

Target 将已注册的主题明确设为当前活动主题；Light/Dark 变体是否自动切换由 Target 和用户偏好决定。

_Avoid_: 扩展已安装

**Canonical theme artifact**

面向用户的唯一推荐主题产物；同一 Mode 的压缩包、兼容别名和事务内部副本不属于可选主题。

_Avoid_: 每个生成文件都是一个主题

**Skill-local runtime root**

由 Skill 自身安装目录解析出的固定运行时根目录；默认的 `.one-tone`、Plan、Transaction 和生成产物都位于该目录下，与 Agent 当前工作目录无关。

_Avoid_: 当前命令所在目录

**Field inventory**  
某个 Target 在指定版本基线下应覆盖的公开主题字段清单，是测试和 Verify 的依据。  
_Avoid_: 可能存在的字段、未经验证的私有字段

**Capability status**  
某个字段在实际 Target 上的状态：supported、applied、verified、unsupported 或 not-applicable。
_Avoid_: 用 Target 总体状态掩盖字段差异

**Mode**  
用户可见的浅色或深色主题变体。Mode 只描述同一 Seed Color 的呈现变体，不等于 Windows 系统模式；工具不替用户切换系统模式。
_Avoid_: 强制模式、运行模式

**Mode coherence**

同一 Seed Color 的 Light 与 Dark 变体共享色相、区域层级和主题身份，只改变必要的明度与对比关系；两者不要求使用相同颜色，但不应因过大的明暗跨度而呈现为两套独立主题。
_Avoid_: 每个 Mode 独立追求最大对比度

### Workflow language

**Plan**  
用户在 Preview 阶段确认的 Seed Color、Mode、Target 和字段能力预期。对于需要发现配置实例的 Target，Plan 还保存已解析且纳入 Hash 的可执行文件、设置文件和扩展目录；Apply 与 Verify 必须使用同一组路径。
_Avoid_: 临时配置、Apply 参数

**Transaction**  
一次 Apply 的持久化操作记录，包含每个 Target 的 Snapshot、Apply、Verify 和 Rollback 信息。  
_Avoid_: 全局状态

**Serialized report value**

Transaction 中用于说明 Target 字段状态、供用户和工具读取的值；它不等同于 Snapshot，也不承担精确恢复原始 Target 状态的职责。
_Avoid_: 把事务报告值当作 Snapshot

Serialized report value 必须能安全写入事务 JSON；二进制值使用不丢失信息的报告表示，但仍不承担 Snapshot 的恢复职责。

**Snapshot**  
修改某个 Target 前保存的原始状态，只能用于该 Transaction 的 Rollback。  
_Avoid_: 通用备份

**Preview**  
只产生 Plan 和检测结果的阶段，不改变 Target。  
_Avoid_: 试应用

**Apply**  
使用已验证 Plan 修改 Target 的阶段。  
_Avoid_: 直接同步

**Verify**  
只读取当前 Target，并按字段和 Visual role 与 Plan 对比的阶段。  
_Avoid_: 再次应用

**Rollback**  
使用明确 Transaction 的 Snapshot 或产物元数据恢复状态的阶段。  
_Avoid_: 撤销所有修改

**Partial**  
至少有一个 Target 或字段完成，同时存在 unsupported、用户操作、失败或未验证项的结果。  
_Avoid_: 大致成功

### Workstation language

**Desktop zero**
当前登录 Windows 用户的桌面最终不保留用户可见内容：快捷方式直接删除，其他文件和文件夹分类移动到 `D:\data`；公共桌面不属于该范围。
_Avoid_: 清理桌面、桌面归档

**Resolved desktop**
Windows 当前用户实际呈现为桌面的目录；它可以是本地目录，也可以是被重定向到 OneDrive 或其他位置的目录。
_Avoid_: 固定桌面路径、默认桌面

**Desktop classification**
桌面上的非快捷方式内容按预先确认的分类规则移动到 `D:\data`；移动前必须展示分类和目标路径。
_Avoid_: 随意搬家、未知分类

**Deterministic classification**
文件分类依据扩展名和已有文件夹等可解释规则，不依据 AI 对文件内容的猜测；无法判断的内容进入未分类区域。
_Avoid_: 智能猜测、静默重命名

**Desktop categories**
规范分类目录为文档、图片、视频、音频、压缩包、安装包、代码和未分类；已有文件夹整体归入相应类别。
_Avoid_: 每次运行临时建类、按文件内容猜类

**Deterministic name collision**
分类目标已有同名内容时不覆盖原内容，使用稳定的数字后缀生成新名称，并在报告中说明。
_Avoid_: 静默覆盖、随机重命名

**Constrained repair**
整理失败时可以申请当前任务所需的权限，并仅针对实际锁定目标的非系统进程尝试关闭；未知或系统进程不得被强行终止。
_Avoid_: 全局提权、关闭所有占用者

**Desktop cleanup workflow**
桌面整理先生成待删除和待移动清单，用户确认后执行，最后验证桌面状态和移动结果。
_Avoid_: 调用即执行、无清单整理

**Move rollback ledger**
文件移动保留内部来源与目标记录，正常整理结果不主动展示；用户明确要求回滚时才使用该记录，快捷方式删除不在回滚范围内。
_Avoid_: 把删除伪装成可恢复、自动回滚

**Cleanup transaction**
一次桌面整理及其文件移动记录通过明确的事务 ID 标识；回滚必须指定该 ID。
_Avoid_: 默认回滚最近一次、回滚所有整理

**Existing tool preservation**
工具链插件不卸载或重置已存在的软件；它只识别缺失项并帮助用户补齐。
_Avoid_: 清理重装、环境归零

**Toolchain source fallback**
缺失软件优先通过 Scoop 安装，Scoop 无法提供或安装失败时再尝试 winget；winget 的安装路径通常由系统决定。
_Avoid_: 强制统一所有安装路径、保证 Scoop 覆盖一切

**Scoop root**
该工具链的 Scoop 安装根目录固定为 `D:\software\scoop`；无法在该位置建立时，Scoop 配置失败。
_Avoid_: 默认用户目录、隐式换盘

**Core toolchain baseline**
Python、Git、uv 和 Node.js 是该工作站规范的基础工具；缺失时优先由 Scoop 补齐，Scoop 无法提供时才转向 winget。
_Avoid_: 可选开发工具、任意软件清单

**Explicit install confirmation**
工具链 Skill 必须先展示缺失项、安装来源和路径限制，用户明确确认后才执行安装。
_Avoid_: 静默安装、模糊授权

**Taskbar search**
Windows 任务栏上的系统 Search 搜索框，是本项目规定的软件启动入口。
_Avoid_: 导航窗口、桌面启动、任意启动器

**Search-first desktop rule**
桌面零规范要求用户通过任务栏搜索启动软件，不在桌面保留快捷方式；该规则由 Skill 提醒和验证，不由后台服务强制。
_Avoid_: 后台监控、启动方式封锁

**Fundamentals reminder**
工具链 Skill 明确提醒用户：AI 不能替代计算机科学基础知识；基础工具优先通过 Scoop 安装，Scoop 无法提供时再使用 winget，并说明 winget 的路径限制。
_Avoid_: 羞辱用户、暗示 AI 能替代基础能力

**Directory ownership**
`zen-desktop-zero` 创建并管理 `D:\data` 及分类目录，`zen-scoop-toolchain` 创建并管理 `D:\software\scoop`；两个插件不重复管理对方的目录。
_Avoid_: 独立目录插件、重复初始化

**Workstation plugin boundary**
第一批只新增 `zen-desktop-zero` 与 `zen-scoop-toolchain` 两个 Plugin；前者负责桌面规范，后者负责基础工具链，均以用户主动调用的 Skill 运行。
_Avoid_: 后台强制服务、为目录初始化单独建插件

**Managed D roots**
`D:\data` 与 `D:\software` 是规范化的工作区根目录；插件可以创建自己的子目录，但不拥有或清空根目录中的既有内容。
_Avoid_: D 盘接管、根目录清空

**D-drive requirement**
依赖可用且可写的 D 盘；条件不满足时任务失败，不回退到其他盘符。
_Avoid_: 自动换盘、备用安装盘

## Relationships

- Seed Color 生成 Palette。
- Palette 提供 Visual role。
- Target Adapter 把 Color field 映射到 Visual role。
- Field inventory 定义应覆盖的 Color field。
- Plan 保存一次 Preview 的 Target 和 Mode 预期。
- Preview 为需要配置实例发现的 Target 解析唯一 Active Target instance；Apply 与 Verify 不重新猜测路径。
- Transaction 记录一次 Apply 及其后续 Verify 或 Rollback。
- `zen-desktop-zero` 将 Resolved desktop 规范化为 Desktop zero；Desktop classification 将非快捷方式内容移动到 `D:\data`，Cleanup transaction 关联 Move rollback ledger。
- `zen-scoop-toolchain` 检查 Core toolchain baseline；Scoop root 是首选安装位置，Toolchain source fallback 在 Scoop 失败时指向 winget。
