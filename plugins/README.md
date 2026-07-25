# Plugin packages

每个直接子目录都是一个可安装的 Codex Plugin，不能把多个 Plugin 的 runtime、Skill 或测试放在同一目录。

## Plugin contract

~~~text
plugins/<plugin-name>/
├─ .codex-plugin/plugin.json
├─ README.md
└─ skills/
   └─ <skill-name>/
      ├─ SKILL.md
      ├─ agents/
      ├─ references/
      ├─ scripts/
      └─ <runtime project>
~~~

Plugin 元数据只描述安装边界；具体 Skill 必须能脱离仓库根目录独立运行。运行时依赖放在 Skill 内，不放在 plugins 根目录，也不共享隐式的根级 runtime。

新增 Plugin 时同步更新根目录 .agents/plugins/marketplace.json、对应 Plugin README、Plugin envelope 测试和 Skill/runtime 测试。

