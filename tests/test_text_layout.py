import pytest

from labels.helpers.text import (
    CELL_LINE_SPACING_FACTOR,
    LINE_SPACING_FACTOR,
    ROW_SEPARATOR,
    _parse_grid,
    divider_positions,
    divider_positions_horizontal,
    iter_text_blocks,
)

PARAMS = {"width": 60.0, "height": 20.0, "font_size": 6.0, "column_separator": "|"}
LINE_SPACING = PARAMS["font_size"] * LINE_SPACING_FACTOR   # gap between grid rows
CELL_SPACING = PARAMS["font_size"] * CELL_LINE_SPACING_FACTOR  # in-cell line gap
RS = ROW_SEPARATOR


# --- _parse_grid: columns -> rows(cells) -> lines ---

def test_parse_grid_columns_and_rows():
    assert _parse_grid(f"a{RS}b|c", PARAMS) == [[["a"], ["b"]], [["c"]]]


def test_parse_grid_in_cell_newline_is_a_multiline_cell():
    # A bare '\n' is an in-cell line break: one column, one cell, two lines.
    assert _parse_grid("a\nb", PARAMS) == [[["a", "b"]]]


def test_parse_grid_rows_and_in_cell_lines_together():
    # Column 0 has two grid rows; its first cell is multiline.
    assert _parse_grid(f"a\nb{RS}c|d", PARAMS) == [[["a", "b"], ["c"]], [["d"]]]


def test_parse_grid_empty_separator_never_splits():
    params = {**PARAMS, "column_separator": ""}
    assert _parse_grid("a|b", params) == [[["a|b"]]]


def test_parse_grid_strips_whitespace_around_separator():
    assert _parse_grid("a | b", PARAMS) == [[["a"]], [["b"]]]


# --- iter_text_blocks ---

def test_single_line_is_centered():
    assert iter_text_blocks("hello", PARAMS) == [("hello", 0.0, 0.0)]


def test_in_cell_two_lines_share_vertical_symmetry():
    blocks = iter_text_blocks("a\nb", PARAMS)
    assert [(t, x) for t, x, _ in blocks] == [("a", 0.0), ("b", 0.0)]
    ys = [y for _, _, y in blocks]
    # In-cell lines use the tighter CELL_SPACING, not the grid-row LINE_SPACING.
    assert ys[0] == pytest.approx(CELL_SPACING / 2)
    assert ys[1] == pytest.approx(-CELL_SPACING / 2)


def test_in_cell_spacing_is_tighter_than_grid_row_spacing():
    in_cell = iter_text_blocks("a\nb", PARAMS)
    grid_rows = iter_text_blocks(f"a{RS}b", PARAMS)
    in_cell_gap = in_cell[0][2] - in_cell[1][2]
    grid_row_gap = grid_rows[0][2] - grid_rows[1][2]
    assert in_cell_gap < grid_row_gap
    assert in_cell_gap == pytest.approx(CELL_SPACING)
    assert grid_row_gap == pytest.approx(LINE_SPACING)


def test_line_spacing_param_overrides_default():
    tight = iter_text_blocks("a\nb", {**PARAMS, "line_spacing": 0.8})
    wide = iter_text_blocks("a\nb", {**PARAMS, "line_spacing": 1.5})
    tight_gap = tight[0][2] - tight[1][2]
    wide_gap = wide[0][2] - wide[1][2]
    assert tight_gap == pytest.approx(PARAMS["font_size"] * 0.8)
    assert wide_gap == pytest.approx(PARAMS["font_size"] * 1.5)
    assert tight_gap < wide_gap


def test_line_spacing_defaults_to_constant_when_absent():
    # PARAMS carries no line_spacing, so the CELL_LINE_SPACING_FACTOR default applies.
    blocks = iter_text_blocks("a\nb", PARAMS)
    gap = blocks[0][2] - blocks[1][2]
    assert gap == pytest.approx(PARAMS["font_size"] * CELL_LINE_SPACING_FACTOR)


def test_grid_two_rows_share_vertical_symmetry():
    blocks = iter_text_blocks(f"a{RS}b", PARAMS)
    ys = [y for _, _, y in blocks]
    assert ys[0] == pytest.approx(LINE_SPACING / 2)
    assert ys[1] == pytest.approx(-LINE_SPACING / 2)


