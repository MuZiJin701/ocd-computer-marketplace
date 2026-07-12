# One-Tone 阶段 3–6 适配器实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在阶段 1–2 核心闭环之上，实现 Windows 10/11、壁纸、Windows Terminal、VS Code Family、Codex、Chrome 的独立 Adapter，并提供八步验收命令与 FULL/PARTIAL/SKIPPED 结果。

**Architecture:** 所有目标通过 `ThemeAdapter` 共享最小生命周期，但每个目标拥有独立配置解析、快照和恢复逻辑。Windows 与壁纸使用可注入系统后端；Terminal 和编辑器使用 JSON/VSIX 文件；Codex 仅接受已验证的显式配置格式；Chrome 只生成主题 ZIP 并明确需要用户操作。Transaction 负责记录扩展操作和目标支持级别，CLI 负责目标注册、确认和显式进程重启。

**Tech Stack:** Python 3.11+、标准库 `winreg`/`ctypes`/`subprocess`/`zipfile`/`zlib`/`tomllib`、pytest、uv、Windows 10 22H2+、Windows 11 22H2+。

## Global Constraints

- 正式支持 Windows 10 22H2+ 与 Windows 11 22H2+；build `>=22621` 归类 Windows 11，build `>=19045` 且 `<22000` 归类 Windows 10。
- 只支持普通深色模式，不实现 Contrast Theme。
- Windows 壁纸由 Palette 生成确定性的深色渐变 PNG，并纳入 Snapshot、Apply、Verify、Rollback。
- Windows Terminal 使用实际 `settings.json`，只修改当前默认 Profile。
- VS Code、Cursor、TRAE 共用主题/VSIX 生成器，但 Adapter、配置路径和结果独立。
- Codex 必须使用独立 Adapter；未验证真实配置格式时返回 `skipped`。
- Chrome 生成主题 ZIP，Apply 可返回 `partial` 与 `requires_user_action=True`，不直接改 Preferences。
- `AdapterResult` 保留五个原有字段，并增加默认值为 `False` 的 `requires_user_action` 与默认值为 `None` 的 `version`。
- Adapter 增加 `restart()` 与 `verify_again(plan)`；未传 `--restart-apps` 时不得关闭或启动用户进程。
- 八步验收顺序固定为 Detect、Snapshot、Apply、Verify、Restart、Verify Again、Rollback、Verify Restore。
- 八步完成、无用户操作要求且记录应用版本才标记 `FULL`；其他明确限制为 `PARTIAL`；未检测到或未验证格式为 `SKIPPED`。
- 失败时自动回滚当前事务中已成功修改的目标；Rollback 只能使用指定 transaction ID 的备份。
- 不增加数据库、后台服务、事件溯源、复杂状态机或插件运行时。
- 真实 Apply、Restart 和 Chrome 用户操作属于外部状态变更；测试默认使用 fixture 和注入后端，CLI 只有显式确认才执行。

## File Map

