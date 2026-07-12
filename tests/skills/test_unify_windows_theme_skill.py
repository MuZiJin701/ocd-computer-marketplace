def test_package_exposes_version():
    import one_tone

    assert one_tone.__version__ == "0.1.0"


def test_readme_describes_stage_one_two_limits():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "Plan" in text
    assert "Windows 10 22H2+" in text
    assert "Preview" in text


def test_readme_documents_full_adapter_boundaries():
    from pathlib import Path

    text = Path("README.md").read_text(encoding="utf-8")
    assert "Windows 10 22H2+" in text
    assert "verify" in text
    assert "verify plan-..." in text
    assert "Transaction ID" in text
    assert "八步" not in text
    assert "壁纸" in text
    assert "partial" in text


def test_skill_package_contains_runtime_and_launcher():
    from pathlib import Path

    root = Path("plugins/one-tone-windows/skills/unify-windows-theme")
    assert (root / "SKILL.md").is_file()
    assert (root / "pyproject.toml").is_file()
    assert (root / "src/one_tone/cli.py").is_file()
    assert (root / "scripts/run_one_tone.py").is_file()
    assert (root / "examples/preview-request.md").is_file()


def test_distributable_skill_does_not_depend_on_plugin_root():
    from pathlib import Path

    script = (Path("plugins/one-tone-windows/skills/unify-windows-theme") / "scripts/run_one_tone.py").read_text(encoding="utf-8")
    assert "plugins/one-tone-windows/src" not in script
    assert "Path(__file__).resolve().parents[1]" in script


def test_launcher_uses_skill_root_as_uv_project():
    from pathlib import Path

    script = (Path("plugins/one-tone-windows/skills/unify-windows-theme") / "scripts/run_one_tone.py").read_text(encoding="utf-8")
    assert "skill_root = Path(__file__).resolve().parents[1]" in script
    assert '"--project", str(skill_root)' in script


def test_agents_documents_current_scope():
    from pathlib import Path

    agents = Path("AGENTS.md").read_text(encoding="utf-8")
    assert "Windows 10" in agents
    assert "Windows 11" in agents
    assert "只回滚失败目标" in agents


def test_active_docs_describe_current_workflow():
    from pathlib import Path

    readme = Path("README.md").read_text(encoding="utf-8")
    assert "Windows 10 22H2+" in readme
    assert "verify plan-..." in readme
    assert "Transaction ID" in readme
    assert "八步" not in readme


def test_root_project_is_test_only_and_skill_owns_cli():
    import tomllib
    from pathlib import Path

    root = tomllib.loads(Path("pyproject.toml").read_text(encoding="utf-8"))
    skill = tomllib.loads(
        Path("plugins/one-tone-windows/skills/unify-windows-theme/pyproject.toml")
        .read_text(encoding="utf-8")
    )

    assert root["tool"]["uv"]["package"] is False
    assert "scripts" not in root["project"]
    assert root["tool"]["pytest"]["ini_options"]["pythonpath"] == [
        "plugins/one-tone-windows/skills/unify-windows-theme/src"
    ]
    assert skill["project"]["scripts"]["one-tone"] == "one_tone.cli:main"
