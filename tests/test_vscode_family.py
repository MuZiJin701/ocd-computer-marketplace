import json
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
    adapter = VSCodeFamilyAdapter(spec, command_runner=lambda *args, **kwargs: None)
    plan = create_plan("#7C3AED", ["trae"], plan_id="plan-editor-002")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    result = adapter.verify(plan)
    assert result.verified is True
    assert result.status == "partial"
    assert adapter.rollback(tmp_path / "backup").verified is True