- Modify: `src/one_tone/adapters/base.py` — 扩展 AdapterResult 和 ThemeAdapter 生命周期。
- Modify: `src/one_tone/adapters/file.py` — 提供 restart/verify_again，保持现有测试 Adapter 可用于八步测试。
- Modify: `src/one_tone/adapters/__init__.py` — 导出新增 Adapter 和支持级别类型。
- Create: `src/one_tone/adapters/windows.py` — Windows 版本、主题注册表、壁纸和系统生命周期。
- Create: `src/one_tone/adapters/terminal.py` — Windows Terminal Profile 解析和恢复。
- Create: `src/one_tone/adapters/vscode_family.py` — VS Code/Cursor/TRAE 共享主题和 VSIX 生成器。
- Create: `src/one_tone/adapters/codex.py` — 独立 Codex 配置 Adapter。
- Create: `src/one_tone/adapters/chrome.py` — Chrome 主题 ZIP 和用户操作结果。
- Modify: `src/one_tone/transaction.py` — 八步编排、操作记录和目标支持级别。
- Modify: `src/one_tone/cli.py` — 真实目标注册、`verify` 命令和 `--restart-apps`。
- Modify: `README.md` — 支持范围、Scoop 路径、壁纸、确认和限制。
- Modify: `OCD_Windows_Theme_Skill_计划书.md` — 同步 Windows 10、壁纸、开放问题和阶段验收。
- Create: `tests/test_windows_adapter.py` — Windows 后端 fixture 和壁纸测试。
- Create: `tests/test_terminal_adapter.py` — Terminal JSON fixture 测试。
- Create: `tests/test_vscode_family.py` — 主题/VSIX 和三编辑器配置测试。
- Create: `tests/test_codex_adapter.py` — Codex skipped 和显式 fixture 测试。
- Create: `tests/test_chrome_adapter.py` — Chrome ZIP 和 user-action 测试。
- Modify: `tests/test_transaction.py` — 八步记录和支持级别测试。
- Modify: `tests/test_cli.py` — `verify`、目标路径和 restart 参数测试。

---

### Task 1: 扩展 Adapter 合同和事务结果模型

**Files:**
- Modify: `src/one_tone/adapters/base.py`
- Modify: `src/one_tone/adapters/file.py`
- Modify: `src/one_tone/adapters/__init__.py`
- Modify: `src/one_tone/transaction.py`
- Test: `tests/test_adapters.py`
- Test: `tests/test_transaction.py`

**Interfaces:**
- `AdapterResult(..., requires_user_action: bool = False, version: str | None = None)` 保持旧五参数调用兼容。
- `ThemeAdapter` 增加 `restart() -> AdapterResult` 和 `verify_again(plan: Plan) -> AdapterResult`。
- `SupportLevel = Literal["FULL", "PARTIAL", "SKIPPED"]`。
- `TransactionRecord.support_levels: dict[str, SupportLevel]` 序列化到 `transaction.json`。
- `TransactionStore.append_operation(record, target, operation, result)` 记录操作名和完整结果。

- [ ] **Step 1: Write the failing tests**

```python
from one_tone.adapters import AdapterResult, FileAdapter
from one_tone.cli import main
from one_tone.plan import create_plan


def test_adapter_result_stores_user_action_and_version():
    result = AdapterResult("chrome", "partial", False, False, "load theme", True, "Chrome 138")
    assert result.requires_user_action is True
    assert result.version == "Chrome 138"


def test_file_adapter_supports_restart_and_verify_again(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    adapter = FileAdapter("file-demo", config)
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-contract-001")

    assert adapter.restart().status == "ok"
    assert adapter.verify_again(plan).status == "failed"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_adapters.py::test_adapter_result_user_action_field_defaults_false tests/test_adapters.py::test_file_adapter_supports_restart_and_verify_again -q`
Expected: FAIL because the new field and lifecycle methods do not exist.

- [ ] **Step 3: Write minimal implementation**

Add the optional dataclass field and lifecycle methods. `FileAdapter.restart()` returns `ok` with `verified=True` and message `file target does not require process restart`; `verify_again()` delegates to `verify(plan)`. `UnsupportedAdapter` returns `skipped` for both methods. Extend `TransactionRecord.to_dict/from_dict` with an empty-default `support_levels` mapping so old transaction files remain loadable.

