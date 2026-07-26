import json
import subprocess
import zipfile

from one_tone.adapters.vscode_family import EditorSpec, VSCodeFamilyAdapter, build_theme_json, build_vsix
from one_tone.plan import create_plan


def _write_valid_extension(spec, registered=True):
    actual = spec.extensions_dir / f"one-tone.one-tone-{spec.target}-0.1.0"
    (actual / "themes").mkdir(parents=True, exist_ok=True)
    (actual / "themes" / "one-tone-color-theme.json").write_text("{}", encoding="utf-8")
    (actual / "themes" / "one-tone-light-color-theme.json").write_text("{}", encoding="utf-8")
    (actual / "package.json").write_text(json.dumps({
        "contributes": {"themes": [
            {"label": f"One Tone {spec.target} Dark"},
            {"label": f"One Tone {spec.target} Light"},
        ]}
    }), encoding="utf-8")
    if registered:
        (spec.extensions_dir / "extensions.json").write_text(json.dumps([{
            "identifier": {"id": f"one-tone.one-tone-{spec.target}"},
            "version": "0.1.0",
            "relativeLocation": actual.name,
        }]), encoding="utf-8")
    return actual


def test_vsix_contains_manifest_and_theme(tmp_path):
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-001")
    path = build_vsix(plan, tmp_path / "theme.vsix", EditorSpec("trae", "trae", tmp_path / "settings.json", tmp_path / "extensions"))
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "extension/package.json" in names
        assert "extension/themes/one-tone-color-theme.json" in names
        package = json.loads(archive.read("extension/package.json"))
        assert [theme["label"] for theme in package["contributes"]["themes"]] == [
            "One Tone trae Dark",
            "One Tone trae Light",
        ]


def test_vsix_keeps_dark_label_bound_to_dark_palette_when_plan_selects_light(tmp_path):
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-mode-pair-001", mode="light")
    path = build_vsix(plan, tmp_path / "theme.vsix", EditorSpec("trae", "trae", tmp_path / "settings.json", tmp_path / "extensions"))

    with zipfile.ZipFile(path) as archive:
        dark_theme = json.loads(archive.read("extension/themes/one-tone-color-theme.json"))

    assert dark_theme["name"] == "One Tone trae Dark"
    assert dark_theme["type"] == "dark"
    assert dark_theme["colors"]["editor.background"] == plan.palette_for("dark")["surface"]


def test_editor_theme_uses_surface_for_primary_backgrounds():
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-surface-001")

    theme = build_theme_json(plan, "One Tone trae")
    colors = theme["colors"]

    palette = plan.palette_for(plan.mode)
    assert colors["editor.background"] == palette["surface"]
    assert colors["terminal.background"] == palette["surface"]
    assert colors["sideBar.background"] == palette["surface_subtle"]
    assert colors["activityBar.background"] == palette["background"]
    assert colors["statusBar.background"] == palette["surface_raised"]
    assert colors["titleBar.activeBackground"] == palette["surface_raised"]
    assert colors["sideBarSectionHeader.background"] == palette["background"]
    assert colors["activityBarTop.activeBorder"] == palette["accent"]
    assert colors["tab.activeBackground"] == palette["surface"]
    assert colors["panel.background"] == palette["background"]


def test_editor_theme_uses_matching_foregrounds_for_surface_and_background():
    plan = create_plan("#10B981", ["trae"], plan_id="plan-editor-contrast-001")

    colors = build_theme_json(plan, "One Tone trae")["colors"]

    palette = plan.palette_for(plan.mode)
    assert colors["editor.foreground"] == palette["foreground"]
    assert colors["panel.foreground"] == palette["background_foreground"]


