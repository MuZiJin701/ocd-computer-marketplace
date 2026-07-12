import json

import pytest

from one_tone.plan import PlanIntegrityError, compute_plan_hash, create_plan, load_plan, save_plan


def test_plan_round_trips_with_stable_hash(tmp_path):
    plan = create_plan("#7C3AED", ["chrome", "windows"], plan_id="plan-test-001")
    path = save_plan(plan, tmp_path)
    loaded = load_plan("plan-test-001", tmp_path)

    assert loaded == plan
    assert len(plan.hash) == 64
    assert path.name == "plan-test-001.json"


def test_plan_hash_rejects_tampering(tmp_path):
    save_plan(create_plan("#7C3AED", ["windows"], plan_id="plan-test-002"), tmp_path)
    path = tmp_path / "plan-test-002.json"
    payload = json.loads(path.read_text(encoding="utf-8"))
    payload["targets"] = ["chrome"]
    path.write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PlanIntegrityError, match="Hash"):
        load_plan("plan-test-002", tmp_path)


def test_plan_rejects_path_like_targets_and_plan_ids(tmp_path):
    with pytest.raises(ValueError, match="safe"):
        create_plan("#7C3AED", ["../../escaped"], plan_id="plan-safe-001")

    with pytest.raises(ValueError, match="safe"):
        create_plan("#7C3AED", ["windows"], plan_id="../escaped")

    with pytest.raises(ValueError, match="safe"):
        load_plan("../escaped", tmp_path)


def test_plan_rejects_filename_and_payload_id_mismatch(tmp_path):
    plan = create_plan("#7C3AED", ["windows"], plan_id="plan-file-id-001")
    payload = plan.to_dict()
    payload["id"] = "plan-payload-id-002"
    payload["hash"] = compute_plan_hash(payload)
    (tmp_path / "plan-file-id-001.json").write_text(json.dumps(payload), encoding="utf-8")

    with pytest.raises(PlanIntegrityError, match="ID mismatch"):
        load_plan("plan-file-id-001", tmp_path)