```python
@dataclass(frozen=True)
class AdapterResult:
    target: str
    status: AdapterStatus
    changed: bool
    verified: bool
    message: str
    requires_user_action: bool = False
    version: str | None = None
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_adapters.py tests/test_transaction.py -q`
Expected: all existing Adapter and Transaction tests plus the two new contract tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters src/one_tone/transaction.py tests/test_adapters.py tests/test_transaction.py
git commit -m "feat: extend adapter lifecycle for full verification"
```

### Task 2: 实现 Windows 版本、主题注册表和渐变壁纸 Adapter

**Files:**
- Create: `src/one_tone/adapters/windows.py`
- Create: `tests/test_windows_adapter.py`
- Modify: `src/one_tone/adapters/__init__.py`

**Interfaces:**
- `detect_windows_version(registry: RegistryBackend) -> tuple[str, int] | None` returns `("windows-10", build)` or `("windows-11", build)`.
- `generate_wallpaper(palette: Mapping[str, str], path: Path, width: int = 1920, height: int = 1080) -> Path` writes a deterministic PNG.
- `WindowsAdapter(config: WindowsConfig, registry: RegistryBackend, desktop: DesktopBackend)` implements all seven lifecycle methods.
- `WindowsConfig` contains `wallpaper_dir: Path`, `min_windows_10_build: int = 19045`, `min_windows_11_build: int = 22621`.

- [ ] **Step 1: Write the failing tests**

```python
from one_tone.adapters.windows import (
    InMemoryDesktopBackend,
    InMemoryRegistryBackend,
    WindowsAdapter,
    WindowsConfig,
    detect_windows_version,
    generate_wallpaper,
)
from one_tone.plan import create_plan


def test_build_26200_is_windows_11_even_if_product_name_is_legacy():
    backend = InMemoryRegistryBackend({"CurrentBuild": "26200", "ProductName": "Windows 10 Home China"})
    assert detect_windows_version(backend) == ("windows-11", 26200)


def test_build_19045_is_windows_10():
    backend = InMemoryRegistryBackend({"CurrentBuild": "19045", "ProductName": "Windows 10 Pro"})
    assert detect_windows_version(backend) == ("windows-10", 19045)


def test_wallpaper_generation_is_png_and_deterministic(tmp_path):
    plan = create_plan("#7C3AED", ["windows"], plan_id="plan-windows-001")
    first = generate_wallpaper(plan.palette, tmp_path / "first.png", width=32, height=16)
    second = generate_wallpaper(plan.palette, tmp_path / "second.png", width=32, height=16)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().startswith(b"\\x89PNG\\r\\n\\x1a\\n")


def test_windows_adapter_snapshots_applies_verifies_and_restores(tmp_path):
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200", "AppsUseLightTheme": 1, "SystemUsesLightTheme": 1})
    desktop = InMemoryDesktopBackend(wallpaper="C:/old.jpg")
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    plan = create_plan("#7C3AED", ["windows"], plan_id="plan-windows-002")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert registry.values["AppsUseLightTheme"] == 1
    assert desktop.wallpaper == "C:/old.jpg"
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_windows_adapter.py -q`
Expected: FAIL because `one_tone.adapters.windows` does not exist.

- [ ] **Step 3: Write minimal implementation**

Use `winreg` for the real registry backend and `ctypes.windll.user32.SystemParametersInfoW` for the real desktop backend. Use `struct`/`zlib` to write a PNG without Pillow. Snapshot registry values and the old wallpaper file when it exists; write all generated assets under the current transaction backup/assets directory. Set both ordinary dark-mode values to `0`, set the wallpaper path, and verify by reading both back. Use the injected backends in tests so no real desktop is modified.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_windows_adapter.py -q`
Expected: all Windows version, deterministic PNG, apply and restore tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters/windows.py src/one_tone/adapters/__init__.py tests/test_windows_adapter.py
git commit -m "feat: add Windows theme and wallpaper adapter"
```

### Task 3: 实现 Windows Terminal 当前默认 Profile Adapter

**Files:**
- Create: `src/one_tone/adapters/terminal.py`
- Create: `tests/test_terminal_adapter.py`
- Modify: `src/one_tone/adapters/__init__.py`

**Interfaces:**
- `resolve_default_profile(settings: Mapping[str, Any]) -> tuple[int, str] | None` returns list index and resolution message.
- `TerminalAdapter(settings_path: Path, allow_restart: bool = False)` implements all seven lifecycle methods.
- `TerminalAdapter` only changes the resolved Profile, never `profiles.defaults` or other Profile entries.

- [ ] **Step 1: Write the failing tests**

```python
import json

