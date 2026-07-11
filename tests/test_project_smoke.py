def test_package_exposes_version():
    import one_tone

    assert one_tone.__version__ == "0.1.0"


def test_readme_describes_stage_one_two_limits():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "阶段 1–2" in text
    assert "不实现真实应用适配" in text
    assert "uv run pytest" in text
