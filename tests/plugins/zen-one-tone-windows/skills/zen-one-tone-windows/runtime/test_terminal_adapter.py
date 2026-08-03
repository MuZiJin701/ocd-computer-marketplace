import json
import subprocess

from one_tone.adapters.terminal import TerminalAdapter, resolve_default_profile
from one_tone.palette import parse_hex_color
from one_tone.plan import create_plan


def _psreadline_probe_runner(command, **kwargs):
    return subprocess.CompletedProcess(
        command,
        0,
        stdout=json.dumps({
            "profile": str(kwargs["profile_path"]),
            "version": "2.4.5",
            "fields": ["InlinePrediction", "ListPrediction", "ListPredictionSelected"],
        }),
        stderr="",
    )


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
    expected_mapping = {"light": "One Tone Light", "dark": "One Tone Dark"}
    assert changed["profiles"]["defaults"]["colorScheme"] == expected_mapping
    assert all(profile["colorScheme"] == expected_mapping for profile in changed["profiles"]["list"])
    assert changed["theme"] == "One Tone"
    palette = plan.palette_for(plan.mode)
    assert all(profile["tabColor"] == palette["accent"] for profile in changed["profiles"]["list"])
    assert scheme["background"] == palette["surface"]
    assert scheme["cursorColor"] == palette["accent_text"]
    assert scheme["black"] == palette["foreground"]
    assert scheme["brightBlack"] == palette["foreground"]
    assert scheme["cyan"] == palette["accent_text"]
    assert scheme["green"] == palette["success_text"]
    assert theme["tabRow"]["background"] == palette["surface_subtle"]
    assert theme["window"]["frame"] == palette["accent"]
    assert theme["window"]["applicationTheme"] == "system"
    assert adapter.verify(plan).verified is True


def test_terminal_adapter_applies_theme_to_all_profiles_and_restores(tmp_path):
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
    assert all(profile["colorScheme"] == {"light": "One Tone Light", "dark": "One Tone Dark"} for profile in changed["profiles"]["list"])
    assert all(profile["tabColor"] == plan.palette_for(plan.mode)["accent"] for profile in changed["profiles"]["list"])
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert settings_path.read_text(encoding="utf-8") == original_text


def test_terminal_adapter_discovers_and_rolls_back_psreadline_profile(tmp_path):
    settings_path = tmp_path / "settings.json"
    profile_path = tmp_path / "profile.ps1"
    settings_path.write_text(json.dumps({
        "profiles": {"default": "{one}", "list": [{"name": "PowerShell", "guid": "{one}"}]},
    }), encoding="utf-8")
    original_profile = "Set-Alias ll Get-ChildItem\n"
    profile_path.write_text(original_profile, encoding="utf-8")

    def runner(command, **kwargs):
        return _psreadline_probe_runner(command, profile_path=profile_path)

    adapter = TerminalAdapter(settings_path, powershell_executable=tmp_path / "pwsh", command_runner=runner)
    plan = create_plan("#10B981", ["terminal"], plan_id="plan-terminal-psreadline-001")

    assert adapter.detect().status == "ok"
    instance = adapter.target_instance()
    assert instance["profile_path"] == str(profile_path)
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    changed_profile = profile_path.read_text(encoding="utf-8")
    assert "Set-Alias ll Get-ChildItem" in changed_profile
    assert "if ($env:WT_SESSION)" in changed_profile
    assert "InlinePrediction = $oneToneInlinePrediction" in changed_profile
    assert "ListPredictionSelected = $oneToneListPredictionSelected" in changed_profile
    red, green, blue = parse_hex_color(plan.palette_for("light")["prediction_foreground"])
    assert f"[38;2;{red};{green};{blue}m" in changed_profile
    assert adapter.apply(plan).status == "ok"
    assert profile_path.read_text(encoding="utf-8") == changed_profile
    assert adapter.verify(plan).verified is True
    with profile_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("Set-Location C:\\Users\n")
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert profile_path.read_text(encoding="utf-8") == original_profile + "\nSet-Location C:\\Users\n"


