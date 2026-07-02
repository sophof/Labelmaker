import labels
from labels.label_style import LabelStyle


def test_builtin_styles_are_discovered():
    for style_id in ("plain", "bordered"):
        style = labels.get_style(style_id)
        assert isinstance(style, LabelStyle)
        assert style.STYLE_ID == style_id


def test_unknown_style_returns_none():
    assert labels.get_style("does-not-exist") is None


def test_all_styles_shape():
    styles = labels.all_styles()
    assert "plain" in styles
    for entry in styles.values():
        assert set(entry) == {"name", "params"}
        # Every style must expose the core schema keys the UI relies on.
        assert {"text_style", "font", "font_size", "width", "height", "depth"} <= set(entry["params"])
        for schema in entry["params"].values():
            assert "default" in schema
            assert "label" in schema
