import struct
import zlib
from pathlib import Path

from one_tone.adapters.windows import (
    InMemoryDesktopBackend,
    InMemoryRegistryBackend,
    WindowsAdapter,
    WindowsConfig,
    detect_windows_version,
    generate_wallpaper,
    generate_accent_palette,
    windows_color_value,
    windows_colorization_value,
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


def test_wallpaper_generation_is_one_solid_seed_color(tmp_path):
    plan = create_plan("#00A86B", ["windows"], plan_id="plan-windows-solid-wallpaper-001")
    wallpaper = generate_wallpaper(plan.palette, tmp_path / "solid.png", width=8, height=4)
    payload = wallpaper.read_bytes()
    offset = 8
    idat = bytearray()
    width = height = None
    while offset < len(payload):
        length = struct.unpack(">I", payload[offset:offset + 4])[0]
        kind = payload[offset + 4:offset + 8]
        chunk = payload[offset + 8:offset + 8 + length]
        if kind == b"IHDR":
            width, height = struct.unpack(">II", chunk[:8])
        elif kind == b"IDAT":
            idat.extend(chunk)
        offset += 12 + length

    raw = zlib.decompress(bytes(idat))
    assert width == 8 and height == 4
    pixels = set()
    stride = width * 3 + 1
    for row in range(height):
        scanline = raw[row * stride:(row + 1) * stride]
        assert scanline[0] == 0
        pixels.update(tuple(scanline[index:index + 3]) for index in range(1, stride, 3))

    expected = tuple(bytes.fromhex(plan.seed_color[1:]))
    assert pixels == {expected}


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


def test_windows_verify_reloads_generated_wallpaper_path_in_new_process(tmp_path):
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200"})
    desktop = InMemoryDesktopBackend()
    plan = create_plan("#00A86B", ["windows"], plan_id="plan-windows-cross-process-verify-001")

    apply_adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    assert apply_adapter.apply(plan).status == "ok"

    verify_adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    assert verify_adapter.verify(plan).verified is True


def test_windows_snapshot_round_trips_binary_registry_values(tmp_path):
    original_palette = b"original accent palette"
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200", "AccentPalette": original_palette})
    desktop = InMemoryDesktopBackend()
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    registry.values["AccentPalette"] = b"changed accent palette"

    assert adapter.rollback(tmp_path / "backup").verified is True
    assert registry.values["AccentPalette"] == original_palette


def test_windows_rollback_restores_auto_colorization_after_wallpaper(tmp_path):
    registry = InMemoryRegistryBackend({
        "CurrentBuild": "26200",
        "AutoColorization": 1,
        "AccentColor": 123,
    })

    class AutoColorizingDesktop(InMemoryDesktopBackend):
        def set_wallpaper(self, path: str) -> bool:
            result = super().set_wallpaper(path)
            if registry.get_value("AutoColorization"):
                registry.set_value("AccentColor", 0xFFFFFFFF)
            return result

    old_wallpaper = tmp_path / "old.jpg"
    old_wallpaper.write_bytes(b"old wallpaper")
    desktop = AutoColorizingDesktop(str(old_wallpaper))
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    plan = create_plan("#FFD700", ["windows"], plan_id="plan-windows-rollback-order-001")

    assert adapter.snapshot(tmp_path / "backup").status == "ok"
    assert adapter.apply(plan).status == "partial"
    assert adapter.rollback(tmp_path / "backup").verified is True
    assert registry.values["AccentColor"] == 123


def test_windows_apply_sets_green_accent_and_taskbar_prevalence(tmp_path):
    registry = InMemoryRegistryBackend({
        "CurrentBuild": "26200",
        "AutoColorization": 1,
        "AppsUseLightTheme": 1,
        "SystemUsesLightTheme": 1,
    })
    desktop = InMemoryDesktopBackend()
    adapter = WindowsAdapter(WindowsConfig(tmp_path), registry, desktop)
    plan = create_plan("#00A86B", ["windows"], plan_id="plan-windows-accent-001")

    assert adapter.apply(plan).status == "partial"
    assert registry.values["AutoColorization"] == 1
    assert registry.values["AppsUseLightTheme"] == 1
    assert registry.values["SystemUsesLightTheme"] == 1
    assert registry.values["StartTaskbarColorPrevalence"] == 1
    assert registry.values["TitleBarColorPrevalence"] == 1
    assert registry.values["AccentColorMenu"] == windows_color_value(plan.palette["accent"])
    assert registry.values["ColorizationColor"] == windows_colorization_value(plan.palette["accent"])
    assert adapter.verify(plan).verified is True


def test_windows_accent_palette_is_an_eight_color_bgra_binary_value():
    palette = generate_accent_palette("#005436")

    assert len(palette) == 32
    assert palette[:4] == bytes((0x36, 0x54, 0x00, 0x00))


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


def test_windows_registry_writes_both_prevalence_toggles_to_distinct_paths(monkeypatch):
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
        REG_DWORD = "REG_DWORD"

        def __init__(self):
            self.writes = []

        def CreateKey(self, root, path):
            return FakeKey(self, root, path)

        def SetValueEx(self, key, name, reserved, kind, value):
            key.set_value(name, reserved, kind, value)

    fake = FakeWinreg()
    monkeypatch.setattr(windows_module, "winreg", fake)
    backend = windows_module.WindowsRegistryBackend()

    backend.set_value("StartTaskbarColorPrevalence", 1)
    backend.set_value("TitleBarColorPrevalence", 1)

    assert fake.writes == [
        ("HKCU", windows_module.PERSONALIZE_KEY, "ColorPrevalence", "REG_DWORD", 1),
        ("HKCU", windows_module.DWM_KEY, "ColorPrevalence", "REG_DWORD", 1),
    ]


def test_windows_apply_persists_an_absolute_wallpaper_path(tmp_path, monkeypatch):
    monkeypatch.chdir(tmp_path)
    registry = InMemoryRegistryBackend({"CurrentBuild": "26200"})
    desktop = InMemoryDesktopBackend()
    adapter = WindowsAdapter(WindowsConfig(Path("relative-wallpapers")), registry, desktop)
    plan = create_plan("#00A86B", ["windows"], plan_id="plan-windows-absolute-wallpaper-001")

    assert adapter.apply(plan).status == "ok"
    assert Path(desktop.wallpaper).is_absolute()
