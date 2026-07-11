# One-Tone Codex Skill/Plugin Implementation Plan

> **Superseded architecture note:** The initial local-wrapper plan kept the Python core at the repository root. The marketplace-ready correction is defined in `docs/superpowers/plans/2026-07-11-marketplace-runtime-architecture.md`: the Plugin now owns the runtime, the repository adds `.agents/plugins/marketplace.json`, and Skill execution uses a single Python launcher.

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 将已完成的 Python 核心包装成项目内可校验、可打包的 `one-tone-windows` Codex Plugin，并提供 `unify-windows-theme` Skill 的安全对话工作流。

**Architecture:** 插件包位于 `plugins/one-tone-windows/`，核心 Python 项目继续位于仓库根目录。Skill 只收集参数、调用 Skill 脚本和解释结构化结果；脚本通过 `uv run --project <repo-root> one-tone ... --output json` 调用核心 CLI，不复制业务逻辑。所有全局安装、市场写入和真实 Apply 保持在本计划之外，除非用户另行确认。

**Tech Stack:** Python 3.11+、uv、pytest、Codex plugin-creator、Codex skill-creator、JSON、Markdown、ZIP。

## Global Constraints

- 插件目录固定为 `plugins/one-tone-windows/`，插件 manifest 名称为 `one-tone-windows`。
- Skill 目录固定为 `plugins/one-tone-windows/skills/unify-windows-theme/`。
- 只在项目内生成、校验和打包，不自动写入 `$CODEX_HOME`，不创建个人 marketplace 条目。
- Python 核心是唯一业务实现；Skill 和 scripts 不重复实现 Palette、Plan、Adapter 或 Transaction。
- Preview 不产生外部变更；Apply 必须有 Plan ID 和确认；Rollback 必须有 transaction ID。
- `verify --restart-apps` 是允许应用进程重启的显式门禁；默认不重启应用。
- Chrome 的 `requires_user_action` 必须原样传递给用户，不得解释为自动激活成功。
- 只有真实目标完成八步验收并记录实际版本，才可标记 `FULL`；fixture 结果只能用于自动化测试。
- 当前项目原有 `AGENTS.md` 和计划书未跟踪文件必须保留，不纳入无关重置或删除。

## File Map

- Modify: `.gitignore` — 忽略 `.pytest-tmp/`、插件构建产物和本地运行目录。
- Modify: `pyproject.toml` — 增加 CLI JSON 输出测试所需的 pytest 配置，不增加运行时框架。
- Modify: `src/one_tone/cli.py` — 增加 `--output human|json`，保留现有人类输出。
- Modify: `tests/test_cli.py` — CLI JSON 输出和错误结构测试。
- Create: `plugins/one-tone-windows/.codex-plugin/plugin.json` — scaffold 生成的插件 manifest。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md` — Skill 触发描述和工作流。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/agents/openai.yaml` — Skill UI 元数据。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_common.py` — 项目根路径和 JSON 子进程调用公共函数。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_preview.py` — Preview 包装脚本。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_apply.py` — Apply 确认门禁包装脚本。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_verify.py` — Verify 和重启许可包装脚本。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_rollback.py` — Rollback 包装脚本。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/supported-targets.md` — 支持目标、路径和支持级别规则。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/safety-and-confirmation.md` — 外部写入、重启、Chrome 和回滚门禁。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/result-schema.md` — JSON 结果字段解释。
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/assets/README.md` — 说明当前没有必须随 Skill 分发的二进制资源。
- Create: `tests/test_plugin_package.py` — manifest、Skill、脚本和校验命令测试。
- Create: `tests/test_skill_scripts.py` — 脚本调用核心 CLI 的 fixture 测试。
- Create: `docs/marketplace-examples.md` — 三个市场示例和限制。
- Modify: `README.md` — 插件安装/本地校验/触发方式和当前限制。

---

### Task 1: 稳定 CLI JSON 输出和受限环境测试入口

**Files:**
- Modify: `src/one_tone/cli.py`
- Modify: `tests/test_cli.py`
- Modify: `tests/conftest.py`
- Modify: `.gitignore`
- Test: `tests/test_cli.py`

**Interfaces:**
- Every command accepts `--output human|json`, defaulting to `human`.
- `main([... "--output", "json"]) -> int` writes exactly one JSON object to stdout for command results and JSON errors to stderr.
- JSON result includes `command`, `status`, `plan_id` or `transaction_id`, `targets`, `support_levels`, `requires_user_action`, and `message`.

- [ ] **Step 1: Write the failing tests**

```python
import json

from one_tone.cli import main


