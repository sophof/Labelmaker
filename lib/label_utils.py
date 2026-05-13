from build123d import Axis, BuildPart, BuildSketch, RectangleRounded, Solid, chamfer, extrude

FONTS = ["Impact", "Arial", "DejaVu Sans", "Liberation Sans", "Verdana", "Courier New"]

PARAMS = {
    "font":             {"type": "str",   "default": "Impact", "label": "Font", "options": FONTS},
    "font_size":        {"type": "float", "default": 6.0,  "unit": "mm", "label": "Font size"},
    "width":            {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height":           {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":            {"type": "float", "default": 1.0,  "unit": "mm", "label": "Depth"},
    "column_separator": {"type": "str",   "default": "|",   "label": "Column separator"},
}

LINE_SPACING_FACTOR = 1.3


def iter_text_blocks(text: str, params: dict) -> list[tuple[str, float, float]]:
    """Return (line_text, x_offset, y_offset) for every line in every column.

    Splits on column_separator first (if set), then on newlines within each column.
    All offsets are relative to the label center.
    """
    separator = params.get("column_separator", "")
    font_size = params["font_size"]
    line_spacing = font_size * LINE_SPACING_FACTOR

    if separator and separator in text:
        columns = [c.strip() for c in text.split(separator)]
    else:
        columns = [text]

    num_cols = len(columns)
    col_width = params["width"] / num_cols

    result = []
    for col_idx, col_text in enumerate(columns):
        x = -params["width"] / 2 + (col_idx + 0.5) * col_width

        lines = col_text.split("\n")
        num_lines = len(lines)
        for line_idx, line in enumerate(lines):
            y = (num_lines - 1) / 2 * line_spacing - line_idx * line_spacing
            result.append((line.strip(), x, y))

    return result


DIVIDER_WIDTH = 0.4
DIVIDER_CLEARANCE = 2.0


def divider_positions(text: str, params: dict) -> list[float]:
    """Return the X centre of each vertical divider bar between columns."""
    separator = params.get("column_separator", "")
    if not separator or separator not in text:
        return []
    columns = text.split(separator)
    num_cols = len(columns)
    col_width = params["width"] / num_cols
    return [-params["width"] / 2 + (i + 1) * col_width for i in range(num_cols - 1)]


def build_base(params: dict, corner_radius: float, chamfer_size: float) -> Solid:
    with BuildPart() as base_part:
        with BuildSketch():
            RectangleRounded(params["width"], params["height"], corner_radius)
        extrude(amount=params["depth"])
        top_edges = base_part.faces().sort_by(Axis.Z)[-1].edges()
        bot_edges = base_part.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edges + bot_edges, length=chamfer_size)
    return base_part.solids()[0]
