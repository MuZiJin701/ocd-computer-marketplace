import pytest

import one_tone.storage as storage


def test_atomic_write_text_preserves_original_when_replace_fails(tmp_path, monkeypatch):
    path = tmp_path / "state.json"
    path.write_text("original", encoding="utf-8")

    def fail_replace(source, destination):
        raise OSError("forced replace failure")

    monkeypatch.setattr(storage.os, "replace", fail_replace)

    with pytest.raises(OSError, match="forced replace failure"):
        storage.atomic_write_text(path, "updated")

    assert path.read_text(encoding="utf-8") == "original"
    assert not list(tmp_path.glob(".state.json.*.tmp"))
