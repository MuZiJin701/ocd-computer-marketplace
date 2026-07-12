import json
from pathlib import Path

from one_tone.cli import build_target_adapters, main


def test_preview_json_output_contains_plan_id_and_targets(tmp_path, capsys, monkeypatch):
    monkeypatch.setenv("ONE_TONE_CODEX_THEME_CONFIG", str(tmp_path / "missing-config.toml"))
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


def test_preview_writes_plan_without_creating_transaction(tmp_path, capsys):
    plans = tmp_path / "plans"
    transactions = tmp_path / "transactions"

    assert main([
        "preview", "#7C3AED", "--targets", "codex,chrome",
        "--plans-dir", str(plans), "--transactions-dir", str(transactions),
    ]) == 0
    assert list(plans.glob("*.json"))
    assert not transactions.exists()
    assert "Plan ID:" in capsys.readouterr().out


def test_apply_requires_plan_id_and_confirmation(capsys):
    assert main(["apply"]) == 2
    assert "plan_id" in capsys.readouterr().err

    assert main(["apply", "plan-test-007"]) == 2
    assert "--confirm" in capsys.readouterr().err


def test_apply_consumes_saved_plan_for_file_adapter(tmp_path, capsys):
    plans = tmp_path / "plans"
    transactions = tmp_path / "transactions"
    state = tmp_path / "state"
    state.mkdir()
    (state / "file-demo.json").write_text('{"theme": "original"}', encoding="utf-8")

    assert main([
        "preview", "#7C3AED", "--targets", "file-demo",
        "--plans-dir", str(plans),
    ]) == 0
    plan_id = json.loads(next(plans.glob("*.json")).read_text(encoding="utf-8"))["id"]

    assert main([
        "apply", plan_id, "--confirm",
        "--plans-dir", str(plans),
        "--transactions-dir", str(transactions),
        "--state-dir", str(state),
    ]) == 0
    assert "APPLIED" in capsys.readouterr().out


def test_verify_cli_reports_missing_plan(capsys):
    assert main(["verify", "plan-cycle-002"]) != 0
    assert "Plan not found" in capsys.readouterr().err


def test_verify_cli_rejects_confirmation_flag(capsys):
    assert main(["verify", "plan-cycle-002", "--confirm"]) == 2
    assert "unrecognized arguments" in capsys.readouterr().err


def test_vscode_family_adapter_resolves_path_cli_fallback(monkeypatch, tmp_path):
    from one_tone.adapters.vscode_family import EditorSpec, VSCodeFamilyAdapter

    settings_path = tmp_path / 'settings.json'
    settings_path.write_text('{}', encoding='utf-8')
    extensions_dir = tmp_path / 'extensions'
    spec = EditorSpec('vscode', Path('code'), settings_path, extensions_dir)

    monkeypatch.setattr(
        'one_tone.adapters.vscode_family.shutil.which',
        lambda command: r'C:\bin\code.cmd' if command == 'code' else None,
    )

    assert VSCodeFamilyAdapter(spec).detect().status == 'ok'


def test_cursor_adapter_uses_user_extension_directory_for_cli_installs(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    monkeypatch.setenv("ONE_TONE_CURSOR_EXECUTABLE", "cursor")

    adapter = build_target_adapters(("cursor",), tmp_path / "state")["cursor"]

    assert adapter.spec.extensions_dir == Path(tmp_path) / ".cursor" / "extensions"


def test_vscode_adapter_accepts_environment_path_overrides(tmp_path, monkeypatch):
    executable = tmp_path / "bin" / "code.cmd"
    settings = tmp_path / "portable" / "settings.json"
    extensions = tmp_path / "portable" / "extensions"
    monkeypatch.setenv("ONE_TONE_VSCODE_EXECUTABLE", str(executable))
    monkeypatch.setenv("ONE_TONE_VSCODE_SETTINGS", str(settings))
    monkeypatch.setenv("ONE_TONE_VSCODE_EXTENSIONS", str(extensions))

    adapter = build_target_adapters(("vscode",), tmp_path / "state")["vscode"]

    assert adapter.spec.executable == executable
    assert adapter.spec.settings_path == settings
    assert adapter.spec.extensions_dir == extensions


def test_cursor_adapter_derives_data_paths_from_launcher_arguments(tmp_path, monkeypatch):
    launcher = tmp_path / "cursor.cmd"
    data_root = tmp_path / "cursor-data"
    launcher.write_text(
        f'@"cursor.exe" --user-data-dir="{data_root / "user-data"}" --extensions-dir="{data_root / "extensions"}" %*',
        encoding="utf-8",
    )
    monkeypatch.delenv("ONE_TONE_CURSOR_SETTINGS", raising=False)
    monkeypatch.delenv("ONE_TONE_CURSOR_EXTENSIONS", raising=False)
    monkeypatch.setattr("one_tone.cli.shutil.which", lambda command: str(launcher) if command == "cursor" else None)

    adapter = build_target_adapters(("cursor",), tmp_path / "state")["cursor"]

    assert adapter.spec.settings_path == data_root / "user-data" / "User" / "settings.json"
    assert adapter.spec.extensions_dir == data_root / "extensions"


def test_cli_defaults_runtime_data_to_single_project_directory():
    from one_tone.cli import _build_parser

    args = _build_parser().parse_args(["preview", "#FFD700", "--targets", "windows"])

    assert args.plans_dir == Path(".one-tone") / "plans"
    assert args.transactions_dir == Path(".one-tone") / "transactions"
    assert args.state_dir == Path(".one-tone") / "state"


def test_apply_parser_defaults_transaction_retention_to_five():
    from one_tone.cli import _build_parser

    args = _build_parser().parse_args(["apply", "plan-001", "--confirm"])

    assert args.keep_transactions == 5


def test_preview_defaults_to_all_supported_targets():
    from one_tone.cli import DEFAULT_TARGETS, _build_parser

    args = _build_parser().parse_args(["preview", "#10B981"])

    assert args.targets == ",".join(DEFAULT_TARGETS)


def test_terminal_adapter_derives_scoop_persist_settings_from_shim(tmp_path, monkeypatch):
    scoop_root = tmp_path / "scoop"
    executable = scoop_root / "shims" / "wt.exe"
    settings = scoop_root / "persist" / "windows-terminal" / "settings" / "settings.json"
    executable.parent.mkdir(parents=True)
    executable.write_bytes(b"shim")
    settings.parent.mkdir(parents=True)
    settings.write_text("{}", encoding="utf-8")
    monkeypatch.setenv("ONE_TONE_TERMINAL_EXECUTABLE", str(executable))

    adapter = build_target_adapters(("terminal",), tmp_path / "state")["terminal"]

    assert adapter.settings_path == settings
