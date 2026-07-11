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
    original_text = json.dumps(original)
    settings_path.write_text(original_text, encoding="utf-8")
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
    assert settings_path.read_text(encoding="utf-8") == original_text
