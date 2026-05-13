from build123d import Align, Axis, BuildPart, BuildSketch, Plane, Text, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.threemf import export_3mf

STYLE_ID = "debossed-open"
STYLE_NAME = "Debossed open (recessed cutout)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, base_stl_path: str, text_stl_path: str | None = None) -> None:
    base_part = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base_part.faces().sort_by(Axis.Z)[-1]

    with BuildPart() as text_part:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=-TEXT_DEPTH)

    base_with_recess = base_part.part - text_part.part

    export_3mf([(base_with_recess, "base", "#FFFFFF")], tmf_path)
    export_stl(base_with_recess, base_stl_path)
    # text_stl_path unused: open cutout has no separate text object
