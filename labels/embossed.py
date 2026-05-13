from build123d import Align, Axis, BuildPart, BuildSketch, Plane, Text, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.threemf import export_3mf

STYLE_ID = "embossed"
STYLE_NAME = "Embossed (raised text)"
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
        extrude(amount=TEXT_DEPTH)

    export_3mf([(base_part.part, "base", "#FFFFFF"), (text_part.part, "text", "#000000")], tmf_path)
    export_stl(base_part.part, base_stl_path)
    if text_stl_path is not None:
        export_stl(text_part.part, text_stl_path)
