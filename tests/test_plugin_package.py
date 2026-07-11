from pathlib import Path


def test_plugin_scaffold_is_present():
    root = Path("plugins/one-tone-windows")
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert (root / "pyproject.toml").is_file()
    assert (root / "skills/unify-windows-theme/SKILL.md").is_file()
    assert (root / "skills/unify-windows-theme/agents/openai.yaml").is_file()
    assert (root / "skills/unify-windows-theme/references/workflow.md").is_file()
    assert (root / "skills/unify-windows-theme/references/target-matrix.md").is_file()
    assert (root / "skills/unify-windows-theme/scripts/run_one_tone.py").is_file()
    assert not list((root / "skills/unify-windows-theme/scripts").glob("*.ps1"))
