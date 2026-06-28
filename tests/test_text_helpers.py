import warnings
from unittest.mock import MagicMock

from labels.helpers.text import check_overflow


def _compound(x, y):
    """Return a fake text compound whose bounding box reports size (x, y)."""
    bbox = MagicMock()
    bbox.size.X = x
    bbox.size.Y = y
    c = MagicMock()
    c.bounding_box.return_value = bbox
    return c


PARAMS = {"width": 60.0, "height": 20.0}


def test_no_warning_when_text_fits():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_overflow(_compound(50, 15), PARAMS)
    assert caught == []


def test_warns_when_text_too_wide():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_overflow(_compound(61, 15), PARAMS)
    messages = [str(w.message) for w in caught]
    assert any("width" in m for m in messages)


def test_warns_when_text_too_tall():
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        check_overflow(_compound(50, 21), PARAMS)
    messages = [str(w.message) for w in caught]
    assert any("height" in m for m in messages)
