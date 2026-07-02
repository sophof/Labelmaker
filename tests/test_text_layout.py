import pytest

from labels.helpers.text import (
    LINE_SPACING_FACTOR,
    _parse_columns,
    divider_positions,
    divider_positions_horizontal,
    iter_text_blocks,
)

PARAMS = {"width": 60.0, "height": 20.0, "font_size": 6.0, "column_separator": "|"}
LINE_SPACING = PARAMS["font_size"] * LINE_SPACING_FACTOR


# --- _parse_columns ---

def test_parse_columns_column_major():
    assert _parse_columns("a\nb|c", PARAMS) == [["a", "b"], ["c"]]


def test_parse_columns_no_separator_in_text():
    assert _parse_columns("a\nb", PARAMS) == [["a", "b"]]


def test_parse_columns_empty_separator_never_splits():
    params = {**PARAMS, "column_separator": ""}
    assert _parse_columns("a|b", params) == [["a|b"]]


def test_parse_columns_strips_whitespace_around_separator():
    assert _parse_columns("a | b", PARAMS) == [["a"], ["b"]]


# --- iter_text_blocks ---

def test_single_line_is_centered():
    assert iter_text_blocks("hello", PARAMS) == [("hello", 0.0, 0.0)]


def test_two_rows_share_vertical_symmetry():
    blocks = iter_text_blocks("a\nb", PARAMS)
    assert [(t, x) for t, x, _ in blocks] == [("a", 0.0), ("b", 0.0)]
    ys = [y for _, _, y in blocks]
    assert ys[0] == pytest.approx(LINE_SPACING / 2)
    assert ys[1] == pytest.approx(-LINE_SPACING / 2)


def test_columns_are_horizontally_centered_per_column():
    blocks = iter_text_blocks("a|b", PARAMS)
    xs = [x for _, x, _ in blocks]
    assert xs[0] == pytest.approx(-15.0)  # centre of left half of 60mm
    assert xs[1] == pytest.approx(15.0)


def test_columns_share_row_baselines():
    # Left column has 2 rows, right column 1 row: right's row 0 must sit on
    # the same baseline as left's row 0 (global max_rows drives Y).
    blocks = {t: y for t, _, y in iter_text_blocks("a\nb|c", PARAMS)}
    assert blocks["c"] == pytest.approx(blocks["a"])


def test_blank_lines_are_skipped_but_keep_row_position():
    blocks = iter_text_blocks("a\n\nc", PARAMS)
    assert [t for t, _, _ in blocks] == ["a", "c"]
    ys = [y for _, _, y in blocks]
    assert ys[0] - ys[1] == pytest.approx(2 * LINE_SPACING)


# --- divider_positions (vertical, between columns) ---

def test_no_vertical_divider_without_separator():
    assert divider_positions("hello", PARAMS) == []


def test_vertical_divider_between_two_equal_columns():
    assert divider_positions("a|b", PARAMS) == [pytest.approx(0.0)]


def test_vertical_dividers_for_three_columns():
    positions = divider_positions("a|b|c", PARAMS)
    assert positions == [pytest.approx(-10.0), pytest.approx(10.0)]


# --- divider_positions_horizontal (between rows) ---

def test_no_horizontal_divider_for_single_row():
    assert divider_positions_horizontal("a|b", PARAMS) == []


def test_horizontal_divider_between_two_full_rows():
    assert divider_positions_horizontal("a\nb", PARAMS) == [pytest.approx(0.0)]


def test_no_horizontal_divider_next_to_empty_row():
    # Row 1 is blank in every column, so neither gap gets a divider.
    assert divider_positions_horizontal("a\n\nc", PARAMS) == []


def test_horizontal_divider_when_any_column_fills_both_rows():
    # Right column has content in both rows, so the divider spans the label.
    positions = divider_positions_horizontal("a|b\nc", PARAMS)
    assert positions == [pytest.approx(0.0)]
