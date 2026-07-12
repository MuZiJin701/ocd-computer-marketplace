import json

from one_tone.adapters.terminal import TerminalAdapter, resolve_default_profile
from one_tone.plan import create_plan


def test_null_default_uses_first_local_profile():
    settings = {"profiles": {"default": None, "list": [
        {"name": "Windows PowerShell", "guid": "{one}"},
        {"name": "Azure", "guid": "{two}", "source": "Windows.Terminal.Azure"},
    ]}}
    assert resolve_default_profile(settings) == (0, "profiles.default is null; first local profile selected")


def test_root_default_profile_is_used_when_profiles_default_is_missing():
    settings = {"defaultProfile": "{two}", "profiles": {"list": [
        {"name": "Windows PowerShell", "guid": "{one}"},
        {"name": "PowerShell", "guid": "{two}"},
    ]}}
    assert resolve_default_profile(settings) == (1, "defaultProfile resolved by GUID/name")


def test_terminal_apply_registers_and_selects_a_valid_scheme(tmp_path):
    settings_path = tmp_path / "settings.json"
    settings = {
        "defaultProfile": "{two}",
        "profiles": {
            "defaults": {"colorScheme": "Missing Scheme"},
            "list": [
                {"name": "Windows PowerShell", "guid": "{one}"},
                {"name": "PowerShell", "guid": "{two}"},
            ],
        },
        "schemes": [],
    }
    settings_path.write_text(json.dumps(settings), encoding="utf-8")
    adapter = TerminalAdapter(settings_path)
    plan = create_plan("#00A86B", ["terminal"], plan_id="plan-terminal-scheme-001")

    assert adapter.apply(plan).status == "ok"
    changed = json.loads(settings_path.read_text(encoding="utf-8"))
    scheme = next(item for item in changed["schemes"] if item["name"] == "One Tone")
    theme = next(item for item in changed["themes"] if item["name"] == "One Tone")
    assert changed["profiles"]["defaults"]["colorScheme"] == "One Tone"
    assert changed["profiles"]["list"][1]["colorScheme"] == "One Tone"
    assert changed["theme"] == "One Tone"
    assert changed["profiles"]["list"][1]["tabColor"] == plan.palette["accent"]
    assert scheme["background"] == plan.palette["surface"]
    assert scheme["cyan"] == plan.palette["accent_text"]
    assert scheme["green"] == plan.palette["success_text"]
    assert theme["tabRow"]["background"] == plan.palette["surface"]
    assert theme["window"]["frame"] == plan.palette["accent"]
    assert adapter.verify(plan).verified is True


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
    assert changed["profiles"]["list"][1]["background"] == plan.palette["surface"]
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert settings_path.read_text(encoding="utf-8") == original_text
