from pathlib import Path
import json


def test_workstation_plugins_are_registered_and_self_contained():
    manifest = json.loads(Path(".agents/plugins/marketplace.json").read_text(encoding="utf-8"))
    names = {item["name"] for item in manifest["plugins"]}
    assert {"zen-desktop-zero", "zen-scoop-toolchain"} <= names
    for plugin, skill in (("ocd-desktop-zero", "desktop-zero"), ("ocd-scoop-toolchain", "scoop-toolchain")):
        root = Path("plugins") / plugin
        assert (root / ".codex-plugin/plugin.json").is_file()
        assert (root / "skills" / skill / "SKILL.md").is_file()
        assert len(list((root / "skills").iterdir())) == 1
