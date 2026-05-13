from build123d import Align, Axis, BuildPart, BuildSketch, Location, Plane, Text, Vector, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.threemf import export_3mf

STYLE_ID = "debossed"
STYLE_NAME = "Debossed (two-color inlay)"
PARAMS = PARAMS


def build(text: str, params: dict, tmf_path: str, stl_path: str) -> None:
    base_part = build_base(params)
    top_face = base_part.faces().sort_by(Axis.Z)[-1]

    # Extrude text upward (positive direction = correct outward normals)
    with BuildPart() as text_above:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=params["text_depth"])

    # Move fill piece down so it sits inside the base, flush with the top surface
    text_fill = text_above.part.moved(Location(Vector(0, 0, -params["text_depth"])))

    base_with_recess = base_part.part - text_fill

    export_3mf([(base_with_recess, "base"), (text_fill, "text")], tmf_path)
    export_stl(base_with_recess, stl_path)
