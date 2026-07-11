from one_tone.adapters import AdapterResult, FileAdapter, UnsupportedAdapter
from one_tone.plan import create_plan
from one_tone.transaction import TransactionStatus, TransactionStore, apply_plan


def test_apply_creates_isolated_transaction_and_rollback_restores_only_it(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-test-004")
    store = TransactionStore(tmp_path / "transactions")
    adapter = FileAdapter("file-demo", config)

    record = apply_plan(plan, {"file-demo": adapter}, store, confirm=True)
    assert record.status == TransactionStatus.APPLIED
    assert (store.path_for(record.id) / "backup" / "file-demo.json").exists()
    assert "plan-test-004" in config.read_text(encoding="utf-8")

    restored = store.rollback(record.id, {"file-demo": adapter})
    assert restored.status == TransactionStatus.ROLLED_BACK
    assert config.read_text(encoding="utf-8") == '{"theme": "original"}'


def test_apply_failure_automatically_rolls_back_successful_targets(tmp_path):
    first = tmp_path / "first.json"
    second = tmp_path / "second.json"
    first.write_text('{"theme": "first"}', encoding="utf-8")
    second.write_text('{"theme": "second"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["first", "second"], plan_id="plan-test-005")
    store = TransactionStore(tmp_path / "transactions")

    class FailingVerifyAdapter(FileAdapter):
        def verify(self, plan):
            return AdapterResult(self.target, "failed", True, False, "forced verify failure")

    adapters = {
        "first": FileAdapter("first", first),
        "second": FailingVerifyAdapter("second", second),
    }
    record = apply_plan(plan, adapters, store, confirm=True)

    assert record.status == TransactionStatus.FAILED
    assert first.read_text(encoding="utf-8") == '{"theme": "first"}'
    assert second.read_text(encoding="utf-8") == '{"theme": "second"}'


def test_apply_marks_mixed_success_and_skipped_targets_partial(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["file-demo", "codex"], plan_id="plan-test-006")
    store = TransactionStore(tmp_path / "transactions")
    adapters = {
        "file-demo": FileAdapter("file-demo", config),
        "codex": UnsupportedAdapter("codex"),
    }

    record = apply_plan(plan, adapters, store, confirm=True)

    assert record.status == TransactionStatus.PARTIAL
    assert "plan-test-006" in config.read_text(encoding="utf-8")
