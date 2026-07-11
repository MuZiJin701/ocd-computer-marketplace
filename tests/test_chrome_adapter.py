import json
import zipfile

from one_tone.adapters.chrome import ChromeAdapter, build_chrome_theme
from one_tone.plan import create_plan


def test_chrome_theme_zip_has_manifest_and_palette_colors(tmp_path):
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-001")
    path = build_chrome_theme(plan, tmp_path / "chrome-theme.zip")
    with zipfile.ZipFile(path) as archive:
        manifest = json.loads(archive.read("manifest.json"))
    assert manifest["manifest_version"] == 2
    assert manifest["theme"]["colors"]["frame"] == plan.palette["surface"]


def test_chrome_apply_requires_explicit_user_action(tmp_path):
    adapter = ChromeAdapter(tmp_path / "output")
    plan = create_plan("#7C3AED", ["chrome"], plan_id="plan-chrome-002")

    assert adapter.detect().status == "ok"
    result = adapter.apply(plan)
    assert result.status == "partial"
    assert result.requires_user_action is True
    assert adapter.verify(plan).verified is True
