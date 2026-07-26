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

新增 Plugin 时同步更新根目录 .agents/plugins/marketplace.json、对应 Plugin README、Plugin envelope 测试和 Skill/runtime 测试。当前 Plugin：`zen-one-tone-windows`、`zen-desktop-zero`、`zen-scoop-toolchain`。

## 当前 Plugin

| Plugin | Skill | 能力 |
| --- | --- | --- |
| `zen-one-tone-windows` | `zen-one-tone-windows` | 预览、应用、验证并回滚统一 Windows 主题 |
| `zen-desktop-zero` | `zen-desktop-zero` | 删除当前用户桌面快捷方式，分类移动其他内容到 `D:\data` |
| `zen-scoop-toolchain` | `zen-scoop-toolchain` | 在 `D:\software\scoop` 优先通过 Scoop 补齐 Python、Git、uv 和 Node.js |

两个工作站 Skill 都先 Preview，Apply 需要明确确认；`zen-desktop-zero` 的快捷方式删除不可恢复，`zen-scoop-toolchain` 不卸载或重置已有软件。

