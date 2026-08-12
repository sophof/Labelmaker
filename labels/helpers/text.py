from build123d import Align, BuildPart, BuildSketch, FontStyle, Locations, Plane, Rectangle, Text, extrude

# Gap between grid rows (created with +Row); wide enough to seat a divider.
LINE_SPACING_FACTOR = 1.3
# Gap between lines inside a single cell (in-cell "\n" / Enter); tighter, since
# these lines belong together and have no divider between them.
CELL_LINE_SPACING_FACTOR = 1.1
DIVIDER_WIDTH = 0.4
DIVIDER_CLEARANCE = 2.0

# Grid rows (created with the +Row button) are joined with this sentinel and
# draw a horizontal divider between them. A plain "\n" inside a cell is an
# in-cell line break: it stacks another centred line but draws no divider.
ROW_SEPARATOR = "\x1e"


def _parse_grid(text: str, params: dict) -> list[list[list[str]]]:
    """Return columns → rows(cells) → lines.

    Columns split on the (visible) column separator, grid rows on
    ROW_SEPARATOR, and each cell's lines on "\\n".
    """
    separator = params.get("column_separator", "")
    if separator and separator in text:
        columns = [c.strip() for c in text.split(separator)]
    else:
        columns = [text]
    return [[cell.split("\n") for cell in col.split(ROW_SEPARATOR)] for col in columns]


def _band_line_counts(grid: list[list[list[str]]], num_rows: int) -> list[int]:
    """Line count of each grid row's tallest cell, across all columns."""
    counts = []
    for r in range(num_rows):
        counts.append(max((len(col[r]) for col in grid if r < len(col)), default=0))
    return counts


def _band_layout(grid: list[list[list[str]]], params: dict):
    """Return (band_counts, band_extents, band_centers, cell_spacing).

    Every grid row is given the SAME height — that of the tallest row — so the
    rows divide the label evenly and the dividers between them stay centred,
    even when one row holds a multiline cell. Lines inside a cell are spaced by
    the tighter CELL_LINE_SPACING_FACTOR; each row adds a LINE_SPACING_FACTOR
    gap on top so its divider has room. The stack is centred on y=0.
    """
    font_size = params["font_size"]
    cell_spacing = font_size * CELL_LINE_SPACING_FACTOR

    num_rows = max((len(col) for col in grid), default=0)
    band_counts = _band_line_counts(grid, num_rows)

    row_extent = max((count - 1 for count in band_counts), default=0) * cell_spacing
    row_pitch = row_extent + font_size * LINE_SPACING_FACTOR
    centers = [(num_rows - 1) / 2 * row_pitch - r * row_pitch for r in range(num_rows)]
    extents = [row_extent] * num_rows

    return band_counts, extents, centers, cell_spacing


def iter_text_blocks(text: str, params: dict) -> list[tuple[str, float, float]]:
    """Return (line_text, x_offset, y_offset) for every rendered line.

    Grid rows stack into vertical bands (see _band_layout) so all columns share
    the same row baselines. Lines inside a multiline cell are centred within
    their band using the tighter in-cell spacing.
    """
    grid = _parse_grid(text, params)
    num_cols = len(grid)
    col_width = params["width"] / num_cols
    _, _, centers, cell_spacing = _band_layout(grid, params)

    result = []
    for r, center in enumerate(centers):
        for col_idx, col in enumerate(grid):
            x = -params["width"] / 2 + (col_idx + 0.5) * col_width
            if r >= len(col):
                continue
            cell = col[r]
            cell_extent = (len(cell) - 1) * cell_spacing
            for i, line in enumerate(cell):
                stripped = line.strip()
                if not stripped:
                    continue
                y = center + cell_extent / 2 - i * cell_spacing
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
    """Return the Y centre of each horizontal divider bar between grid rows.

    Dividers sit on the boundary between two grid rows (created with +Row),
    never between in-cell line breaks. A gap is only drawn when both adjacent
    rows have content in at least one column.
    """
    grid = _parse_grid(text, params)
    band_counts, extents, centers, _ = _band_layout(grid, params)
    num_rows = len(centers)
    if num_rows <= 1:
        return []

    def has_content(r: int) -> bool:
        return any(r < len(col) and any(ln.strip() for ln in col[r]) for col in grid)

    result = []
    for k in range(num_rows - 1):
        if has_content(k) and has_content(k + 1) and band_counts[k] and band_counts[k + 1]:
            bottom_of_k = centers[k] - extents[k] / 2
            top_of_next = centers[k + 1] + extents[k + 1] / 2
            result.append((bottom_of_k + top_of_next) / 2)
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
