import json
import tomllib

from one_tone.adapters.codex import (
    CODEX_CONFIG_SCHEMA_V1,
    CodexAdapter,
    default_codex_config_path,
    locate_verified_codex_config,
)
from one_tone.plan import create_plan


def write_codex_v1_fixture(path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        """# Keep this comment and unrelated fields.\n[desktop]\nappearanceTheme = \"dark\"\nunrelatedSetting = \"keep\"\n\n[desktop.appearanceLightChromeTheme]\naccent = \"#FFE66D\"\ncontrast = 100\nink = \"#FFFFFF\"\nopaqueWindows = true\nsurface = \"#062D14\"\n\n[desktop.appearanceLightChromeTheme.fonts]\neditor = \"keep\"\n\n[desktop.appearanceLightChromeTheme.semanticColors]\ndiffAdded = \"#2EFF45\"\ndiffRemoved = \"#FF9AAF\"\nskill = \"#FFE66D\"\n\n[desktop.appearanceDarkChromeTheme]\naccent = \"#FFE66D\"\ncontrast = 100\nink = \"#FFFFFF\"\nopaqueWindows = true\nsurface = \"#062D14\"\n\n[desktop.appearanceDarkChromeTheme.fonts]\neditor = \"keep\"\n\n[desktop.appearanceDarkChromeTheme.semanticColors]\ndiffAdded = \"#2EFF45\"\ndiffRemoved = \"#FF9AAF\"\nskill = \"#FFE66D\"\n""",
        encoding="utf-8",
    )
    return path


def test_codex_v1_config_is_detected(tmp_path):
    path = write_codex_v1_fixture(tmp_path / "config.toml")
    result = CodexAdapter(path).detect()
    assert result.status == "ok"
    assert result.version == CODEX_CONFIG_SCHEMA_V1


def test_codex_system_appearance_mode_is_detected(tmp_path):
    path = write_codex_v1_fixture(tmp_path / "config.toml")
    path.write_text(
        path.read_text(encoding="utf-8").replace('appearanceTheme = "dark"', 'appearanceTheme = "system"'),
        encoding="utf-8",
    )

    assert CodexAdapter(path).detect().status == "ok"


def test_codex_default_path_uses_userprofile(monkeypatch, tmp_path):
    monkeypatch.setenv("USERPROFILE", str(tmp_path))
    path = write_codex_v1_fixture(tmp_path / ".codex" / "config.toml")
    assert default_codex_config_path() == path
    assert locate_verified_codex_config() == path


def test_codex_unknown_config_is_skipped(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[desktop]\nappearanceTheme = 'dark'\n", encoding="utf-8")
    result = CodexAdapter(path).detect()
    assert result.status == "skipped"
    assert "codex-config-v1" in result.message


def test_codex_malformed_toml_is_skipped(tmp_path):
    path = tmp_path / "config.toml"
    path.write_text("[desktop\nappearanceTheme = 'dark'\n", encoding="utf-8")
    assert CodexAdapter(path).detect().status == "skipped"


def test_codex_v1_fixture_applies_verifies_and_restores_preserving_fields(tmp_path):
    path = write_codex_v1_fixture(tmp_path / "config.toml")
    original = path.read_bytes()
    adapter = CodexAdapter(path)
    plan = create_plan("#00A86B", ["codex"], plan_id="plan-codex-v1-001")

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    applied = adapter.apply(plan)
    assert applied.status == "ok"
    assert applied.version == CODEX_CONFIG_SCHEMA_V1

    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    for mode in ("appearanceLightChromeTheme", "appearanceDarkChromeTheme"):
        theme = payload["desktop"][mode]
        assert theme["accent"] == plan.palette["accent"]
        assert theme["ink"] == plan.palette["foreground"]
        assert theme["surface"] == plan.seed_color
        assert theme["contrast"] == 100
        assert theme["opaqueWindows"] is True
        assert theme["fonts"]["editor"] == "keep"
        assert theme["semanticColors"]["diffAdded"] == plan.palette["success"]
        assert theme["semanticColors"]["diffRemoved"] == plan.palette["error"]
        assert theme["semanticColors"]["skill"] == plan.palette["accent"]
    assert payload["desktop"]["unrelatedSetting"] == "keep"

    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert path.read_bytes() == original


def test_codex_apply_raises_existing_theme_contrast_to_maximum(tmp_path):
    path = write_codex_v1_fixture(tmp_path / "config.toml")
    path.write_text(path.read_text(encoding="utf-8").replace("contrast = 100", "contrast = 20"), encoding="utf-8")
    adapter = CodexAdapter(path)
    plan = create_plan("#10B981", ["codex"], plan_id="plan-codex-contrast-100-001")

    assert adapter.apply(plan).status == "ok"

    payload = tomllib.loads(path.read_text(encoding="utf-8"))
    assert payload["desktop"]["appearanceTheme"] == "dark"
    assert payload["desktop"]["appearanceLightChromeTheme"]["contrast"] == 100
    assert payload["desktop"]["appearanceDarkChromeTheme"]["contrast"] == 100
