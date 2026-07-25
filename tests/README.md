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

当前 One-Tone runtime 测试位于 tests/plugins/one-tone-windows/skills/unify-windows-theme/runtime/，与可分发 Skill 的目录边界对应。

默认测试使用 fixture，不触碰真实桌面。真实 Target 测试必须单独标记并说明风险。
