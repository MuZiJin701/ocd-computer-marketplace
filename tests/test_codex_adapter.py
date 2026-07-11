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
