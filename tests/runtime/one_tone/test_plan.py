import json

import pytest

from one_tone.plan import PlanIntegrityError, create_plan, load_plan, save_plan


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
