from pathlib import Path

from scoop_toolchain.tools import ScoopInstaller, WingetInstaller
from scoop_toolchain.workflow import apply, preview, verify


def test_toolchain_preview_detects_existing_without_installing(tmp_path):
    root = tmp_path / "scoop"
    result = preview(root, tmp_path / "plans", which=lambda name: None)
    assert result["plan_id"]
    assert result["changed"] is False
    assert not root.exists()
    assert {item["name"] for item in result["tools"]} == {"python", "git", "uv", "node"}


def test_scoop_first_then_winget_fallback_and_verify(tmp_path):
    root = tmp_path / "scoop"; root.mkdir()
    plan = preview(root, tmp_path / "plans", which=lambda name: None)
    calls = []
    class FakeScoop(ScoopInstaller):
        def install(self, tool, root):
            calls.append(("scoop", tool)); return (tool == "uv", "scoop output")
    class FakeWinget(WingetInstaller):
        def install(self, tool, root):
            calls.append(("winget", tool)); return True, "winget output"
    import scoop_toolchain.workflow as workflow
    old = workflow.scoop_available
    workflow.scoop_available = lambda: True
    try:
        result = apply(plan["plan_id"], True, tmp_path / "plans", FakeScoop(), FakeWinget())
    finally:
        workflow.scoop_available = old
    assert result["status"] == "partial"
    assert ("scoop", "uv") in calls
    assert any(source == "winget" for source, _ in calls)

    missing = verify(plan["plan_id"], tmp_path / "plans", which=lambda name: "C:/bin/" + name if name == "python" else None)
    assert missing["status"] == "partial"
