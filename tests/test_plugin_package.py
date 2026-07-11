from pathlib import Path


def test_plugin_scaffold_is_present():
    root = Path("plugins/one-tone-windows")
    assert (root / ".codex-plugin/plugin.json").is_file()
    assert (root / "agents/openai.yaml").is_file()
    assert (root / "skills/unify-windows-theme/SKILL.md").is_file()
    assert (root / "skills/unify-windows-theme/references/workflow.md").is_file()
    assert (root / "skills/unify-windows-theme/references/target-matrix.md").is_file()
    assert (root / "skills/unify-windows-theme/scripts/preview.ps1").is_file()
    assert (root / "skills/unify-windows-theme/scripts/apply.ps1").is_file()
    assert (root / "skills/unify-windows-theme/scripts/verify.ps1").is_file()
    assert (root / "skills/unify-windows-theme/scripts/rollback.ps1").is_file()
