from build123d import Axis

from ..helpers.params import BASE_PARAMS, TEXT_PARAMS, TEXT_STYLE_OPTIONS
from ..helpers.geometry import build_base
from ..helpers.combine_geometry_and_text import combine_geometry_and_text

STYLE_ID = "label"
STYLE_NAME = "Label"

CORNER_RADIUS = 2.0
CHAMFER = 0.2
TEXT_DEPTH = 0.4

PARAMS = {
    "text_style": {
        "type": "str",
        "default": "debossed",
        "label": "Text style",
        "options": TEXT_STYLE_OPTIONS,
    },
    **TEXT_PARAMS,
    **BASE_PARAMS,
}


def build(text: str, params: dict, base_color: str = "#FFFFFF", text_color: str = "#000000") -> tuple[list[tuple], list[str]]:
    base = build_base(params, CORNER_RADIUS, CHAMFER)
    top_face = base.faces().sort_by(Axis.Z)[-1]
    return combine_geometry_and_text(base, top_face, text, params, TEXT_DEPTH, base_color, text_color)
