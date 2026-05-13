from build123d import Align, Axis, BuildPart, BuildSketch, Plane, Text, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.threemf import export_3mf

STYLE_ID = "embossed"
STYLE_NAME = "Embossed (raised text)"
PARAMS = PARAMS


def build(text: str, params: dict, tmf_path: str, stl_path: str) -> None:
    base_part = build_base(params)
    top_face = base_part.faces().sort_by(Axis.Z)[-1]

    with BuildPart() as text_part:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=params["text_depth"])

    export_3mf([(base_part.part, "base"), (text_part.part, "text")], tmf_path)
    export_stl(base_part.part + text_part.part, stl_path)