def test_preview_json_output_contains_plan_id_and_targets(tmp_path, capsys):
    code = main([
        "preview", "#7C3AED", "--targets", "codex",
        "--plans-dir", str(tmp_path / "plans"),
        "--state-dir", str(tmp_path / "state"),
        "--output", "json",
    ])

    assert code == 0
    payload = json.loads(capsys.readouterr().out)
    assert payload["command"] == "preview"
    assert payload["plan_id"].startswith("plan-")
    assert payload["targets"][0]["target"] == "codex"


def test_apply_json_error_is_machine_readable(capsys):
    assert main(["apply", "missing-plan", "--confirm", "--output", "json"]) == 1
    error = json.loads(capsys.readouterr().err)
    assert error["command"] == "apply"
    assert error["error"] == "Plan not found: missing-plan"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_cli.py -q`
Expected: FAIL because CLI does not parse `--output` or emit JSON.

- [ ] **Step 3: Write minimal implementation**

Add one serializer in `cli.py` instead of duplicating output code in each command:

```python
def emit_result(payload: dict[str, object], output: str, *, error: bool = False) -> None:
    stream = sys.stderr if error else sys.stdout
    if output == "json":
        print(json.dumps(payload, ensure_ascii=False, sort_keys=True), file=stream)
    else:
        print_human_result(payload, stream)
```

Thread `output` through Preview, Apply, Verify and Rollback. Add `.pytest-tmp/` and `/dist/` to `.gitignore`. Configure the documented fallback command with `--basetemp .pytest-tmp`; do not change runtime dependencies.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_cli.py -q`
Expected: all CLI tests pass, including existing human-output tests and the new JSON tests.

- [ ] **Step 5: Commit**

```powershell
git add .gitignore src/one_tone/cli.py tests/conftest.py tests/test_cli.py
git commit -m "feat: add machine-readable CLI results"
```

### Task 2: 使用官方 scaffold 创建项目内 Plugin 和 Skill 目录

**Files:**
- Create: `plugins/one-tone-windows/.codex-plugin/plugin.json`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/`
- Test: `tests/test_plugin_package.py`

**Interfaces:**
- Plugin root is `plugins/one-tone-windows`; manifest name is `one-tone-windows`.
- Skill root is `plugins/one-tone-windows/skills/unify-windows-theme`.
- No marketplace file or global install is created.

- [ ] **Step 1: Write the failing structure test**

```python
from pathlib import Path


def test_plugin_scaffold_is_present():
    root = Path("plugins/one-tone-windows")
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert (root / "skills/unify-windows-theme/SKILL.md").is_file()
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_plugin_package.py::test_plugin_scaffold_is_present -q`
Expected: FAIL because the Plugin and Skill directories do not exist.

- [ ] **Step 3: Run the required scaffold commands**

Run from the plugin-creator skill root:

```powershell
python scripts/create_basic_plugin.py one-tone-windows --path D:/data/projects/practice/OCD/plugins --with-skills --force
```

Run from the skill-creator skill root:

```powershell
python scripts/init_skill.py unify-windows-theme --path D:/data/projects/practice/OCD/plugins/one-tone-windows/skills --resources scripts,references,assets --interface display_name="Unify Windows Theme" --interface short_description="Preview, apply, verify, and roll back a shared high-contrast Windows theme" --interface default_prompt="Use this Skill to preview and safely apply one Palette to selected Windows targets with confirmation and rollback."
```

Replace every generated placeholder with real content before validation. Do not pass `--with-marketplace`; this phase is project-local only.

- [ ] **Step 4: Run scaffold validators**

Run:

```powershell
python C:/Users/30733/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/one-tone-windows
python C:/Users/30733/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
```

Expected: both validators exit `0`; manifest and Skill frontmatter are structurally valid.

- [ ] **Step 5: Commit**

```powershell
git add plugins/one-tone-windows
git commit -m "feat: scaffold local one-tone Codex plugin"
```

### Task 3: 编写 Skill 工作流和引用资料

**Files:**
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/agents/openai.yaml`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/supported-targets.md`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/safety-and-confirmation.md`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/references/result-schema.md`
- Modify: `plugins/one-tone-windows/skills/unify-windows-theme/assets/README.md`
- Test: `tests/test_plugin_package.py`

**Interfaces:**
- `SKILL.md` frontmatter contains only `name` and `description`.
- Body uses imperative instructions and links directly to the three references.
- `agents/openai.yaml` is generated from the final Skill metadata and does not contain stale copy.

- [ ] **Step 1: Write the failing tests**

```python
import json
from pathlib import Path