from one_tone.adapters.terminal import TerminalAdapter, resolve_default_profile
from one_tone.plan import create_plan


def test_null_default_uses_first_local_profile():
    settings = {"profiles": {"default": None, "list": [
        {"name": "Windows PowerShell", "guid": "{one}"},
        {"name": "Azure", "guid": "{two}", "source": "Windows.Terminal.Azure"},
    ]}}
    assert resolve_default_profile(settings) == (0, "profiles.default is null; first local profile selected")


def test_terminal_adapter_only_changes_selected_profile_and_restores(tmp_path):
    settings_path = tmp_path / "settings.json"
    original = {"profiles": {"default": "{two}", "list": [
        {"name": "PowerShell", "guid": "{one}", "background": "#000000"},
        {"name": "Ubuntu", "guid": "{two}", "background": "#111111"},
    ]}}
    settings_path.write_text(json.dumps(original), encoding="utf-8")
    adapter = TerminalAdapter(settings_path)
    plan = create_plan("#7C3AED", ["terminal"], plan_id="plan-terminal-001")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    assert adapter.verify(plan).verified is True
    changed = json.loads(settings_path.read_text(encoding="utf-8"))
    assert changed["profiles"]["list"][0] == original["profiles"]["list"][0]
    assert changed["profiles"]["list"][1]["background"] == plan.palette["background"]
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert settings_path.read_text(encoding="utf-8") == json.dumps(original)
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_terminal_adapter.py -q`
Expected: FAIL because `one_tone.adapters.terminal` does not exist.

- [ ] **Step 3: Write minimal implementation**

Load JSON with `utf-8`, resolve `profiles.default` by GUID/name, and when it is `null` choose the first profile without `source`. Apply only `background`, `foreground`, `selectionBackground`, `selectionForeground`, and ANSI color keys derived from the Palette. Snapshot the original file to the transaction backup and replace via a temporary sibling file. `restart()` returns `partial` unless `allow_restart=True`; with explicit permission it closes/relaunches the `wt` command and returns the process result.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_terminal_adapter.py -q`
Expected: all default resolution, isolation and restore tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters/terminal.py src/one_tone/adapters/__init__.py tests/test_terminal_adapter.py
git commit -m "feat: add Windows Terminal profile adapter"
```

### Task 4: 实现 VS Code/Cursor/TRAE 共享主题和 VSIX Adapter

**Files:**
- Create: `src/one_tone/adapters/vscode_family.py`
- Create: `tests/test_vscode_family.py`
- Modify: `src/one_tone/adapters/__init__.py`

**Interfaces:**
- `EditorSpec(target, executable, settings_path, extensions_dir, ai_panel_supported=False)`.
- `build_theme_json(plan: Plan, theme_name: str) -> dict[str, Any]`.
- `build_vsix(plan: Plan, output_path: Path, spec: EditorSpec) -> Path`.
- `VSCodeFamilyAdapter(spec: EditorSpec, command_runner: Callable[..., CompletedProcess] | None = None)` implements all seven lifecycle methods.

- [ ] **Step 1: Write the failing tests**

```python
import json
import zipfile

from one_tone.adapters.vscode_family import EditorSpec, VSCodeFamilyAdapter, build_vsix
from one_tone.plan import create_plan


def test_vsix_contains_manifest_and_theme(tmp_path):
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-001")
    path = build_vsix(plan, tmp_path / "theme.vsix", EditorSpec("trae", "trae", tmp_path / "settings.json", tmp_path / "extensions"))
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "extension/package.json" in names
        assert "extension/themes/one-tone-color-theme.json" in names


