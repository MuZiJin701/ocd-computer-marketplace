from one_tone.adapters.windows import (
    InMemoryDesktopBackend,
    InMemoryRegistryBackend,
    WindowsAdapter,
    WindowsConfig,
    detect_windows_version,
    generate_wallpaper,
)
from one_tone.plan import create_plan


def test_build_26200_is_windows_11_even_if_product_name_is_legacy():
    backend = InMemoryRegistryBackend({"CurrentBuild": "26200", "ProductName": "Windows 10 Home China"})
    assert detect_windows_version(backend) == ("windows-11", 26200)


def test_build_19045_is_windows_10():
    backend = InMemoryRegistryBackend({"CurrentBuild": "19045", "ProductName": "Windows 10 Pro"})
    assert detect_windows_version(backend) == ("windows-10", 19045)


def test_wallpaper_generation_is_png_and_deterministic(tmp_path):
    plan = create_plan("#7C3AED", ["windows"], plan_id="plan-windows-001")
    first = generate_wallpaper(plan.palette, tmp_path / "first.png", width=32, height=16)
    second = generate_wallpaper(plan.palette, tmp_path / "second.png", width=32, height=16)
    assert first.read_bytes() == second.read_bytes()
    assert first.read_bytes().startswith(b"\x89PNG\r\n\x1a\n")


def test_windows_adapter_snapshots_applies_verifies_and_restores(tmp_path):
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200", "AppsUseLightTheme": 1, "SystemUsesLightTheme": 1})
    desktop = InMemoryDesktopBackend(wallpaper="C:/old.jpg")
    old_wallpaper = tmp_path / "old.jpg"
    old_wallpaper.write_bytes(b"old wallpaper")
    desktop.wallpaper = str(old_wallpaper)
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    plan = create_plan("#7C3AED", ["windows"], plan_id="plan-windows-002")

    assert adapter.detect().status == "ok"
    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "ok"
    assert adapter.verify(plan).verified is True
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert registry.values["AppsUseLightTheme"] == 1
    assert desktop.wallpaper == str(old_wallpaper)
