from pathlib import Path


def test_scoop_toolchain_package_shape():
    root = Path("plugins/ocd-scoop-toolchain")
    skill = root / "skills/scoop-toolchain"
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert (skill / "SKILL.md").is_file()
    assert (skill / "pyproject.toml").is_file()
    assert (skill / "agents/openai.yaml").is_file()
    assert (skill / "scripts/run_scoop_toolchain.py").is_file()
    assert (skill / "src/scoop_toolchain/workflow.py").is_file()
