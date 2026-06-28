from build123d import Align, BuildPart, BuildSketch, FontStyle, Locations, Plane, Rectangle, Text, extrude

LINE_SPACING_FACTOR = 1.3
DIVIDER_WIDTH = 0.4
DIVIDER_CLEARANCE = 2.0


def _parse_columns(text: str, params: dict) -> list[list[str]]:
    """Return a list of columns, each a list of row strings."""
    separator = params.get("column_separator", "")
    if separator and separator in text:
        columns = [c.strip() for c in text.split(separator)]
    else:
        columns = [text]
    return [col.split("\n") for col in columns]


def iter_text_blocks(text: str, params: dict) -> list[tuple[str, float, float]]:
    """Return (line_text, x_offset, y_offset) for every line in every column.

    Y positions are based on the global max row count so all columns share
    the same row baselines regardless of how many rows each column has.
    """
    font_size = params["font_size"]
    line_spacing = font_size * LINE_SPACING_FACTOR

    columns = _parse_columns(text, params)
    num_cols = len(columns)
    col_width = params["width"] / num_cols
    max_rows = max(len(rows) for rows in columns)

    result = []
    for col_idx, rows in enumerate(columns):
        x = -params["width"] / 2 + (col_idx + 0.5) * col_width
        for row_idx, line in enumerate(rows):
            stripped = line.strip()
            if not stripped:
                continue
            y = (max_rows - 1) / 2 * line_spacing - row_idx * line_spacing
            result.append((stripped, x, y))

    return result


def divider_positions(text: str, params: dict) -> list[float]:
    """Return the X centre of each vertical divider bar between columns."""
    separator = params.get("column_separator", "")
    if not separator or separator not in text:
        return []
    columns = text.split(separator)
    col_width = params["width"] / len(columns)
    return [-params["width"] / 2 + (i + 1) * col_width for i in range(len(columns) - 1)]


def divider_positions_horizontal(text: str, params: dict) -> list[float]:
    """Return the Y centre of each horizontal divider bar between rows.

    Only inserts a divider between row k and row k+1 when both rows have
    content in at least one column — empty rows don't get a divider.
    """
    font_size = params["font_size"]
    line_spacing = font_size * LINE_SPACING_FACTOR

    columns = _parse_columns(text, params)
    max_rows = max(len(rows) for rows in columns)
    if max_rows <= 1:
        return []

    result = []
    for k in range(max_rows - 1):
        above = any(k < len(col) and col[k].strip() for col in columns)
        below = any(k + 1 < len(col) and col[k + 1].strip() for col in columns)
        if above and below:
            y = (max_rows - 1) / 2 * line_spacing - k * line_spacing - line_spacing / 2
            result.append(y)
    return result


def build_text_compound(top_face, text: str, params: dict, depth: float):
    """Build text + column and row dividers extruded from top_face. depth>0 = up, <0 = down."""
    bold = params.get("bold", False)
    italic = params.get("italic", False)
    font_style = {
        (True, True): FontStyle.BOLDITALIC,
        (True, False): FontStyle.BOLD,
        (False, True): FontStyle.ITALIC,
    }.get((bold, italic), FontStyle.REGULAR)

    with BuildPart() as part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"],
                         font_style=font_style, align=(Align.CENTER, Align.CENTER))
            extrude(amount=depth)
        for div_x in divider_positions(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(div_x, 0)]):
                    Rectangle(DIVIDER_WIDTH, params["height"] - 2 * DIVIDER_CLEARANCE)
            extrude(amount=depth)
        h_clearance = max(DIVIDER_CLEARANCE, params.get("side_margin", 0))
        for div_y in divider_positions_horizontal(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(0, div_y)]):
                    Rectangle(params["width"] - 2 * h_clearance, DIVIDER_WIDTH)
            extrude(amount=depth)
    return part.part


def check_overflow(text_compound, params: dict) -> None:
    import warnings
    bbox = text_compound.bounding_box()
    margin = params.get("side_margin", 0)
    if bbox.size.X > params["width"] - 2 * margin:
        warnings.warn("Text overflows visible label width")
    if bbox.size.Y > params["height"]:
        warnings.warn("Text overflows label height")