def test_skill_contains_trigger_workflow_and_direct_references():
    root = Path("plugins/one-tone-windows/skills/unify-windows-theme")
    skill = (root / "SKILL.md").read_text(encoding="utf-8")
    manifest = json.loads(Path("plugins/one-tone-windows/.codex-plugin/plugin.json").read_text(encoding="utf-8"))
    assert "Seed Color" in skill
    assert "Preview" in skill and "Rollback" in skill
    assert "requires_user_action" in skill
    assert "references/supported-targets.md" in skill
    assert manifest["name"] == "one-tone-windows"
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_plugin_package.py::test_skill_contains_trigger_workflow_and_direct_references -q`
Expected: FAIL until the generated template is replaced with the real workflow.

- [ ] **Step 3: Write the Skill and references**

The Skill body must implement this decision table:

```text
No Seed Color → ask for HEX color
No Targets → show supported targets and ask for selection
Before Preview → no external change
Before Apply → show Plan ID, targets, changes, warnings; require confirmation
requires_user_action → pause and explain the exact manual action
FAILED → show failed target, auto-rollback result, and transaction ID
Rollback request → require explicit transaction ID
```

References document the confirmed Windows 10/11 range, Scoop paths, ordinary dark mode, wallpaper, Terminal current Profile, VS Code AI-panel limitation, Codex `SKIPPED` rule, Chrome manual action, and FULL/PARTIAL/SKIPPED semantics. Keep details in references instead of bloating `SKILL.md`.

- [ ] **Step 4: Regenerate metadata and validate**

Run:

```powershell
python C:/Users/30733/.codex/skills/.system/skill-creator/scripts/generate_openai_yaml.py plugins/one-tone-windows/skills/unify-windows-theme --interface display_name="Unify Windows Theme" --interface short_description="Preview, apply, verify, and roll back a shared high-contrast Windows theme" --interface default_prompt="Use this Skill to preview and safely apply one Palette to selected Windows targets with confirmation and rollback."
python C:/Users/30733/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
python C:/Users/30733/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/one-tone-windows
```

Expected: no placeholder, frontmatter, metadata, or manifest validation errors.

- [ ] **Step 5: Commit**

```powershell
git add plugins/one-tone-windows/skills tests/test_plugin_package.py
git commit -m "feat: add safe theme Skill workflow"
```

### Task 4: 实现四个 Skill CLI 包装脚本

**Files:**
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_common.py`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_preview.py`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_apply.py`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_verify.py`
- Create: `plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_rollback.py`
- Create: `tests/test_skill_scripts.py`

**Interfaces:**
- `one_tone_common.py` exposes `repo_root() -> Path` and `run_core(args: list[str]) -> int`.
- Every wrapper accepts `--help`, forwards `--output json`, and preserves the core CLI exit code.
- Apply wrapper refuses to run without a Plan ID and `--confirm`.
- Verify wrapper forwards `--restart-apps` only when explicitly passed.

- [ ] **Step 1: Write the failing tests**

```python
import json
import subprocess
import sys
from pathlib import Path


def test_preview_script_calls_core_cli_with_json(tmp_path):
    script = Path("plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_preview.py")
    completed = subprocess.run([
        sys.executable, str(script), "#7C3AED", "--targets", "codex",
        "--plans-dir", str(tmp_path / "plans"), "--state-dir", str(tmp_path / "state"),
    ], capture_output=True, text=True)
    assert completed.returncode == 0
    assert json.loads(completed.stdout)["command"] == "preview"


def test_apply_script_rejects_missing_confirmation():
    script = Path("plugins/one-tone-windows/skills/unify-windows-theme/scripts/one_tone_apply.py")
    completed = subprocess.run([sys.executable, str(script)], capture_output=True, text=True)
    assert completed.returncode == 2
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_skill_scripts.py -q`
Expected: FAIL because wrapper scripts do not exist.

- [ ] **Step 3: Write the wrappers**

Resolve the repository root from `Path(__file__).resolve().parents[4]` and call the core without shell interpolation:

```python
command = ["uv", "run", "--project", str(repo_root()), "one-tone", *args, "--output", "json"]
return subprocess.run(command, cwd=repo_root()).returncode
```

Use argparse for required positional IDs and confirmation flags. Do not parse human output, do not call `reg`, do not write user configuration directly, and do not install the plugin.

- [ ] **Step 4: Run wrapper tests**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_skill_scripts.py -q`
Expected: wrapper help, JSON forwarding and confirmation-gate tests pass.

- [ ] **Step 5: Commit**

```powershell
git add plugins/one-tone-windows/skills/unify-windows-theme/scripts tests/test_skill_scripts.py
git commit -m "feat: add Skill CLI wrappers"
```

### Task 5: 增加插件包测试、示例和本地打包

**Files:**
- Modify: `tests/test_plugin_package.py`
- Create: `docs/marketplace-examples.md`
- Modify: `README.md`
- Create: `scripts/package_one_tone_plugin.py`
- Modify: `.gitignore`

