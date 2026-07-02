"""Controller orchestration tests: does main.py call the right Model-layer
function (lib/storage.py) at the right time? These assert on side effects
(filesystem state), not on the HTTP response — HTTP is just the trigger.

Pure API contract tests (status codes, response shapes) live in test_api.py.
"""
import os
import time

from fastapi.testclient import TestClient

import labels
import lib.storage as storage
import main
from conftest import VALID


def test_startup_wipes_generated_dir(tmp_path, monkeypatch):
    # Nothing should survive a restart — verify the lifespan wipe is actually
    # wired up, not just that wipe_generated_dir() works in isolation.
    monkeypatch.setattr(storage, "GENERATED_DIR", str(tmp_path))
    leftover = tmp_path / "leftover_batch.3mf"
    leftover.write_bytes(b"")

    with TestClient(main.app):
        pass

    assert not leftover.exists()


def test_generate_sweeps_files_older_than_max_age(client, monkeypatch, tmp_path):
    # Verifies the time-based safety net actually fires through the live
    # /generate endpoint, not just when cleanup_old_files() is called directly.
    monkeypatch.setattr(storage, "GENERATED_DIR", str(tmp_path))
    stale = tmp_path / "stale_batch.3mf"
    fresh = tmp_path / "fresh_batch.3mf"
    stale.write_bytes(b"")
    fresh.write_bytes(b"")
    stale_time = time.time() - storage.MAX_FILE_AGE - 60
    os.utime(stale, (stale_time, stale_time))

    monkeypatch.setattr(labels.get_style("plain"), "build", lambda *a, **k: [object()])
    monkeypatch.setattr(
        main, "write_batch_session",
        lambda parts, params, base, text: {"3mf_url": "/download/x_batch.3mf"},
    )

    client.post("/generate", json={**VALID, "text": "hi"})

    assert not stale.exists()
    assert fresh.exists()
