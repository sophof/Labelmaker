"""Geometry smoke tests — build real build123d solids. Run with the full suite:
`.venv/bin/pytest` (excluded from the fast loop via `-m "not slow"`).
"""
import os
import zipfile

import pytest
from fastapi.testclient import TestClient

import labels
import main

pytestmark = pytest.mark.slow

PARAMS = {
    "width": 40.0, "height": 16.0, "depth": 1.0, "side_margin": 2,
    "font": "DejaVu Sans", "bold": False, "italic": False,
    "font_size": 6.0, "column_separator": "|",
}


def _build(style_id, text, text_style):
    style = labels.get_style(style_id)
    return style.build(text, {**PARAMS, "text_style": text_style}, "#112233", "#AABBCC")


def _names(parts):
    return [p.name for p in parts]


def assert_solid_parts(parts):
    for p in parts:
        assert p.shape.volume > 0, f"part {p.name} has no volume"


def test_plain_embossed_has_base_and_text():
    parts = _build("plain", "AB", "embossed")
    assert _names(parts) == ["base", "text"]
    assert_solid_parts(parts)


def test_plain_debossed_has_base_and_text():
    parts = _build("plain", "AB", "debossed")
    assert _names(parts) == ["base", "text"]
    assert_solid_parts(parts)


def test_plain_debossed_open_omits_text_part():
    parts = _build("plain", "AB", "debossed-open")
    assert _names(parts) == ["base"]
    # The glyphs must actually be carved out of the base.
    solid_base = _build("plain", "", "debossed-open")[0]
    assert parts[0].shape.volume < solid_base.shape.volume


def test_plain_empty_text_is_base_only():
    parts = _build("plain", "", "debossed")
    assert _names(parts) == ["base"]
    assert_solid_parts(parts)


def test_bordered_adds_accent_ring():
    parts = _build("bordered", "AB", "debossed")
    assert _names(parts) == ["base", "border", "text"]
    assert_solid_parts(parts)


def test_generate_end_to_end_writes_colored_3mf():
    with TestClient(main.app) as client:
        resp = client.post("/generate", json={
            "system_id": "small-transparent-boxes",
            "box_id": "standard-box",
            "style_id": "plain",
            "text": "A",
            "font": "DejaVu Sans",
            "font_size": 6.0,
            "text_style": "debossed",
            "base_color": "#112233",
            "text_color": "#AABBCC",
        })
        assert resp.status_code == 200
        url = resp.json()["3mf_url"]
        path = os.path.join("generated", url.removeprefix("/download/"))

        with zipfile.ZipFile(path) as zf:
            model = zf.read("3D/3dmodel.model").decode()
        assert "<m:colorgroup" in model
        assert '#112233FF' in model
        assert '#AABBCCFF' in model

        # Downloading no longer deletes the file — cleanup is startup wipe +
        # the 1h age sweep only, not tied to individual downloads.
        assert client.get(url).status_code == 200
        assert os.path.exists(path)
