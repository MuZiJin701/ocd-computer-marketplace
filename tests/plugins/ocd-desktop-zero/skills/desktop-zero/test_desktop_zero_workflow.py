from pathlib import Path

import pytest

from desktop_zero.repair import LockHolder, repair_locked_target
from desktop_zero.workflow import apply, preview, rollback, verify


def test_preview_is_read_only_and_classifies_deterministically(tmp_path):
    desktop = tmp_path / "Desktop"; desktop.mkdir()
    data = tmp_path / "data"; data.mkdir()
    (desktop / "delete.lnk").write_text("shortcut")
    (desktop / "notes.txt").write_text("notes")
    (desktop / "photo.png").write_text("image")
    (desktop / "mystery.xyz").write_text("unknown")
    (desktop / "folder").mkdir()
    (data / "文档").mkdir()
    (data / "文档" / "notes.txt").write_text("existing")

    result = preview(desktop, data, tmp_path / "plans")

    assert result["status"] == "ok"
    assert (desktop / "delete.lnk").exists()
    assert (desktop / "notes.txt").exists()
    planned = {Path(item["source"]).name: item for item in result["operations"]}
    assert planned["delete.lnk"]["kind"] == "delete_shortcut"
    assert planned["notes.txt"]["final_destination"].endswith("notes (1).txt")
    assert planned["mystery.xyz"]["category"] == "未分类"
    assert not (data / "图片" ).exists()


def test_apply_verify_and_explicit_rollback(tmp_path):
    desktop = tmp_path / "Desktop"; desktop.mkdir()
    data = tmp_path / "data"; data.mkdir()
    (desktop / "tool.py").write_text("print(1)")
    (desktop / "link.url").write_text("[InternetShortcut]")
    plan = preview(desktop, data, tmp_path / "plans")

    with pytest.raises(ValueError):
        apply(plan["plan_id"], plans_dir=tmp_path / "plans", transactions_dir=tmp_path / "tx")
    applied = apply(plan["plan_id"], True, tmp_path / "plans", tmp_path / "tx")
    assert applied["status"] == "ok"
    assert not (desktop / "link.url").exists()
    assert (data / "代码" / "tool.py").exists()
    assert verify(plan["plan_id"], tmp_path / "plans")["verified"]
    restored = rollback(applied["transaction_id"], tmp_path / "tx")
    assert restored["status"] == "ok"
    assert (desktop / "tool.py").exists()
    assert not (desktop / "link.url").exists()


def test_constrained_repair_never_closes_unknown_or_system_processes(tmp_path):
    calls = []
    result = repair_locked_target(tmp_path / "locked.txt", [
        LockHolder(1, "system", system=True, confirmed=True),
        LockHolder(None, None),
        LockHolder(2, "safe.exe", confirmed=True),
    ], lambda pid: calls.append(pid) or True, lambda holder, target: True)
    assert calls == [2]
    assert [item["status"] for item in result] == ["skipped", "skipped", "ok"]
