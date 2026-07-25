import json
import zipfile

from one_tone.adapters.chrome import ChromeAdapter, build_chrome_theme, build_chrome_theme_directory
from one_tone.palette import parse_hex_color
from one_tone.plan import create_plan
from one_tone.transaction import TransactionStore, apply_plan


def test_chrome_theme_zip_has_manifest_and_palette_colors(tmp_path):
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-001")
    path = build_chrome_theme(plan, tmp_path / "chrome-theme.zip")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["manifest_version"] == 3
    palette = plan.palette_for(plan.mode)
    expected_surface = list(parse_hex_color(palette["surface"]))
    expected_background = list(parse_hex_color(palette["background"]))
    expected_surface_subtle = list(parse_hex_color(palette["surface_subtle"]))
    expected_surface_raised = list(parse_hex_color(palette["surface_raised"]))
    expected_foreground = list(parse_hex_color(palette["foreground"]))
    expected_accent_text = list(parse_hex_color(palette["accent_text"]))
    assert manifest["theme"]["colors"]["frame"] == expected_surface
    assert manifest["theme"]["colors"]["toolbar"] == expected_surface_subtle
    assert manifest["theme"]["colors"]["toolbar_text"] == expected_foreground
    assert manifest["theme"]["colors"]["toolbar_button_icon"] == expected_foreground
    assert manifest["theme"]["colors"]["tab_text"] == expected_foreground
    assert manifest["theme"]["colors"]["ntp_background"] == expected_background
    assert manifest["theme"]["colors"]["omnibox_background"] == expected_surface_raised
    assert manifest["theme"]["colors"]["ntp_header"] == expected_foreground
    assert manifest["theme"]["colors"]["ntp_link"] == expected_accent_text
    assert all(isinstance(value, list) for value in manifest["theme"]["colors"].values())
    assert all(any(value) for value in manifest["theme"]["tints"].values())


def test_chrome_theme_directory_contains_loadable_manifest(tmp_path):
    plan = create_plan("#00A86B", ["chrome"], plan_id="plan-chrome-directory-001")
    directory = build_chrome_theme_directory(plan, tmp_path / "one-tone-theme")

    manifest = json.loads((directory / "manifest.json").read_text(encoding="utf-8"))
    assert manifest["manifest_version"] == 3
    assert manifest["theme"]["colors"]["frame"] == list(parse_hex_color(plan.palette_for(plan.mode)["surface"]))


def test_chrome_apply_requires_explicit_user_action(tmp_path):
    adapter = ChromeAdapter(tmp_path / "output")
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-002")

    assert adapter.detect().status == "ok"
    result = adapter.apply(plan)
    assert result.status == "partial"
    assert result.requires_user_action is True
    assert adapter.verify(plan).verified is True
    assert (tmp_path / "output" / "one-tone-plan-chrome-002-dark" / "manifest.json").is_file()
    assert (tmp_path / "output" / "one-tone-plan-chrome-002-light" / "manifest.json").is_file()
    assert sorted(path.name for path in (tmp_path / "output").iterdir() if path.is_dir()) == [
        "one-tone-plan-chrome-002-dark",
        "one-tone-plan-chrome-002-light",
    ]


def test_chrome_mode_artifacts_preserve_plan_palette_roles(tmp_path):
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-coherence-001")
    adapter = ChromeAdapter(tmp_path / "output")

    assert adapter.apply(plan).status == "partial"

    light_manifest = json.loads(
        (tmp_path / "output" / "one-tone-plan-chrome-coherence-001-light" / "manifest.json").read_text(encoding="utf-8")
    )
    dark_manifest = json.loads(
        (tmp_path / "output" / "one-tone-plan-chrome-coherence-001-dark" / "manifest.json").read_text(encoding="utf-8")
    )
    assert light_manifest["theme"]["colors"]["frame"] == list(parse_hex_color(plan.palette_for("light")["surface"]))
    assert dark_manifest["theme"]["colors"]["frame"] == list(parse_hex_color(plan.palette_for("dark")["surface"]))


def test_chrome_rollback_removes_zip_and_unpacked_artifacts(tmp_path):
    adapter = ChromeAdapter(tmp_path / "output")
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-rollback-001")

    assert adapter.apply(plan).status == "partial"
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert not any((tmp_path / "output").iterdir())


def test_chrome_rollback_removes_artifacts_after_new_adapter_instance(tmp_path):
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-cross-process-001")
    store = TransactionStore(tmp_path / "transactions")
    first_adapter = ChromeAdapter(tmp_path / "output")
    record = apply_plan(plan, {"chrome": first_adapter}, store, confirm=True)
    assert record.status.value == "PARTIAL"

    second_adapter = ChromeAdapter(tmp_path / "output")
    result = store.rollback(record.id, {"chrome": second_adapter})

    assert result.status.value == "ROLLED_BACK"
    assert not (tmp_path / "output" / "one-tone-plan-chrome-cross-process-001").exists()
    assert not (tmp_path / "output" / "one-tone-plan-chrome-cross-process-001.zip").exists()
