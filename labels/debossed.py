from build123d import Align, Axis, BuildPart, BuildSketch, Location, Plane, Text, Vector, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.threemf import export_3mf

STYLE_ID = "debossed"
STYLE_NAME = "Debossed (two-color inlay)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, stl_path: str) -> None:
    base_part = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base_part.faces().sort_by(Axis.Z)[-1]

    # Extrude text upward (positive direction = correct outward normals)
    with BuildPart() as text_above:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=TEXT_DEPTH)

    # Move fill piece down so it sits inside the base, flush with the top surface
    text_fill = text_above.part.moved(Location(Vector(0, 0, -TEXT_DEPTH)))

    base_with_recess = base_part.part - text_fill

    export_3mf([(base_with_recess, "base"), (text_fill, "text")], tmf_path)
    export_stl(base_with_recess, stl_path)
