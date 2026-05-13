from build123d import Align, Axis, BuildPart, BuildSketch, Compound, Location, Locations, Plane, Rectangle, RectangleRounded, Solid, Text, Vector, chamfer, export_stl, extrude

from lib.build_3mf import export_3mf

FONTS = ["Impact", "Arial", "DejaVu Sans", "Liberation Sans", "Verdana", "Courier New"]

TEXT_PARAMS = {
    "font":             {"type": "str",   "default": "Impact", "label": "Font", "options": FONTS},
    "font_size":        {"type": "float", "default": 6.0,  "unit": "mm", "label": "Font size"},
    "column_separator": {"type": "str",   "default": "|",   "label": "Column separator"},
}

BASE_PARAMS = {
    "width":  {"type": "float", "default": 60.0, "unit": "mm", "label": "Width"},
    "height": {"type": "float", "default": 20.0, "unit": "mm", "label": "Height"},
    "depth":  {"type": "float", "default": 1.0,  "unit": "mm", "label": "Depth"},
}

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


def apply_text_and_export(
    base, top_face, text: str, params: dict, text_depth: float,
    tmf_path: str, base_stl_path: str, text_stl_path: str | None,
    base_color: str, text_color: str,
    accent_components: list | None = None,
) -> list[str]:
    """Apply text to base and export. accent_components are extra (shape, name, color) tuples
    added to the 3MF alongside the text component (e.g. a ring fill for the bordered style)."""
    style = params.get("text_style", "debossed")
    accents = accent_components or []
    accent_shapes = [c[0] for c in accents]

    def export_accent_stl(text_shape=None):
        shapes = [*accent_shapes, text_shape] if text_shape is not None else accent_shapes
        if shapes and text_stl_path is not None:
            export_stl(Compound(shapes) if len(shapes) > 1 else shapes[0], text_stl_path)

    if style == "embossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        warnings = overflow_warnings(txt, params)
        export_3mf([(base, "base", base_color)] + accents + [(txt, "text", text_color)], tmf_path)
        export_stl(base, base_stl_path)
        export_accent_stl(txt)

    elif style == "debossed":
        txt = build_text_compound(top_face, text, params, text_depth)
        text_fill = txt.moved(Location(Vector(0, 0, -text_depth)))
        warnings = overflow_warnings(txt, params)
        base_carved = base
        for glyph in text_fill.solids():
            base_carved = base_carved - glyph
        export_3mf([(base_carved, "base", base_color)] + accents + [(text_fill, "text", text_color)], tmf_path)
        export_stl(base_carved, base_stl_path)
        export_accent_stl(text_fill)

    elif style == "debossed-open":
        txt = build_text_compound(top_face, text, params, -text_depth)
        warnings = overflow_warnings(txt, params)
        base_carved = base
        for glyph in txt.solids():
            base_carved = base_carved - glyph
        export_3mf([(base_carved, "base", base_color)] + accents, tmf_path)
        export_stl(base_carved, base_stl_path)
        export_accent_stl()  # accent only, no text fill

    else:
        return [f"Unknown text style: {style}"]

    return warnings


def build_base(params: dict, corner_radius: float, chamfer_size: float) -> Solid:
    with BuildPart() as base_part:
        with BuildSketch():
            RectangleRounded(params["width"], params["height"], corner_radius)
        extrude(amount=params["depth"])
        top_edges = base_part.faces().sort_by(Axis.Z)[-1].edges()
        bot_edges = base_part.faces().sort_by(Axis.Z)[0].edges()
        chamfer(top_edges + bot_edges, length=chamfer_size)
    return base_part.solids()[0]