def test_columns_are_horizontally_centered_per_column():
    blocks = iter_text_blocks("a|b", PARAMS)
    xs = [x for _, x, _ in blocks]
    assert xs[0] == pytest.approx(-15.0)  # centre of left half of 60mm
    assert xs[1] == pytest.approx(15.0)


def test_columns_share_row_baselines():
    # Left column has 2 grid rows, right column 1: right's row 0 sits on the
    # same baseline as left's row 0 (global row bands drive Y).
    blocks = {t: y for t, _, y in iter_text_blocks(f"a{RS}b|c", PARAMS)}
    assert blocks["c"] == pytest.approx(blocks["a"])


def test_two_row_divider_stays_centred_with_a_multiline_cell():
    # Reproduces the off-centre divider from the 2x2 label: the top-right cell
    # is two lines ("test"/"hoi"). Grid rows must be equal height so the divider
    # sits on the label centre (y=0), not pushed down by the taller row.
    text = f"test{RS}test|test\nhoi{RS}"
    assert divider_positions_horizontal(text, PARAMS) == [pytest.approx(0.0)]


def test_equal_row_heights_are_symmetric_about_centre():
    # Row 0 is a 2-line cell, row 1 a single line. With equal-height rows the
    # two band centres are mirror images about y=0, not weighted toward the
    # taller row.
    ys = {t: y for t, _, y in iter_text_blocks(f"A\nB{RS}Z", PARAMS)}
    row0_centre = (ys["A"] + ys["B"]) / 2
    row1_centre = ys["Z"]
    assert row0_centre == pytest.approx(-row1_centre)


def test_blank_line_within_cell_keeps_its_slot():
    blocks = iter_text_blocks("a\n\nc", PARAMS)
    assert [t for t, _, _ in blocks] == ["a", "c"]
    ys = [y for _, _, y in blocks]
    assert ys[0] - ys[1] == pytest.approx(2 * CELL_SPACING)


def test_multiline_cell_then_grid_row_stacks_all_lines():
    # Both grid rows are equal height (that of the 2-line row). Row 0's two
    # lines use the tight CELL_SPACING; row 1's single line sits at the mirror
    # centre of row 0's midpoint.
    blocks = iter_text_blocks(f"x\ny{RS}z", PARAMS)
    ys = {t: y for t, _, y in blocks}
    assert ys["x"] == pytest.approx(LINE_SPACING / 2 + CELL_SPACING)
    assert ys["y"] == pytest.approx(LINE_SPACING / 2)
    assert ys["z"] == pytest.approx(-LINE_SPACING / 2 - CELL_SPACING / 2)


# --- divider_positions (vertical, between columns) ---

def test_no_vertical_divider_without_separator():
    assert divider_positions("hello", PARAMS) == []


def test_vertical_divider_between_two_equal_columns():
    assert divider_positions("a|b", PARAMS) == [pytest.approx(0.0)]


def test_vertical_dividers_for_three_columns():
    positions = divider_positions("a|b|c", PARAMS)
    assert positions == [pytest.approx(-10.0), pytest.approx(10.0)]


# --- divider_positions_horizontal (between grid rows only) ---

def test_no_horizontal_divider_for_multiline_single_cell():
    # KEY: in-cell newlines must NOT draw a divider.
    assert divider_positions_horizontal("a\nb", PARAMS) == []


def test_no_horizontal_divider_for_single_grid_row():
    assert divider_positions_horizontal("a|b", PARAMS) == []


def test_horizontal_divider_between_two_grid_rows():
    assert divider_positions_horizontal(f"a{RS}b", PARAMS) == [pytest.approx(0.0)]


def test_horizontal_divider_centred_with_multiline_first_row():
    # Row 0 is a 2-line cell, row 1 a single line. Equal-height rows keep the
    # divider on the centre line (y=0), not pushed down by the taller row.
    positions = divider_positions_horizontal(f"x\ny{RS}z", PARAMS)
    assert positions == [pytest.approx(0.0)]


def test_no_horizontal_divider_next_to_empty_grid_row():
    assert divider_positions_horizontal(f"a{RS}{RS}c", PARAMS) == []


def test_horizontal_divider_when_any_column_fills_both_rows():
    positions = divider_positions_horizontal(f"a|b{RS}c", PARAMS)
    assert positions == [pytest.approx(0.0)]
