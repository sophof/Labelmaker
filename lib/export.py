import math

from build123d import Compound, Location, Vector, export_stl

from labels.label_style import ColoredPart
from .build_3mf import export_3mf



PLATE_SIZE = 254.0  # Bambu X1C build plate (mm)
PLATE_SPACING = 30.0  # gap between virtual plates when overflow occurs


def _arrange_positions(
    count: int,
    label_width: float,
    label_height: float,
    gap: float,
) -> list[tuple[float, float]]:
    """Return (x, y) positions for `count` labels in a square-ish grid.

    Fills the 254×254 mm build plate; overflowing labels start on a new virtual
    plate offset along X by PLATE_SIZE + PLATE_SPACING, repeating as needed.
    Each plate's grid is centered on the plate.
    """
    if label_width <= 0 or label_height <= 0:
        # Fallback: single row with gap
        return [(i * (label_width + gap), 0.0) for i in range(count)]

    cols_per_plate = max(1, int((PLATE_SIZE + gap) / (label_width + gap)))
    rows_per_plate = max(1, int((PLATE_SIZE + gap) / (label_height + gap)))
    per_plate = cols_per_plate * rows_per_plate

    # Choose column count to minimise |rows - cols| (count-based squareness).
    # Measuring in mm biases toward fewer columns for wide labels; label count
    # is a more intuitive proxy for "square arrangement".
    # Ties are broken by preferring fewer columns (taller, not wider).
    optimize_for = min(count, per_plate)
    best_cols = 1
    best_score = float("inf")
    for c in range(1, cols_per_plate + 1):
        r = math.ceil(optimize_for / c)
        if r > rows_per_plate:
            continue
        if c * label_width + (c - 1) * gap > PLATE_SIZE:
            continue
        score = abs(r - c)
        if score < best_score:  # strict: ties keep the earlier (fewer-col) winner
            best_score = score
            best_cols = c

    cols = best_cols if best_score < float("inf") else cols_per_plate

    positions: list[tuple[float, float]] = []
    plate = 0
    plate_start = 0
    while plate_start < count:
        plate_count = min(per_plate, count - plate_start)
        plate_cols = min(cols, plate_count)
        plate_rows = math.ceil(plate_count / plate_cols)

        grid_w = plate_cols * label_width + (plate_cols - 1) * gap
        grid_h = plate_rows * label_height + (plate_rows - 1) * gap
        plate_origin_x = plate * (PLATE_SIZE + PLATE_SPACING)
        # Center the grid on the plate
        origin_x = plate_origin_x + (PLATE_SIZE - grid_w) / 2
        origin_y = (PLATE_SIZE - grid_h) / 2

        for local_i in range(plate_count):
            # Column-major: fill down first, then step right
            col = local_i // plate_rows
            row = local_i % plate_rows
            x = origin_x + col * (label_width + gap)
            y = origin_y + row * (label_height + gap)
            positions.append((x, y))

        plate += 1
        plate_start += per_plate

    return positions


def export_labels_batch(
    label_parts_list: list[list[ColoredPart]],
    tmf_path: str,
    label_width: float = 0.0,
    label_height: float = 0.0,
    gap: float = 2.0,
    base_stl_path: str | None = None,
    text_stl_path: str | None = None,
) -> None:
    """Write a single 3MF with labels arranged in a square-ish grid on 254×254 mm plates.

    Optionally also writes combined base and text STLs for preview.
    """
    positions = _arrange_positions(len(label_parts_list), label_width, label_height, gap)

    all_shapes = []
    base_shapes = []
    text_shapes = []
    for i, (parts, (x, y)) in enumerate(zip(label_parts_list, positions)):
        for j, p in enumerate(parts):
            shifted = p.shape.moved(Location(Vector(x, y, 0)))
            all_shapes.append((shifted, f"label{i + 1}_{p.name}", p.color))
            if j == 0:
                base_shapes.append(shifted)
            else:
                text_shapes.append(shifted)

    export_3mf(all_shapes, tmf_path)

    if base_stl_path and base_shapes:
        export_stl(Compound(base_shapes) if len(base_shapes) > 1 else base_shapes[0], base_stl_path)
    if text_stl_path and text_shapes:
        export_stl(Compound(text_shapes) if len(text_shapes) > 1 else text_shapes[0], text_stl_path)
