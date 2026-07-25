# One-Tone Domain Context

One-Tone 是一个把同一 Seed Color 统一到受支持 Windows Target 的可回滚主题工具。

## Language

### Color language

**Seed Color**  
用户选择的源颜色，作为主题统一的起点和产品语义中的主色。  
_Avoid_: 随机主题色、默认主色

**Palette**  
由 Seed Color 派生的一组颜色角色，而不是一组按界面字段随意生成的颜色。  
_Avoid_: 颜色字典、字段颜色

**Visual role**  
Palette 中描述一种稳定视觉语义的角色，例如 surface、surface_subtle、surface_raised、foreground、selection 或 border。  
_Avoid_: 某个应用的临时颜色、每个字段一个颜色

**Adjacent UI region**  
在同一视图中视觉上相邻、需要彼此分辨的背景区域，例如工具栏与内容区、活动标签与非活动标签、面板与编辑器。  
_Avoid_: 任意两个颜色、所有颜色必须不同

**Color field**  
某个 Target 公开主题 schema 中接受颜色、色调或显示属性的字段。  
_Avoid_: 所有配置项

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

Target 记录主题扩展或主题包，使其出现在可选择的主题清单中。注册成功不代表该主题已经成为当前活动主题。

_Avoid_: 已自动生效

**Theme activation**

Target 将已注册的主题明确设为当前活动主题；Light/Dark 变体是否自动切换由 Target 和用户偏好决定。

_Avoid_: 扩展已安装

**Canonical theme artifact**

面向用户的唯一推荐主题产物；同一 Mode 的压缩包、兼容别名和事务内部副本不属于可选主题。

_Avoid_: 每个生成文件都是一个主题

**Field inventory**  
某个 Target 在指定版本基线下应覆盖的公开主题字段清单，是测试和 Verify 的依据。  
_Avoid_: 可能存在的字段、未经验证的私有字段

**Capability status**  
某个字段在实际 Target 上的状态：supported、applied、verified、unsupported 或 not-applicable。
_Avoid_: 用 Target 总体状态掩盖字段差异

**Mode**  
用户可见的浅色或深色主题变体。Mode 只描述同一 Seed Color 的呈现变体，不等于 Windows 系统模式；工具不替用户切换系统模式。
_Avoid_: 强制模式、运行模式

### Workflow language

**Plan**  
用户在 Preview 阶段确认的 Seed Color、Mode、Target 和字段能力预期。  
_Avoid_: 临时配置、Apply 参数

**Transaction**  
一次 Apply 的持久化操作记录，包含每个 Target 的 Snapshot、Apply、Verify 和 Rollback 信息。  
_Avoid_: 全局状态

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

## Relationships

- Seed Color 生成 Palette。
- Palette 提供 Visual role。
- Target Adapter 把 Color field 映射到 Visual role。
- Field inventory 定义应覆盖的 Color field。
- Plan 保存一次 Preview 的 Target 和 Mode 预期。
- Transaction 记录一次 Apply 及其后续 Verify 或 Rollback。
