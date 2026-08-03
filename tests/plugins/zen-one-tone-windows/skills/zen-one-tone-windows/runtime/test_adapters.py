from one_tone.adapters import AdapterResult, UnsupportedAdapter


def test_adapter_result_has_required_structured_fields():
    result = AdapterResult("chrome", "skipped", False, False, "not verified")
    assert result.target == "chrome"
    assert result.status == "skipped"


def test_adapter_result_stores_user_action_and_version():
    result = AdapterResult("chrome", "partial", False, False, "load theme", True, "Chrome 138")
    assert result.requires_user_action is True
    assert result.version == "Chrome 138"


def test_unsupported_adapter_never_claims_success():
    result = UnsupportedAdapter("codex").detect()
    assert result.status == "skipped"
    assert result.changed is False


def test_cursor_is_explicitly_skipped_without_touching_files(tmp_path):
    from one_tone.cli import build_target_adapters

    adapter = build_target_adapters(("cursor",), tmp_path / "state")["cursor"]

    result = adapter.detect()

    assert isinstance(adapter, UnsupportedAdapter)
    assert result.status == "skipped"
    assert not (tmp_path / "state").exists()


def test_field_inventory_keeps_evidence_and_visual_region_details():
    from one_tone.inventory import inventory_groups

    groups = inventory_groups("chrome")

    assert "browser chrome" in groups
    field = groups["browser chrome"][0]
    assert field["technical_field"]
    assert field["official_source"].startswith("https://")
    assert field["version_baseline"]
    assert field["inventory_version"] == "2026-08-03.v2"
    assert field["capability_status"] == "supported"


def test_field_inventory_classifies_text_evidence_and_opacity_policy():
    from one_tone.inventory import field_inventory_for

    fields = {entry["technical_field"]: entry for entry in field_inventory_for("vscode")}

    assert fields["editor.foreground"]["text_class"] == "dense-primary"
    assert fields["editor.foreground"]["paired_background_role"] == "surface"
    assert fields["editor.foreground"]["opacity_policy"] == "opaque"
    assert fields["editor.foreground"]["reference_theme"] == "VS Code Light Modern 1.131.0"

    assert fields["editor.placeholder.foreground"]["text_class"] == "secondary"
    assert fields["editorError.foreground"]["text_class"] == "state"


def test_field_inventory_keeps_git_and_prediction_text_semantic():
    from one_tone.inventory import field_inventory_for

    fields = {entry["technical_field"]: entry for entry in field_inventory_for("trae")}
    assert fields["gitDecoration.untrackedResourceForeground"]["visual_role"] == "success_text"
    assert fields["gitDecoration.modifiedResourceForeground"]["visual_role"] == "warning_text"
    assert fields["gitDecoration.ignoredResourceForeground"]["visual_role"] == "muted_foreground"
    assert fields["gitDecoration.untrackedResourceForeground"]["text_class"] == "semantic"

    terminal = {entry["technical_field"]: entry for entry in field_inventory_for("terminal")}
    assert terminal["InlinePrediction"]["visual_role"] == "muted_foreground"
    assert terminal["ListPredictionSelected"]["paired_background_role"] == "selection"
