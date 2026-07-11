from one_tone.adapters.windows import (
    InMemoryDesktopBackend,
    InMemoryRegistryBackend,
    WindowsAdapter,
    WindowsConfig,
    detect_windows_version,
    generate_wallpaper,
    windows_color_value,
)
import one_tone.adapters.windows as windows_module
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


def test_windows_apply_sets_green_accent_and_taskbar_prevalence(tmp_path):
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200"})
    desktop = InMemoryDesktopBackend()
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    plan = create_plan("#00A86B", ["windows"], plan_id="plan-windows-accent-001")

    assert adapter.apply(plan).status == "ok"
    assert registry.values["ColorPrevalence"] == 1
    assert registry.values["AccentColorMenu"] == windows_color_value(plan.palette["accent"])
    assert registry.values["ColorizationColor"] == 0xC4005436


def test_windows_registry_writes_each_value_to_its_declared_hive_path(monkeypatch):
    class FakeKey:
        def __init__(self, owner, root, path):
            self.owner = owner
            self.root = root
            self.path = path

        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def set_value(self, name, reserved, kind, value):
            self.owner.writes.append((self.root, self.path, name, kind, value))

    class FakeWinreg:
        HKEY_CURRENT_USER = "HKCU"
        HKEY_LOCAL_MACHINE = "HKLM"
        REG_DWORD = "REG_DWORD"

        def __init__(self):
            self.writes = []

        def CreateKey(self, root, path):
            return FakeKey(self, root, path)

        def OpenKey(self, *args):
            raise AssertionError("OpenKey is not expected in this test")

        def SetValueEx(self, key, name, reserved, kind, value):
            key.set_value(name, reserved, kind, value)

    fake = FakeWinreg()
    monkeypatch.setattr(windows_module, "winreg", fake)

    windows_module.WindowsRegistryBackend().set_value("AccentColor", 123)

    assert fake.writes == [("HKCU", windows_module.DWM_KEY, "AccentColor", "REG_DWORD", 123)]
