from build123d import Align, Axis, BuildPart, BuildSketch, Location, Plane, Text, Vector, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.build_3mf import export_3mf

STYLE_ID = "debossed"
STYLE_NAME = "Debossed (two-color inlay)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> None:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]

    # Extrude text upward (positive direction = correct outward normals)
    with BuildPart() as text_part:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=TEXT_DEPTH)

    # Move the whole text compound down so it sits inside the base, flush with the top surface
    text_fill = text_part.part.moved(Location(Vector(0, 0, -TEXT_DEPTH)))

    # Subtract each glyph solid individually — safe regardless of whether
    # OCC's BooleanCut handles Compound tools correctly
    base_with_recess = base
    for glyph in text_fill.solids():
        base_with_recess = base_with_recess - glyph

    export_3mf([(base_with_recess, "base", base_color), (text_fill, "text", text_color)], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    if text_stl_path is not None:
        export_stl(text_fill, text_stl_path)
