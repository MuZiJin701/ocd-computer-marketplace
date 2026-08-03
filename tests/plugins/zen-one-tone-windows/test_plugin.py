from pathlib import Path


def test_plugin_scaffold_is_present():
    root = Path("plugins/zen-one-tone-windows")
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert not (root / "pyproject.toml").exists()
    assert (root / "skills/zen-one-tone-windows/SKILL.md").is_file()
    assert (root / "skills/zen-one-tone-windows/agents/openai.yaml").is_file()
    assert (root / "skills/zen-one-tone-windows/references/targets.md").is_file()
    assert (root / "skills/zen-one-tone-windows/examples/preview-request.md").is_file()
    assert not (root / "examples").exists()
    assert not (root / "skills/zen-one-tone-windows/references/workflow.md").exists()
    assert not (root / "skills/zen-one-tone-windows/references/target-matrix.md").exists()
    assert (root / "skills/zen-one-tone-windows/scripts/run_one_tone.py").is_file()
    assert not list((root / "skills/zen-one-tone-windows/scripts").glob("*.ps1"))


def test_skill_package_does_not_include_repository_tests_or_archive():
    root = Path("plugins/zen-one-tone-windows/skills/zen-one-tone-windows")
    assert not (root / "tests").exists()
    assert not (root / "docs").exists()


def test_generated_runtime_directories_are_ignored():
    ignore = Path(".gitignore")
    assert ignore.is_file()
    text = ignore.read_text(encoding="utf-8")
    assert ".one-tone/" in text
    assert "__pycache__/" in text
    assert ".pytest_cache/" in text
