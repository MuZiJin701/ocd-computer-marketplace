import json
from pathlib import Path


def test_repo_marketplace_points_to_plugin():
    payload = json.loads(Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    entry = payload["plugins"][0]
    assert entry["source"]["source"] == "local"
    assert entry["source"]["path"] == "./plugins/one-tone-windows"
    assert entry["policy"]["installation"] == "AVAILABLE"
    assert entry["policy"]["authentication"] == "ON_INSTALL"


def test_plugin_contains_runtime_source():
    root = Path("plugins/one-tone-windows")
    assert (root / "src/one_tone/cli.py").is_file()
    assert (root / "pyproject.toml").is_file()


def test_skill_launcher_points_at_plugin_runtime():
    script = Path("plugins/one-tone-windows/skills/unify-windows-theme/scripts/run_one_tone.py").read_text(encoding="utf-8")
    skill = Path("plugins/one-tone-windows/skills/unify-windows-theme/SKILL.md").read_text(encoding="utf-8")
    assert "uv" in script
    assert "--project" in script
    assert "parents[3]" in script
    assert "run_one_tone.py" in skill


def test_readme_documents_repo_marketplace_and_plugin_runtime():
    root_readme = Path("README.md").read_text(encoding="utf-8")
    plugin_readme = Path("plugins/one-tone-windows/README.md").read_text(encoding="utf-8")
    assert ".agents/plugins/marketplace.json" in root_readme
    assert "plugins/one-tone-windows" in root_readme
    assert "self-contained" in plugin_readme
