from build123d import Align, Axis, BuildPart, BuildSketch, Locations, Plane, Rectangle, Text, export_stl, extrude

from lib.label_utils import DIVIDER_CLEARANCE, DIVIDER_WIDTH, PARAMS, build_base, divider_positions, iter_text_blocks
from lib.build_3mf import export_3mf

STYLE_ID = "debossed-open"
STYLE_NAME = "Debossed open (recessed cutout)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[str]:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]

    with BuildPart() as text_part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
            extrude(amount=-TEXT_DEPTH)
        for div_x in divider_positions(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(div_x, 0)]):
                    Rectangle(DIVIDER_WIDTH, params["height"] - 2 * DIVIDER_CLEARANCE)
            extrude(amount=-TEXT_DEPTH)

    warnings = []
    bbox = text_part.part.bounding_box()
    if bbox.size.X > params["width"]:
        warnings.append("Text overflows label width")
    if bbox.size.Y > params["height"]:
        warnings.append("Text overflows label height")

    base_with_recess = base
    for glyph in text_part.solids():
        base_with_recess = base_with_recess - glyph

    export_3mf([(base_with_recess, "base", base_color)], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    return warnings
