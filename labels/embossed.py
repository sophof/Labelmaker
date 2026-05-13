from build123d import Align, Axis, BuildPart, BuildSketch, Plane, Text, export_stl, extrude

from lib.label_utils import PARAMS, build_base
from lib.build_3mf import export_3mf

STYLE_ID = "embossed"
STYLE_NAME = "Embossed (raised text)"
PARAMS = PARAMS

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4


def build(text: str, params: dict, tmf_path: str, base_stl_path: str,
          text_stl_path: str | None = None, base_color: str = "#FFFFFF", text_color: str = "#000000") -> None:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]

    with BuildPart() as text_part:
        with BuildSketch(Plane(top_face)):
            Text(text, font_size=params["font_size"], font=params["font"], align=(Align.CENTER, Align.CENTER))
        extrude(amount=TEXT_DEPTH)
    txt = text_part.part  # Compound of per-glyph solids — exported as one mesh

    export_3mf([(base, "base", base_color), (txt, "text", text_color)], tmf_path)
    export_stl(base, base_stl_path)
    if text_stl_path is not None:
        export_stl(txt, text_stl_path)
