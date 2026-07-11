def test_package_exposes_version():
    import one_tone

    assert one_tone.__version__ == "0.1.0"


def test_readme_describes_stage_one_two_limits():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "Plan" in text
    assert "Windows 10 22H2+" in text
    assert "uv run pytest" in text


def test_readme_documents_full_adapter_boundaries():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "Windows 10 22H2+" in text
    assert "verify" in text
    assert "--restart-apps" in text
    assert "壁纸" in text
    assert "requires_user_action" in text
