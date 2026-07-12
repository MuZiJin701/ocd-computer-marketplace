import json
import subprocess
import zipfile

from one_tone.adapters.vscode_family import EditorSpec, VSCodeFamilyAdapter, build_theme_json, build_vsix
from one_tone.plan import create_plan


def test_vsix_contains_manifest_and_theme(tmp_path):
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-001")
    path = build_vsix(plan, tmp_path / "theme.vsix", EditorSpec("trae", "trae", tmp_path / "settings.json", tmp_path / "extensions"))
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "extension/package.json" in names
        assert "extension/themes/one-tone-color-theme.json" in names


def test_editor_theme_uses_surface_for_primary_backgrounds():
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-surface-001")

    theme = build_theme_json(plan, "One Tone trae")
    colors = theme["colors"]

    assert colors["editor.background"] == plan.palette["surface"]
    assert colors["terminal.background"] == plan.palette["surface"]
    assert colors["sideBar.background"] == plan.palette["surface"]
    assert colors["activityBar.background"] == plan.palette["surface"]
    assert colors["statusBar.background"] == plan.palette["surface"]
    assert colors["titleBar.activeBackground"] == plan.palette["surface"]
    assert colors["sideBarSectionHeader.background"] == plan.palette["background"]
    assert colors["activityBarTop.activeBorder"] == plan.palette["accent"]
    assert colors["tab.activeBackground"] == plan.palette["surface"]
    assert colors["panel.background"] == plan.palette["background"]


def test_editor_adapter_snapshots_applies_verifies_and_restores(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, tmp_path / "extensions", ai_panel_supported=False)
    def command_runner(command, **kwargs):
        actual = spec.extensions_dir / "one-tone.one-tone-trae-0.1.0"
        (actual / "themes").mkdir(parents=True)
        (actual / "themes" / "one-tone-color-theme.json").write_text("{}", encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-002")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    result = adapter.verify(plan)
    assert result.verified is True
    assert result.status == "partial"
    changed = json.loads(settings.read_text(encoding="utf-8"))
    assert changed["workbench.preferredDarkColorTheme"] == "One Tone trae"
    assert changed["workbench.preferredLightColorTheme"] == "One Tone trae"
    assert adapter.rollback(tmp_path / "backup").verified is True


def test_editor_verify_does_not_accept_uninstalled_flat_theme(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("cursor", "cursor", settings, tmp_path / "extensions", ai_panel_supported=False)
    adapter = VSCodeFamilyAdapter(spec, command_runner=lambda *args, **kwargs: None)
    plan = create_plan("#7C3AED", ["cursor"], plan_id="plan-editor-uninstalled-001")

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "failed"


def test_editor_apply_leaves_valid_installed_extension_for_cli_force(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    actual = extensions / "one-tone.one-tone-trae-0.1.0"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    (actual / "themes").mkdir(parents=True)
    (actual / "themes" / "one-tone-color-theme.json").write_text("{}", encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, extensions, ai_panel_supported=False)

    def command_runner(command, **kwargs):
        assert actual.exists()
        return subprocess.CompletedProcess(command, 0)

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-existing-001")

    assert adapter.apply(plan).status == "ok"


def test_editor_apply_recovers_from_cli_restart_required_state(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    extensions.mkdir()
    index = extensions / "extensions.json"
    index.write_text(json.dumps([{
        "identifier": {"id": "one-tone.one-tone-trae"},
        "version": "0.1.0",
        "relativeLocation": "one-tone.one-tone-trae-0.1.0",
    }]), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, extensions, ai_panel_supported=False)

    def command_runner(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout=b"",
            stderr=b"Please restart VS Code before reinstalling One Tone trae.",
        )

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-restart-required-001")

    assert adapter.apply(plan).status == "ok"
    installed = extensions / "one-tone.one-tone-trae-0.1.0"
    assert (installed / "package.json").is_file()
    assert (installed / "themes" / "one-tone-color-theme.json").is_file()
    assert adapter.verify(plan).verified is True


def test_cursor_apply_recovers_from_cursor_restart_required_state(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    extensions.mkdir()
    index = extensions / "extensions.json"
    index.write_text(json.dumps([{
        "identifier": {"id": "one-tone.one-tone-cursor"},
        "version": "0.1.0",
        "relativeLocation": "one-tone.one-tone-cursor-0.1.0",
    }]), encoding="utf-8")
    spec = EditorSpec("cursor", "cursor", settings, extensions, ai_panel_supported=False)

    def command_runner(command, **kwargs):
        return subprocess.CompletedProcess(
            command,
            1,
            stdout=b"",
            stderr=b"Please restart Cursor before reinstalling One Tone cursor.",
        )

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#00A86B", ["cursor"], plan_id="plan-editor-cursor-restart-001")

    assert adapter.apply(plan).status == "ok"
    installed = extensions / "one-tone.one-tone-cursor-0.1.0"
    assert (installed / "package.json").is_file()
    assert adapter.verify(plan).verified is True


def test_editor_adapter_tracks_and_uninstalls_actual_extension_directory(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    extensions.mkdir()
    index = extensions / "extensions.json"
    index.write_text("[]", encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, extensions, ai_panel_supported=False)
    actual = extensions / "one-tone.one-tone-trae-0.1.0"
    commands = []

    def command_runner(command, **kwargs):
        commands.append(command)
        if "--install-extension" in command:
            actual.mkdir(parents=True)
            (actual / "themes").mkdir()
            (actual / "themes" / "one-tone-color-theme.json").write_text("{}", encoding="utf-8")
            index.write_text(json.dumps([{"identifier": {"id": "one-tone.one-tone-trae"}}]), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-003")

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert actual.exists() is False
    assert index.read_text(encoding="utf-8") == "[]"


def test_editor_verify_discovers_extension_after_new_adapter_instance(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    extensions.mkdir()
    actual = extensions / "one-tone.one-tone-trae-0.1.0"

    def command_runner(command, **kwargs):
        actual.mkdir(parents=True)
        (actual / "themes").mkdir()
        (actual / "themes" / "one-tone-color-theme.json").write_text("{}", encoding="utf-8")
        (extensions / "extensions.json").write_text(json.dumps([{
            "identifier": {"id": "one-tone.one-tone-trae"},
            "relativeLocation": actual.name,
        }]), encoding="utf-8")
        return subprocess.CompletedProcess(command, 0)

    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-cross-process-001")
    spec = EditorSpec("trae", "trae", settings, extensions)
    first_adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    assert first_adapter.snapshot(tmp_path / "backup").status == "ok"
    assert first_adapter.apply(plan).status == "ok"

    second_adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    result = second_adapter.verify(plan)

    assert result.verified is True