def test_editor_theme_uses_contrast_safe_text_for_accented_tokens():
    plan = create_plan("#10B981", ["trae"], plan_id="plan-editor-accent-text-001")

    theme = build_theme_json(plan, "One Tone trae")

    palette = plan.palette_for(plan.mode)
    assert theme["colors"]["editorCursor.foreground"] == palette["accent_text"]
    assert theme["colors"]["editor.selectionForeground"] == palette["selection_foreground"]
    assert theme["colors"]["terminalCursor.foreground"] == palette["accent_text"]
    assert theme["colors"]["textLink.foreground"] == palette["accent_text"]
    assert theme["colors"]["errorForeground"] == palette["error_text"]
    assert theme["semanticHighlighting"] is True
    assert theme["semanticTokenColors"]["function"] == palette["success_text"]
    assert theme["semanticTokenColors"]["type"] == palette["accent_text"]
    assert theme["tokenColors"][1]["settings"]["foreground"] == palette["success_text"]
    assert theme["tokenColors"][2]["settings"]["foreground"] == palette["accent_text"]
    assert theme["tokenColors"][3]["settings"]["foreground"] == palette["error_text"]


def test_editor_adapter_snapshots_applies_verifies_and_restores(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+", "window.autoDetectColorScheme": False}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, tmp_path / "extensions", ai_panel_supported=False)
    def command_runner(command, **kwargs):
        _write_valid_extension(spec)
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
    assert changed["workbench.colorTheme"] == "One Tone trae Dark"
    assert changed["workbench.preferredDarkColorTheme"] == "One Tone trae Dark"
    assert changed["workbench.preferredLightColorTheme"] == "One Tone trae Light"
    assert changed["window.autoDetectColorScheme"] is True
    assert adapter.rollback(tmp_path / "backup").verified is True


def test_editor_apply_enables_auto_detect_when_setting_is_missing(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, tmp_path / "extensions", ai_panel_supported=True)

    def command_runner(command, **kwargs):
        _write_valid_extension(spec)
        return subprocess.CompletedProcess(command, 0)

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-auto-detect-001")

    assert adapter.apply(plan).status == "ok"
    changed = json.loads(settings.read_text(encoding="utf-8"))
    assert changed["window.autoDetectColorScheme"] is True


def test_editor_apply_leaves_valid_installed_extension_for_cli_force(tmp_path):
    settings = tmp_path / "settings.json"
    extensions = tmp_path / "extensions"
    actual = extensions / "one-tone.one-tone-trae-0.1.0"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, extensions, ai_panel_supported=False)
    _write_valid_extension(spec)

    def command_runner(command, **kwargs):
        assert actual.exists()
        return subprocess.CompletedProcess(command, 0)

    adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-existing-001")

    assert adapter.apply(plan).status == "ok"


def test_editor_apply_rejects_unregistered_extension_directory(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("trae", "trae", settings, tmp_path / "extensions")
    _write_valid_extension(spec, registered=False)

    adapter = VSCodeFamilyAdapter(spec, command_runner=lambda command, **kwargs: subprocess.CompletedProcess(command, 0))
    plan = create_plan("#00A86B", ["trae"], plan_id="plan-editor-unregistered-001")

    result = adapter.apply(plan)

    assert result.status == "failed"
    assert "evidence" in result.message


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

    result = adapter.apply(plan)
    assert result.status == "partial"
    assert result.metadata["cli_returncode"] == 1
    assert "Please restart VS Code" in result.metadata["cli_diagnostic"]
    installed = extensions / "one-tone.one-tone-trae-0.1.0"
    assert (installed / "package.json").is_file()
    assert (installed / "themes" / "one-tone-color-theme.json").is_file()
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
            _write_valid_extension(spec)
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
        _write_valid_extension(spec)
        return subprocess.CompletedProcess(command, 0)

    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-cross-process-001")
    spec = EditorSpec("trae", "trae", settings, extensions)
    first_adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    assert first_adapter.snapshot(tmp_path / "backup").status == "ok"
    assert first_adapter.apply(plan).status == "ok"

    second_adapter = VSCodeFamilyAdapter(spec, command_runner=command_runner)
    result = second_adapter.verify(plan)

    assert result.verified is True
