from one_tone.adapters import AdapterResult, FileAdapter, UnsupportedAdapter
from one_tone.plan import create_plan


def test_adapter_result_has_required_structured_fields():
    result = AdapterResult("chrome", "skipped", False, False, "not verified")
    assert result.target == "chrome"
    assert result.status == "skipped"


def test_adapter_result_stores_user_action_and_version():
    result = AdapterResult("chrome", "partial", False, False, "load theme", True, "Chrome 138")
    assert result.requires_user_action is True
    assert result.version == "Chrome 138"


def test_file_adapter_snapshots_applies_verifies_and_rolls_back(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    adapter = FileAdapter("file-demo", config)
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-test-003")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).changed is True
    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert config.read_text(encoding="utf-8") == '{"theme": "original"}'


def test_unsupported_adapter_never_claims_success():
    result = UnsupportedAdapter("codex").detect()
    assert result.status == "skipped"
    assert result.changed is False


def test_cursor_is_explicitly_skipped_without_touching_files(tmp_path):
    from one_tone.cli import build_target_adapters

    adapter = build_target_adapters(("cursor",), tmp_path / "state")["cursor"]

    result = adapter.detect()

    assert isinstance(adapter, UnsupportedAdapter)
    assert result.status == "skipped"
    assert not (tmp_path / "state").exists()