**Interfaces:**
- `scripts/package_one_tone_plugin.py` accepts `--output PATH` and writes a ZIP containing only `plugins/one-tone-windows`.
- The ZIP excludes `.venv`, `.pytest-tmp`, `plans`, `transactions`, and system state directories.
- Examples cover purple all-target preview, blue-green selected targets, and editor-only application.

- [ ] **Step 1: Write the failing tests**

```python
from pathlib import Path


def test_market_examples_and_packager_exist():
    assert Path("docs/marketplace-examples.md").is_file()
    assert Path("scripts/package_one_tone_plugin.py").is_file()


def test_plugin_package_does_not_contain_runtime_state():
    text = Path("docs/marketplace-examples.md").read_text(encoding="utf-8")
    assert "紫色" in text
    assert "只更新编辑器" in text
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_plugin_package.py -q`
Expected: FAIL because examples and package script do not exist.

- [ ] **Step 3: Write packager and examples**

Use `zipfile` with paths relative to the repository root; refuse an output path inside the source tree if it would include itself. Write the three examples with expected confirmation messages and limitations, not claims of `FULL`.

- [ ] **Step 4: Build and inspect the package**

Run:

```powershell
python scripts/package_one_tone_plugin.py --output dist/one-tone-windows.zip
python -m zipfile -l dist/one-tone-windows.zip
```

Expected: ZIP contains `.codex-plugin/plugin.json`, Skill files, scripts, references and assets only.

- [ ] **Step 5: Commit**

```powershell
git add scripts/package_one_tone_plugin.py docs/marketplace-examples.md README.md tests/test_plugin_package.py .gitignore
git commit -m "feat: add local plugin packaging and examples"
```

### Task 6: 完成发布门禁和最终文档同步

**Files:**
- Modify: `README.md`
- Modify: `OCD_Windows_Theme_Skill_计划书.md`
- Modify: `tests/test_project_smoke.py`

**Interfaces:**
- README documents project-local build, validation commands, no-global-install boundary, real target FULL gate, and current Codex/Cursor limitations.
- Plan book reflects completed stages 0/1–2/3–6 and remaining real-target evidence requirements.

- [ ] **Step 1: Write the failing documentation test**

```python
def test_readme_documents_local_plugin_release_gate():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "one-tone-windows" in text
    assert "不自动安装" in text
    assert "FULL" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run --no-cache pytest --basetemp .pytest-tmp tests/test_project_smoke.py::test_readme_documents_local_plugin_release_gate -q`
Expected: FAIL until README and plan wording are synchronized.

- [ ] **Step 3: Update documentation**

Document exact commands:

```powershell
uv run --no-cache pytest --basetemp .pytest-tmp
python C:/Users/30733/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/one-tone-windows
python C:/Users/30733/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
python scripts/package_one_tone_plugin.py --output dist/one-tone-windows.zip
```

State that real Apply/Restart/Chrome confirmation remains a separate user-approved validation step and that unverified Codex/Cursor targets remain `SKIPPED`.

- [ ] **Step 4: Run final validation**

Run:

```powershell
uv run --no-cache pytest --basetemp .pytest-tmp
python C:/Users/30733/.codex/skills/.system/plugin-creator/scripts/validate_plugin.py plugins/one-tone-windows
python C:/Users/30733/.codex/skills/.system/skill-creator/scripts/quick_validate.py plugins/one-tone-windows/skills/unify-windows-theme
python scripts/package_one_tone_plugin.py --output dist/one-tone-windows.zip
git diff --check
git status --short
```

Expected: tests and validators exit `0`, package is created, and no unrelated user files are staged.

- [ ] **Step 5: Commit**

```powershell
git add README.md tests/test_project_smoke.py plugins/one-tone-windows scripts/package_one_tone_plugin.py docs/marketplace-examples.md
git commit -m "feat: complete local Codex Skill plugin release gate"
```

`OCD_Windows_Theme_Skill_计划书.md` is an existing user-owned untracked document; update it in place as required by the project rules, verify its content, and leave its staging/commit decision to the user.

## Plan Self-Review

- Covers updated plan stages 0, 7 and 8, while preserving the already implemented Python core and stages 1–6.
- Uses official scaffold/validator tools instead of inventing plugin manifest or Skill metadata schemas.
- Keeps the plugin project-local and explicitly excludes global installation and marketplace writes.
- Includes JSON CLI output before wrapper scripts, preventing fragile human-output parsing.
- Includes tests before each new implementation and a reproducible pytest fallback for the current cache/temp permission constraints.
- Preserves real-target FULL evidence as a separate gate; no fixture result is promoted to FULL.
- No unresolved placeholder or undefined interface remains.
