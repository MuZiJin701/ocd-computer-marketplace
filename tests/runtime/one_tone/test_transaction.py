from one_tone.adapters import AdapterResult, FileAdapter, UnsupportedAdapter
from one_tone.plan import create_plan
from one_tone.transaction import TransactionRecord, TransactionStatus, TransactionStore, apply_plan
import one_tone.transaction as transaction_module


def test_apply_creates_isolated_transaction_and_rollback_restores_only_it(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-test-004")
    store = TransactionStore(tmp_path / "transactions")
    adapter = FileAdapter("file-demo", config)

    record = apply_plan(plan, {"file-demo": adapter}, store, confirm=True)
    assert record.status == TransactionStatus.APPLIED
    assert (store.path_for(record.id) / "file-demo" / "snapshot" / "file-demo.json").exists()
    assert "plan-test-004" in config.read_text(encoding="utf-8")

    restored = store.rollback(record.id, {"file-demo": adapter})
    assert restored.status == TransactionStatus.ROLLED_BACK
    assert config.read_text(encoding="utf-8") == '{"theme": "original"}'


def test_apply_failure_rolls_back_only_failed_target(tmp_path):
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

    assert record.status == TransactionStatus.PARTIAL
    assert "plan-test-005" in first.read_text(encoding="utf-8")
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


def test_verify_plan_reads_current_state_without_transaction(tmp_path):
    config = tmp_path / "theme.json"
    config.write_text('{"theme": "original"}', encoding="utf-8")
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-verify-001")
    adapter = FileAdapter("file-demo", config)
    adapter.apply(plan)

    verify_plan = getattr(transaction_module, "verify_plan", None)
    assert callable(verify_plan)
    result = verify_plan(plan, {"file-demo": adapter})

    assert result["file-demo"].status == "ok"
    assert not list((tmp_path / "transactions").glob("**/transaction.json"))


def test_transaction_store_prunes_old_completed_transactions(tmp_path):
    store = TransactionStore(tmp_path / "transactions")
    plan = create_plan("#7C3AED", ["file-demo"], plan_id="plan-retention-001")
    completed_ids = []

    for index in range(7):
        record = store.create(plan)
        record.status = TransactionStatus.ROLLED_BACK
        record.created_at = f"2026-07-12T00:00:{index:02d}+00:00"
        store.save(record)
        completed_ids.append(record.id)

    pending = store.create(plan)
    prune = getattr(store, "prune", None)
    assert callable(prune)
    removed = prune(keep=5, preserve={completed_ids[-1], pending.id})

    assert len(removed) == 1
    assert not store.path_for(completed_ids[0]).exists()
    assert store.path_for(completed_ids[-1]).exists()
    assert store.path_for(pending.id).exists()


def test_transaction_store_rejects_zero_retention(tmp_path):
    store = TransactionStore(tmp_path / "transactions")
    prune = getattr(store, "prune", None)
    assert callable(prune)

    try:
        prune(keep=0)
    except ValueError:
        pass
    else:
        raise AssertionError("prune(keep=0) must raise ValueError")
