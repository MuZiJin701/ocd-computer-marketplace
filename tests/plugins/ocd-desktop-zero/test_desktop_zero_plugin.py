from pathlib import Path


def test_desktop_zero_package_shape():
    root = Path("plugins/ocd-desktop-zero")
    skill = root / "skills/desktop-zero"
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert (skill / "SKILL.md").is_file()
    assert (skill / "pyproject.toml").is_file()
    assert (skill / "agents/openai.yaml").is_file()
    assert (skill / "scripts/run_desktop_zero.py").is_file()
    assert (skill / "src/desktop_zero/workflow.py").is_file()
