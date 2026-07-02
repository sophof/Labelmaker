from unittest.mock import MagicMock

from labels.label import Label


def _label(**overrides):
    defaults = dict(
        style=MagicMock(),
        box_params={"width": 41.4, "height": 16.0, "depth": 1.0, "side_margin": 3},
        text="hello",
        font="Arial",
        bold=True,
        italic=False,
        font_size=6.0,
        text_style="debossed",
        base_color="#FF6600",
        text_color="#000000",
        column_separator="|",
    )
    return Label(**{**defaults, **overrides})


def test_params_merges_box_and_text_settings():
    params = _label().params()
    assert params["width"] == 41.4
    assert params["side_margin"] == 3
    assert params["font"] == "Arial"
    assert params["text_style"] == "debossed"
    assert params["column_separator"] == "|"


def test_label_font_size_overrides_box_font_size():
    label = _label(
        box_params={"width": 41.4, "height": 16.0, "depth": 1.0, "font_size": 4.0},
        font_size=8.0,
    )
    assert label.params()["font_size"] == 8.0
