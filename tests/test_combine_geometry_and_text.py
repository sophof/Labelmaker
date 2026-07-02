"""Fast tests for the non-geometry branches of combine_geometry_and_text.

The embossed/debossed branches build real solids and are covered by the slow
geometry smoke tests.
"""
import warnings

from labels.helpers.combine_geometry_and_text import combine_geometry_and_text
from labels.label_style import ColoredPart

BASE = object()
TOP_FACE = object()


def test_empty_text_returns_base_only():
    parts = combine_geometry_and_text(BASE, TOP_FACE, "   ", {}, "#111111", "#222222")
    assert [(p.shape, p.name, p.color) for p in parts] == [(BASE, "base", "#111111")]


def test_empty_text_keeps_accent_components():
    accent = ColoredPart(object(), "border", "#333333")
    parts = combine_geometry_and_text(
        BASE, TOP_FACE, "", {}, "#111111", "#222222", accent_components=[accent]
    )
    assert parts == [ColoredPart(BASE, "base", "#111111"), accent]


def test_unknown_text_style_warns_and_returns_nothing():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        parts = combine_geometry_and_text(
            BASE, TOP_FACE, "hello", {"text_style": "sparkly"}, "#111111", "#222222"
        )
    assert parts == []
    assert any("Unknown text style" in str(w.message) for w in caught)
