import os
import time

import pytest

import lib.storage as storage


@pytest.fixture
def generated_dir(tmp_path, monkeypatch):
    monkeypatch.setattr(storage, "GENERATED_DIR", str(tmp_path))
    return tmp_path


def test_path_for_joins_generated_dir(generated_dir):
    assert storage.path_for("x.3mf") == os.path.join(str(generated_dir), "x.3mf")


def test_cleanup_old_files_removes_only_stale_files(generated_dir):
    old = generated_dir / "old.3mf"
    fresh = generated_dir / "fresh.3mf"
    old.write_bytes(b"")
    fresh.write_bytes(b"")
    stale = time.time() - storage.MAX_FILE_AGE - 60
    os.utime(old, (stale, stale))

    storage.cleanup_old_files()

    assert not old.exists()
    assert fresh.exists()


def test_max_file_age_is_one_hour():
    # Generated files are meant to be consumed within seconds, not archived —
    # 1h is a safety net for abandoned previews, not a retention window.
    assert storage.MAX_FILE_AGE == 3600


def test_wipe_generated_dir_removes_all_files(generated_dir):
    a = generated_dir / "a_batch.3mf"
    b = generated_dir / "b_batch_base.stl"
    a.write_bytes(b"")
    b.write_bytes(b"")

    storage.wipe_generated_dir()

    assert not a.exists()
    assert not b.exists()
    assert generated_dir.exists()  # the directory itself survives


def test_wipe_generated_dir_on_empty_dir_is_a_noop(generated_dir):
    storage.wipe_generated_dir()  # must not raise
    assert list(generated_dir.iterdir()) == []


def _capture_export(monkeypatch):
    calls = {}

    def fake_export(label_parts_list, tmf_path, **kwargs):
        calls["parts"] = label_parts_list
        calls["tmf_path"] = tmf_path
        calls.update(kwargs)

    monkeypatch.setattr(storage, "export_labels_batch", fake_export)
    return calls


def test_write_batch_session_with_text(generated_dir, monkeypatch):
    calls = _capture_export(monkeypatch)
    result = storage.write_batch_session(
        [["base", "text"]], {"width": 40, "height": 16}, "#112233", "#AABBCC"
    )

    assert result["3mf_url"].startswith("/download/")
    assert result["3mf_url"].endswith("_batch.3mf")
    assert "text_stl_url" in result
    assert result["base_color"] == "#112233"
    assert calls["label_width"] == 40.0
    assert calls["text_stl_path"] is not None


def test_write_batch_session_without_text(generated_dir, monkeypatch):
    calls = _capture_export(monkeypatch)
    result = storage.write_batch_session(
        [["base-only"]], {"width": 40, "height": 16}, "#112233", "#AABBCC"
    )

    assert "text_stl_url" not in result
    assert calls["text_stl_path"] is None
