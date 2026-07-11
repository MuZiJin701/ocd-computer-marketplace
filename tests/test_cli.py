import json

from one_tone.cli import main


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
