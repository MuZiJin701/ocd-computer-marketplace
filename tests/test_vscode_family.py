import json
import subprocess
import zipfile

from one_tone.adapters.vscode_family import EditorSpec, VSCodeFamilyAdapter, build_vsix
from one_tone.plan import create_plan


def test_vsix_contains_manifest_and_theme(tmp_path):
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-001")
    path = build_vsix(plan, tmp_path / "theme.vsix", EditorSpec("trae", "trae", tmp_path / "settings.json", tmp_path / "extensions"))
    with zipfile.ZipFile(path) as archive:
        names = set(archive.namelist())
        assert "extension/package.json" in names
        assert "extension/themes/one-tone-color-theme.json" in names


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
    assert adapter.rollback(tmp_path / "backup").verified is True


def test_editor_verify_does_not_accept_uninstalled_flat_theme(tmp_path):
    settings = tmp_path / "settings.json"
    settings.write_text(json.dumps({"workbench.colorTheme": "Default Dark+"}), encoding="utf-8")
    spec = EditorSpec("cursor", "cursor", settings, tmp_path / "extensions", ai_panel_supported=False)
    adapter = VSCodeFamilyAdapter(spec, command_runner=lambda *args, **kwargs: None)
    plan = create_plan("#7C3AED", ["cursor"], plan_id="plan-editor-uninstalled-001")

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "failed"


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
