"""API contract tests: given a request, what status/body main.py returns.

Controller orchestration (what main.py calls into the Model layer, and when)
lives in tests/test_main.py instead.
"""
import warnings

import pytest

import labels
import main
from conftest import VALID


def test_systems_returns_hierarchy(client):
    data = client.get("/systems").json()
    ids = {s["id"] for s in data}
    assert "small-transparent-boxes" in ids
    system = next(s for s in data if s["id"] == "small-transparent-boxes")
    assert system["boxes"], "system should list at least one box"
    assert system["boxes"][0]["labels"], "box should list label styles"


def test_generate_unknown_style_is_400(client):
    resp = client.post("/generate", json={**VALID, "style_id": "nope"})
    assert resp.status_code == 400
    assert "Unknown style" in resp.json()["detail"]


def test_generate_unknown_system_is_400(client):
    resp = client.post("/generate", json={**VALID, "system_id": "nope"})
    assert resp.status_code == 400
    assert "Unknown system/box" in resp.json()["detail"]


def test_generate_unknown_box_is_400(client):
    resp = client.post("/generate", json={**VALID, "box_id": "nope"})
    assert resp.status_code == 400


def test_generate_batch_empty_is_400(client):
    resp = client.post("/generate-batch", json=[])
    assert resp.status_code == 400


def test_download_encoded_slash_never_serves_a_file(client):
    # Starlette decodes %2F before routing, so the multi-segment path falls off
    # the route entirely — the request must fail either way.
    resp = client.get("/download/sub%2Fdir.3mf")
    assert resp.status_code in (400, 404)


def test_download_rejects_dotdot_directly():
    # httpx normalizes "..%2F" away before the request is sent, so exercise
    # the endpoint function itself for the classic traversal payload.
    from fastapi import HTTPException

    with pytest.raises(HTTPException) as exc:
        main.download("../config.yaml")
    assert exc.value.status_code == 400


def test_download_missing_file_is_404(client):
    resp = client.get("/download/does-not-exist.3mf")
    assert resp.status_code == 404


def test_generate_happy_path_with_stubbed_geometry(client, monkeypatch):
    def fake_build(text, params, base_color, text_color):
        warnings.warn("Text overflows visible label width")
        return [object()]

    monkeypatch.setattr(labels.get_style("plain"), "build", fake_build)
    monkeypatch.setattr(
        main, "write_batch_session",
        lambda parts, params, base, text: {"3mf_url": "/download/x_batch.3mf"},
    )

    resp = client.post("/generate", json={**VALID, "text": "hello"})
    assert resp.status_code == 200
    body = resp.json()
    assert body["3mf_url"] == "/download/x_batch.3mf"
    assert body["warnings"] == ["Text overflows visible label width"]
