import pytest

from lib.export import PLATE_SIZE, PLATE_SPACING, _arrange_positions

W, H, GAP = 30.0, 10.0, 2.0


def test_single_label_is_centered_on_plate():
    positions = _arrange_positions(1, W, H, GAP)
    assert positions == [((PLATE_SIZE - W) / 2, (PLATE_SIZE - H) / 2)]


def test_four_labels_form_square_grid_column_major():
    positions = _arrange_positions(4, W, H, GAP)
    assert len(positions) == 4
    # Column-major: first two fill down column 0, next two column 1.
    assert positions[0][0] == pytest.approx(positions[1][0])
    assert positions[1][1] - positions[0][1] == pytest.approx(H + GAP)
    assert positions[2][0] - positions[0][0] == pytest.approx(W + GAP)
    assert positions[2][1] == pytest.approx(positions[0][1])


def test_positions_are_unique():
    positions = _arrange_positions(25, W, H, GAP)
    assert len(set(positions)) == 25


def test_overflow_starts_new_plate():
    # 200mm labels: only one fits per 254mm plate.
    positions = _arrange_positions(3, 200.0, 200.0, GAP)
    xs = [x for x, _ in positions]
    assert xs[1] - xs[0] == pytest.approx(PLATE_SIZE + PLATE_SPACING)
    assert xs[2] - xs[1] == pytest.approx(PLATE_SIZE + PLATE_SPACING)


def test_zero_dimensions_fall_back_to_single_row():
    positions = _arrange_positions(3, 0.0, 0.0, GAP)
    assert positions == [(0.0, 0.0), (GAP, 0.0), (2 * GAP, 0.0)]


def test_grid_stays_within_plate():
    for count in (1, 2, 5, 12, 60):
        positions = _arrange_positions(count, W, H, GAP)
        for x, y in positions:
            assert 0 <= y <= PLATE_SIZE - H
            # x may move to later plates; check position within its plate
            plate_x = x % (PLATE_SIZE + PLATE_SPACING)
            assert 0 <= plate_x <= PLATE_SIZE - W