def test_editor_adapter_snapshots_applies_verifies_and_restores(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, tmp_path / "extensions", ai_panel_supported=False)
    adapter = VSCodeFamilyAdapter(spec, command_runner=lambda *args, **kwargs: None)
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-002")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    result = adapter.verify(plan)
    assert result.verified is True
    assert result.status == "partial"
    assert adapter.rollback(tmp_path / "backup").verified is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_vscode_family.py -q`
Expected: FAIL because `one_tone.adapters.vscode_family` does not exist.

- [ ] **Step 3: Write minimal implementation**

Generate a VS Code theme with the twelve semantic colors mapped to workbench and token color fields. Create a VSIX using `zipfile` with `extension/package.json` and `extension/themes/one-tone-color-theme.json`. Snapshot settings JSON, install through the configured executable with `--install-extension <vsix> --force`, set `workbench.colorTheme`, and verify the setting plus extension artifact. Rollback restores settings and removes the generated extension directory. If `ai_panel_supported` is false, preserve `verified=True` for the common workbench but return `status="partial"` with an explicit message.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_vscode_family.py -q`
Expected: VSIX, settings isolation, partial AI-panel result and restore tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters/vscode_family.py src/one_tone/adapters/__init__.py tests/test_vscode_family.py
git commit -m "feat: add VS Code family theme adapter"
```

### Task 5: 实现独立 Codex Adapter

**Files:**
- Create: `src/one_tone/adapters/codex.py`
- Create: `tests/test_codex_adapter.py`
- Modify: `src/one_tone/adapters/__init__.py`

**Interfaces:**
- `locate_verified_codex_config(explicit_path: Path | None = None) -> Path | None` returns only an existing file that passes the known schema check.
- `CodexAdapter(config_path: Path | None = None)` implements all seven lifecycle methods.
- The fixture schema is JSON with top-level `theme` object containing `name` and `colors`; unknown files return `skipped`.

- [ ] **Step 1: Write the failing tests**

```python
import json

from one_tone.adapters.codex import CodexAdapter, locate_verified_codex_config
from one_tone.plan import create_plan


def test_codex_without_verified_config_is_skipped(tmp_path):
    adapter = CodexAdapter(tmp_path / "missing.json")
    assert adapter.detect().status == "skipped"
    assert adapter.apply(create_plan("#7C3AED", ["codex"], plan_id="plan-codex-001")).status == "skipped"


def test_codex_fixture_completes_config_lifecycle(tmp_path):
    path = tmp_path / "codex-theme.json"
    path.write_text(json.dumps({"theme": {"name": "Original", "colors": {"background": "#000000"}}}), encoding="utf-8")
    adapter = CodexAdapter(path)
    plan = create_plan("#7C3AED", ["codex"], plan_id="plan-codex-002")

    assert locate_verified_codex_config(path) == path
    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_codex_adapter.py -q`
Expected: FAIL because `one_tone.adapters.codex` does not exist.

- [ ] **Step 3: Write minimal implementation**

Validate the exact JSON schema before returning `ok`; do not treat arbitrary Codex files, `.codex` directories or VS Code settings as Codex theme configuration. Snapshot the full JSON, write the Plan palette under `theme.colors` and Plan ID under `theme.name`, verify both, and restore only the transaction backup. `restart()` returns `skipped` unless a verified Codex process command is explicitly provided.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_codex_adapter.py -q`
Expected: skipped-path and explicit-fixture lifecycle tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters/codex.py src/one_tone/adapters/__init__.py tests/test_codex_adapter.py
git commit -m "feat: add independent Codex adapter"
```

### Task 6: 实现 Chrome 主题 ZIP 和用户操作结果

**Files:**
- Create: `src/one_tone/adapters/chrome.py`
- Create: `tests/test_chrome_adapter.py`
- Modify: `src/one_tone/adapters/__init__.py`

**Interfaces:**
- `build_chrome_theme(plan: Plan, output_path: Path) -> Path` writes `manifest.json` and theme resources into a ZIP.
- `ChromeAdapter(output_dir: Path, preferences_path: Path | None = None)` implements all seven lifecycle methods.

- [ ] **Step 1: Write the failing tests**

```python
import json
import zipfile

