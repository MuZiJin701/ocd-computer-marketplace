# Tests

测试目录按 Marketplace → Plugin → Skill 的层级组织：

~~~text
tests/
├─ marketplace/                         # Marketplace manifest 和索引
├─ plugins/<plugin-name>/               # Plugin envelope
│  ├─ test_plugin.py                    # Plugin contract
│  └─ skills/<skill-name>/              # Skill package contract
│     ├─ test_skill.py
│     └─ runtime/                       # 该 Skill runtime 的行为
~~~

当前 runtime 测试按 Plugin 和 Skill 分开：One-Tone 位于 `tests/plugins/zen-one-tone-windows/skills/zen-one-tone-windows/runtime/`，Desktop zero 和 Scoop toolchain 的行为测试分别位于对应 Plugin 的 Skill 测试目录，与可分发 Skill 的目录边界对应。

默认测试使用临时目录和 fake backend，不触碰真实桌面、不提权、不终止进程，也不安装真实软件。真实桌面删除、进程处理、Scoop 和 winget 测试必须单独标记并说明风险。
