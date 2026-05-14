from build123d import Align, BuildPart, BuildSketch, Locations, Plane, Rectangle, Text, extrude

LINE_SPACING_FACTOR = 1.3
DIVIDER_WIDTH = 0.4
DIVIDER_CLEARANCE = 2.0


def iter_text_blocks(text: str, params: dict) -> list[tuple[str, float, float]]:
    """Return (line_text, x_offset, y_offset) for every line in every column."""
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


def divider_positions(text: str, params: dict) -> list[float]:
    """Return the X centre of each vertical divider bar between columns."""
    separator = params.get("column_separator", "")
    if not separator or separator not in text:
        return []
    columns = text.split(separator)
    col_width = params["width"] / len(columns)
    return [-params["width"] / 2 + (i + 1) * col_width for i in range(len(columns) - 1)]


def build_text_compound(top_face, text: str, params: dict, depth: float):
    """Build text + column dividers extruded from top_face. depth>0 = up, <0 = down."""
    with BuildPart() as part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"],
                         align=(Align.CENTER, Align.CENTER))
            extrude(amount=depth)
        for div_x in divider_positions(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(div_x, 0)]):
                    Rectangle(DIVIDER_WIDTH, params["height"] - 2 * DIVIDER_CLEARANCE)
            extrude(amount=depth)
    return part.part


def overflow_warnings(text_compound, params: dict) -> list[str]:
    warnings = []
    bbox = text_compound.bounding_box()
    if bbox.size.X > params["width"]:
        warnings.append("Text overflows label width")
    if bbox.size.Y > params["height"]:
        warnings.append("Text overflows label height")
    return warnings
