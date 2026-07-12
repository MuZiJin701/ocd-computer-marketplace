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


def test_cursor_adapter_uses_user_extension_directory_for_cli_installs(tmp_path, monkeypatch):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))

    adapter = build_target_adapters(("cursor",), tmp_path / "state")["cursor"]

    assert adapter.spec.extensions_dir == Path(tmp_path) / ".cursor" / "extensions"


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