def test_terminal_adapter_upgrades_existing_prediction_block_in_place(tmp_path):
    settings_path = tmp_path / "settings.json"
    profile_path = tmp_path / "profile.ps1"
    settings_path.write_text(json.dumps({
        "profiles": {"default": "{one}", "list": [{"name": "PowerShell", "guid": "{one}"}]},
    }), encoding="utf-8")
    profile_path.write_text(
        "before\n"
        "# >>> one-tone windows-terminal prediction colors >>>\n"
        "old prediction settings\n"
        "# <<< one-tone windows-terminal prediction colors <<<\n"
        "after\n",
        encoding="utf-8",
    )

    def runner(command, **kwargs):
        return _psreadline_probe_runner(command, profile_path=profile_path)

    adapter = TerminalAdapter(settings_path, powershell_executable=tmp_path / "pwsh", command_runner=runner)
    plan = create_plan("#10B981", ["terminal"], mode="light")

    assert adapter.apply(plan).status == "ok"
    changed_profile = profile_path.read_text(encoding="utf-8")
    assert changed_profile.count("# >>> one-tone windows-terminal prediction colors >>>") == 1
    assert "old prediction settings" not in changed_profile
    assert changed_profile.startswith("before\n")
    assert changed_profile.endswith("after\n")


def test_terminal_adapter_reports_missing_prediction_role_without_writing_profile(tmp_path):
    settings_path = tmp_path / "settings.json"
    profile_path = tmp_path / "profile.ps1"
    settings_path.write_text(json.dumps({
        "profiles": {"default": "{one}", "list": [{"name": "PowerShell", "guid": "{one}"}]},
    }), encoding="utf-8")
    profile_path.write_text("Set-Alias ll Get-ChildItem\n", encoding="utf-8")

    def runner(command, **kwargs):
        return _psreadline_probe_runner(command, profile_path=profile_path)

    adapter = TerminalAdapter(settings_path, powershell_executable=tmp_path / "pwsh", command_runner=runner)
    plan = create_plan("#10B981", ["terminal"], mode="light")
    plan.palettes["light"].pop("prediction_foreground")

    result = adapter.apply(plan)

    assert result.status == "partial"
    assert "prediction colors unavailable" in result.message
    assert "one-tone windows-terminal prediction colors" not in profile_path.read_text(encoding="utf-8")


def test_terminal_rollback_removes_only_managed_profile_block(tmp_path):
    settings_path = tmp_path / "settings.json"
    profile_path = tmp_path / "new-profile.ps1"
    settings_path.write_text(json.dumps({
        "profiles": {"default": "{one}", "list": [{"name": "PowerShell", "guid": "{one}"}]},
    }), encoding="utf-8")

    def runner(command, **kwargs):
        return _psreadline_probe_runner(command, profile_path=profile_path)

    adapter = TerminalAdapter(settings_path, powershell_executable=tmp_path / "pwsh", command_runner=runner)
    plan = create_plan("#10B981", ["terminal"], plan_id="plan-terminal-profile-preserve-001")
    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    with profile_path.open("a", encoding="utf-8", newline="") as handle:
        handle.write("Set-Alias ll Get-ChildItem\n")

    assert adapter.rollback(tmp_path / "backup").verified is True
    assert profile_path.read_text(encoding="utf-8") == "\nSet-Alias ll Get-ChildItem\n"


def test_terminal_adapter_reports_unsupported_prediction_fields_without_guessing(tmp_path):
    settings_path = tmp_path / "settings.json"
    profile_path = tmp_path / "profile.ps1"
    settings_path.write_text(json.dumps({
        "profiles": {"default": "{one}", "list": [{"name": "PowerShell", "guid": "{one}"}]},
    }), encoding="utf-8")
    profile_path.write_text("Write-Host ready\n", encoding="utf-8")

    def runner(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            0,
            stdout=json.dumps({"profile": str(profile_path), "version": "2.0.0", "fields": ["InlinePrediction"]}),
            stderr="",
        )

    adapter = TerminalAdapter(settings_path, powershell_executable=tmp_path / "pwsh", command_runner=runner)
    plan = create_plan("#10B981", ["terminal"], plan_id="plan-terminal-psreadline-unsupported-001")
    assert adapter.detect().status == "partial"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    result = adapter.apply(plan)
    assert result.status == "partial"
    assert profile_path.read_text(encoding="utf-8") == "Write-Host ready\n"
