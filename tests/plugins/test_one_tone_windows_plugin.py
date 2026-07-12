from pathlib import Path


def test_plugin_scaffold_is_present():
    root = Path("plugins/one-tone-windows")
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert not (root / "pyproject.toml").exists()
    assert (root / "skills/unify-windows-theme/SKILL.md").is_file()
    assert (root / "skills/unify-windows-theme/agents/openai.yaml").is_file()
    assert (root / "skills/unify-windows-theme/references/targets.md").is_file()
    assert not (root / "skills/unify-windows-theme/references/workflow.md").exists()
    assert not (root / "skills/unify-windows-theme/references/target-matrix.md").exists()
    assert (root / "skills/unify-windows-theme/scripts/run_one_tone.py").is_file()
    assert not list((root / "skills/unify-windows-theme/scripts").glob("*.ps1"))


def test_skill_package_does_not_include_repository_tests_or_archive():
    root = Path("plugins/one-tone-windows/skills/unify-windows-theme")
    assert not (root / "tests").exists()
    assert not (root / "docs").exists()


def test_generated_runtime_directories_are_ignored():
    ignore = Path(".gitignore")
    assert ignore.is_file()
    text = ignore.read_text(encoding="utf-8")
    assert ".one-tone/" in text
    assert "__pycache__/" in text
    assert ".pytest_cache/" in text