from one_tone.adapters.chrome import ChromeAdapter, build_chrome_theme
from one_tone.plan import create_plan


def test_chrome_theme_zip_has_manifest_and_palette_colors(tmp_path):
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-001")
    path = build_chrome_theme(plan, tmp_path / "chrome-theme.zip")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["version"] == 2
    assert manifest["theme"]["colors"]["frame"] == plan.palette["surface"]


def test_chrome_apply_requires_explicit_user_action(tmp_path):
    adapter = ChromeAdapter(tmp_path / "output")
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-002")

    assert adapter.detect().status == "ok"
    result = adapter.apply(plan)
    assert result.status == "partial"
    assert result.requires_user_action is True
    assert adapter.verify(plan).verified is True
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_chrome_adapter.py -q`
Expected: FAIL because `one_tone.adapters.chrome` does not exist.

- [ ] **Step 3: Write minimal implementation**

Use `zipfile` to write a Chrome manifest version 2 with frame, toolbar, tab and omnibox colors from the Palette. Snapshot an existing Preferences file only when a path is explicitly provided. Apply writes the ZIP under the current transaction asset directory and returns `partial`, `requires_user_action=True`, with the exact manual loading instruction. Verify checks the ZIP manifest and Plan ID; rollback removes only this transaction’s generated ZIP.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_chrome_adapter.py -q`
Expected: ZIP and user-action result tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/adapters/chrome.py src/one_tone/adapters/__init__.py tests/test_chrome_adapter.py
git commit -m "feat: add Chrome theme package adapter"
```

### Task 7: 接入八步事务、支持级别和真实目标 CLI

**Files:**
- Modify: `src/one_tone/transaction.py`
- Modify: `src/one_tone/cli.py`
- Modify: `tests/test_transaction.py`
- Modify: `tests/test_cli.py`

**Interfaces:**
- `run_full_cycle(plan: Plan, adapters: Mapping[str, ThemeAdapter], store: TransactionStore, confirm: bool, restart_apps: bool) -> TransactionRecord`.
- `build_target_adapters(targets: Iterable[str], state_dir: Path, restart_apps: bool) -> dict[str, ThemeAdapter]`.
- CLI adds `verify PLAN_ID --confirm [--restart-apps]`.

- [ ] **Step 1: Write the failing tests**

```python
from one_tone.adapters import AdapterResult, FileAdapter
from one_tone.plan import create_plan
from one_tone.transaction import TransactionStatus, TransactionStore, run_full_cycle


