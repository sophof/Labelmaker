from build123d import Align, Axis, BuildPart, BuildSketch, Location, Locations, Plane, Text, Vector, export_stl, extrude

from lib.label_utils import PARAMS, build_base, iter_text_blocks
from lib.build_3mf import export_3mf

STYLE_ID = "debossed"
STYLE_NAME = "Debossed (two-color inlay)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> list[str]:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]

    # Extrude text upward (positive direction = correct outward normals)
    with BuildPart() as text_part:
        for line, x, y in iter_text_blocks(text, params):
            with BuildSketch(Plane(top_face)):
                with Locations([(x, y)]):
                    Text(line, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
            extrude(amount=TEXT_DEPTH)

    # Move the whole text compound down so it sits inside the base, flush with the top surface
    text_fill = text_part.part.moved(Location(Vector(0, 0, -TEXT_DEPTH)))

    warnings = []
    bbox = text_part.part.bounding_box()
    if bbox.size.X > params["width"]:
        warnings.append("Text overflows label width")
    if bbox.size.Y > params["height"]:
        warnings.append("Text overflows label height")

    base_with_recess = base
    for glyph in text_fill.solids():
        base_with_recess = base_with_recess - glyph

    export_3mf([(base_with_recess, "base", base_color), (text_fill, "text", text_color)], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    if text_stl_path is not None:
        export_stl(text_fill, text_stl_path)
    return warnings