def test_full_cycle_records_eight_operations_and_full_level(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-cycle-001")
    store = TransactionStore(tmp_path / "transactions")
    class VersionedFileAdapter(FileAdapter):
        def detect(self):
            return AdapterResult(self.target, "ok", False, True, "fixture config detected", version="fixture-1")

    record = run_full_cycle(plan, {"file-demo": VersionedFileAdapter("file-demo", config)}, store, True, False)

    operations = [item["operation"] for item in record.results["file-demo"]]
    assert operations == ["detect", "snapshot", "apply", "verify", "restart", "verify_again", "rollback", "verify_restore"]
    assert record.support_levels["file-demo"] == "FULL"
    assert record.status == TransactionStatus.ROLLED_BACK


def test_verify_cli_requires_explicit_restart_flag_only_for_process_restart(tmp_path, capsys):
    assert main(["verify", "plan-cycle-002", "--confirm"]) != 0
    assert "Plan not found" in capsys.readouterr().err
```

- [ ] **Step 2: Run tests to verify they fail**

Run: `uv run pytest tests/test_transaction.py::test_full_cycle_records_eight_operations_and_full_level tests/test_cli.py::test_verify_cli_requires_explicit_restart_flag_only_for_process_restart -q`
Expected: FAIL because `run_full_cycle`, support-level persistence and the `verify` command do not exist.

- [ ] **Step 3: Write minimal implementation**

Implement the exact eight operation sequence. `run_full_cycle` applies, optionally restarts, verifies again, rolls back, verifies the restored state, and computes support level. `restart_apps=False` lets adapters return a verified “not required” result for file/system targets and a partial result for process targets; `--restart-apps` passes explicit permission to real process adapters. Register targets using actual Scoop paths: Windows, terminal, vscode, cursor, trae, codex, chrome; unknown targets remain `UnsupportedAdapter`.

Preserve normal `apply` behavior and return `APPLIED`/`PARTIAL` without automatic validation rollback. `verify` is the command that runs and records the full validation cycle. Print each target’s support level and message.

- [ ] **Step 4: Run tests to verify they pass**

Run: `uv run pytest tests/test_transaction.py tests/test_cli.py -q`
Expected: existing transaction/CLI tests plus full-cycle tests pass.

- [ ] **Step 5: Commit**

```powershell
git add src/one_tone/transaction.py src/one_tone/cli.py tests/test_transaction.py tests/test_cli.py
git commit -m "feat: add eight-step verification workflow"
```

### Task 8: 同步文档、运行全量验证并记录真实环境限制

**Files:**
- Modify: `README.md`
- Modify: `OCD_Windows_Theme_Skill_计划书.md`
- Modify: `tests/test_project_smoke.py`

**Interfaces:**
- Documentation states Windows 10/11 support range, wallpaper behavior, actual Scoop paths, `verify` usage, `--restart-apps` impact, Chrome user action, Codex skipped rule, and FULL/PARTIAL/SKIPPED definitions.

- [ ] **Step 1: Write the failing documentation test**

```python
def test_readme_documents_full_adapter_boundaries():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "Windows 10 22H2+" in text
    assert "verify" in text
    assert "--restart-apps" in text
    assert "壁纸" in text
    assert "requires_user_action" in text
```

- [ ] **Step 2: Run test to verify it fails**

Run: `uv run pytest tests/test_project_smoke.py::test_readme_documents_full_adapter_boundaries -q`
Expected: FAIL because the current README only documents stage 1–2.

- [ ] **Step 3: Write documentation and final checks**

Update README and the plan book with exact commands:

```powershell
uv run one-tone preview "#7C3AED" --targets windows,terminal,vscode,cursor,trae,codex,chrome
uv run one-tone apply plan-... --confirm
uv run one-tone verify plan-... --confirm --restart-apps
uv run one-tone rollback tx-...
uv run pytest
```

Document that a fixture test is not a `FULL` result, that current environment results must be reported per target, and that real Apply/Restart/Chrome loading requires explicit user confirmation.

- [ ] **Step 4: Run complete verification**

Run:

```powershell
uv run pytest
uv run one-tone --help
git diff --check
git status --short
```

Expected: all tests pass with exit code `0`, help lists `preview`, `apply`, `verify`, `rollback`, `git diff --check` is clean, and only scoped files plus pre-existing untracked user files remain.

- [ ] **Step 5: Commit**

```powershell
git add README.md OCD_Windows_Theme_Skill_计划书.md tests/test_project_smoke.py
git commit -m "docs: document full adapter workflow"
```

## Plan Self-Review

- The confirmed Windows 10/11 scope, ordinary dark mode, Wallpaper, Terminal current Profile, VS Code/Cursor/TRAE shared generator, independent Codex, Chrome user action and FULL criteria each have a task.
- Every new real Adapter has fixture tests before implementation and preserves the existing `AdapterResult` minimum fields.
- The design records `restart`, `verify_again`, `rollback` and `verify_restore` separately, so a passing Apply cannot be confused with a completed FULL validation.
- Real process termination is opt-in through `--restart-apps`; fixture tests do not change the current desktop or installed applications.
- Codex does not infer a configuration format from arbitrary files; unverified environments remain `SKIPPED`.
- No unresolved placeholder or undefined file/interface reference remains.
